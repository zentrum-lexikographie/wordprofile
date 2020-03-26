import datetime
import enum
import re
from collections import namedtuple
from typing import List

from sqlalchemy import Table, Column, types, MetaData, Enum
from sqlalchemy.engine import Engine
from sqlalchemy.sql.schema import Index

from wordprofile import zdl
from wordprofile.zdl import RELATIONS, RELATIONS_PREP, SIMPLE_TAG_MAP

LEMMA_TYPE = types.VARCHAR(50)
SURFACE_TYPE = types.VARCHAR(50)
CORPUS_FILE_TYPE = types.VARCHAR(24)
RELATION_TYPE = enum.Enum('RELATION_TYPE', sorted(list(relations.keys()) + list(relations_prep.keys())))
TAG_TYPE = enum.Enum('TAG_TYPE', sorted(set(simplified_pos.values())))
CorpusFile = namedtuple('CorpusFile', ['id', 'corpus', 'file', 'orig', 'scan', 'text_class', 'available'])
ConcordSentence = namedtuple('ConcordSentence', ['corpus_file_id', 'sentence_id', 'sentence', 'page'])
Match = namedtuple('Match',
                   ['relation_label', 'head_lemma', 'dep_lemma', 'head_tag', 'dep_tag',
                    'head_surface', 'dep_surface', 'head_position', 'dep_position',
                    'prep_position', 'corpus_file_id', 'sentence_id', 'creation_date'])

re_pattern = re.compile(r'[^\u0000-\uD7FF\uE000-\uFFFF]', re.UNICODE)
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
        Column('sentence_id', types.Integer),
        Column('corpus_file_id', CORPUS_FILE_TYPE),
        Column('sentence', types.Text),
        Column('page', types.VARCHAR(10)),
        mysql_engine='Aria',
    )


def get_table_matches(meta: MetaData):
    return Table(
        'matches', meta,
        Column('relation_label', Enum(RELATION_TYPE)),
        Column('head_lemma', LEMMA_TYPE),
        Column('dep_lemma', LEMMA_TYPE),
        Column('head_tag', Enum(TAG_TYPE)),
        Column('dep_tag', Enum(TAG_TYPE)),
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
        Column('id', types.Integer, primary_key=True, autoincrement=True),
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


def insert_bulk_corpus_file(engine: Engine, corpus_files):
    meta = MetaData()
    corpus_file_tb = get_table_corpus_files(meta)
    query = corpus_file_tb.insert()
    conn = engine.connect()
    conn.execute(query, corpus_files)
    conn.close()


def prepare_corpus_file(doc):
    return CorpusFile(
        id=str(doc['_id']),
        corpus=doc['collection'],
        file=doc['basename'],
        orig=doc['bibl'],
        scan=doc['biblLex'],
        text_class=doc['textClass'],
        available=doc['collection'],
    )


def insert_bulk_concord_sentences(engine: Engine, concord_sentences):
    meta = MetaData()
    concord_sentences_tb = get_table_concord_sentences(meta)
    query = concord_sentences_tb.insert()
    conn = engine.connect()
    conn.execute(query, concord_sentences)
    conn.close()


def prepare_concord_sentences(doc_id, parses):
    return [ConcordSentence(
        corpus_file_id=doc_id,
        sentence_id=sent_i + 1,
        sentence=''.join('{}{}'.format('' if tok_i == 0 else '\x01' if tok.misc == 0 else '\x02', tok.surface)
                         for tok_i, tok in enumerate(parse)),
        page='-'
    ) for sent_i, parse in enumerate(parses)]


def insert_bulk_matches(engine: Engine, matches: List[dict]):
    meta = MetaData()
    matches_tb = get_table_matches(meta)
    query = matches_tb.insert()
    conn = engine.connect()
    conn.execute(query, matches)
    conn.close()


def prepare_matches(doc_id, matches: List[zdl.Match]):
    db_matches = []
    for m in matches:
        if (len(m.head.surface) > SURFACE_TYPE.length or len(m.dep.surface) > SURFACE_TYPE.length or
                len(m.head.lemma) > LEMMA_TYPE.length or len(m.dep.lemma) > LEMMA_TYPE.length):
            print("SKIP LOONG MATCH", doc_id, m)
            continue
        if m.prep:
            if (len(m.head.surface) + len(m.prep.surface) + 1 > SURFACE_TYPE.length or
                    len(m.dep.surface) + len(m.prep.surface) + 1 > SURFACE_TYPE.length or
                    len(m.head.lemma) + len(m.prep.surface) + 1 > LEMMA_TYPE.length or
                    len(m.dep.lemma) + len(m.prep.surface) + 1 > LEMMA_TYPE.length):
                print("SKIP LOONG MATCH", doc_id, m)
                continue
            db_matches.append(Match(
                relation_label=RELATION_TYPE[m.relation],
                head_lemma="{} {}".format(m.head.lemma, m.prep.lemma),
                dep_lemma=m.dep.lemma,
                head_tag=TAG_TYPE[m.head.tag],
                dep_tag=TAG_TYPE[m.dep.tag],
                head_surface="{} {}".format(m.head.surface, m.prep.surface),
                dep_surface=m.dep.surface,
                head_position=m.head.idx,
                dep_position=m.dep.idx,
                prep_position=m.prep.idx,
                corpus_file_id=doc_id,
                sentence_id=m.sid,
                creation_date=datetime.datetime.now()
            ))
            db_matches.append(Match(
                relation_label=m.relation,
                head_lemma=m.head.lemma,
                dep_lemma="{} {}".format(m.prep.lemma, m.dep.lemma),
                head_tag=m.head.tag,
                dep_tag=m.dep.tag,
                head_surface=m.head.surface,
                dep_surface="{} {}".format(m.prep.surface, m.dep.surface),
                head_position=m.head.idx,
                dep_position=m.dep.idx,
                prep_position=m.prep.idx,
                corpus_file_id=doc_id,
                sentence_id=m.sid,
                creation_date=datetime.datetime.now()
            ))
        else:
            db_matches.append(Match(
                relation_label=m.relation,
                head_lemma=m.head.lemma,
                dep_lemma=m.dep.lemma,
                head_tag=m.head.tag,
                dep_tag=m.dep.tag,
                head_surface=m.head.surface,
                dep_surface=m.dep.surface,
                head_position=m.head.idx,
                dep_position=m.dep.idx,
                prep_position=0,
                corpus_file_id=doc_id,
                sentence_id=m.sid,
                creation_date=datetime.datetime.now()
            ))
    return db_matches
