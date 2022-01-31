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
    wordprofile.wpse.db_tables.get_table_token_frequencies(meta)
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


def create_indices(engine: Engine):
    logging.info("CREATE INDEX indices for files, concordances, and matches")
    logging.info("CREATE INDEX corpus_index")
    engine.execute("CREATE UNIQUE INDEX corpus_index ON corpus_files (id);")
    logging.info("CREATE INDEX concord_corpus_index")
    engine.execute("CREATE INDEX concord_corpus_index ON concord_sentences (corpus_file_id);")
    logging.info("CREATE INDEX concord_corpus_sentence_index")
    engine.execute("CREATE UNIQUE INDEX concord_corpus_sentence_index "
                   "ON concord_sentences (corpus_file_id, sentence_id);")
    logging.info("CREATE INDEX matches_index")
    engine.execute("CREATE UNIQUE INDEX matches_index ON matches (id);")
    logging.info("CREATE INDEX matches_corpus_index")
    engine.execute("CREATE INDEX matches_corpus_index ON matches (corpus_file_id);")
    logging.info("CREATE INDEX matches_corpus_sentence_index")
    engine.execute("CREATE INDEX matches_corpus_sentence_index ON matches (corpus_file_id, sentence_id);")
    logging.info("CREATE INDEX matches_relation_label_index")
    engine.execute("CREATE INDEX matches_relation_label_index ON matches (collocation_id);")
    logging.info("CREATE INDEX mwe_index")
    engine.execute("CREATE INDEX mwe_index ON mwe (id);")
    logging.info("CREATE INDEX mwe_collocation1_index")
    engine.execute("CREATE INDEX mwe_collocation1_index ON mwe (collocation1_id);")
    logging.info("CREATE INDEX mwe_match_index")
    engine.execute("CREATE INDEX mwe_match_index ON mwe_match (mwe_id);")
    logging.info("CREATE colloc_id")
    engine.execute("CREATE INDEX colloc_id ON collocations (id);")
    logging.info("CREATE colloc_lemma1_index")
    engine.execute("CREATE INDEX colloc_lemma1_index ON collocations (lemma1);")
    logging.info("CREATE colloc_lemma1_tag_index")
    engine.execute("CREATE INDEX colloc_lemma1_tag_index ON collocations (lemma1, lemma1_tag);")
    logging.info("CREATE colloc_lemma2_tag_index")
    engine.execute("CREATE INDEX colloc_lemma2_tag_index ON collocations (lemma2, lemma2_tag);")
    logging.info("CREATE colloc_lemma_index")
    engine.execute("CREATE INDEX colloc_lemma_index ON collocations (lemma1, lemma2);")
    logging.info("CREATE token_freq_lemma")
    engine.execute("CREATE INDEX token_freq_lemma ON token_freqs (lemma);")
    logging.info("CREATE token_freq_lemma_tag")
    engine.execute("CREATE INDEX token_freq_lemma_tag ON token_freqs (lemma, tag);")


def create_statistics(engine: Engine):
    meta = MetaData()
    wordprofile.wpse.db_tables.get_table_corpus_frequencies(meta)
    meta.create_all(engine)

    logging.info("INSERT corpus_freqs")
    engine.execute("""
        INSERT INTO corpus_freqs (label, freq)
        SELECT label, SUM(frequency) as freq
        FROM collocations c
        GROUP BY label
    """)
