#!/usr/bin/env python

import argparse
import getpass
import logging
import multiprocessing
import sys
import time
from functools import wraps

import pymongo
from sqlalchemy import create_engine

from wordprofile.wpse.db_tables import insert_concord_sentences, get_relation_id, insert_matches, \
    insert_corpus_file, get_corpus_file_id
from wordprofile.zdl import extract_matches_from_document, ConllToken


def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
        exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """

    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


@retry(Exception, tries=3, delay=7)
def process_files_parallel(mongo_db_keys, db_engine_key, doc_id):
    mongo_db = pymongo.MongoClient(mongo_db_keys[0])[mongo_db_keys[1]]
    engine = create_engine(db_engine_key,
                           pool_size=16, max_overflow=32)

    doc = mongo_db["documents"].find_one({'_id': doc_id})
    if get_corpus_file_id(engine, doc):
        print("({}) - SKIP document already in db".format(doc['basename']))
    else:
        parses = [[ConllToken(*[token[f] for f in ConllToken._fields]) for token in sentence]
                  for sentence in doc["sentences"]]
        print("({}) - load document".format(doc['basename']))
        corpus_file_id = insert_corpus_file(engine, doc)
        insert_concord_sentences(engine, corpus_file_id, parses)
        matches = extract_matches_from_document(parses)
        print("({}) - extracted matches".format(doc['basename']))
        matches = {get_relation_id(engine, ms[0]): ms for _, ms in matches.items() if ms}
        for relation_id, relation_matches in matches.items():
            insert_matches(engine, corpus_file_id, relation_id, relation_matches)
        print("({}) - inserted matches".format(doc['basename']))


def main():
    lformat = '[%(levelname)s] %(asctime)s %(name)s# %(message)s'
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=lformat)
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", type=str, help="database username", required=True)
    parser.add_argument("--mariadb", type=str, help="database name", required=True)
    parser.add_argument("--mongodb", type=str, help="database name", required=True)
    parser.add_argument("--passwd", action="store_true", help="ask for database password")
    parser.add_argument("--jobs", help="", type=int, default=1)
    args = parser.parse_args()

    print('|: user: ' + args.user)
    print('|: db: ' + args.mariadb)
    if args.passwd:
        db_password = getpass.getpass("db password: ")
    else:
        db_password = args.user
    db_engine_key = 'mysql+pymysql://{}:{}@localhost/{}'.format(args.user, db_password, args.mariadb)

    mongo_db_keys = ("mongodb://localhost:27017/", args.mongodb)
    mongo_db = pymongo.MongoClient(mongo_db_keys[0])[mongo_db_keys[1]]

    document_ids = mongo_db["documents"].find().distinct('_id')
    print("Found documents:", len(document_ids))
    files = [(mongo_db_keys, db_engine_key, doc_id) for doc_id in document_ids]
    print("Create MPPool with #njobs:", args.jobs)
    with multiprocessing.Pool(args.jobs) as pool:
        pool.starmap(process_files_parallel, files, chunksize=10)


if __name__ == '__main__':
    main()
