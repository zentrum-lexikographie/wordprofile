#!/usr/bin/python3

"""

  Das Programm erstellt anhand der Wortprofil-Statistik-Tabellen eine MySQL-Datenbank:
    -mapping_POS.table
    -mapping_function.table
    -mapping_lemma.table
    -mapping_lemma_lower.table
    -mapping_surface.table
    -relations.table
    -head_pos_freq.table
    -head_pos_rel_freq.table
    -mapping_file.table
    -mapping_corpus.table
    -threshold_rel.table
    -rel_info.table

"""

import os
import sys
from optparse import OptionParser

import MySQLdb
import pandas as pd
from sqlalchemy import create_engine


# from sqlalchemy.dialects.mysql import INTEGER

def read_table(path, columns=None, mapping=False):
    file_lines = open(path, 'rb').readlines()
    df = pd.DataFrame(map(lambda b: b.decode().strip().split('\t'), file_lines), columns=columns)
    if mapping:
        # df.iloc[:, 0] = df.iloc[:, 0].apply(pd.to_numeric)
        return df.set_index(keys=[0], drop=True).T.iloc[0]
    else:
        return df


tables_columns = {
    # mappings
    'mapping_function': ['Id', 'Relation', 'RandomType', 'Usage', 'Label', 'Example'],  # TODO what is random type?
    'mapping_POS': ['Id', 'POS'],
    'mapping_lemma': ['Id', 'Lemma'],
    'mapping_corpus': ['Id', 'CorpusName'],
    'mapping_corpus_name': ['CorpusName', 'CorpusFullName'],
    'mapping_surface': ['Id', 'Surface'],
    'mapping_file': ['Id', 'FileName'],
    # TEI mappings?
    'mapping_TEI': ['CorpusId', 'FileId', 'Orig', 'Scan', 'TextClassId', 'AvailId'],
    'mapping_TEI_textclass': ['Id', 'TextClass'],
    'mapping_TEI_sigle': ['Id', 'Sigle'],
    'mapping_TEI_orig': ['Id', 'BiblString'],
    'mapping_TEI_scan': ['Id', 'BiblString'],
    'mapping_TEI_date': ['Id', 'Date'],
    'mapping_TEI_avail': ['Id', 'Rights'],
    # important tables!
    'mapping_position_info_tei': ['MatchId', 'WortPosition1', 'WordPosition2', 'PrepPosition',
                                  'SentencePosition', 'FileId', 'CorpusId', 'Rights', 'DatumId', 'NegDatumId',
                                  'GdexScore'],
    'relations': ['RelationId', 'Lemma1Id', 'Lemma2Id', 'Lemma3Id',
                  'Surface1Id', 'Surface2Id', 'Surface3Id',
                  'Pos1Id', 'Pos2Id', 'Pos3Id',
                  'MatchId', 'CountsWithRights',
                  'Frequency', 'MI3', 'MiLogFreq', 'TScore', 'LogDice', 'LogLike'],
    'concord_sentences': ['CorpusId', 'FileId', 'SentencePosition', 'Sentence', 'Page'],
}

"""
"""

g_strLocal = ''
g_bSubCorpus = False
g_listCorpus = []

"""
 für ein Integer den unsigned-MySQL-Typ ermitteln
"""


def get_type(iSize):
    if iSize <= 255:
        return "TINYINT unsigned NOT NULL"
    elif iSize <= 65535:
        return "SMALLINT unsigned NOT NULL"
    elif iSize <= 16777215:
        return "MEDIUMINT unsigned NOT NULL"
    elif iSize <= 4294967295:
        return "INT unsigned NOT NULL"
    else:
        return "BIGINT unsigned NOT NULL"


"""
 für ein Integer den signed-MySQL-Typ ermitteln
"""


def get_type_signed(iSize):
    if iSize <= 127:
        return "TINYINT signed NOT NULL"
    elif iSize <= 32767:
        return "SMALLINT signed NOT NULL"
    elif iSize <= 8388607:
        return "MEDIUMINT signed NOT NULL"
    elif iSize <= 2147483647:
        return "INT signed NOT NULL"
    else:
        return "BIGINT signed NOT NULL"


"""
 für einen String (anhand der Länge) den MySQL-Typ ermitteln
"""


def get_type_char(iLength):
    if iLength > 4294967295:
        print("text zu groß")
        sys.exit(-1)
    elif iLength > 16777215:
        return "LONGTEXT BINARY NOT NULL"
    elif iLength > 65535:
        return "MEDIUMTEXT BINARY NOT NULL"
    elif iLength > 255:
        return "TEXT BINARY NOT NULL"
    else:
        return "CHAR(" + str(iLength) + ") BINARY NOT NULL"


"""
 Erstellen der MySQL-Tabellen
"""


def create_tables(cursor, directory, g_bSubCorpus=False):
    global g_listCorpus
    engine = create_engine('mysql+pymysql://wpuser:wpuser@localhost/wordprofile2')

    # table_relations = read_table(os.path.realpath(directory + '/relations.table'), columns=tables_columns['relations'])
    # mapping_function = read_table(os.path.realpath(directory + '/mapping_function.table'),
    #                               columns=tables_columns['mapping_function'])
    # table_relations['Relation'] = pd.merge(
    #     table_relations, mapping_function, left_on='RelationId', right_on='Id')['Relation']
    # mapping_lemma = read_table(os.path.realpath(directory + '/mapping_lemma.table'),
    #                            columns=tables_columns['mapping_lemma'])
    # table_relations['Lemma1'] = pd.merge(
    #     table_relations, mapping_lemma, left_on='Lemma1Id', right_on='Id')['Lemma']
    # table_relations['Lemma2'] = pd.merge(
    #     table_relations, mapping_lemma, left_on='Lemma2Id', right_on='Id')['Lemma']
    # table_relations['Lemma3'] = pd.merge(
    #     table_relations, mapping_lemma, left_on='Lemma3Id', right_on='Id')['Lemma']
    # mapping_surface = read_table(os.path.realpath(directory + '/mapping_surface.table'),
    #                              columns=tables_columns['mapping_surface'])
    # table_relations['Surface1'] = pd.merge(
    #     table_relations, mapping_surface, left_on='Surface1Id', right_on='Id')['Surface']
    # table_relations['Surface2'] = pd.merge(
    #     table_relations, mapping_surface, left_on='Surface2Id', right_on='Id')['Surface']
    # table_relations['Surface3'] = pd.merge(
    #     table_relations, mapping_surface, left_on='Surface3Id', right_on='Id')['Surface']
    # mapping_pos = read_table(os.path.realpath(directory + '/mapping_POS.table'), columns=tables_columns['mapping_POS'])
    # table_relations['Pos1'] = pd.merge(
    #     table_relations, mapping_pos, left_on='Pos1Id', right_on='Id')['POS']
    # table_relations['Pos2'] = pd.merge(
    #     table_relations, mapping_pos, left_on='Pos2Id', right_on='Id')['POS']
    # table_relations['Pos3'] = pd.merge(
    #     table_relations, mapping_pos, left_on='Pos3Id', right_on='Id')['POS']
    # table_relations = table_relations[
    #     ['Relation', 'Lemma1', 'Lemma2', 'Lemma3', 'Surface1', 'Surface2', 'Surface3', 'Pos1', 'Pos2', 'Pos3',
    #      'MatchId', 'CountsWithRights', 'Frequency', 'MI3', 'MiLogFreq', 'TScore', 'LogDice', 'LogLike']]
    # table_relations.to_sql('relations_test', con=engine, index=False, chunksize=32)

    mapping_tei = read_table(os.path.realpath(directory + '/mapping_TEI.table'),
                             columns=tables_columns['mapping_TEI'])
    mapping_textclass = read_table(os.path.realpath(directory + '/mapping_TEI_textclass.table'),
                                   columns=tables_columns['mapping_TEI_textclass'])
    mapping_tei['TextClass'] = pd.merge(mapping_tei, mapping_textclass, left_on='TextClassId', right_on='Id')[
        'TextClass']
    mapping_avail = read_table(os.path.realpath(directory + '/mapping_TEI_avail.table'),
                               columns=tables_columns['mapping_TEI_avail'])
    mapping_tei['Avail'] = pd.merge(mapping_tei, mapping_avail, left_on='AvailId', right_on='Id')['Rights']
    mapping_files = read_table(os.path.realpath(directory + '/mapping_file.table'),
                               columns=tables_columns['mapping_file'])
    mapping_tei['FileId'] = pd.merge(mapping_tei, mapping_files, left_on='FileId', right_on='Id')['FileName']
    mapping_corpus = read_table(os.path.realpath(directory + '/mapping_corpus.table'),
                                columns=tables_columns['mapping_corpus'])
    mapping_tei['CorpusId'] = pd.merge(mapping_tei, mapping_corpus, left_on='CorpusId', right_on='Id')['CorpusName']
    mapping_tei = mapping_tei[['CorpusId', 'FileId', 'Orig', 'Scan', 'TextClass', 'Avail']]
    mapping_tei.to_sql('mapping_tei_test', con=engine, index=False, chunksize=32)

    print('(: get data types')
    table_types = read_table(os.path.realpath(directory + '/types.table'), mapping=True)
    cursor.execute("""
    CREATE TABLE types
    (
     type     CHAR(30),
     value int unsigned,
     index (type)
    )
    """)
    cursor.execute(
        "LOAD DATA " + g_strLocal + " INFILE \"" + os.path.realpath(directory + "/types.table") + "\" INTO TABLE types")

    ### Ermitteln der MySQL-Typen
    typeMI3Str = str(int(table_types['MI3Length']) + 2)
    typeMiLogFreqStr = str(int(table_types['MiLogFreqLength']) + 2)
    typeTScoreStr = str(int(table_types['TScoreLength']) + 2)
    typelogDiceStr = str(int(table_types['LogDiceLength']) + 2)
    typelogLikeStr = str(int(table_types['LogLikeLength']) + 2)

    typeLemmaId = get_type(int(table_types['lemmaSize']))
    typeLemmaStrCaseInsensitive = "CHAR(" + str(int(table_types['lemmaLength'])) + ") BINARY"

    typeSurfaceId = get_type(int(table_types['surfaceSize']))
    typeSurfaceStr = "CHAR(" + str(int(table_types['surfaceLength'])) + ") BINARY"

    typePOSId = get_type(int(table_types['POSSize']))
    typePOSStr = "CHAR(" + str(int(table_types['POSLength'])) + ") BINARY"

    typeCorpusId = get_type(int(table_types['corpusSize']))
    typeCorpusStr = "CHAR(" + str(int(table_types['corpusLength'])) + ") BINARY"

    typeInfoId = get_type(int(table_types['infoSize']))

    typeFrequency = get_type_signed(int(table_types['highestFrequency']))
    typeHeadPosFrequency = get_type(int(table_types['highestHeadPosFrequency']))

    typeText = get_type(int(table_types['highestText']))

    typeFunctionId = get_type(int(table_types['highestFunction']))
    typeFunctionStr = "CHAR(" + str(int(table_types['functionLength'])) + ") BINARY"
    typeSnippetStr = "CHAR(" + str(int(table_types['snippetLength'])) + ") BINARY"
    typeDescriptionStr = "CHAR(" + str(int(table_types['descriptionLength'])) + ") BINARY"
    typeExampleStr = "CHAR(" + str(int(table_types['exampleLength'])) + ") BINARY"

    ### Erzeugen der MySQL-Tabellen
    print('(: create tables')

    ### mapping_corpus.table
    cursor.execute("""
  CREATE TABLE idToCorpus
  (
   id """ + typeCorpusId + """,
   Corpus """ + typeCorpusStr + """,
   primary key (id)
  )
  """)
    ### Abfragen der verwendeten Korpusnamen
    cursor.execute("LOAD DATA " + g_strLocal + " INFILE \"" + os.path.realpath(
        directory + "/mapping_corpus.table") + "\" INTO TABLE idToCorpus")
    cursor = conn.cursor()
    cursor.execute("SELECT Corpus FROM idToCorpus")
    g_listCorpus = cursor.fetchall()

    ### mapping_corpus.table
    cursor.execute("""
  CREATE TABLE idToFile
  (
   id """ + typeText + """,
   File     TEXT,
   primary key (id)
  )
  """)

    cursor.execute("""
  CREATE TABLE idToPOS
  (
   id """ + typePOSId + """,
   POS     """ + typePOSStr + """,
   primary key (id)
  )
  """)

    cursor.execute("""
  CREATE TABLE headPosFreq
  (
   id """ + typeLemmaId + """,
   POS     """ + typePOSId + """,
   frequency """ + typeHeadPosFrequency + """,
   count """ + typeHeadPosFrequency + """,
   index (id)
  )
  """)

    cursor.execute("""
  CREATE TABLE headPosRelFreq
  (
   id """ + typeLemmaId + """,
   POS     """ + typePOSId + """,
   relation  """ + typeFunctionId + """,
   frequency """ + typeHeadPosFrequency + """,
   count """ + typeHeadPosFrequency + """,
   index (id)
  )
  """)

    cursor.execute("""
  CREATE TABLE idToFunction
  (
   id """ + typeFunctionId + """,
   Function """ + typeFunctionStr + """,
   Type TINYINT unsigned,
   Snippet """ + typeSnippetStr + """,
   Description """ + typeDescriptionStr + """,
   Example """ + typeExampleStr + """,
   primary key (id)
  )
  """)

    cursor.execute("""
  CREATE TABLE lemmaToRelation
  (
   id """ + typeLemmaId + """,
   lemma """ + typeLemmaStrCaseInsensitive + """,
   index (lemma),
   index (id)
  )
  """)

    #   cursor.execute("""
    # CREATE TABLE lemmaToRelationLower
    # (
    #  id """ + typeLemmaId + """,
    #  lemma """ + typeLemmaStrCaseInsensitive + """,
    #  index (lemma),
    #  index (id)
    # )
    # """)

    cursor.execute("""
  CREATE TABLE idToSurface
  (
   id """ + typeSurfaceId + """,
   surface """ + typeSurfaceStr + """,
   primary key (id)
  )
  """)

    cursor.execute("""
  CREATE TABLE relations
  (
   function """ + typeFunctionId + """,
   prep """ + typeLemmaId + """,
   lemma1 """ + typeLemmaId + """,
   lemma2 """ + typeLemmaId + """,
   surfacePrep """ + typeSurfaceId + """,
   surface1 """ + typeSurfaceId + """,
   surface2 """ + typeSurfaceId + """,
   PrepPOS """ + typePOSId + """,
   POS1 """ + typePOSId + """,
   POS2 """ + typePOSId + """,
   info """ + typeInfoId + """,
   freqBelege """ + typeFrequency + """,
   frequency """ + typeFrequency + """,
   MI3 float(""" + typeMI3Str + """,2),
   MiLogFreq float(""" + typeMiLogFreqStr + """,2),
   TScore float(""" + typeTScoreStr + """,2),
   logDice float(""" + typelogDiceStr + """,2),
   logLike float(""" + typelogLikeStr + """,0),

   index I_MiLogFreq (function,lemma1,POS1,MiLogFreq),
   index I_frequency (function,lemma1,POS1,frequency),
   index I_logDice (function,lemma1,POS1,logDice),

   index I_info (info)
  )
  """)

    #   cursor.execute("""
    # CREATE TABLE relationsOhneIndex
    # (
    #  function """ + typeFunctionId + """,
    #  prep """ + typeLemmaId + """,
    #  lemma1 """ + typeLemmaId + """,
    #  lemma2 """ + typeLemmaId + """,
    #  surfacePrep """ + typeSurfaceId + """,
    #  surface1 """ + typeSurfaceId + """,
    #  surface2 """ + typeSurfaceId + """,
    #  PrepPOS """ + typePOSId + """,
    #  POS1 """ + typePOSId + """,
    #  POS2 """ + typePOSId + """,
    #  info """ + typeInfoId + """,
    #  freqBelege """ + typeFrequency + """,
    #  frequency """ + typeFrequency + """,
    #  MI3 float(""" + typeMI3Str + """,2),
    #  MiLogFreq float(""" + typeMiLogFreqStr + """,2),
    #  TScore float(""" + typeTScoreStr + """,2),
    #  logDice float(""" + typelogDiceStr + """,2),
    #  logLike float(""" + typelogLikeStr + """,0)
    # )
    # """)

    ### threshold_rel.table
    cursor.execute("""
  CREATE TABLE threshold
  (
   id """ + typeFunctionId + """,
   type CHAR(20) BINARY NOT NULL,
   value float,

   index I_id (id)
  )
  """)

    ### info.table
    cursor.execute("""
  CREATE TABLE Info
  (
   InfoKey VARCHAR(1000) NOT NULL,
   InfoValue VARCHAR(1000) NOT NULL
  )
  """)

    ### rel_info.table
    cursor.execute("""
  CREATE TABLE relInfo
  (
   id """ + typeFunctionId + """,

   count INT unsigned NOT NULL,
   frequency INT unsigned NOT NULL,
   freqBelege INT unsigned NOT NULL,

   primary key (id)
  )
  """)

    ### mapping_corpus_name.table
    cursor.execute("""
  CREATE TABLE CorpusName
  (
   shortName VARCHAR(1000) NOT NULL,
   fullName VARCHAR(1000) NOT NULL
  )
  """)

    if g_bSubCorpus:
        for i in g_listCorpus:
            cursor.execute("""
      CREATE TABLE """ + i[0] + """headPosFreq
      (
       id """ + typeLemmaId + """,
       POS     """ + typePOSId + """,
       frequency """ + typeHeadPosFrequency + """,
       count """ + typeHeadPosFrequency + """,
       index (id)
      )
      """)

        for i in g_listCorpus:
            cursor.execute("""
      CREATE TABLE """ + i[0] + """headPosRelFreq
      (
       id """ + typeLemmaId + """,
       POS     """ + typePOSId + """,
       relation  """ + typeFunctionId + """,
       frequency """ + typeHeadPosFrequency + """,
       count """ + typeHeadPosFrequency + """,
       index (id)
      )
      """)

        for i in g_listCorpus:
            cursor.execute("""
      CREATE TABLE """ + i[0] + """relations
      (
       function """ + typeFunctionId + """,
       prep """ + typeLemmaId + """,
       lemma1 """ + typeLemmaId + """,
       lemma2 """ + typeLemmaId + """,
       surfacePrep """ + typeSurfaceId + """,
       surface1 """ + typeSurfaceId + """,
       surface2 """ + typeSurfaceId + """,
       PrepPOS """ + typePOSId + """,
       POS1 """ + typePOSId + """,
       POS2 """ + typePOSId + """,
       info """ + typeInfoId + """,
       freqBelege """ + typeFrequency + """,
       frequency """ + typeFrequency + """,
       MI3 float(""" + typeMI3Str + """,2),
       MiLogFreq float(""" + typeMiLogFreqStr + """,2),
       AScore float(""" + typeTScoreStr + """,2),
       logDice float(""" + typelogDiceStr + """,2),
       LogLike float(""" + typelogLikeStr + """,0),

       index I_MiLogFreq (lemma1,POS1,MiLogFreq),
       index I_frequency (lemma1,POS1,frequency),
       index I_MI3 (lemma1,POS1,MI3),
       index I_AScore (lemma1,POS1,AScore),
       index I_logDice (lemma1,POS1,logDice),

       index I_info (info)
      )
      """)

    return


"""
 Laden der Wortprofiltabellen in die MySQL-Tabellen
"""


def load_into_tables(cursor, directory):
    global g_bSubCorpus
    global g_listCorpus

    # print '(: load data: '+ os.path.realpath(directory +'/mapping_corpus.table')
    # cursor.execute ("LOAD DATA " + g_strLocal + " INFILE \""+os.path.realpath(directory +"/mapping_corpus.table")+"\" INTO TABLE idToCorpus")

    print('(: load data: ' + os.path.realpath(directory + '/mapping_corpus_name.table'))
    cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
        directory + '/mapping_corpus_name.table') + '\" INTO TABLE CorpusName')

    print('(: load data: ' + os.path.realpath(directory + '/mapping_POS.table'))
    cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
        directory + '/mapping_POS.table') + '\" INTO TABLE idToPOS')

    print('(: load data: ' + os.path.realpath(directory + '/mapping_function.table'))
    cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
        directory + '/mapping_function.table') + '\" INTO TABLE idToFunction')

    print('(: load data: ' + os.path.realpath(directory + '/mapping_lemma.table'))
    cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
        directory + '/mapping_lemma.table') + '\" INTO TABLE lemmaToRelation')

    # print('(: load data: ' + os.path.realpath(directory + '/mapping_lemma_lower.table'))
    # cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
    #     directory + '/mapping_lemma_lower.table') + '\" INTO TABLE lemmaToRelationLower')

    print('(: load data: ' + os.path.realpath(directory + '/mapping_surface.table'))
    cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
        directory + '/mapping_surface.table') + '\" INTO TABLE idToSurface')

    print('(: load data: ' + os.path.realpath(directory + '/relations.table'))
    cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
        directory + '/relations.table') + '\" INTO TABLE relations')

    print('(: load data: ' + os.path.realpath(directory + '/head_pos_freq.table'))
    cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
        directory + '/head_pos_freq.table') + '\" INTO TABLE headPosFreq')

    print('(: load data: ' + os.path.realpath(directory + '/head_pos_rel_freq.table'))
    cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
        directory + '/head_pos_rel_freq.table') + '\" INTO TABLE headPosRelFreq')

    print('(: load data: ' + os.path.realpath(directory + '/mapping_file.table'))
    cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
        directory + '/mapping_file.table') + '\" INTO TABLE idToFile')

    print('(: load data: ' + os.path.realpath(directory + '/threshold_rel.table'))
    cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
        directory + '/threshold_rel.table') + '\" INTO TABLE threshold')

    print('(: load data: ' + os.path.realpath(directory + '/info.table'))
    cursor.execute(
        'LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(directory + '/info.table') + '\" INTO TABLE Info')

    print('(: load data: ' + os.path.realpath(directory + '/rel_info.table'))
    cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
        directory + '/rel_info.table') + '\" INTO TABLE relInfo')

    if g_bSubCorpus:
        if True:  # len(g_listCorpus)>1:
            for i in g_listCorpus:
                print('(: load data: ' + os.path.realpath(directory + '/relations.' + i[0] + '.table'))
                cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
                    directory + '/relations.' + i[0] + '.table') + '\" INTO TABLE ' + i[0] + 'relations')
                print('(: load data: ' + os.path.realpath(directory + '/head_pos_freq.' + i[0] + '.table'))
                cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
                    directory + '/head_pos_freq.' + i[0] + '.table') + '\" INTO TABLE ' + i[0] + 'headPosFreq')
                print('(: load data: ' + os.path.realpath(directory + '/head_pos_rel_freq.' + i[0] + '.table'))
                cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
                    directory + '/head_pos_rel_freq.' + i[0] + '.table') + '\" INTO TABLE ' + i[0] + 'headPosRelFreq')


def create_tables_hits(cursor, directory):
    print('(: get data types')
    table_types = read_table(os.path.realpath(directory + '/types.table')).set_index(keys=[0], drop=True).T.iloc[0]

    ### Ermitteln der MySQL-Typen
    typeCorpusId = get_type(int(table_types['corpusSize']))
    typeInfoId = get_type(int(table_types['infoSize']))
    typeText = get_type(int(table_types['highestText']))
    typeTokenPositionW1 = get_type(int(table_types['highestTokenPositionW1']))
    typeTokenPositionW2 = get_type(int(table_types['highestTokenPositionW2']))
    typePrepPosition = get_type(int(table_types['highestPrepPosition']))
    typeSentence = get_type(int(table_types['highestSentence']))

    ### Ermitteln der MySQL-Typen für die TEI-Informationen
    ### Einlesen der Typinformationen in eine Tabelle
    table_tei_types = \
        read_table(os.path.realpath(directory + '/TEI_types.table')).set_index(keys=[0], drop=True).T.iloc[0]

    cursor.execute("""
    CREATE TABLE teiTypes
    (
     type     CHAR(30),
     value int unsigned,
     index (type)
    )
    """)

    cursor.execute("LOAD DATA " + g_strLocal + " INFILE \"" + os.path.realpath(
        directory + "/TEI_types.table") + "\" INTO TABLE teiTypes")

    typeDateId = get_type(int(table_tei_types['DateSize']))
    typeDateDescId = get_type_signed(int(table_tei_types['DateSize']))
    typeTextclassId = get_type(int(table_tei_types['TextclassSize']))
    typeOrigId = get_type(int(table_tei_types['OrigSize']))
    typeScanId = get_type(int(table_tei_types['ScanSize']))
    typeAvailId = get_type(int(table_tei_types['AvailSize']))
    typeDateStr = get_type_char(int(table_tei_types['lengthDate']))
    typeOrigStr = get_type_char(int(table_tei_types['lengthOrig']))
    typeScanStr = get_type_char(int(table_tei_types['lengthScan']))
    typeAvailStr = get_type_char(int(table_tei_types['lengthAvail']))
    typeTextclassStr = get_type_char(int(table_tei_types['lengthTextclass']))

    ###Erzeugen der MySQL-Tabellen
    print('(: create tables')

    ### concord_sentences.table
    cursor.execute("""DROP TABLE IF EXISTS concordSentences""")
    cursor.execute("""
  CREATE TABLE concordSentences
  (
   corpus """ + typeCorpusId + """,
   FileId """ + typeText + """,
   SentenceId """ + typeSentence + """,
   Sentence TEXT,
   Page TEXT,
   primary key (corpus,FileId,SentenceId)
  )
  """)

    ### mapping_TEI_textclass.table
    cursor.execute("""DROP TABLE IF EXISTS idToTextclass""")
    cursor.execute("""
  CREATE TABLE idToTextclass
  (
   id """ + typeTextclassId + """,
   Textclass     """ + typeTextclassStr + """,
   primary key (id)
  )
  """)

    ### mapping_TEI_date.table
    cursor.execute("""DROP TABLE IF EXISTS idToDate""")
    cursor.execute("""
  CREATE TABLE idToDate
  (
   id """ + typeDateId + """,
   Date     """ + typeDateStr + """,
   primary key (id)
  )
  """)

    #   ### mapping_TEI_orig.table
    #   cursor.execute("""DROP TABLE IF EXISTS idToOrig""")
    #   cursor.execute("""
    # CREATE TABLE idToOrig
    # (
    #  id """ + typeOrigId + """,
    #  Orig     """ + typeOrigStr + """,
    #  primary key (id)
    # )
    # """)

    #   ### mapping_TEI_scan.table
    #   cursor.execute("""DROP TABLE IF EXISTS idToScan""")
    #   cursor.execute("""
    # CREATE TABLE idToScan
    # (
    #  id """ + typeScanId + """,
    #  Scan     """ + typeScanStr + """,
    #  primary key (id)
    # )
    # """)

    ### mapping_TEI_avail.table
    cursor.execute("""DROP TABLE IF EXISTS idToAvail""")
    cursor.execute("""
  CREATE TABLE idToAvail
  (
   id """ + typeAvailId + """,
   Avail     """ + typeAvailStr + """,
   primary key (id),
   index (Avail)
  )
  """)

    ### mapping_TEI.table
    cursor.execute("""DROP TABLE IF EXISTS idToTei""")
    cursor.execute("""
  CREATE TABLE idToTei
  (
   corpus """ + typeCorpusId + """,
   file """ + typeText + """,
   Orig     """ + typeOrigStr + """,
   Scan     """ + typeScanStr + """,
   Textclass """ + typeTextclassId + """,
   Avail """ + typeAvailId + """,
   primary key (corpus,file)
  )
  """)

    ### mapping_position_info_tei.table
    cursor.execute("""DROP TABLE IF EXISTS idToInfo""")
    cursor.execute("""
  CREATE TABLE idToInfo
  (
   id """ + typeInfoId + """,
   tokenPosition1 """ + typeTokenPositionW1 + """,
   tokenPosition2 """ + typeTokenPositionW2 + """,
   prepPosition """ + typePrepPosition + """,
   sentence """ + typeSentence + """,
   file """ + typeText + """,
   corpus """ + typeCorpusId + """,
   avail BOOL,
   Date """ + typeDateId + """,
   DateDesc """ + typeDateDescId + """,
   Score INT NOT NULL,

   index I_date (id,Date,Avail,corpus),
   index I_date_desc (id,DateDesc,Avail,corpus),

   index I_score_date (id,Score,Date,Avail,corpus),
   index I_score_date_desc (id,Score,DateDesc,Avail,corpus)

  )

  PARTITION BY HASH(id)
  PARTITIONS 100

  """)

    ### Temporäre Tabelle für Berechnungen des Wortprofil-Servers
    cursor.execute("""DROP TABLE IF EXISTS idToInfoTmp""")
    cursor.execute("""
  CREATE TABLE idToInfoTmp
  (
   id """ + typeInfoId + """,
   tokenPosition1 """ + typeTokenPositionW1 + """,
   tokenPosition2 """ + typeTokenPositionW2 + """,
   prepPosition """ + typePrepPosition + """,
   sentence """ + typeSentence + """,
   file """ + typeText + """,
   corpus """ + typeCorpusId + """,
   avail BOOL,
   Date """ + typeDateId + """,
   DateDesc """ + typeDateDescId + """,
   Score INT NOT NULL
  )

  """)


def load_into_tables_hits(cursor, directory):
    print('(: load data: ' + os.path.realpath(directory + '/mapping_TEI_date.table'))
    cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
        directory + '/mapping_TEI_date.table') + '\" INTO TABLE idToDate')
    # print('(: load data: ' + os.path.realpath(directory + '/mapping_TEI_orig.table'))
    # cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
    #     directory + '/mapping_TEI_orig.table') + '\" INTO TABLE idToOrig')
    # print('(: load data: ' + os.path.realpath(directory + '/mapping_TEI_scan.table'))
    # cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
    #     directory + '/mapping_TEI_scan.table') + '\" INTO TABLE idToScan')
    print('(: load data: ' + os.path.realpath(directory + '/mapping_TEI_avail.table'))
    cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
        directory + '/mapping_TEI_avail.table') + '\" INTO TABLE idToAvail')
    print('(: load data: ' + os.path.realpath(directory + '/mapping_TEI_textclass.table'))
    cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
        directory + '/mapping_TEI_textclass.table') + '\" INTO TABLE idToTextclass')
    print('(: load data: ' + os.path.realpath(directory + '/concord_sentences.table'))
    cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
        directory + '/concord_sentences.table') + "\" INTO TABLE concordSentences FIELDS TERMINATED BY '\t' ENCLOSED BY '' ESCAPED BY ''")
    print('(: load data: ' + os.path.realpath(directory + '/mapping_position_info_tei.table'))
    cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
        directory + '/mapping_position_info_tei.table') + '\" INTO TABLE idToInfo')
    print('(: load data: ' + os.path.realpath(directory + '/mapping_TEI.table'))
    cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
        directory + '/mapping_TEI.table') + '\" INTO TABLE idToTei')


print("|: CREATE MYSQL DATABASE")

### Create option parser
parser = OptionParser()
parser.add_option("-s", dest="spec", default=None, help="Angabe der Settings-Datei (*.xml)")
parser.add_option("-l", action="store_true", dest="local", default=False,
                  help="Ob MySQL die Tabellen 'local' einlesen sollen")
parser.add_option("-c", action="store_true", dest="subcorpus", default=False,
                  help="Ob die Subkorpora eingespielt werden sollen")
(options, args) = parser.parse_args()

if options.local:
    g_strLocal = "LOCAL"

g_bSubCorpus = options.subcorpus

### Prüfen der Parameter
if options.spec == None:
    parser.error("missing settings file")
    sys.exit(-1)

try:
    daten = open(options.spec, 'r')
    daten.close()
except:
    parser.error("unknown settings file: " + options.spec)
    sys.exit(-1)

### read specifications
mapConfig = {}
fileConfig = open(options.spec, 'r')
for i in fileConfig.readlines():
    setting = i.rstrip('\n').split('\t')
    if len(setting) == 2:
        mapConfig[setting[0]] = setting[1]

### Parameter aus der Konfigurationsdatei prüfen
if 'TablePath' not in mapConfig:
    parser.error("missing table path in settings file")
    sys.exit(-1)

if not os.path.exists(mapConfig['TablePath']):
    parser.error("directory does not exist: " + mapConfig['TablePath'])
    sys.exit(-1)

if 'User' not in mapConfig:
    parser.error("missing user name in config file")
    sys.exit(-1)

if 'Database' not in mapConfig:
    parser.error("missing database name in config file")
    sys.exit(-1)

if 'Port' not in mapConfig:
    parser.error("missing port in config file")
    sys.exit(-1)

if 'Host' not in mapConfig and 'Socket' not in mapConfig:
    parser.error("missing Host/Socket in config file")
    sys.exit(-1)

mapConfig['Database'] = 'wordprofile2'

if 'Host' in mapConfig:
    print('|: host: ' + mapConfig['Host'])
else:
    print('|: socket: ' + mapConfig['Socket'])
print('|: user: ' + mapConfig['User'])
print('|: db: ' + mapConfig['Database'])
print('|: port: ' + mapConfig['Port'])

conn = None
if 'Host' in mapConfig:
    conn = MySQLdb.connect(
        host=mapConfig['Host'],
        user=mapConfig['User'],
        passwd=mapConfig['Passwd'],
        local_infile=True,
        port=int(mapConfig['Port']))
else:
    conn = MySQLdb.connect(
        unix_socket=mapConfig['Socket'],
        user=mapConfig['User'],
        passwd=mapConfig['Passwd'],
        local_infile=True,
        port=int(mapConfig['Port']))

### create database
cursor = conn.cursor()
cursor.execute("DROP DATABASE IF EXISTS " + mapConfig['Database'])
cursor.execute("CREATE DATABASE " + mapConfig['Database'] + " CHARACTER SET utf8")
cursor.execute("set autocommit=1")
cursor.execute("USE " + mapConfig['Database'])

### Erstellen der MySQL-Tabellen
create_tables(cursor, mapConfig['TablePath'].rstrip('/'))
### Laden in die MySQL-Tabellen
load_into_tables(cursor, mapConfig['TablePath'].rstrip('/'))

print("|: UPDATE DATABASE")

### MySQL-Tabellen erstellen
create_tables_hits(cursor, mapConfig['TablePath'].rstrip('/'))
### Wortprofil-Texttreffer-Tabellen in die MySQL-Tabellen einspielen
load_into_tables_hits(cursor, mapConfig['TablePath'].rstrip('/'))

print()
print("(: done")
