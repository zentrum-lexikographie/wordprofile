#!/usr/bin/python3

import getpass
from argparse import ArgumentParser

import wordprofile.wpse.db_tables
from sqlalchemy import create_engine, MetaData


def init_word_profile_tables(engine):
    meta = MetaData()
    wordprofile.wpse.db_tables.get_table_corpus_files(meta)
    wordprofile.wpse.db_tables.get_table_concord_sentences(meta)
    wordprofile.wpse.db_tables.get_table_matches(meta)
    wordprofile.wpse.db_tables.get_table_relations(meta)
    meta.create_all(engine)


def main():
    print("|: CREATE MYSQL DATABASE")
    parser = ArgumentParser()
    parser.add_argument("--user", type=str, help="database username", required=True)
    parser.add_argument("--database", type=str, help="database name", required=True)

    args = parser.parse_args()

    print('|: user: ' + args.user)
    print('|: db: ' + args.database)
    db_password = getpass.getpass("db password: ")

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
