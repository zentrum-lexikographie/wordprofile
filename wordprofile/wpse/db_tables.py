import datetime
from collections import namedtuple

from sqlalchemy import Table, Column, types, MetaData

LEMMA_TYPE = types.VARCHAR(100)
SURFACE_TYPE = types.VARCHAR(100)
CorpusFile = namedtuple('CorpusFile', ['id', 'corpus', 'file', 'orig', 'scan', 'text_class', 'available'])
ConcordSentence = namedtuple('ConcordSentence', ['corpus_file_id', 'sentence_id', 'sentence', 'page'])
Match = namedtuple('Match',
                   ['relation_label', 'head_lemma', 'dep_lemma', 'head_tag', 'dep_tag',
                    'head_surface', 'dep_surface', 'head_position', 'dep_position',
                    'prep_position', 'corpus_file_id', 'sentence_id', 'creation_date'])


def get_table_corpus_files(meta):
    return Table(
        'corpus_files', meta,
        Column('id', types.VARCHAR(24)),
        Column('corpus', types.VARCHAR(100)),
        Column('file', types.VARCHAR(200)),
        Column('orig', types.Text),
        Column('scan', types.Text),
        Column('text_class', types.Text),
        Column('available', types.Text),
    )


def get_table_concord_sentences(meta):
    return Table(
        'concord_sentences', meta,
        Column('sentence_id', types.Integer),
        Column('corpus_file_id', types.VARCHAR(24)),
        Column('sentence', types.Text),
        Column('page', types.VARCHAR(10)),
    )


def get_table_matches(meta):
    return Table(
        'matches', meta,
        Column('relation_label', types.VARCHAR(10)),
        Column('head_lemma', LEMMA_TYPE),
        Column('dep_lemma', LEMMA_TYPE),
        Column('head_tag', types.VARCHAR(10)),
        Column('dep_tag', types.VARCHAR(10)),
        Column('head_surface', SURFACE_TYPE),
        Column('dep_surface', SURFACE_TYPE),
        Column('head_position', types.Integer),
        Column('dep_position', types.Integer),
        Column('prep_position', types.Integer),
        Column('corpus_file_id', types.VARCHAR(24)),
        Column('sentence_id', types.Integer),
        Column('creation_date', types.DateTime),
    )


def get_table_collocations(meta):
    return Table(
        'collocations', meta,
        Column('id', types.Integer, primary_key=True, autoincrement=True),
        Column('label', types.VARCHAR(10)),
        Column('lemma1', LEMMA_TYPE),
        Column('lemma2', LEMMA_TYPE),
        Column('lemma1_tag', types.VARCHAR(10)),
        Column('lemma2_tag', types.VARCHAR(10)),
        Column('inv', types.Boolean, default=0),
        Column('frequency', types.Integer, default=1),
    )


def get_table_statistics(meta):
    return Table(
        'wp_stats', meta,
        Column('collocation_id', types.Integer),
        Column('mi', types.Float, default=0),
        Column('mi_log_freq', types.Float),
        Column('t_score', types.Float),
        Column('log_dice', types.Float),
        Column('log_like', types.Float),
    )


def insert_bulk_corpus_file(engine, corpus_files):
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


def insert_bulk_concord_sentences(engine, concord_sentences):
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


def insert_bulk_matches(engine, matches):
    meta = MetaData()
    matches_tb = get_table_matches(meta)
    query = matches_tb.insert()
    conn = engine.connect()
    conn.execute(query, matches)
    conn.close()


def prepare_matches(doc_id, matches):
    db_matches = []
    for m in matches:
        if m.prep:
            db_matches.append(Match(
                relation_label=m.relation,
                head_lemma="{} {}".format(m.head.lemma, m.prep.lemma),
                dep_lemma=m.dep.lemma,
                head_tag=m.head.upos,
                dep_tag=m.dep.upos,
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
                head_tag=m.head.upos,
                dep_tag=m.dep.upos,
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
                head_tag=m.head.upos,
                dep_tag=m.dep.upos,
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
