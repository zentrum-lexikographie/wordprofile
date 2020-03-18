#!/usr/bin/env python

import argparse
import getpass
import logging
import multiprocessing
import sys

import pymongo
from sqlalchemy import create_engine

from wordprofile.utils import chunks
from wordprofile.wpse.db_tables import prepare_corpus_file, prepare_concord_sentences, prepare_matches, \
    insert_bulk_concord_sentences, insert_bulk_corpus_file, insert_bulk_matches, remove_invalid_chars
from wordprofile.zdl import extract_matches_from_doc, DBToken, simplified_pos, load_lemma_repair_files

LEMMA_REPAIR = load_lemma_repair_files()


def repair_lemma(lemma, lemma_tag):
    if lemma_tag in LEMMA_REPAIR:
        return LEMMA_REPAIR[lemma_tag].get(lemma, lemma)
    return lemma


def sent_filter_length(sentence):
    return 3 <= len(sentence) <= 100


def sent_filter_endings(sentence):
    return not sentence[-1].surface in [":", ","] or len(sentence) >= 5


def sent_filter_lower_start(sentence):
    return not sentence[0].surface.islower() or sentence[0].tag == 'PPER'


def sent_filter_tags(sentence):
    return any(t.tag in ["NN", "VV", "VM", "VA"] for t in sentence)


def sentence_is_valid(s):
    return sent_filter_length(s) and sent_filter_tags(s) and sent_filter_endings(s)


def convert_sentence(sentence):
    return [DBToken(
        idx=i + 1,
        surface=remove_invalid_chars(token['surface']),
        lemma=repair_lemma(remove_invalid_chars(token['lemma']), simplified_pos.get(token['xpos'], token['xpos'])),
        tag=simplified_pos.get(token['xpos'], token['xpos']),
        head=token['head'],
        rel=token['rel'],
        misc=bool(token['misc'])
    ) for i, token in enumerate(sentence)]


def process_doc(mongo_db_keys, doc_id):
    mongo_db = pymongo.MongoClient(mongo_db_keys[0])[mongo_db_keys[1]][mongo_db_keys[2]]
    doc = mongo_db.find_one({'_id': doc_id})
    try:
        db_corpus_file = prepare_corpus_file(doc)
        parses = list(filter(sentence_is_valid, map(convert_sentence, doc["sentences"])))
        db_concord_sentences = prepare_concord_sentences(str(doc_id), parses)
        matches = extract_matches_from_doc(parses)
        db_matches = prepare_matches(str(doc_id), matches)
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


def get_corpus_file_ids(mongo_db_keys, db_engine_key, filter_existing=True):
    mongo_db = pymongo.MongoClient(mongo_db_keys[0])[mongo_db_keys[1]][mongo_db_keys[2]]
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


def process_files(mongo_db_keys, db_engine_key):
    engine = create_engine(db_engine_key)
    document_ids = get_corpus_file_ids(mongo_db_keys, db_engine_key)
    delete_indices(db_engine_key)

    for doc_i, doc_ids in enumerate(chunks(document_ids, 5000)):
        with multiprocessing.Pool(10) as pool:
            db_corpus_files, db_concord_sentences, db_matches = zip(
                *pool.starmap(process_doc, [(mongo_db_keys, doc_id) for doc_id in doc_ids], chunksize=50)
            )
        db_corpus_files = [x._asdict() for x in db_corpus_files if x]
        db_concord_sentences = [sentence._asdict() for sentences in db_concord_sentences for sentence in sentences]
        db_matches = [match._asdict() for file_matches in db_matches for match in file_matches]
        print(doc_i, len(db_corpus_files), len(db_concord_sentences), len(db_matches))

        try:
            insert_bulk_corpus_file(engine, db_corpus_files)
            insert_bulk_concord_sentences(engine, db_concord_sentences)
            insert_bulk_matches(engine, db_matches)
        except Exception as e:
            print(e)


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
        mongo_db_keys = ("mongodb://localhost:27017/", args.mongo_db, args.mongo_index)
        process_files(mongo_db_keys, db_engine_key)
    if args.create_index:
        delete_indices(db_engine_key)
        create_indices(db_engine_key)


if __name__ == '__main__':
    main()
