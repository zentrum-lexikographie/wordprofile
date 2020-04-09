import enum
import re
from collections import namedtuple

from sqlalchemy import Table, Column, types, MetaData, Enum
from sqlalchemy.sql.schema import Index

from wordprofile.zdl import RELATIONS, SIMPLE_TAG_MAP

LEMMA_TYPE = types.VARCHAR(50)
SURFACE_TYPE = types.VARCHAR(50)
CORPUS_FILE_TYPE = types.CHAR(length=24)
RELATION_TYPE = enum.Enum('RELATION_TYPE', sorted(list(RELATIONS.keys())))
TAG_TYPE = enum.Enum('TAG_TYPE', sorted(set(SIMPLE_TAG_MAP.values())))
DBCorpusFile = namedtuple('DBCorpusFile', ['id', 'corpus', 'file', 'orig', 'scan', 'text_class', 'available'])
DBConcordance = namedtuple('DBConcordance', ['corpus_file_id', 'sentence_id', 'sentence', 'page'])
DBMatch = namedtuple('DBMatch',
                     ['relation_label', 'head_lemma', 'dep_lemma', 'head_tag', 'dep_tag',
                      'head_surface', 'dep_surface', 'head_position', 'dep_position',
                      'prep_position', 'corpus_file_id', 'sentence_id', 'creation_date'])

re_pattern = re.compile(r'[^\u0000-\uD7FF\uE000-\uFFFF]|\\', re.UNICODE)
re2_pattern = re.compile(r'(^\W+)|(\W+$)')


def remove_invalid_chars(unicode_string):
    return re_pattern.sub('', unicode_string)


def get_table_corpus_files(meta: MetaData):
    return Table(
        'corpus_files', meta,
        Column('id', CORPUS_FILE_TYPE),
        Column('corpus', types.VARCHAR(50)),
        Column('file', types.VARCHAR(200)),
        Column('orig', types.Text),
        Column('scan', types.Text),
        Column('text_class', types.Text),
        Column('available', types.Text),
        mysql_engine='Aria',
    )


def get_table_concord_sentences(meta: MetaData):
    return Table(
        'concord_sentences', meta,
        Column('corpus_file_id', CORPUS_FILE_TYPE),
        Column('sentence_id', types.Integer),
        Column('sentence', types.Text),
        Column('page', types.VARCHAR(10)),
        mysql_engine='Aria',
    )


def get_table_matches(meta: MetaData):
    return Table(
        'matches', meta,
        Column('collocation_id', types.Integer),
        Column('head_surface', SURFACE_TYPE),
        Column('dep_surface', SURFACE_TYPE),
        Column('head_position', types.Integer),
        Column('dep_position', types.Integer),
        Column('prep_position', types.Integer),
        Column('corpus_file_id', CORPUS_FILE_TYPE),
        Column('sentence_id', types.Integer),
        Column('creation_date', types.DateTime),
        mysql_engine='Aria'
    )


def get_table_collocations(meta: MetaData):
    return Table(
        'collocations', meta,
        Column('id', types.Integer),
        Column('label', Enum(RELATION_TYPE)),
        Column('lemma1', LEMMA_TYPE),
        Column('lemma2', LEMMA_TYPE),
        Column('lemma1_tag', Enum(TAG_TYPE)),
        Column('lemma2_tag', Enum(TAG_TYPE)),
        Column('inv', types.Boolean, default=0),
        Column('frequency', types.Integer, default=1),
        mysql_engine='Aria',
    )


def get_table_corpus_frequencies(meta: MetaData):
    return Table(
        'corpus_freqs', meta,
        Column('label', Enum(RELATION_TYPE)),
        Column('freq', types.Integer),
        Index('label_index', 'label'),
        mysql_engine='Aria',
    )


def get_table_token_frequencies(meta: MetaData):
    return Table(
        'token_freqs', meta,
        Column('lemma', LEMMA_TYPE),
        Column('tag', Enum(TAG_TYPE)),
        Column('freq', types.Integer),
        Index('label_index', 'lemma'),
        Index('label_tag_index', 'lemma', 'tag'),
        mysql_engine='Aria',
    )


def get_table_statistics(meta: MetaData, metric: str = 'log_dice'):
    return Table(
        metric, meta,
        Column('collocation_id', types.Integer),
        Column('value', types.Float),
        mysql_engine='Aria',
    )
