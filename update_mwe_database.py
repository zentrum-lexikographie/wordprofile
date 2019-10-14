#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
  Das Programm erweitert anhand der Wortprofil-MWE-Tabellen eine MySQL-Wortprofil-Datenbank:

  *mwe_{MWE Tiefe}.table
  *mwe_check_{MWE Tiefe}.table
  *mwe_free_{MWE Tiefe}.table

"""

import os
import sys
# from read_settings import *
from optparse import OptionParser

import MySQLdb

### globale Variablen
g_strLocal=''
g_bConcord=False
g_bGoodExamples=False
g_iMaxLevel=1

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
  global g_iMaxLevel

  typeInfoId=0
  typeCorpusId=0
  typeText=0  
  typeTokenPositionW1=0  
  typeTokenPositionW2=0  
  typePrepPosition=0  
  typeSentence=0  

  print '(: get data types'

  cursor.execute ("SELECT type, value FROM types where type=\"InfoSize\"")
  typeInfoId = get_type(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"corpusSize\"")
  typeCorpusId = get_type(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"highestText\"")
  typeText = get_type(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"highestTokenPositionW1\"")
  iTokenPositionW1=cursor.fetchone()[1]
  typeTokenPositionW1 = get_type(iTokenPositionW1);
  cursor.execute ("SELECT type, value FROM types where type=\"highestTokenPositionW2\"")
  iTokenPositionW2=cursor.fetchone()[1]
  typeTokenPositionW2 = get_type(iTokenPositionW2);
  cursor.execute ("SELECT type, value FROM types where type=\"highestPrepPosition\"")
  typePrepPosition = get_type(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"highestSentence\"")
  typeSentence = get_type(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"lemmaSize\"")
  typeLemmaId = get_type(cursor.fetchone()[1])
  cursor.execute ("SELECT type, value FROM types where type=\"posSize\"")
  typePOSId = get_type(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"highestFunction\"")
  typeFunctionId = get_type(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"highestFrequency\"")
  typeFrequency = get_type_signed(cursor.fetchone()[1]);
  cursor.execute ("SELECT type, value FROM types where type=\"logDiceLength\"")
  typelogDiceStr = str(cursor.fetchone()[1]+2)

  ###Erzeugen der MySQL-Tabellen
  print '(: create tables'

  ### Anlegen der MWE-Tabellen
  for i in range(1,g_iMaxLevel+1):
    strId=""
    for j in range(1,i+1):
      strId+="id"+str(j)+" "+typeInfoId+",\n"

    strFirstIndex=""
    strIndex=""
    for j in range(1,i+1):
      if strIndex != "":
        strIndex+=","
      else:
        strFirstIndex="id"+str(j)
      strIndex+="id"+str(j)
    strIndex1LogDice = "index I_logDice ("+strIndex+",lemma,POS,logDice),\n"
    strIndex1Frequency = "index I_frequency ("+strIndex+",lemma,POS,frequency),\n"
    strPartition = "PARTITION BY HASH("+strFirstIndex+")\n"

    cursor.execute ("DROP TABLE IF EXISTS idToConditional_"+str(i))
    strExecute = """
    CREATE TABLE idToConditional_"""+str(i)+"""
    (
     """+strId+"""
     mate """+typeInfoId+""",
     frequency """+typeFrequency+""",
     freqBelege """+typeFrequency+""",
     logDice float("""+typelogDiceStr+""",2),
     function """+typeFunctionId+""",

     lemma """+typeLemmaId+""",
     POS """+typePOSId+""",

     """+strIndex1LogDice+"""
     """+strIndex1Frequency+"""
     index I_mate (mate)
    )
    """+strPartition+"""
    PARTITIONS 100;
    """
    cursor.execute (strExecute)

  ### Anlegen der MWE-Check-Tabellen
  for i in range(1,g_iMaxLevel+1):
    strId=""
    for j in range(1,i+1):
      strId+="id"+str(j)+" "+typeInfoId+",\n"

    strIndex=""
    for j in range(1,i+1):
      if strIndex != "":
        strIndex+=","
      else:
        strFirstIndex="id"+str(j)
      strIndex+="id"+str(j)
    strIndex = "index I_id ("+strIndex+")\n"

    cursor.execute ("DROP TABLE IF EXISTS ConditionalCheck_"+str(i))
    strExecute = """
    CREATE TABLE ConditionalCheck_"""+str(i)+"""
    (
     """+strId+"""

     frequency """+typeFrequency+""",
     logDice float("""+typelogDiceStr+""",2),

     """+strIndex+"""
    )
    """
    cursor.execute (strExecute)
  
  ### Anlegen der Tabellen für 'ConditionalFree'
  for i in range(1,g_iMaxLevel+1):
    strId=""
    for j in range(1,i+1):
      strId+="id"+str(j)+" "+typeInfoId+",\n"
    strFirstIndex=""
    strIndex=""
    for j in range(1,i+1):
      if strIndex != "":
        strIndex+=","
      else:
        strFirstIndex="id"+str(j)
      strIndex+="id"+str(j)
    strIndex1LogDice = "index I_logDice ("+strIndex+",lemma,POS,logDice),\n"
    strIndex1Frequency = "index I_frequency ("+strIndex+",lemma,POS,frequency),\n"
    strIndex2 = "index I_id ("+strIndex+")\n"
    strPartition = "PARTITION BY HASH("+strFirstIndex+")\n"
    cursor.execute ("DROP TABLE IF EXISTS idToConditionalFree_"+str(i))
    strExecute = """
    CREATE TABLE idToConditionalFree_"""+str(i)+"""
    (
     """+strId+"""
     mate """+typeInfoId+""",
     function """+typeFunctionId+""",

     prep """+typeLemmaId+""",

     lemma1 """+typeLemmaId+""",
     POS1 """+typePOSId+""",

     lemma2 """+typeLemmaId+""",
     POS2 """+typePOSId+""",

     """+strIndex2+"""
    )
    """+strPartition+"""
    PARTITIONS 100;
    """
    cursor.execute (strExecute)


"""
 Laden der Wortprofiltabellen in die MySQL-Tabellen
"""
def load_into_tables(cursor,directory):
  global g_iMaxLevel

  ### für alle MWE-Ebenen die Tabellen Einlesen
  for i in range(1,g_iMaxLevel+1):
    print '(: load data: '+ os.path.realpath(directory +'/conditional_'+str(i)+'.table')
    cursor.execute ('LOAD DATA ' + g_strLocal + ' INFILE \"'+os.path.realpath(directory+'/mwe_'+str(i)+'.table')+'\" INTO TABLE idToConditional_'+str(i))

    print '(: load data: '+ os.path.realpath(directory +'/conditional_check_'+str(i)+'.table')
    cursor.execute ('LOAD DATA ' + g_strLocal + ' INFILE \"'+os.path.realpath(directory+'/mwe_check_'+str(i)+'.table')+'\" INTO TABLE ConditionalCheck_'+str(i))

    print '(: load data: '+ os.path.realpath(directory +'/conditional_free_'+str(i)+'.table')
    cursor.execute ('LOAD DATA ' + g_strLocal + ' INFILE \"'+os.path.realpath(directory+'/mwe_free_'+str(i)+'.table')+'\" INTO TABLE idToConditionalFree_'+str(i))



print "|: UPDATE DATABASE"

# Create option parser
parser = OptionParser()
parser.add_option("-s", dest="spec", default="wordprofile-specification.xml", help=u"Angabe der Settings-Datei (*.xml)")
parser.add_option("-l", action="store_true", dest="local", default=False, help=u"Ob MySQL die Tabellen 'local' einlesen sollen")
(options, args) = parser.parse_args()

if options.local:
  g_strLocal="LOCAL"

### Prüfen der Parameter
if options.spec==None:
  parser.error("missing settings file")
  sys.exit(-1)
try:
  daten = file(options.spec,'r')
except:
  parser.error("unknown settings file: " + options.spec)
  sys.exit(-1)

#read specifications
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

if 'MweDepth' in mapConfig:
  g_iMaxLevel = int(mapConfig['MweDepth'])
else:
  parser.error("missing 'MweDepth' in settings file")
  sys.exit(-1)

if not os.path.exists(mapConfig['TablePath']):
  parser.error("directory does not exist: " + mapConfig['TablePath'])
  sys.exit(-1)

if 'User' not in mapConfig:
  parser.error("missing user name in settings file")
  sys.exit(-1)

if 'Database' not in mapConfig:
  parser.error("missing wpse name in settings file")
  sys.exit(-1)

if 'Port' not in mapConfig:
  parser.error("missing port in settings file")
  sys.exit(-1)

if 'Host' not in mapConfig and 'Socket' not in mapConfig:
  parser.error("missing Host/Socket in settings file")
  sys.exit(-1)



#connect to mysql
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

# create wpse
cursor = conn.cursor ()

### Datenbank öffnen
cursor.execute("set autocommit=1")
cursor.execute ("USE "+mapConfig['Database']);

### MySQL-Tabellen erstellen
create_tables(cursor,mapConfig['TablePath'].rstrip('/'))
### Wortprofil-Texttreffer-Tabellen in die MySQL-Tabellen einspielen
load_into_tables(cursor,mapConfig['TablePath'].rstrip('/'))

print
print "(: done"

