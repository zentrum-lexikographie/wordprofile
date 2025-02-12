import logging

from pathlib import Path

from sqlalchemy import Column, Enum, MetaData, Table, create_engine, text, types
from sqlalchemy.sql import func
from sqlalchemy.sql.schema import Index

import wordprofile.config as config
from wordprofile.extract import relation_types, word_classes

logger = logging.getLogger(__name__)

FORM_TYPE = types.VARCHAR(config.max_form_length)
CORPUS_FILE_TYPE = types.Integer
RELATION_TYPE = Enum(relation_types)
TAG_TYPE = Enum(word_classes)

meta = MetaData()
corpus_files = Table(
    "corpus_files",
    meta,
    Column("id", CORPUS_FILE_TYPE),
    Column("corpus", types.VARCHAR(50)),
    Column("file", types.VARCHAR(200)),
    Column("orig", types.Text),
    Column("date", types.DateTime),
    Column("available", types.Text),
    mysql_engine="Aria",
)
concord_sentences = Table(
    "concord_sentences",
    meta,
    Column("corpus_file_id", CORPUS_FILE_TYPE),
    Column("sentence_id", types.Integer),
    Column("sentence", types.Text),
    Column("random_val", types.Float, server_default=func.rand()),
    mysql_engine="Aria",
)
matches = Table(
    "matches",
    meta,
    Column("id", types.Integer),
    Column("collocation_id", types.Integer),
    Column("head_surface", FORM_TYPE),
    Column("dep_surface", FORM_TYPE),
    Column("head_position", types.Integer),
    Column("dep_position", types.Integer),
    Column("prep_position", types.Text),
    Column("corpus_file_id", CORPUS_FILE_TYPE),
    Column("sentence_id", types.Integer),
    mysql_engine="Aria",
)
collocations = Table(
    "collocations",
    meta,
    Column("id", types.Integer),
    Column("label", RELATION_TYPE),
    Column("lemma1", FORM_TYPE),
    Column("lemma2", FORM_TYPE),
    Column("lemma1_tag", TAG_TYPE),
    Column("lemma2_tag", TAG_TYPE),
    Column("preposition", FORM_TYPE),
    Column("inv", types.Boolean, default=0),
    Column("frequency", types.Integer, default=1),
    Column("score", types.Float),
    mysql_engine="Aria",
)
mwe = Table(
    "mwe",
    meta,
    Column("id", types.Integer),
    Column("collocation1_id", types.Integer),
    Column("collocation2_id", types.Integer),
    Column("label", RELATION_TYPE),
    Column("lemma", FORM_TYPE),
    Column("lemma_tag", TAG_TYPE),
    Column("inv", types.Boolean, default=0),
    Column("frequency", types.Integer, default=1),
    Column("score", types.Float),
    mysql_engine="Aria",
)
mwe_match = Table(
    "mwe_match",
    meta,
    Column("mwe_id", types.Integer),
    Column("match1_id", types.Integer),
    Column("match2_id", types.Integer),
    mysql_engine="Aria",
)
corpus_freqs = Table(
    "corpus_freqs",
    meta,
    Column("label", RELATION_TYPE),
    Column("freq", types.Integer),
    Index("label_index", "label"),
    mysql_engine="Aria",
)
token_freqs = Table(
    "token_freqs",
    meta,
    Column("lemma", FORM_TYPE),
    Column("tag", TAG_TYPE),
    Column("freq", types.Integer),
    Column("surface", FORM_TYPE),
    Column("surface_freq", types.Integer),
    mysql_engine="Aria",
)

indices = (
    Index("corpus_index", corpus_files.c.id, unique=True),
    Index("concord_corpus_index", concord_sentences.c.corpus_file_id),
    Index(
        "concord_corpus_sentence_index",
        concord_sentences.c.corpus_file_id,
        concord_sentences.c.sentence_id,
        unique=True,
    ),
    Index("rand_val", concord_sentences.c.random_val),
    Index("matches_index", matches.c.id, unique=True),
    Index("matches_corpus_index", matches.c.corpus_file_id),
    Index(
        "matches_corpus_sentence_index", matches.c.corpus_file_id, matches.c.sentence_id
    ),
    Index("matches_collocation_index", matches.c.collocation_id),
    Index("mwe_index", mwe.c.id, unique=True),
    Index("mwe_collocation1_index", mwe.c.collocation1_id),
    Index("mwe_match_index", mwe_match.c.mwe_id),
    Index("colloc_id", collocations.c.id, unique=True),
    Index("colloc_lemma1_index", collocations.c.lemma1),
    Index("colloc_lemma1_tag_index", collocations.c.lemma1, collocations.c.lemma1_tag),
    Index("colloc_lemma2_tag_index", collocations.c.lemma2, collocations.c.lemma2_tag),
    Index("colloc_lemma_index", collocations.c.lemma1, collocations.c.lemma2),
    Index("token_freq_lemma", token_freqs.c.lemma),
    Index("token_freq_lemma_tag", token_freqs.c.lemma, token_freqs.c.tag),
)


def open_db(create_schema=True, clear=False, **args):
    url = "mysql+pymysql://{}:{}@{}/{}?charset=utf8mb4&local_infile=1".format(
        config.DB_USER, config.DB_PASSWORD, config.DB_HOST, config.DB_NAME
    )
    db = create_engine(url, **args)
    logger.info("Opening '%s'" % db)
    if clear:
        logger.info("Clearing '%s'" % db)
        with db.connect() as c:
            meta.drop_all(c)
    if create_schema:
        logger.info("Initializing '%s'" % db)
        with db.connect() as c:
            meta.create_all(c)
    return db


loaded_tables = (
    "corpus_files",
    "concord_sentences",
    "collocations",
    "token_freqs",
    "matches",
    "mwe",
    "mwe_match",
)


def load_db(db, data_dir):
    data_dir = Path(data_dir)
    logger.info("Loading '%s'" % data_dir)
    with db.connect() as c:
        logger.info("Dropping indices")
        for index in indices:
            index.drop(c)
        for table in loaded_tables:
            table_file = data_dir / table
            if not table_file.exists():
                logger.warning("Local file '%s' does not exist." % table_file)
                continue
            logger.info("Loading table '%s'" % table)
            sql = f"LOAD DATA LOCAL INFILE '{table_file}' INTO TABLE {table}"
            if table == "concord_sentences":
                sql += " (corpus_file_id, sentence_id, sentence)"
            sql += ";"
            c.execute(text(sql))
        logger.info("Creating corpus frequency statistics")
        c.execute(
            text(
                """
            INSERT INTO corpus_freqs (label, freq)
            SELECT label, SUM(frequency) as freq
            FROM collocations c
            GROUP BY label
            """
            )
        )
        for index in indices:
            logger.info("Creating index '%s" % index.name)
            index.create(c)
