#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
  Das Programm erweitert die MySQL-Wortprofil-Datenbank anhand der Wortprofil-Texttreffer-Tabellen:
    -mapping_TEI_date.table
    -mapping_TEI_orig.table
    -mapping_TEI_scan.table
    -mapping_TEI_avail.table
    -mapping_TEI_textclass.table
    -concord_sentences.table
    -mapping_position_info_tei.table
    -mapping_TEI.table
    -TEI_types.table

"""

import os
import sys
from optparse import OptionParser

import MySQLdb

g_strLocal = ''

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


def create_tables(cursor, directory):
    print('(: get data types')

    ### Ermitteln der MySQL-Typen aus den Wortprofil-Statistik-Tabellen
    cursor.execute("SELECT type, value FROM types where type=\"InfoSize\"")
    typeInfoId = get_type(cursor.fetchone()[1])
    cursor.execute("SELECT type, value FROM types where type=\"corpusSize\"")
    typeCorpusId = get_type(cursor.fetchone()[1])
    cursor.execute("SELECT type, value FROM types where type=\"highestText\"")
    typeText = get_type(cursor.fetchone()[1])
    cursor.execute("SELECT type, value FROM types where type=\"highestTokenPositionW1\"")
    typeTokenPositionW1 = get_type(cursor.fetchone()[1])
    cursor.execute("SELECT type, value FROM types where type=\"highestTokenPositionW2\"")
    typeTokenPositionW2 = get_type(cursor.fetchone()[1])
    cursor.execute("SELECT type, value FROM types where type=\"highestPrepPosition\"")
    typePrepPosition = get_type(cursor.fetchone()[1])
    cursor.execute("SELECT type, value FROM types where type=\"highestSentence\"")
    typeSentence = get_type(cursor.fetchone()[1])

    ### Ermitteln der MySQL-Typen für die TEI-Informationen
    ### Einlesen der Typinformationen in eine Tabelle
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
    cursor = conn.cursor()
    cursor.execute("SELECT type, value FROM teiTypes where type=\"DateSize\"")
    typeDateId = get_type(cursor.fetchone()[1])
    cursor.execute("SELECT type, value FROM teiTypes where type=\"DateSize\"")
    typeDateDescId = get_type_signed(cursor.fetchone()[1])
    cursor.execute("SELECT type, value FROM teiTypes where type=\"TextclassSize\"")
    typeTextclassId = get_type(cursor.fetchone()[1])
    cursor.execute("SELECT type, value FROM teiTypes where type=\"OrigSize\"")
    typeOrigId = get_type(cursor.fetchone()[1])
    cursor.execute("SELECT type, value FROM teiTypes where type=\"ScanSize\"")
    typeScanId = get_type(cursor.fetchone()[1])
    cursor.execute("SELECT type, value FROM teiTypes where type=\"AvailSize\"")
    typeAvailId = get_type(cursor.fetchone()[1])
    cursor.execute("SELECT type, value FROM teiTypes where type=\"lengthDate\"")
    typeDateStr = get_type_char(cursor.fetchone()[1])
    cursor.execute("SELECT type, value FROM teiTypes where type=\"lengthOrig\"")
    typeOrigStr = get_type_char(cursor.fetchone()[1])
    cursor.execute("SELECT type, value FROM teiTypes where type=\"lengthScan\"")
    typeScanStr = get_type_char(cursor.fetchone()[1])
    cursor.execute("SELECT type, value FROM teiTypes where type=\"lengthAvail\"")
    typeAvailStr = get_type_char(cursor.fetchone()[1])
    cursor.execute("SELECT type, value FROM teiTypes where type=\"lengthTextclass\"")
    typeTextclassStr = get_type_char(cursor.fetchone()[1])

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

    ### mapping_TEI_orig.table
    cursor.execute("""DROP TABLE IF EXISTS idToOrig""")
    cursor.execute("""
  CREATE TABLE idToOrig
  (
   id """ + typeOrigId + """,
   Orig     """ + typeOrigStr + """,
   primary key (id)
  )
  """)

    ### mapping_TEI_scan.table
    cursor.execute("""DROP TABLE IF EXISTS idToScan""")
    cursor.execute("""
  CREATE TABLE idToScan
  (
   id """ + typeScanId + """,
   Scan     """ + typeScanStr + """,
   primary key (id)
  )
  """)

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


"""
 Laden der Wortprofiltabellen in die MySQL-Tabellen
"""


def load_into_tables(cursor, directory):
    print('(: load data: ' + os.path.realpath(directory + '/mapping_TEI_date.table'))
    cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
        directory + '/mapping_TEI_date.table') + '\" INTO TABLE idToDate')
    print('(: load data: ' + os.path.realpath(directory + '/mapping_TEI_orig.table'))
    cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
        directory + '/mapping_TEI_orig.table') + '\" INTO TABLE idToOrig')
    print('(: load data: ' + os.path.realpath(directory + '/mapping_TEI_scan.table'))
    cursor.execute('LOAD DATA ' + g_strLocal + ' INFILE \"' + os.path.realpath(
        directory + '/mapping_TEI_scan.table') + '\" INTO TABLE idToScan')
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


print("|: UPDATE DATABASE")

# Create option parser
parser = OptionParser()
parser.add_option("-s", dest="spec", default="query-specification.xml", help="Angabe der Settings-Datei (*.xml)")
parser.add_option("-l", action="store_true", dest="local", default=False,
                  help="Ob MySQL die Tabellen 'local' einlesen sollen")
(options, args) = parser.parse_args()

if options.local:
    g_strLocal = "LOCAL"

### Prüfen der Parameter
if options.spec == None:
    parser.error("missing settings file")
    sys.exit(-1)
try:
    daten = open(options.spec, 'r')
except:
    parser.error("unknown settings file: " + options.spec)
    sys.exit(-1)

# read specifications
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

# connect to mysql
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

# create database
cursor = conn.cursor()

### Datenbank öffnen
cursor.execute("set autocommit=1")
cursor.execute("USE " + mapConfig['Database'])

### MySQL-Tabellen erstellen
create_tables(cursor, mapConfig['TablePath'].rstrip('/'))
### Wortprofil-Texttreffer-Tabellen in die MySQL-Tabellen einspielen
load_into_tables(cursor, mapConfig['TablePath'].rstrip('/'))

print()
print("(: done")
