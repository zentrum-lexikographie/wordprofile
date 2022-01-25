import enum
import re
from collections import namedtuple

from sqlalchemy import Table, Column, types, MetaData, Enum
from sqlalchemy.sql.schema import Index

from wordprofile.extract import get_relation_types, get_word_classes

LEMMA_TYPE = types.VARCHAR(50)
SURFACE_TYPE = types.VARCHAR(50)
CORPUS_FILE_TYPE = types.Integer
RELATION_TYPE = enum.Enum('RELATION_TYPE', get_relation_types())
TAG_TYPE = enum.Enum('TAG_TYPE', get_word_classes())
DBCorpusFile = namedtuple('DBCorpusFile', ['id', 'corpus', 'file', 'orig', 'scan', 'date', 'text_class', 'available'])
DBConcordance = namedtuple('DBConcordance', ['corpus_file_id', 'sentence_id', 'sentence', 'page'])
DBMatch = namedtuple('DBMatch',
                     ['relation_label', 'head_lemma', 'dep_lemma', 'head_tag', 'dep_tag',
                      'head_surface', 'dep_surface', 'head_position', 'dep_position',
                      'prep_position', 'corpus_file_id', 'sentence_id'])

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
        Column('date', types.DateTime),
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
        Column('id', types.Integer),
        Column('collocation_id', types.Integer),
        Column('head_surface', SURFACE_TYPE),
        Column('dep_surface', SURFACE_TYPE),
        Column('head_position', types.Integer),
        Column('dep_position', types.Integer),
        Column('prep_position', types.Integer),
        Column('corpus_file_id', CORPUS_FILE_TYPE),
        Column('sentence_id', types.Integer),
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
        Column('score', types.Float),
        mysql_engine='Aria',
    )


def get_table_mwe(meta: MetaData):
    return Table(
        'mwe', meta,
        Column('id', types.Integer),
        Column('collocation1_id', types.Integer),
        Column('collocation2_id', types.Integer),
        Column('label', Enum(RELATION_TYPE)),
        Column('lemma', LEMMA_TYPE),
        Column('lemma_tag', Enum(TAG_TYPE)),
        Column('frequency', types.Integer, default=1),
        Column('score', types.Float),
        mysql_engine='Aria',
    )


def get_table_mwe_match(meta: MetaData):
    return Table(
        'mwe_match', meta,
        Column('mwe_id', types.Integer),
        Column('match1_id', types.Integer),
        Column('match2_id', types.Integer),
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
