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
        return df.set_index(keys=['Id'], drop=True).T.iloc[0]
    else:
        return df


tables_columns = {
    'types': {
        'Id': str,
        'value': int
    },
    'mapping_function': {
        'Id': int,
        'Relation': str,
        'RelationType': int,
        'Usage': str,
        'Label': str,
        'Example': str
    },
    'mapping_POS': {
        'Id': int,
        'Pos': str
    },
    'mapping_lemma': {
        'Id': int,
        'Lemma': str
    },
    'mapping_corpus': {
        'Id': int,
        'CorpusName': str
    },
    'mapping_corpus_name': {
        'CorpusName': str,
        'CorpusFullName': str
    },
    'mapping_surface': {
        'Id': int,
        'Surface': str
    },
    'mapping_file': {
        'Id': int,
        'FileName': str
    },
    'mapping_TEI': {
        'CorpusId': int,
        'FileId': int,
        'Orig': str,
        'Scan': str,
        'TextClassId': int,
        'AvailId': int
    },
    'mapping_TEI_textclass': {
        'Id': int,
        'TextClass': str
    },
    'mapping_TEI_sigle': {
        'Id': int,
        'Sigle': str
    },
    'mapping_TEI_orig': {
        'Id': int,
        'BiblString': str
    },
    'mapping_TEI_scan': {
        'Id': int,
        'BiblString': str
    },
    'mapping_TEI_date': {
        'Id': int,
        'Date': "datetime64"
    },
    'mapping_TEI_avail': {
        'Id': int,
        'Rights': str
    },
    'mapping_position_info_tei': {
        'MatchId': int,
        'Word1Position': int, 'Word2Position': int, 'PrepPosition': int,
        'SentenceId': int, 'FileId': int, 'CorpusId': int,
        'Rights': int, 'DateId': int,
        'NegDateId': int,
        'GdexScore': int
    },
    'head_pos_rel_freq': {
        'LemmaId': int,
        'PosId': int,
        'RelationId': int,
        'Frequency': int, 'Count': int},
    'relations': {
        'RelationId': int,
        'PrepId': int, 'Lemma1Id': int, 'Lemma2Id': int,
        'PrepSurfaceId': int, 'Surface1Id': int, 'Surface2Id': int,
        'PrepPosId': int, 'Pos1Id': int, 'Pos2Id': int,
        'MatchId': int,
        'CountsWithRights': int,
        'Frequency': int,
        'MI3': float,
        'MiLogFreq': float,
        'TScore': float,
        'LogDice': float,
        'LogLike': float
    },
    'concord_sentences': {
        'CorpusId': int,
        'FileId': int,
        'SentencePosition': int,
        'Sentence': str,
        'Page': str
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

    map_function_name = dict(mapping_function[['Id', 'Relation']].values)
    map_function_type = dict(mapping_function[['Id', 'RelationType']].values)
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
    table_relations['Relation'] = table_relations.RelationId.map(map_function_name)
    table_relations['Prep'] = table_relations.PrepId.map(map_lemma)
    table_relations['Lemma1'] = table_relations.Lemma1Id.map(map_lemma)
    table_relations['Lemma2'] = table_relations.Lemma2Id.map(map_lemma)
    table_relations['PrepSurface'] = table_relations.PrepSurfaceId.map(map_surface)
    table_relations['Surface1'] = table_relations.Surface1Id.map(map_surface)
    table_relations['Surface2'] = table_relations.Surface2Id.map(map_surface)
    table_relations['PrepPos'] = table_relations.PrepPosId.map(map_pos)
    table_relations['Pos1'] = table_relations.Pos1Id.map(map_pos)
    table_relations['Pos2'] = table_relations.Pos2Id.map(map_pos)
    table_relations = table_relations[
        ['Relation', 'Prep', 'Lemma1', 'Lemma2', 'PrepSurface', 'Surface1', 'Surface2', 'PrepPos', 'Pos1', 'Pos2',
         'MatchId', 'CountsWithRights', 'Frequency', 'MI3', 'MiLogFreq', 'TScore', 'LogDice', 'LogLike']]
    table_relations.to_sql('rk_relations', con=engine, index=False, chunksize=256, if_exists='replace',
                           dtype={'PrepPos': types.VARCHAR(20), 'Pos1': types.VARCHAR(20), "Pos2": types.VARCHAR(20),
                                  'Relation': types.VARCHAR(10)})

    print('(: process head_pos_rel_freq')
    table_freqs = read_table(os.path.realpath(directory + '/head_pos_rel_freq.table'),
                             columns=tables_columns['head_pos_rel_freq'])
    table_freqs['Lemma'] = table_freqs.LemmaId.map(map_lemma)
    table_freqs['Pos'] = table_freqs.PosId.map(map_pos)
    table_freqs['Relation'] = table_freqs.RelationId.map(map_function_name)
    table_freqs['RelationType'] = table_freqs.RelationId.map(map_function_type)
    table_freqs = table_freqs[['Lemma', 'Pos', 'Relation', 'RelationType', 'Frequency', 'Count']]
    table_freqs.to_sql('rk_head_pos_rel_freq', con=engine, index=False, chunksize=256, if_exists='replace')

    print('(: process TEI infos')
    table_tei = read_table(os.path.realpath(directory + '/mapping_TEI.table'),
                           columns=tables_columns['mapping_TEI'])
    table_tei['TextClass'] = table_tei.TextClassId.map(map_textclass)
    table_tei['Avail'] = table_tei.AvailId.map(map_avail)
    table_tei['File'] = table_tei.FileId.map(map_file)
    table_tei['Corpus'] = table_tei.CorpusId.map(map_corpus)
    table_tei = table_tei[['Corpus', 'File', 'Orig', 'Scan', 'TextClass', 'Avail']]
    table_tei.to_sql('rk_tei', con=engine, index=False, chunksize=256, if_exists='replace',
                     dtype={'Corpus': types.VARCHAR(20), 'File': types.VARCHAR(100)})

    print('(: process concord sentences')
    concord_sentences = read_table(os.path.realpath(directory + '/concord_sentences.table'),
                                   columns=tables_columns['concord_sentences'])
    concord_sentences['File'] = concord_sentences.FileId.map(map_file)
    concord_sentences['Corpus'] = concord_sentences.CorpusId.map(map_corpus)
    concord_sentences = concord_sentences[['Corpus', 'File', 'SentencePosition', 'Sentence', 'Page']]
    concord_sentences.to_sql('rk_concord_sentences', con=engine, index=False, chunksize=256, if_exists='replace',
                             dtype={'Corpus': types.VARCHAR(20), 'File': types.VARCHAR(100)})
    print('(: build concord sentences INDEX')
    engine.execute("""
    CREATE UNIQUE INDEX rk_concord_sentences_CorpusId_IDX 
    USING BTREE 
    ON rk_concord_sentences (Corpus,File,SentencePosition);
    """)

    print('(: process matches')
    table_matches = read_table(os.path.realpath(directory + '/mapping_position_info_tei.table'),
                               columns=tables_columns['mapping_position_info_tei'])
    table_matches['File'] = table_matches.FileId.map(map_file)
    table_matches['Corpus'] = table_matches.CorpusId.map(map_corpus)
    table_matches['Date'] = table_matches.DateId.map(map_date)
    table_matches = table_matches[['MatchId', 'Word1Position', 'Word2Position', 'PrepPosition', 'SentenceId',
                                   'File', 'Corpus', 'Rights', 'Date', 'GdexScore']]
    table_matches.to_sql('rk_matches', con=engine, index=False, chunksize=256, if_exists='replace',
                         dtype={'Corpus': types.VARCHAR(20), 'File': types.VARCHAR(100)})
    print('(: build matches INDEX')
    engine.execute("""
        CREATE INDEX rk_matches_IDX 
        USING BTREE 
        ON rk_matches (MatchId);
        """)
    print('(: build matches corpus-file-sentence INDEX')
    engine.execute("""
        CREATE INDEX rk_matches_corpus_file_sent_IDX 
        USING BTREE 
        ON rk_matches (Corpus, File, SentenceId);
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
