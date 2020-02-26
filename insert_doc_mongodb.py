#!/usr/bin/env python

import argparse
import getpass
import logging
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


def process_files(mongo_db_keys, db_engine_key):
    mongo_db = pymongo.MongoClient(mongo_db_keys[0])[mongo_db_keys[1]]
    engine = create_engine(db_engine_key, pool_size=16, max_overflow=32)

    db_corpus_files = []
    db_concord_sentences = []
    db_matches = []

    document_ids = mongo_db["documents"].find({}).distinct('_id')
    print("Found documents:", len(document_ids))

    for doc_i, doc_id in enumerate(document_ids):
        if (doc_i + 1) % 1000 == 0:
            print(doc_i, len(db_corpus_files), len(db_concord_sentences), len(db_matches))
            db_corpus_files = list(map(lambda x: x._asdict(), db_corpus_files))
            db_concord_sentences = list(map(lambda x: x._asdict(), db_concord_sentences))
            db_matches = list(map(lambda x: x._asdict(), db_matches))
            insert_bulk_corpus_file(engine, db_corpus_files)
            insert_bulk_concord_sentences(engine, db_concord_sentences)
            insert_bulk_matches(engine, db_matches)
            db_corpus_files = []
            db_concord_sentences = []
            db_matches = []

        doc = mongo_db["documents"].find_one({'_id': doc_id})
        db_corpus_files.append(prepare_corpus_file(doc))
        parses = [[ConllToken(*[token[f] for f in ConllToken._fields]) for token in sentence]
                  for sentence in doc["sentences"]]
        parses = [s for s in parses if sentence_is_valid(s)]
        db_concord_sentences.extend(prepare_concord_sentences(str(doc_id), parses))
        matches = extract_matches_from_doc(parses)
        db_matches.extend(prepare_matches(str(doc_id), matches))

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


def main():
    lformat = '[%(levelname)s] %(asctime)s %(name)s# %(message)s'
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=lformat)
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", type=str, help="database username", required=True)
    parser.add_argument("--mariadb", type=str, help="database name", required=True)
    parser.add_argument("--mongodb", type=str, help="database name", required=True)
    parser.add_argument("--passwd", action="store_true", help="ask for database password")
    args = parser.parse_args()

    print('|: user: ' + args.user)
    print('|: db: ' + args.mariadb)
    if args.passwd:
        db_password = getpass.getpass("db password: ")
    else:
        db_password = args.user
    db_engine_key = 'mysql+pymysql://{}:{}@localhost/{}'.format(args.user, db_password, args.mariadb)

    mongo_db_keys = ("mongodb://localhost:27017/", args.mongodb)
    process_files(mongo_db_keys, db_engine_key)


if __name__ == '__main__':
    main()
