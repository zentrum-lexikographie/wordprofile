import datetime

from sqlalchemy import Table, Column, types, Index, ForeignKey, MetaData, and_


def get_table_corpus_files(meta):
    return Table(
        'corpus_files', meta,
        Column('id', types.Integer, primary_key=True, autoincrement=True),
        Column('corpus', types.VARCHAR(100)),
        Column('file', types.VARCHAR(200)),
        Column('orig', types.Text),
        Column('scan', types.Text),
        Column('text_class', types.Text),
        Column('available', types.Text),
        Index('corpus_file_index', 'corpus', 'file', unique=True)
    )


def get_table_concord_sentences(meta):
    return Table(
        'concord_sentences', meta,
        Column('id', types.Integer, primary_key=True, autoincrement=True),
        Column('sentence_id', types.Integer),
        Column('corpus_file_id', types.Integer, ForeignKey('corpus_files.id')),
        Column('sentence', types.Text),
        Column('page', types.VARCHAR(10)),
        Index('corpus_file_sentence_index', 'corpus_file_id', 'sentence_id', unique=True)
    )


def get_table_matches(meta):
    return Table(
        'matches', meta,
        Column('id', types.Integer, primary_key=True, autoincrement=True),
        Column('relation_id', types.Integer, ForeignKey('relations.id')),
        Column('head_position', types.Integer),
        Column('dep_position', types.Integer),
        Column('prep_position', types.Integer),
        Column('corpus_file_id', types.Integer, ForeignKey('corpus_files.id')),
        Column('sentence_id', types.Integer),
        Column('gdex_score', types.Integer),
        Column('creation_date', types.DateTime),
        Index('corpus_file_sentence_index', 'corpus_file_id', 'sentence_id')
    )


def get_table_relations(meta):
    return Table(
        'relations', meta,
        Column('id', types.Integer, primary_key=True, autoincrement=True),
        Column('label', types.VARCHAR(10)),
        Column('head_surface', types.Text),
        Column('dep_surface', types.Text),
        Column('prep_surface', types.Text),
        Column('head_lemma', types.Text),
        Column('dep_lemma', types.Text),
        Column('prep_lemma', types.Text),
        Column('head_pos', types.Text),
        Column('dep_pos', types.Text),
        Column('prep_pos', types.Text),
    )


def get_table_statistics(meta):
    return Table(
        'statistics', meta,
        Column('relation_id', types.Integer, ForeignKey('relations.id')),
        Column('date', types.Integer),
        Column('frequency', types.Integer),
        Column('mi', types.Float),
        Column('mi_log_freq', types.Float),
        Column('t_score', types.Float),
        Column('log_dice', types.Float),
        Column('log_like', types.Float),
        Index('wp_index', 'date', 'relation_id', unique=True)
    )


def get_corpus_file_id(engine, meta_data):
    meta = MetaData()
    corpus_file_tb = get_table_corpus_files(meta)
    query = corpus_file_tb.select().where(
        and_(
            corpus_file_tb.c.corpus == meta_data['collection'],
            corpus_file_tb.c.file == meta_data['basename']))
    conn = engine.connect()
    result = conn.execute(query)
    for row in result:
        return row['id']
    query = corpus_file_tb.insert().values(
        corpus=meta_data['collection'],
        file=meta_data['basename'],
        orig=meta_data['bibl'],
        scan=meta_data['biblLex'],
        text_class=meta_data['textClass'],
        available=meta_data['collection'],
    )
    result = conn.execute(query)
    return result.inserted_primary_key[0]


def insert_concord_sentences(engine, corpus_file_id, parses):
    meta = MetaData()
    concord_sentences_tb = get_table_concord_sentences(meta)
    query = concord_sentences_tb.insert()
    conn = engine.connect()
    result = conn.execute(query, [
        {
            'corpus_file_id': corpus_file_id,
            'sentence_id': sent_i + 1,
            'sentence': ''.join('{}{}'.format('\x01' if tok.misc == 0 else '\x02', tok.surface) for tok in parse),
            'page': '-'
        } for sent_i, parse in enumerate(parses)
    ])


def get_relation_id(engine, match):
    meta = MetaData()
    relations_tb = get_table_relations(meta)
    query = relations_tb.select().where(
        and_(
            relations_tb.c.head_surface == match.head.surface,
            relations_tb.c.dep_surface == match.dep.surface,
            relations_tb.c.prep_surface == (match.prep.surface if match.prep else '-'),
            relations_tb.c.head_pos == match.head.xpos,
            relations_tb.c.dep_pos == match.dep.xpos,
        ))
    conn = engine.connect()
    result = conn.execute(query)
    for row in result:
        return row['id']
    query = relations_tb.insert().values(
        label=match.relation,
        head_surface=match.head.surface,
        dep_surface=match.dep.surface,
        prep_surface=(match.prep.surface if match.prep else '-'),
        head_lemma=match.head.lemma,
        dep_lemma=match.dep.lemma,
        prep_lemma=(match.prep.lemma if match.prep else '-'),
        head_pos=match.head.xpos,
        dep_pos=match.dep.xpos,
        prep_pos=(match.prep.xpos if match.prep else '-'),

    )
    result = conn.execute(query)
    return result.inserted_primary_key[0]


def insert_matches(engine, corpus_file_id, relation_id, matches):
    meta = MetaData()
    matches_tb = get_table_matches(meta)
    query = matches_tb.insert()
    conn = engine.connect()
    result = conn.execute(query, [
        {
            'relation_id': relation_id,
            'head_position': match.head.idx,
            'dep_position': match.dep.idx,
            'prep_position': match.prep.idx if match.prep else 0,
            'corpus_file_id': corpus_file_id,
            'sentence_id': match.sid,
            'gdex_score': 0,
            'creation_date': datetime.datetime.now(),
        } for match in matches
    ])
