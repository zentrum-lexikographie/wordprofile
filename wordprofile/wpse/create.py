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
    wordprofile.wpse.db_tables.get_table_mwe(meta)
    wordprofile.wpse.db_tables.get_table_mwe_match(meta)
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
