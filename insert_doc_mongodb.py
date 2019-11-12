#!/usr/bin/env python

import argparse
import getpass
import logging
import multiprocessing
import sys

import pymongo
from sqlalchemy import create_engine
from wordprofile.wpse.db_tables import insert_concord_sentences, get_relation_id, insert_matches, \
    insert_corpus_file, get_corpus_file_id
from wordprofile.zdl import extract_matches_from_document, ConllToken


def process_files_parallel(mongo_db_keys, db_engine_key, doc_id):
    mongo_db = pymongo.MongoClient(mongo_db_keys[0])[mongo_db_keys[1]]
    engine = create_engine(db_engine_key)

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
    print('|: db: ' + args.database)
    if args.passwd:
        db_password = getpass.getpass("db password: ")
    else:
        db_password = args.user
    db_engine_key = 'mysql+pymysql://{}:{}@localhost/{}'.format(args.user, db_password, args.database)

    mongo_db_keys = ("mongodb://localhost:27017/", "zdl")
    mongo_db = pymongo.MongoClient(mongo_db_keys[0])[mongo_db_keys[1]]

    document_ids = mongo_db["documents"].find().distinct('_id')
    print("Found documents:", len(document_ids))
    files = [(mongo_db_keys, db_engine_key, doc_id) for doc_id in document_ids]
    print("Create MPPool with #njobs:", args.jobs)
    with multiprocessing.Pool(args.jobs) as pool:
        pool.starmap(process_files_parallel, files, chunksize=10)


if __name__ == '__main__':
    main()
