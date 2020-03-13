#!/usr/bin/python3

import getpass
from argparse import ArgumentParser

from sqlalchemy import create_engine, MetaData
from sqlalchemy.engine import Engine

import wordprofile.wpse.db_tables


def init_word_profile_tables(engine: Engine, database: str):
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
        VIEW corpus_file_freqs
        AS
        SELECT cf.corpus, COUNT(cf.file) 
        FROM corpus_files cf 
        GROUP BY cf.corpus
    """)


def create_collocations(engine: Engine, database: str):
    engine.execute("USE " + database)
    engine.execute("DROP TABLE IF EXISTS collocations")

    meta = MetaData()
    wordprofile.wpse.db_tables.get_table_collocations(meta)
    meta.create_all(engine)

    print("INSERT collocations")
    engine.execute("""
    INSERT INTO collocations (label, lemma1, lemma2, lemma1_tag, lemma2_tag, inv, frequency)
    SELECT relation_label, lemma1, lemma2, lemma1_tag, lemma2_tag, inv, SUM(rel_count) as rel_sum
    FROM (
        SELECT 
        relation_label, head_lemma as lemma1, dep_lemma as lemma2, head_tag as lemma1_tag, dep_tag as lemma2_tag, 
        0 as inv, COUNT(relation_label) as rel_count
        FROM matches m
        GROUP BY relation_label, lemma1, lemma2, lemma1_tag, lemma2_tag
        HAVING COUNT(relation_label) > 5
        
        UNION ALL
        
        SELECT 
            relation_label, dep_lemma as lemma1, head_lemma as lemma2, dep_tag as lemma1_tag, head_tag as lemma2_tag, 
            1 as inv, COUNT(relation_label) as rel_count
        FROM matches m
        GROUP BY relation_label, lemma1, lemma2, lemma1_tag, lemma2_tag
        HAVING COUNT(relation_label) > 5
    ) tbf
    GROUP BY tbf.relation_label, tbf.lemma1, tbf.lemma2, tbf.lemma1_tag, tbf.lemma2_tag, tbf.inv;
    """)
    print("CREATE INDEX")
    engine.execute("CREATE INDEX lemma1_index USING HASH ON collocations (lemma1)")
    engine.execute("CREATE INDEX lemma1_tag_index USING HASH ON collocations (lemma1, lemma1_tag);")
    engine.execute("CREATE INDEX lemma2_tag_index USING HASH ON collocations (lemma2, lemma2_tag);")
    engine.execute("CREATE INDEX lemma USING HASH ON collocations (lemma1, lemma2);")


def create_statistics(engine: Engine, database: str):
    engine.execute("USE " + database)
    engine.execute("DROP TABLE IF EXISTS wp_stats")

    meta = MetaData()
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
    engine.execute("""
    INSERT INTO wp_stats
        (collocation_id)
    SELECT c.id
    FROM collocations c;
    """)
    engine.execute("CREATE INDEX stats_index USING HASH ON wp_stats (collocation_id);")
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
    parser.add_argument("--init", action="store_true", help="ask for database init")
    parser.add_argument("--collocations", action="store_true", help="ask for wordprofile creation")
    parser.add_argument("--stats", action="store_true", help="ask for wordprofile creation")

    args = parser.parse_args()

    print('|: user: ' + args.user)
    print('|: db: ' + args.database)
    if args.passwd:
        db_password = getpass.getpass("db password: ")
    else:
        db_password = args.user
    engine = create_engine('mysql+pymysql://{}:{}@localhost'.format(
        args.user, db_password))
    if args.init:
        print("init database")
        init_word_profile_tables(engine, args.database)
    if args.collocations:
        print("create word profile stats")
        create_collocations(engine, args.database)
    if args.stats:
        print("create word profile stats")
        create_statistics(engine, args.database)
    print()
    print("(: done")


if __name__ == '__main__':
    main()
