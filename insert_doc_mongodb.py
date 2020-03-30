#!/usr/bin/env python

import argparse
import getpass
import logging
import multiprocessing
import sys
from typing import List, Dict

import pymongo
from sqlalchemy import create_engine

from wordprofile.datatypes import DBToken
from wordprofile.utils import chunks
from wordprofile.wpse.db_tables import prepare_corpus_file, prepare_concord_sentences, prepare_matches, \
    insert_bulk_concord_sentences, insert_bulk_corpus_file, insert_bulk_matches, remove_invalid_chars
from wordprofile.zdl import extract_matches_from_doc, SIMPLE_TAG_MAP, repair_lemma, \
    sentence_is_valid


def convert_sentence(sentence: List[Dict[str, str]]) -> List[DBToken]:
    return [DBToken(
        idx=i + 1,
        surface=remove_invalid_chars(token['surface']),
        lemma=repair_lemma(remove_invalid_chars(token['lemma']), SIMPLE_TAG_MAP.get(token['xpos'], '')),
        tag=SIMPLE_TAG_MAP.get(token['xpos'], ''),
        head=token['head'],
        rel=token['rel'],
        misc=bool(token['misc'])
    ) for i, token in enumerate(sentence)]


def process_doc(mongo_db_keys, mongo_index, doc_id):
    mongo_db = pymongo.MongoClient(mongo_db_keys[0])[mongo_db_keys[1]][mongo_index]
    doc = mongo_db.find_one({'_id': doc_id})
    try:
        doc_id, db_corpus_file = prepare_corpus_file(doc)
        parses = list(filter(sentence_is_valid, map(convert_sentence, doc["sentences"])))
        db_concord_sentences = prepare_concord_sentences(doc_id, parses)
        matches = extract_matches_from_doc(parses)
        db_matches = prepare_matches(doc_id, matches)
        return db_corpus_file, db_concord_sentences, db_matches
    except Exception as e:
        print(e)
        return None, [], []


def delete_indices(db_engine_key):
    engine = create_engine(db_engine_key)
    print("DELETE indices for files, concordances, and matches")
    engine.execute("DROP INDEX IF EXISTS corpus_index ON corpus_files")
    engine.execute("DROP INDEX IF EXISTS concord_corpus_index ON concord_sentences")
    engine.execute("DROP INDEX IF EXISTS concord_corpus_sentence_index ON concord_sentences")
    engine.execute("DROP INDEX IF EXISTS matches_corpus_index ON matches")
    engine.execute("DROP INDEX IF EXISTS matches_corpus_sentence_index ON matches")
    engine.execute("DROP INDEX IF EXISTS matches_relation_label_index ON matches")


def create_indices(db_engine_key):
    engine = create_engine(db_engine_key)
    print("CREATE indices for files, concordances, and matches")
    print("CREATE corpus_index")
    engine.execute("CREATE UNIQUE INDEX corpus_index USING HASH ON corpus_files (id);")
    print("CREATE concord_corpus_index")
    engine.execute("CREATE INDEX concord_corpus_index USING HASH ON concord_sentences (corpus_file_id);")
    print("CREATE concord_corpus_sentence_index")
    engine.execute("CREATE UNIQUE INDEX concord_corpus_sentence_index USING HASH "
                   "ON concord_sentences (corpus_file_id, sentence_id);")
    print("CREATE matches_corpus_index")
    engine.execute("CREATE INDEX matches_corpus_index USING HASH ON matches (corpus_file_id);")
    print("CREATE matches_corpus_sentence_index")
    engine.execute("CREATE INDEX matches_corpus_sentence_index USING HASH ON matches (corpus_file_id, sentence_id);")
    print("CREATE matches_relation_label_index")
    engine.execute("CREATE INDEX matches_relation_label_index USING HASH "
                   "ON matches (relation_label, head_lemma, dep_lemma, head_tag, dep_tag);")


def get_corpus_file_ids(mongo_db_keys, mongo_index, db_engine_key, filter_existing=True):
    mongo_db = pymongo.MongoClient(mongo_db_keys[0])[mongo_db_keys[1]][mongo_index]
    engine = create_engine(db_engine_key)
    if filter_existing:
        print("LOAD corpus file ids: ", end='')
        inserted_ids = {i[0] for i in engine.execute('SELECT id FROM corpus_files')}
        print(len(inserted_ids))
    else:
        inserted_ids = {}
    print("LOAD document ids for processing: ", end='')
    document_ids = [i['_id'] for i in mongo_db.find({'sentence': {'$ne': []}}, {'_id': 1}) if
                    str(i['_id']) not in inserted_ids]
    print(len(document_ids))
    return document_ids


def listener(q, db_engine_key):
    engine = create_engine(db_engine_key)
    print('INIT queue, wait for jobs')
    while True:
        m = q.get()
        if not m:
            print('CLOSE queue')
            break
        try:
            db_corpus_files, db_concord_sentences, db_matches = m
            db_corpus_files = [x._asdict() for x in db_corpus_files if x]
            db_concord_sentences = [sentence._asdict() for sentences in db_concord_sentences for sentence in sentences]
            db_matches = [match._asdict() for file_matches in db_matches for match in file_matches]

            insert_bulk_corpus_file(engine, db_corpus_files)
            insert_bulk_concord_sentences(engine, db_concord_sentences)
            insert_bulk_matches(engine, db_matches)
            print('INSERT', len(db_corpus_files), len(db_concord_sentences), len(db_matches))
        except Exception as e:
            print(e)


def process_files_index(mongo_db_keys, mongo_index, db_engine_key, db_queue):
    document_ids = get_corpus_file_ids(mongo_db_keys, mongo_index, db_engine_key, filter_existing=False)
    for doc_i, doc_ids in enumerate(chunks(document_ids, 3000)):
        with multiprocessing.Pool(5) as pool:
            db_corpus_files, db_concord_sentences, db_matches = list(zip(
                *pool.starmap(process_doc, [(mongo_db_keys, mongo_index, doc_id) for doc_id in doc_ids], chunksize=100)
            ))
        db_queue.put((db_corpus_files, db_concord_sentences, db_matches))


def process_files(mongo_db_keys, db_engine_key, mongo_indices):
    mongo_indices = [i.strip() for i in mongo_indices.split(",") if i.strip()]
    delete_indices(db_engine_key)
    manager = multiprocessing.Manager()
    db_queue = manager.Queue()
    queue_p1 = multiprocessing.Process(target=listener, args=(db_queue, db_engine_key))
    queue_p2 = multiprocessing.Process(target=listener, args=(db_queue, db_engine_key))
    queue_p1.start()
    queue_p2.start()
    doc_ps = []
    for mongo_index in mongo_indices:
        print('Start Process:', mongo_index)
        p = multiprocessing.Process(target=process_files_index,
                                    args=(mongo_db_keys, mongo_index, db_engine_key, db_queue))
        p.start()
        doc_ps.append((mongo_index, p))

    for mongo_index, p in doc_ps:
        p.join()
        print('INDEX DONE:', mongo_index)

    print('INDICES DONE')
    db_queue.put(None)
    db_queue.put(None)
    print('PUT NONE to queue and wait...')
    queue_p1.join()
    queue_p2.join()
    print('ALL DONE')


def main():
    lformat = '[%(levelname)s] %(asctime)s %(name)s# %(message)s'
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=lformat)
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", type=str, help="database username", required=True)
    parser.add_argument("--maria-db", type=str, help="database name", required=True)
    parser.add_argument("--mongo-db", type=str, help="database name", required=True)
    parser.add_argument("--mongo-index", default='', help="database index")
    parser.add_argument("--passwd", action="store_true", help="ask for database password")
    parser.add_argument("--create-index", action="store_true", help="create indices")
    args = parser.parse_args()

    print('|: user: ' + args.user)
    print('|: db: ' + args.maria_db)
    if args.passwd:
        db_password = getpass.getpass("db password: ")
    else:
        db_password = args.user
    db_engine_key = 'mysql+pymysql://{}:{}@localhost/{}'.format(args.user, db_password, args.maria_db)
    if args.mongo_index:
        mongo_db_keys = ("mongodb://localhost:27017/", args.mongo_db)
        process_files(mongo_db_keys, db_engine_key, args.mongo_index)
    if args.create_index:
        delete_indices(db_engine_key)
        create_indices(db_engine_key)


if __name__ == '__main__':
    main()
