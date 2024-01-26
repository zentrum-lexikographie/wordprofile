import logging

from sqlalchemy import MetaData
from sqlalchemy.engine import Engine

import wordprofile.wpse.db_tables

logger = logging.getLogger(__name__)


def init_word_profile_tables(engine: Engine, database: str):
    engine.execute("DROP DATABASE IF EXISTS " + database)
    engine.execute(
        "CREATE DATABASE " + database + " CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin"
    )
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

    engine.execute(
        """
        CREATE OR REPLACE
        VIEW corpus_file_freqs
        AS
        SELECT cf.corpus, COUNT(cf.file)
        FROM corpus_files cf
        GROUP BY cf.corpus
    """
    )


def create_indices(engine: Engine):
    logger.info("CREATE INDEX indices for files, concordances, and matches")
    logger.info("CREATE INDEX corpus_index")
    engine.execute("CREATE UNIQUE INDEX corpus_index ON corpus_files (id);")
    logger.info("CREATE INDEX concord_corpus_index")
    engine.execute(
        "CREATE INDEX concord_corpus_index ON concord_sentences (corpus_file_id);"
    )
    logger.info("CREATE INDEX concord_corpus_sentence_index")
    engine.execute(
        "CREATE UNIQUE INDEX concord_corpus_sentence_index "
        "ON concord_sentences (corpus_file_id, sentence_id);"
    )
    logger.info("CREATE INDEX matches_index")
    engine.execute("CREATE UNIQUE INDEX matches_index ON matches (id);")
    logger.info("CREATE INDEX matches_corpus_index")
    engine.execute("CREATE INDEX matches_corpus_index ON matches (corpus_file_id);")
    logger.info("CREATE INDEX matches_corpus_sentence_index")
    engine.execute(
        "CREATE INDEX matches_corpus_sentence_index ON matches (corpus_file_id, sentence_id);"
    )
    logger.info("CREATE INDEX matches_relation_label_index")
    engine.execute(
        "CREATE INDEX matches_relation_label_index ON matches (collocation_id);"
    )
    logger.info("CREATE INDEX mwe_index")
    engine.execute("CREATE INDEX mwe_index ON mwe (id);")
    logger.info("CREATE INDEX mwe_collocation1_index")
    engine.execute("CREATE INDEX mwe_collocation1_index ON mwe (collocation1_id);")
    logger.info("CREATE INDEX mwe_match_index")
    engine.execute("CREATE INDEX mwe_match_index ON mwe_match (mwe_id);")
    logger.info("CREATE colloc_id")
    engine.execute("CREATE INDEX colloc_id ON collocations (id);")
    logger.info("CREATE colloc_lemma1_index")
    engine.execute("CREATE INDEX colloc_lemma1_index ON collocations (lemma1);")
    logger.info("CREATE colloc_lemma1_tag_index")
    engine.execute(
        "CREATE INDEX colloc_lemma1_tag_index ON collocations (lemma1, lemma1_tag);"
    )
    logger.info("CREATE colloc_lemma2_tag_index")
    engine.execute(
        "CREATE INDEX colloc_lemma2_tag_index ON collocations (lemma2, lemma2_tag);"
    )
    logger.info("CREATE colloc_lemma_index")
    engine.execute("CREATE INDEX colloc_lemma_index ON collocations (lemma1, lemma2);")
    logger.info("CREATE token_freq_lemma")
    engine.execute("CREATE INDEX token_freq_lemma ON token_freqs (lemma);")
    logger.info("CREATE token_freq_lemma_tag")
    engine.execute("CREATE INDEX token_freq_lemma_tag ON token_freqs (lemma, tag);")


def create_statistics(engine: Engine):
    meta = MetaData()
    wordprofile.wpse.db_tables.get_table_corpus_frequencies(meta)
    meta.create_all(engine)

    logger.info("INSERT corpus_freqs")
    engine.execute(
        """
        INSERT INTO corpus_freqs (label, freq)
        SELECT label, SUM(frequency) as freq
        FROM collocations c
        GROUP BY label
    """
    )
