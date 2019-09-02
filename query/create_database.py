#!/usr/bin/python
# -*- coding: utf-8 -*-

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

import MySQLdb
import time
import sys
import os
import codecs
from optparse import OptionParser

g_strLocal=''
g_bSubCorpus=False
g_listCorpus=[]

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
    print "text zu groß"
    sys.exit(-1);
  elif iLength > 16777215:
    return "LONGTEXT BINARY NOT NULL"
  elif iLength > 65535:
    return "MEDIUMTEXT BINARY NOT NULL"
  elif iLength > 255:
    return "TEXT BINARY NOT NULL"
  else:
    return "CHAR("+str(iLength)+") BINARY NOT NULL"

"""
 Erstellen der MySQL-Tabellen
"""
def create_tables(cursor,directory):
  global g_bSubCorpus
  global g_listCorpus

  print '(: get data types'

  ### Einlesen der Typinformationen in eine Tabelle
  cursor.execute ("""
  CREATE TABLE types
  (
   type     CHAR(30),
   value int unsigned,
   index (type)
  )
  """)
  cursor.execute ("LOAD DATA " + g_strLocal + " INFILE \""+os.path.realpath(directory +"/types.table")+"\" INTO TABLE types")
  cursor = conn.cursor ()

  #cursor.execute ("SELECT * FROM types")
  #print os.path.realpath(directory +"/types.table")
  #print cursor.fetchall()
  #sys.exit(-1)

  ### Variablen für die MySQL-Typen
  typeLemmaId=0
  typeSurfaceId=0
  typePrepId=0
  typeCorpusId=0
  typePOSId=0
  typeInfoId=0
  typeFunctionId=0

  typeLemmaStr=""
  typeLemmaStrCaseInsensitive=""
  typeSurfaceStrCaseInsensitive=""
  typeSurfaceStr=""
  typePrepStr=""
  typePOSStr=""
  typeCorpusStr=""
  typeFunctionStr=""
  typeSnippetStr=""
  typeDescriptionStr=""
  typeExampleStr=""

  typeFrequency=0
  typeHeadPosFrequency=0

  typeDepFrequency=0
  typeHeadFrequency=0
  typeDepCount=0
  typeHeadcount=0
  typeGlobalDepFrequency=0
  typeGlobalHeadFrequency=0
  typeGlobalDepCount=0
  typeGlobalHeadcount=0  

  typeTokenPositionW1=0  
  typeTokenPositionW2=0  
  typePrepPosition=0  
  typeSentence=0  
  typeText=0  
  typeTextStr=""  

  ### Ermitteln der MySQL-Typen
  cursor.execute ("SELECT type, value FROM types where type=\"MI3Length\"")
  typeMI3Str = str(cursor.fetchone()[1]+2)
  cursor.execute ("SELECT type, value FROM types where type=\"MiLogFreqLength\"")
  typeMiLogFreqStr = str(cursor.fetchone()[1]+2)
  cursor.execute ("SELECT type, value FROM types where type=\"TScoreLength\"")
  typeTScoreStr = str(cursor.fetchone()[1]+2)
  cursor.execute ("SELECT type, value FROM types where type=\"LogDiceLength\"")
  typelogDiceStr = str(cursor.fetchone()[1]+2)
  cursor.execute ("SELECT type, value FROM types where type=\"LogLikeLength\"")
  typelogLikeStr = str(cursor.fetchone()[1]+2)

  cursor.execute ("SELECT type, value FROM types where type=\"lemmaSize\"")
  typeLemmaId = get_type(cursor.fetchone()[1])
  cursor.execute ("SELECT type, value FROM types where type=\"lemmaLength\"")
  typeLemmaStrCaseInsensitive = "CHAR("+str(cursor.fetchone()[1])+") BINARY"

  cursor.execute ("SELECT type, value FROM types where type=\"SurfaceSize\"")
  typeSurfaceId = get_type(cursor.fetchone()[1])
  cursor.execute ("SELECT type, value FROM types where type=\"SurfaceLength\"")
  typeSurfaceStr = "CHAR("+str(cursor.fetchone()[1])+") BINARY"

  cursor.execute ("SELECT type, value FROM types where type=\"posSize\"")
  typePOSId = get_type(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"POSLength\"")
  typePOSStr = "CHAR("+str(cursor.fetchone()[1])+") BINARY"

  cursor.execute ("SELECT type, value FROM types where type=\"corpusSize\"")
  typeCorpusId = get_type(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"corpusLength\"")
  typeCorpusStr = "CHAR("+str(cursor.fetchone()[1])+") BINARY"

  cursor.execute ("SELECT type, value FROM types where type=\"InfoSize\"")
  typeInfoId = get_type(cursor.fetchone()[1]);

  cursor.execute ("SELECT type, value FROM types where type=\"highestFrequency\"")
  typeFrequency = get_type_signed(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"highestHeadPosFrequency\"")
  typeHeadPosFrequency = get_type(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"highestDepFrequency\"")
  typeDepFrequency = get_type(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"highestHeadFrequency\"")
  typeHeadFrequency = get_type(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"highestDepCount\"")
  typeDepCount = get_type(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"highestHeadCount\"")
  typeHeadCount = get_type(cursor.fetchone()[1]);

  cursor.execute ("SELECT type, value FROM types where type=\"highestGlobalDepFrequency\"")
  typeGlobalDepFrequency = get_type(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"highestGlobalHeadFrequency\"")
  typeGlobalHeadFrequency = get_type(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"highestGlobalDepCount\"")
  typeGlobalDepCount = get_type(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"highestGlobalHeadCount\"")
  typeGlobalHeadCount = get_type(cursor.fetchone()[1]);

  cursor.execute ("SELECT type, value FROM types where type=\"highestTokenPositionW1\"")
  typeTokenPositionW1 = get_type(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"highestTokenPositionW2\"")
  typeTokenPositionW2 = get_type(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"highestPrepPosition\"")
  typePrepPosition = get_type(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"highestSentence\"")
  typeSentence = get_type(cursor.fetchone()[1]);

  cursor.execute ("SELECT type, value FROM types where type=\"highestText\"")
  typeText = get_type(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"textLength\"")
  typeTextStr = "TEXT"

  cursor.execute ("SELECT type, value FROM types where type=\"highestFunction\"")
  typeFunctionId = get_type(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"functionLength\"")
  typeFunctionStr = "CHAR("+str(cursor.fetchone()[1])+") BINARY"
  cursor.execute ("SELECT type, value FROM types where type=\"snippetLength\"")
  typeSnippetStr = "CHAR("+str(cursor.fetchone()[1])+") BINARY"
  cursor.execute ("SELECT type, value FROM types where type=\"descriptionLength\"")
  typeDescriptionStr = "CHAR("+str(cursor.fetchone()[1])+") BINARY"
  cursor.execute ("SELECT type, value FROM types where type=\"exampleLength\"")
  typeExampleStr = "CHAR("+str(cursor.fetchone()[1])+") BINARY"

  ###Erzeugen der MySQL-Tabellen
  print '(: create tables'

  ### mapping_corpus.table
  cursor.execute ("""
  CREATE TABLE idToCorpus
  (
   id """+typeCorpusId+""",
   Corpus """+typeCorpusStr+""",
   primary key (id)
  )
  """)
  ### Abfragen der verwendeten Korpusnamen
  cursor.execute ("LOAD DATA " + g_strLocal + " INFILE \""+os.path.realpath(directory +"/mapping_corpus.table")+"\" INTO TABLE idToCorpus")
  cursor = conn.cursor ()
  cursor.execute ("SELECT Corpus FROM idToCorpus")
  g_listCorpus = cursor.fetchall()

  ### mapping_corpus.table
  cursor.execute ("""
  CREATE TABLE idToFile
  (
   id """+typeText+""",
   File     """+typeTextStr+""",
   primary key (id)
  )
  """)

  cursor.execute ("""
  CREATE TABLE idToPOS
  (
   id """+typePOSId+""",
   POS     """+typePOSStr+""",
   primary key (id)
  )
  """)

  cursor.execute ("""
  CREATE TABLE headPosFreq
  (
   id """+typeLemmaId+""",
   POS     """+typePOSId+""",
   frequency """+typeHeadPosFrequency+""",
   count """+typeHeadPosFrequency+""",
   index (id)
  )
  """)

  cursor.execute ("""
  CREATE TABLE headPosRelFreq
  (
   id """+typeLemmaId+""",
   POS     """+typePOSId+""",
   relation  """+typeFunctionId+""",
   frequency """+typeHeadPosFrequency+""",
   count """+typeHeadPosFrequency+""",
   index (id)
  )
  """)

  cursor.execute ("""
  CREATE TABLE idToFunction
  (
   id """+typeFunctionId+""",
   Function """+typeFunctionStr+""",
   Type TINYINT unsigned,
   Snippet """+typeSnippetStr+""",
   Description """+typeDescriptionStr+""",
   Example """+typeExampleStr+""",
   primary key (id)
  )
  """)

  cursor.execute ("""
  CREATE TABLE lemmaToRelation
  (
   id """+typeLemmaId+""",
   lemma """+typeLemmaStrCaseInsensitive+""",
   index (lemma),
   index (id)
  )
  """)

  cursor.execute ("""
  CREATE TABLE lemmaToRelationLower
  (
   id """+typeLemmaId+""",
   lemma """+typeLemmaStrCaseInsensitive+""",
   index (lemma),
   index (id)
  )
  """)

  cursor.execute ("""
  CREATE TABLE idToSurface
  (
   id """+typeSurfaceId+""",
   surface """+typeSurfaceStr+""",
   primary key (id)
  )
  """)

  cursor.execute ("""
  CREATE TABLE relations
  (
   function """+typeFunctionId+""",
   prep """+typeLemmaId+""",
   lemma1 """+typeLemmaId+""",
   lemma2 """+typeLemmaId+""",
   surfacePrep """+typeSurfaceId+""",
   surface1 """+typeSurfaceId+""",
   surface2 """+typeSurfaceId+""",
   PrepPOS """+typePOSId+""",
   POS1 """+typePOSId+""",
   POS2 """+typePOSId+""",
   info """+typeInfoId+""",
   freqBelege """+typeFrequency+""",
   frequency """+typeFrequency+""",
   MI3 float("""+typeMI3Str+""",2),
   MiLogFreq float("""+typeMiLogFreqStr+""",2),
   TScore float("""+typeTScoreStr+""",2),
   logDice float("""+typelogDiceStr+""",2),
   logLike float("""+typelogLikeStr+""",0),

   index I_MiLogFreq (function,lemma1,POS1,MiLogFreq),
   index I_frequency (function,lemma1,POS1,frequency),
   index I_logDice (function,lemma1,POS1,logDice),

   index I_info (info)
  )
  """)

  cursor.execute ("""
  CREATE TABLE relationsOhneIndex
  (
   function """+typeFunctionId+""",
   prep """+typeLemmaId+""",
   lemma1 """+typeLemmaId+""",
   lemma2 """+typeLemmaId+""",
   surfacePrep """+typeSurfaceId+""",
   surface1 """+typeSurfaceId+""",
   surface2 """+typeSurfaceId+""",
   PrepPOS """+typePOSId+""",
   POS1 """+typePOSId+""",
   POS2 """+typePOSId+""",
   info """+typeInfoId+""",
   freqBelege """+typeFrequency+""",
   frequency """+typeFrequency+""",
   MI3 float("""+typeMI3Str+""",2),
   MiLogFreq float("""+typeMiLogFreqStr+""",2),
   TScore float("""+typeTScoreStr+""",2),
   logDice float("""+typelogDiceStr+""",2),
   logLike float("""+typelogLikeStr+""",0)
  )
  """)

  ### threshold_rel.table
  cursor.execute ("""
  CREATE TABLE threshold
  (
   id """+typeFunctionId+""",
   type CHAR(20) BINARY NOT NULL,
   value float,

   index I_id (id)
  )
  """)

  ### info.table
  cursor.execute ("""
  CREATE TABLE Info
  (
   InfoKey VARCHAR(1000) NOT NULL,
   InfoValue VARCHAR(1000) NOT NULL
  )
  """)

  ### rel_info.table
  cursor.execute ("""
  CREATE TABLE relInfo
  (
   id """+typeFunctionId+""",

   count INT unsigned NOT NULL,
   frequency INT unsigned NOT NULL,
   freqBelege INT unsigned NOT NULL,

   primary key (id)
  )
  """)

  ### mapping_corpus_name.table
  cursor.execute ("""
  CREATE TABLE CorpusName
  (
   shortName VARCHAR(1000) NOT NULL,
   fullName VARCHAR(1000) NOT NULL
  )
  """)

  if g_bSubCorpus:
    for i in g_listCorpus:
      cursor.execute ("""
      CREATE TABLE """+i[0]+"""headPosFreq
      (
       id """+typeLemmaId+""",
       POS     """+typePOSId+""",
       frequency """+typeHeadPosFrequency+""",
       count """+typeHeadPosFrequency+""",
       index (id)
      )
      """)

    for i in g_listCorpus:
      cursor.execute ("""
      CREATE TABLE """+i[0]+"""headPosRelFreq
      (
       id """+typeLemmaId+""",
       POS     """+typePOSId+""",
       relation  """+typeFunctionId+""",
       frequency """+typeHeadPosFrequency+""",
       count """+typeHeadPosFrequency+""",
       index (id)
      )
      """)

    for i in g_listCorpus:
      cursor.execute ("""
      CREATE TABLE """+i[0]+"""relations
      (
       function """+typeFunctionId+""",
       prep """+typeLemmaId+""",
       lemma1 """+typeLemmaId+""",
       lemma2 """+typeLemmaId+""",
       surfacePrep """+typeSurfaceId+""",
       surface1 """+typeSurfaceId+""",
       surface2 """+typeSurfaceId+""",
       PrepPOS """+typePOSId+""",
       POS1 """+typePOSId+""",
       POS2 """+typePOSId+""",
       info """+typeInfoId+""",
       freqBelege """+typeFrequency+""",
       frequency """+typeFrequency+""",
       MI3 float("""+typeMI3Str+""",2),
       MiLogFreq float("""+typeMiLogFreqStr+""",2),
       AScore float("""+typeTScoreStr+""",2),
       logDice float("""+typelogDiceStr+""",2),
       LogLike float("""+typelogLikeStr+""",0),

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
def load_into_tables(cursor,directory):
  global g_bSubCorpus
  global g_listCorpus

  #print '(: load data: '+ os.path.realpath(directory +'/mapping_corpus.table')
  #cursor.execute ("LOAD DATA " + g_strLocal + " INFILE \""+os.path.realpath(directory +"/mapping_corpus.table")+"\" INTO TABLE idToCorpus")

  print '(: load data: '+ os.path.realpath(directory +'/mapping_corpus_name.table')
  cursor.execute ('LOAD DATA ' + g_strLocal + ' INFILE \"'+os.path.realpath(directory+'/mapping_corpus_name.table')+'\" INTO TABLE CorpusName')

  print '(: load data: '+ os.path.realpath(directory +'/mapping_POS.table')
  cursor.execute ('LOAD DATA ' + g_strLocal + ' INFILE \"'+os.path.realpath(directory+'/mapping_POS.table')+'\" INTO TABLE idToPOS')

  print '(: load data: '+ os.path.realpath(directory +'/mapping_function.table')
  cursor.execute ('LOAD DATA ' + g_strLocal + ' INFILE \"'+os.path.realpath(directory+'/mapping_function.table')+'\" INTO TABLE idToFunction')

  print '(: load data: '+ os.path.realpath(directory +'/mapping_lemma.table')
  cursor.execute ('LOAD DATA ' + g_strLocal + ' INFILE \"'+os.path.realpath(directory+'/mapping_lemma.table')+'\" INTO TABLE lemmaToRelation')

  print '(: load data: '+ os.path.realpath(directory +'/mapping_lemma_lower.table')
  cursor.execute ('LOAD DATA ' + g_strLocal + ' INFILE \"'+os.path.realpath(directory+'/mapping_lemma_lower.table')+'\" INTO TABLE lemmaToRelationLower')

  print '(: load data: '+ os.path.realpath(directory +'/mapping_surface.table')
  cursor.execute ('LOAD DATA ' + g_strLocal + ' INFILE \"'+os.path.realpath(directory+'/mapping_surface.table')+'\" INTO TABLE idToSurface')

  print '(: load data: '+ os.path.realpath(directory +'/relations.table')
  cursor.execute ('LOAD DATA ' + g_strLocal + ' INFILE \"'+os.path.realpath(directory+'/relations.table')+'\" INTO TABLE relations')

  print '(: load data: '+ os.path.realpath(directory +'/head_pos_freq.table')
  cursor.execute ('LOAD DATA ' + g_strLocal + ' INFILE \"'+os.path.realpath(directory+'/head_pos_freq.table')+'\" INTO TABLE headPosFreq')

  print '(: load data: '+ os.path.realpath(directory +'/head_pos_rel_freq.table')
  cursor.execute ('LOAD DATA ' + g_strLocal + ' INFILE \"'+os.path.realpath(directory+'/head_pos_rel_freq.table')+'\" INTO TABLE headPosRelFreq')

  print '(: load data: '+ os.path.realpath(directory +'/mapping_file.table')
  cursor.execute ('LOAD DATA ' + g_strLocal + ' INFILE \"'+os.path.realpath(directory+'/mapping_file.table')+'\" INTO TABLE idToFile')

  print '(: load data: '+ os.path.realpath(directory +'/threshold_rel.table')
  cursor.execute ('LOAD DATA ' + g_strLocal + ' INFILE \"'+os.path.realpath(directory+'/threshold_rel.table')+'\" INTO TABLE threshold')

  print '(: load data: '+ os.path.realpath(directory +'/info.table')
  cursor.execute ('LOAD DATA ' + g_strLocal + ' INFILE \"'+os.path.realpath(directory+'/info.table')+'\" INTO TABLE Info')

  print '(: load data: '+ os.path.realpath(directory +'/rel_info.table')
  cursor.execute ('LOAD DATA ' + g_strLocal + ' INFILE \"'+os.path.realpath(directory+'/rel_info.table')+'\" INTO TABLE relInfo')

  if g_bSubCorpus:
    if True:#len(g_listCorpus)>1:
      for i in g_listCorpus:
        print '(: load data: '+ os.path.realpath(directory +'/relations.'+ i[0] +'.table')
        cursor.execute ('LOAD DATA ' + g_strLocal + ' INFILE \"'+os.path.realpath(directory +'/relations.'+ i[0] +'.table')+'\" INTO TABLE '+i[0]+'relations')
        print '(: load data: '+ os.path.realpath(directory +'/head_pos_freq.'+ i[0] +'.table')
        cursor.execute ('LOAD DATA ' + g_strLocal + ' INFILE \"'+os.path.realpath(directory +'/head_pos_freq.'+ i[0] +'.table')+'\" INTO TABLE '+i[0]+'headPosFreq')
        print '(: load data: '+ os.path.realpath(directory +'/head_pos_rel_freq.'+ i[0] +'.table')
        cursor.execute ('LOAD DATA ' + g_strLocal + ' INFILE \"'+os.path.realpath(directory +'/head_pos_rel_freq.'+ i[0] +'.table')+'\" INTO TABLE '+i[0]+'headPosRelFreq')



print "|: CREATE MYSQL DATABASE"

### Create option parser
parser = OptionParser()
parser.add_option("-s", dest="spec", default=None, help=u"Angabe der Settings-Datei (*.xml)")
parser.add_option("-l", action="store_true", dest="local", default=False, help=u"Ob MySQL die Tabellen 'local' einlesen sollen")
parser.add_option("-c", action="store_true", dest="subcorpus", default=False, help=u"Ob die Subkorpora eingespielt werden sollen")
(options, args) = parser.parse_args()

if options.local:
  g_strLocal="LOCAL"

g_bSubCorpus = options.subcorpus

### Prüfen der Parameter
if options.spec==None:
  parser.error("missing settings file")
  sys.exit(-1)

try:
  daten = file(options.spec,'r')
  daten.close()
except:
  parser.error("unknown settings file: " + options.spec)
  sys.exit(-1)

### read specifications
mapConfig={}
fileConfig = file(options.spec,'r')
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

### connect to mysql
if 'Host' in mapConfig:
  print '|: host: '+ mapConfig['Host']
else:
  print '|: socket: '+ mapConfig['Socket']
print '|: user: '+ mapConfig['User']
print '|: db: '+ mapConfig['Database']
print '|: port: '+ mapConfig['Port']

conn = None
if 'Host' in mapConfig:
  conn = MySQLdb.connect (
                     host = mapConfig['Host'],
                     user = mapConfig['User'],
                     passwd = mapConfig['Passwd'],
                     local_infile=True,
                     port = int(mapConfig['Port']))
else:
  conn = MySQLdb.connect (
                     unix_socket = mapConfig['Socket'],
                     user = mapConfig['User'],
                     passwd = mapConfig['Passwd'],
                     local_infile=True,
                     port = int(mapConfig['Port']))

### create database
cursor = conn.cursor ()
cursor.execute ("DROP DATABASE IF EXISTS "+mapConfig['Database'])
cursor.execute ("CREATE DATABASE "+mapConfig['Database']+"  CHARACTER SET utf8mb4 ");
cursor.execute("set autocommit=1")
cursor.execute ("USE "+mapConfig['Database']);

### Erstellen der MySQL-Tabellen
create_tables(cursor,mapConfig['TablePath'].rstrip('/'))
### Laden in die MySQL-Tabellen
load_into_tables(cursor,mapConfig['TablePath'].rstrip('/'))

print
print "(: done"







