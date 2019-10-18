#!/usr/bin/python3

import getpass
from argparse import ArgumentParser

from sqlalchemy import create_engine, MetaData

import wordprofile.wpse.db_tables


def init_word_profile_tables(engine):
    meta = MetaData()
    wordprofile.wpse.db_tables.get_table_corpus_files(meta)
    wordprofile.wpse.db_tables.get_table_concord_sentences(meta)
    wordprofile.wpse.db_tables.get_table_matches(meta)
    wordprofile.wpse.db_tables.get_table_relations(meta)
    wordprofile.wpse.db_tables.get_table_statistics(meta)
    meta.create_all(engine)

    engine.execute("""
    CREATE VIEW relation_lemma_freq AS
    SELECT r.label label, r.head_lemma lemma, r.head_pos pos, COUNT(m.id) freq
    FROM wordprofile_test.relations r
    LEFT JOIN wordprofile_test.matches m ON (r.id = m.relation_id)
    GROUP BY label, lemma, pos
    HAVING freq > 10
    ORDER BY freq DESC
    """)



def main():
    print("|: CREATE MYSQL DATABASE")
    parser = ArgumentParser()
    parser.add_argument("--user", type=str, help="database username", required=True)
    parser.add_argument("--database", type=str, help="database name", required=True)
    parser.add_argument("--passwd", action="store_true", help="ask for database password")

    args = parser.parse_args()

    print('|: user: ' + args.user)
    print('|: db: ' + args.database)
    if args.passwd:
        db_password = getpass.getpass("db password: ")
    else:
        db_password = args.user

    engine = create_engine('mysql+pymysql://{}:{}@localhost'.format(
        args.user, db_password))
    engine.execute("DROP DATABASE IF EXISTS " + args.database)
    engine.execute("CREATE DATABASE " + args.database + " CHARACTER SET utf8")
    engine.execute("set autocommit=1")
    engine.execute("USE " + args.database)

    init_word_profile_tables(engine)

    print()
    print("(: done")


if __name__ == '__main__':
    main()
