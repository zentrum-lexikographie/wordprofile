#!/usr/bin/python3

import logging

from sqlalchemy import MetaData
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
    wordprofile.wpse.db_tables.get_table_mwe(meta)
    meta.create_all(engine)

    engine.execute("""
        CREATE OR REPLACE
        VIEW corpus_file_freqs
        AS
        SELECT cf.corpus, COUNT(cf.file) 
        FROM corpus_files cf 
        GROUP BY cf.corpus
    """)


def create_collocations(engine: Engine):
    logging.info("INSERT collocations")
    engine.execute("""
    INSERT INTO collocations (id, label, lemma1, lemma2, lemma1_tag, lemma2_tag, inv, frequency)
    SELECT -id, label, lemma2, lemma1, lemma2_tag, lemma1_tag, 1 as inv, frequency
    FROM collocations c
    """)
    logging.info("CREATE INDEX")
    logging.info("CREATE id_index")
    engine.execute("CREATE INDEX id_index ON collocations (id);")
    logging.info("CREATE lemma1_index")
    engine.execute("CREATE INDEX lemma1_index ON collocations (lemma1);")
    logging.info("CREATE lemma1_tag_index")
    engine.execute("CREATE INDEX lemma1_tag_index ON collocations (lemma1, lemma1_tag);")
    logging.info("CREATE lemma2_tag_index")
    engine.execute("CREATE INDEX lemma2_tag_index ON collocations (lemma2, lemma2_tag);")
    logging.info("CREATE lemma_index")
    engine.execute("CREATE INDEX lemma_index ON collocations (lemma1, lemma2);")


def create_statistics(engine: Engine):
    meta = MetaData()
    wordprofile.wpse.db_tables.get_table_statistics(meta, metric='log_dice')
    wordprofile.wpse.db_tables.get_table_token_frequencies(meta)
    wordprofile.wpse.db_tables.get_table_corpus_frequencies(meta)
    meta.create_all(engine)

    logging.info("INSERT corpus_freqs")
    engine.execute("""
        INSERT INTO corpus_freqs (label, freq)
        SELECT label, SUM(frequency) as freq
        FROM collocations c
        GROUP BY label
    """)
    logging.info("INSERT token_freqs")
    engine.execute("""
        INSERT INTO token_freqs (lemma, tag, freq)
        SELECT c.lemma1 as lemma, c.lemma1_tag as tag, SUM(c.frequency) freq
        FROM collocations c
        GROUP BY c.lemma1, c.lemma1_tag 
    """)
    logging.info("INSERT log_dice")
    engine.execute("""
    INSERT INTO log_dice (collocation_id, value)
    SELECT c.id, (14 + LOG2((IFNULL(c.frequency, 1) * 2) / (IFNULL(t1.freq, 1) + IFNULL(t2.freq, 1))))
    FROM collocations c
    INNER JOIN token_freqs t1 ON (c.lemma1 = t1.lemma and c.lemma1_tag = t1.tag)
    INNER JOIN token_freqs t2 ON (c.lemma2 = t2.lemma and c.lemma2_tag = t2.tag)
    """)
    engine.execute("CREATE INDEX stats_index ON log_dice (collocation_id);")

    # print("INSERT mi score")
    # engine.execute("""
    # INSERT INTO mi_score (collocation_id, value)
    # SELECT c.id, LOG2((IFNULL(c.frequency, 1) * cf.freq) / (IFNULL(t1.freq, 1) * IFNULL(t2.freq, 1)))
    # FROM collocations c
    # INNER JOIN token_freqs t1 ON (c.lemma1 = t1.lemma and c.lemma1_tag = t1.tag)
    # INNER JOIN token_freqs t2 ON (c.lemma2 = t2.lemma and c.lemma2_tag = t2.tag)
    # INNER JOIN corpus_freqs cf ON (cf.label = c.label)
    # """)
    # engine.execute("CREATE INDEX stats_index USING HASH ON mi_score (collocation_id);")
