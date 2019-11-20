#!/usr/bin/python3

import getpass
from argparse import ArgumentParser

from sqlalchemy import create_engine, MetaData

import wordprofile.wpse.db_tables
from wp_server import WortprofilQuery


def init_word_profile_tables(engine, database):
    engine.execute("DROP DATABASE IF EXISTS " + database)
    engine.execute("CREATE DATABASE " + database + " CHARACTER SET utf8")
    engine.execute("set autocommit=1")
    engine.execute("USE " + database)

    meta = MetaData()
    wordprofile.wpse.db_tables.get_table_corpus_files(meta)
    wordprofile.wpse.db_tables.get_table_concord_sentences(meta)
    wordprofile.wpse.db_tables.get_table_matches(meta)
    wordprofile.wpse.db_tables.get_table_relations(meta)
    wordprofile.wpse.db_tables.get_table_collocations(meta)
    wordprofile.wpse.db_tables.get_table_statistics(meta)
    meta.create_all(engine)

    engine.execute("""
        CREATE OR REPLACE
        VIEW corpus_freqs
        AS
        SELECT label, COUNT(relation_id) as freq
        FROM collocations c
        GROUP BY label
    """)
    engine.execute("""
        CREATE OR REPLACE
        VIEW token_freqs
        AS 
        SELECT c.lemma1 as lemma, c.lemma1_pos as pos, SUM(s.frequency) freq
        FROM collocations c
        LEFT JOIN wp_stats s ON (c.id = s.collocation_id)
        GROUP BY c.lemma1, c.lemma1_pos
    """)


def create_wordprofile(user, passwd, database):
    wp = WortprofilQuery("localhost", user, passwd, database, 8086, "spec/config.json")
    wp.wp_db.create_wordprofile()


def main():
    print("|: CREATE MYSQL DATABASE")
    parser = ArgumentParser()
    parser.add_argument("--user", type=str, help="database username", required=True)
    parser.add_argument("--database", type=str, help="database name", required=True)
    parser.add_argument("--passwd", action="store_true", help="ask for database password")
    parser.add_argument("--init-db", action="store_true", help="ask for database init")
    parser.add_argument("--wp-db", action="store_true", help="ask for wordprofile creation")

    args = parser.parse_args()

    print('|: user: ' + args.user)
    print('|: db: ' + args.database)
    if args.passwd:
        db_password = getpass.getpass("db password: ")
    else:
        db_password = args.user

    if args.init_db:
        print("init database")
        engine = create_engine('mysql+pymysql://{}:{}@localhost'.format(
            args.user, db_password))
        init_word_profile_tables(engine, args.database)
    elif args.wp_db:
        print("create word profile stats")
        create_wordprofile(args.user, db_password, args.database)
    else:
        print("nothing happened...")
    print()
    print("(: done")


if __name__ == '__main__':
    main()
