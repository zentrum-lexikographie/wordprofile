#!/usr/bin/env python

import argparse
import getpass
import logging
import multiprocessing
import sys

import pymongo
from sqlalchemy import create_engine, MetaData, Index

from wordprofile.wpse.db_tables import prepare_corpus_file, prepare_concord_sentences, prepare_matches, \
    insert_bulk_concord_sentences, insert_bulk_corpus_file, insert_bulk_matches, get_table_matches, \
    get_table_corpus_files, get_table_concord_sentences
from wordprofile.zdl import ConllToken, extract_matches_from_doc


def sent_filter_length(sentence):
    return 3 <= len(sentence) <= 100


def sent_filter_endings(sentence):
    return not sentence[-1].surface in [":", ","] or len(sentence) >= 5


def sent_filter_lower_start(sentence):
    return not sentence[0].surface.islower() or sentence[0].xpos == 'PPER'


def sent_filter_tags(sentence):
    return any(t.xpos in ["NN", "VV", "VM", "VA"] for t in sentence)


def sentence_is_valid(s):
    return sent_filter_length(s) and sent_filter_tags(s) and sent_filter_endings(s)


def process_doc(mongo_db_keys, doc_id):
    mongo_db = pymongo.MongoClient(mongo_db_keys[0])[mongo_db_keys[1]][mongo_db_keys[2]]
    doc = mongo_db.find_one({'_id': doc_id})
    try:
        db_corpus_file = prepare_corpus_file(doc)
        parses = [[ConllToken(*[token[f] for f in ConllToken._fields]) for token in sentence]
                  for sentence in doc["sentences"]]
        parses = [s for s in parses if sentence_is_valid(s)]
        db_concord_sentences = prepare_concord_sentences(str(doc_id), parses)
        matches = extract_matches_from_doc(parses)
        db_matches = prepare_matches(str(doc_id), matches)
        return db_corpus_file, db_concord_sentences, db_matches
    except:
        return None, [], []


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


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
    meta = MetaData()
    corpus_files_tb = get_table_corpus_files(meta)
    concord_sentences_tb = get_table_concord_sentences(meta)
    matches_tb = get_table_matches(meta)
    Index('corpus_index', corpus_files_tb.c.id, unique=True).create(engine)
    Index('concord_corpus_index', concord_sentences_tb.c.corpus_file_id).create(engine)
    Index('concord_corpus_sentence_index', concord_sentences_tb.c.corpus_file_id,
          concord_sentences_tb.c.sentence_id).create(engine)
    Index('matches_corpus_index', matches_tb.c.corpus_file_id).create(engine)
    Index('matches_corpus_sentence_index', matches_tb.c.corpus_file_id, matches_tb.c.sentence_id).create(engine)
    Index('matches_relation_label_index', matches_tb.c.relation_label, matches_tb.c.head_lemma, matches_tb.c.dep_lemma,
          matches_tb.c.head_tag, matches_tb.c.dep_tag).create(engine)


def process_files(mongo_db_keys, db_engine_key):
    mongo_db = pymongo.MongoClient(mongo_db_keys[0])[mongo_db_keys[1]][mongo_db_keys[2]]
    engine = create_engine(db_engine_key, pool_size=16, max_overflow=32)

    document_ids = mongo_db.find({}).distinct('_id')
    print("Found documents:", len(document_ids))

    for doc_i, doc_ids in enumerate(chunks(document_ids, 5000)):
        with multiprocessing.Pool(5) as pool:
            db_corpus_files, db_concord_sentences, db_matches = zip(
                *pool.starmap(process_doc, [(mongo_db_keys, doc_id) for doc_id in doc_ids], chunksize=100)
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
        delete_indices(db_engine_key)
        process_files(mongo_db_keys, db_engine_key)
    if args.create_index:
        delete_indices(db_engine_key)
        create_indices(db_engine_key)


if __name__ == '__main__':
    main()
