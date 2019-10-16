#!/usr/bin/python3
import getpass
import os
from argparse import ArgumentParser

import pandas as pd
from sqlalchemy import create_engine, types


def read_table(path, columns=None, mapping=False):
    file_lines = open(path, 'rb').readlines()
    df = pd.DataFrame(map(lambda b: b.decode().strip().split('\t'), file_lines), columns=list(columns.keys()))
    df = df.astype(columns)
    if mapping:
        return df.set_index(keys=['id'], drop=True).T.iloc[0]
    else:
        return df


tables_columns = {
    'types': {
        'id': str,
        'value': int
    },
    'mapping_function': {
        'id': int,
        'relation': str,
        'relation_type': int,
        'usage': str,
        'label': str,
        'example': str
    },
    'mapping_POS': {
        'id': int,
        'pos': str
    },
    'mapping_lemma': {
        'id': int,
        'lemma': str
    },
    'mapping_corpus': {
        'id': int,
        'corpus_name': str
    },
    'mapping_corpus_name': {
        'corpus_name': str,
        'corpus_fullname': str
    },
    'mapping_surface': {
        'id': int,
        'surface': str
    },
    'mapping_file': {
        'id': int,
        'file_name': str
    },
    'mapping_TEI': {
        'corpus_id': int,
        'file_id': int,
        'orig': str,
        'scan': str,
        'text_class_id': int,
        'avail_id': int
    },
    'mapping_TEI_textclass': {
        'id': int,
        'text_class': str
    },
    'mapping_TEI_sigle': {
        'id': int,
        'sigle': str
    },
    'mapping_TEI_orig': {
        'id': int,
        'bibl_string': str
    },
    'mapping_TEI_scan': {
        'id': int,
        'bibl_string': str
    },
    'mapping_TEI_date': {
        'id': int,
        'date': "datetime64"
    },
    'mapping_TEI_avail': {
        'id': int,
        'rights': str
    },
    'mapping_position_info_tei': {
        'match_id': int,
        'head_position': int, 'dep_position': int, 'prep_position': int,
        'sentence_id': int, 'file_id': int, 'corpus_id': int,
        'rights': int, 'date_id': int,
        'neg_date_id': int,
        'gdex_score': int
    },
    'head_pos_rel_freq': {
        'lemma_id': int,
        'pos_id': int,
        'relation_id': int,
        'frequency': int, 'count': int},
    'relations': {
        'relation_id': int,
        'prep_id': int, 'head_lemma': int, 'dep_lemma': int,
        'prep_surface_id': int, 'head_surface_id': int, 'dep_surface_id': int,
        'prep_pos_id': int, 'head_pos_id': int, 'dep_pos_id': int,
        'match_id': int,
        'counts_with_rights': int,
        'frequency': int,
        'mi3': float,
        'mi_log_freq': float,
        't_score': float,
        'log_dice': float,
        'log_like': float
    },
    'concord_sentences': {
        'corpus_id': int,
        'file_id': int,
        'sentence_id': int,
        'sentence': str,
        'page': str
    },
}


def create_new_tables(engine, directory):
    print('(: get mappings')
    mapping_function = read_table(os.path.realpath(directory + '/mapping_function.table'),
                                  columns=tables_columns['mapping_function'])
    mapping_lemma = read_table(os.path.realpath(directory + '/mapping_lemma.table'),
                               columns=tables_columns['mapping_lemma'])
    mapping_surface = read_table(os.path.realpath(directory + '/mapping_surface.table'),
                                 columns=tables_columns['mapping_surface'])
    mapping_pos = read_table(os.path.realpath(directory + '/mapping_POS.table'), columns=tables_columns['mapping_POS'])
    mapping_file = read_table(os.path.realpath(directory + '/mapping_file.table'),
                              columns=tables_columns['mapping_file'])
    mapping_corpus = read_table(os.path.realpath(directory + '/mapping_corpus.table'),
                                columns=tables_columns['mapping_corpus'])
    mapping_date = read_table(os.path.realpath(directory + '/mapping_TEI_date.table'),
                              columns=tables_columns['mapping_TEI_date'])
    mapping_avail = read_table(os.path.realpath(directory + '/mapping_TEI_avail.table'),
                               columns=tables_columns['mapping_TEI_avail'])
    mapping_textclass = read_table(os.path.realpath(directory + '/mapping_TEI_textclass.table'),
                                   columns=tables_columns['mapping_TEI_textclass'])

    map_function_name = dict(mapping_function[['id', 'relation']].values)
    map_function_type = dict(mapping_function[['id', 'relation_type']].values)
    map_lemma = dict(mapping_lemma.values)
    map_surface = dict(mapping_surface.values)
    map_pos = dict(mapping_pos.values)
    map_file = dict(mapping_file.values)
    map_corpus = dict(mapping_corpus.values)
    map_date = dict(mapping_date.values)
    map_avail = dict(mapping_avail.values)
    map_textclass = dict(mapping_textclass.values)

    print('(: process relations')
    table_relations = read_table(os.path.realpath(directory + '/relations.table'), columns=tables_columns['relations'])
    table_relations['relation'] = table_relations.relation_id.map(map_function_name)
    table_relations['prep_lemma'] = table_relations.prep_id.map(map_lemma)
    table_relations['head_lemma'] = table_relations.head_lemma.map(map_lemma)
    table_relations['dep_lemma'] = table_relations.dep_lemma.map(map_lemma)
    table_relations['prep_surface'] = table_relations.prep_surface_id.map(map_surface)
    table_relations['head_surface'] = table_relations.head_surface_id.map(map_surface)
    table_relations['dep_surface'] = table_relations.dep_surface_id.map(map_surface)
    table_relations['prep_surface'] = table_relations.prep_pos_id.map(map_pos)
    table_relations['head_pos'] = table_relations.head_pos_id.map(map_pos)
    table_relations['dep_pos'] = table_relations.dep_pos_id.map(map_pos)
    table_relations = table_relations[
        ['relation', 'prep_lemma', 'head_lemma', 'dep_lemma', 'prep_surface', 'head_surface', 'dep_surface',
         'prep_surface', 'head_pos', 'dep_pos',
         'match_id', 'counts_with_rights', 'frequency', 'mi3', 'mi_log_freq', 't_score', 'log_dice', 'log_like']]
    table_relations.to_sql('relations', con=engine, index=False, chunksize=256, if_exists='replace',
                           dtype={'prep_surface': types.VARCHAR(20), 'head_pos': types.VARCHAR(20),
                                  'dep_pos': types.VARCHAR(20),
                                  'relation': types.VARCHAR(10)})

    print('(: process head_pos_rel_freq')
    table_freqs = read_table(os.path.realpath(directory + '/head_pos_rel_freq.table'),
                             columns=tables_columns['head_pos_rel_freq'])
    table_freqs['lemma'] = table_freqs.lemma_id.map(map_lemma)
    table_freqs['pos'] = table_freqs.pos_id.map(map_pos)
    table_freqs['relation'] = table_freqs.relation_id.map(map_function_name)
    table_freqs['relation_type'] = table_freqs.relation_id.map(map_function_type)
    table_freqs = table_freqs[['lemma', 'pos', 'relation', 'relation_type', 'frequency', 'count']]
    table_freqs.to_sql('head_pos_rel_freq', con=engine, index=False, chunksize=256, if_exists='replace')

    print('(: process TEI infos')
    table_tei = read_table(os.path.realpath(directory + '/mapping_TEI.table'),
                           columns=tables_columns['mapping_TEI'])
    table_tei['text_class'] = table_tei.text_class_id.map(map_textclass)
    table_tei['available'] = table_tei.avail_id.map(map_avail)
    table_tei['file'] = table_tei.file_id.map(map_file)
    table_tei['corpus'] = table_tei.corpus_id.map(map_corpus)
    table_tei = table_tei[['corpus', 'file', 'orig', 'scan', 'text_class', 'available']]
    table_tei.to_sql('corpus_files', con=engine, index=False, chunksize=256, if_exists='replace',
                     dtype={'corpus': types.VARCHAR(20), 'file': types.VARCHAR(100)})

    print('(: process concord sentences')
    concord_sentences = read_table(os.path.realpath(directory + '/concord_sentences.table'),
                                   columns=tables_columns['concord_sentences'])
    concord_sentences['file'] = concord_sentences.file_id.map(map_file)
    concord_sentences['corpus'] = concord_sentences.corpus_id.map(map_corpus)
    concord_sentences = concord_sentences[['corpus', 'file', 'sentence_id', 'sentence', 'page']]
    concord_sentences.to_sql('concord_sentences', con=engine, index=False, chunksize=256, if_exists='replace',
                             dtype={'corpus': types.VARCHAR(20), 'file': types.VARCHAR(100)})
    print('(: build concord sentences INDEX')
    engine.execute("""
    CREATE UNIQUE INDEX concord_sentences_corpus_IDX 
    USING BTREE 
    ON concord_sentences (corpus, file, sentence_id);
    """)

    print('(: process matches')
    table_matches = read_table(os.path.realpath(directory + '/mapping_position_info_tei.table'),
                               columns=tables_columns['mapping_position_info_tei'])
    table_matches['file'] = table_matches.file_id.map(map_file)
    table_matches['corpus'] = table_matches.corpus_id.map(map_corpus)
    table_matches['date'] = table_matches.date_id.map(map_date)
    table_matches = table_matches[['match_id', 'head_position', 'dep_position', 'prep_position', 'sentence_id',
                                   'file', 'corpus', 'rights', 'date', 'gdex_score']]
    table_matches.to_sql('matches', con=engine, index=False, chunksize=256, if_exists='replace',
                         dtype={'corpus': types.VARCHAR(20), 'file': types.VARCHAR(100)})
    print('(: build matches INDEX')
    engine.execute("""
        CREATE INDEX matches_IDX 
        USING BTREE 
        ON matches (match_id);
        """)
    print('(: build matches corpus-file-sentence INDEX')
    engine.execute("""
        CREATE INDEX matches_corpus_file_sent_IDX 
        USING BTREE 
        ON matches (corpus, file, sentence_id);
        """)


def main():
    print("|: CREATE MYSQL DATABASE")
    parser = ArgumentParser()
    parser.add_argument("--user", type=str, help="database username", required=True)
    parser.add_argument("--database", type=str, help="database name", required=True)
    parser.add_argument("--table-path", type=str, help="path for tables", required=True)

    args = parser.parse_args()

    print('|: user: ' + args.user)
    print('|: db: ' + args.database)
    db_password = getpass.getpass("db password: ")

    engine = create_engine('mysql+pymysql://{}:{}@localhost'.format(
        args.user, db_password))

    engine.execute("DROP DATABASE IF EXISTS " + args.database)
    engine.execute("CREATE DATABASE " + args.database + " CHARACTER SET utf8")
    engine.execute("set autocommit=1")
    engine.execute("USE " + args.database)

    create_new_tables(engine, args.table_path.rstrip('/'))

    print()
    print("(: done")


if __name__ == '__main__':
    main()
