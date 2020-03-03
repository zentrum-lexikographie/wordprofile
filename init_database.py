#!/usr/bin/python3

import getpass
from argparse import ArgumentParser

from sqlalchemy import create_engine, MetaData

import wordprofile.wpse.db_tables


def init_word_profile_tables(engine, database):
    engine.execute("DROP DATABASE IF EXISTS " + database)
    engine.execute("CREATE DATABASE " + database + " CHARACTER SET utf8")
    engine.execute("USE " + database)

    meta = MetaData()
    wordprofile.wpse.db_tables.get_table_corpus_files(meta)
    wordprofile.wpse.db_tables.get_table_concord_sentences(meta)
    wordprofile.wpse.db_tables.get_table_matches(meta)
    wordprofile.wpse.db_tables.get_table_collocations(meta)
    wordprofile.wpse.db_tables.get_table_statistics(meta)
    meta.create_all(engine)

    engine.execute("""
        CREATE OR REPLACE
        VIEW corpus_freqs
        AS
        SELECT label, COUNT(id) as freq
        FROM collocations c
        GROUP BY label
    """)
    engine.execute("""
        CREATE OR REPLACE
        VIEW token_freqs
        AS
        SELECT c.lemma1 as lemma, c.lemma1_tag as tag, SUM(c.frequency) freq
        FROM collocations c
        GROUP BY c.lemma1, c.lemma1_tag 
    """)


def create_wordprofile(engine, database):
    engine.execute("USE " + database)
    engine.execute("DROP TABLE IF EXISTS collocations")
    engine.execute("DROP TABLE IF EXISTS wp_stats")

    meta = MetaData()
    wordprofile.wpse.db_tables.get_table_collocations(meta)
    wordprofile.wpse.db_tables.get_table_statistics(meta)
    meta.create_all(engine)

    engine.execute("""
        CREATE OR REPLACE
        VIEW corpus_freqs
        AS
        SELECT label, SUM(frequency) as freq
        FROM collocations c
        GROUP BY label
    """)
    engine.execute("""
        CREATE OR REPLACE
        VIEW token_freqs
        AS
        SELECT c.lemma1 as lemma, c.lemma1_tag as tag, SUM(c.frequency) freq
        FROM collocations c
        GROUP BY c.lemma1, c.lemma1_tag 
    """)
    print("insert collocations")
    engine.execute("""
    INSERT INTO collocations (label, lemma1, lemma2, lemma1_tag, lemma2_tag, inv, frequency)
    SELECT 
        relation_label, head_lemma as lemma1, dep_lemma as lemma2, head_tag as lemma1_tag, dep_tag as lemma2_tag, 
        0, COUNT(m.relation_label)
    FROM matches m
    GROUP BY relation_label, lemma1, lemma2, lemma1_tag, lemma2_tag
    HAVING COUNT(m.relation_label) > 5;
    """)
    engine.execute("""
    INSERT INTO collocations (label, lemma1, lemma2, lemma1_tag, lemma2_tag, inv, frequency)
    SELECT 
        relation_label, dep_lemma as lemma1, head_lemma as lemma2, dep_tag as lemma1_tag, head_tag as lemma2_tag, 
        1, COUNT(m.relation_label)
    FROM matches m
    GROUP BY relation_label, lemma1, lemma2, lemma1_tag, lemma2_tag
    HAVING COUNT(m.relation_label) > 5;
    """)
    engine.execute("create index lemma1_index on collocations (lemma1)")
    engine.execute("create index lemma1_tag_index on collocations (lemma1, lemma1_tag);")
    engine.execute("create index lemma2_tag_index on collocations (lemma2, lemma2_tag);")
    engine.execute("create index lemma on collocations (lemma1, lemma2);")

    engine.execute("""
    INSERT INTO wp_stats
        (collocation_id)
    SELECT c.id
    FROM collocations c;
    """)
    engine.execute("create index stats_index on wp_stats (collocation_id);")
    print("insert mi scores")
    engine.execute("""
    UPDATE wp_stats s
    INNER JOIN collocations c ON (c.id = s.collocation_id)
    INNER JOIN token_freqs t1 ON (c.lemma1 = t1.lemma and c.lemma1_tag = t1.tag)
    INNER JOIN token_freqs t2 ON (c.lemma2 = t2.lemma and c.lemma2_tag = t2.tag)
    INNER JOIN corpus_freqs cf ON (cf.label = c.label)
    SET s.mi=LOG2((IFNULL(c.frequency, 1) * cf.freq) / (IFNULL(t1.freq, 1) * IFNULL(t2.freq, 1)));
    """)
    print("insert log dice scores")
    engine.execute("""
    UPDATE wp_stats s
    INNER JOIN collocations c ON (c.id = s.collocation_id)
    INNER JOIN token_freqs t1 ON (c.lemma1 = t1.lemma and c.lemma1_tag = t1.tag)
    INNER JOIN token_freqs t2 ON (c.lemma2 = t2.lemma and c.lemma2_tag = t2.tag)
    SET s.log_dice=(14 + LOG2((IFNULL(c.frequency, 1) * 2) / (IFNULL(t1.freq, 1) + IFNULL(t2.freq, 1))));
    """)


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
    engine = create_engine('mysql+pymysql://{}:{}@localhost'.format(
        args.user, db_password))
    if args.init_db:
        print("init database")
        init_word_profile_tables(engine, args.database)
    elif args.wp_db:
        print("create word profile stats")
        create_wordprofile(engine, args.database)
    else:
        print("nothing happened...")
    print()
    print("(: done")


if __name__ == '__main__':
    main()
