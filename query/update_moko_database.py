#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
  Das Programm erweitert die MySQL-Wortprofil-Datenbank anhand der MoKo-Tabellen:
    -id_to_class.table
    -w2_to_class_id.table
    -w1_to_class_id.table

"""

import MySQLdb
import time
import sys
import os
import codecs
from optparse import OptionParser

g_strLocal=''

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

  ### Erzeugen der MySQL-Tabellen
  print '(: create tables'

  ### id_to_class.table
  cursor.execute ("""DROP TABLE IF EXISTS id2Class""")
  cursor.execute ("""
  CREATE TABLE id2Class
  (
   Id SMALLINT unsigned NOT NULL,
   Class CHAR(50) BINARY NOT NULL,

   index I_id (Id),
   index I_str (Class)
  )
  """)

  ### w1_to_class_id.table
  cursor.execute ("""DROP TABLE IF EXISTS w1ToClassId""")
  cursor.execute ("""
  CREATE TABLE w1ToClassId
  (
   Id INT unsigned NOT NULL,
   Class INT unsigned NOT NULL,

   index I_id (Id)
  )
  """)

  ### w2_to_class_id.table
  cursor.execute ("""DROP TABLE IF EXISTS w2ToClassId""")
  cursor.execute ("""
  CREATE TABLE w2ToClassId
  (
   LemmaId INT unsigned NOT NULL,
   ClassId SMALLINT unsigned NOT NULL,

   Ct INT unsigned NOT NULL,
   Freq INT unsigned NOT NULL,
   GlobalCt INT unsigned NOT NULL,

   CtLogDice INT unsigned NOT NULL,
   CtMiLogFreq INT unsigned NOT NULL,

   GsLogDice float(6,2),
   GsMiLogFreq float(6,2),

   StLogDice float(6,2),
   StMiLogFreq float(6,2),

   index I_lemma (LemmaId,Ct,Freq,GlobalCt,CtLogDice,CtMiLogFreq,GsLogDice,GsMiLogFreq,StLogDice,StMiLogFreq)
  )
  """)

"""
 Laden der Wortprofiltabellen in die MySQL-Tabellen
"""
def load_into_tables(cursor,directory):


  print '(: load data: '+ os.path.realpath(directory +'/id_to_class.table')
  cursor.execute ('LOAD DATA ' + g_strLocal + ' INFILE \"'+os.path.realpath(directory+'/id_to_class.table')+'\" INTO TABLE id2Class')

  print '(: load data: '+ os.path.realpath(directory +'/w2_to_class_id.table')
  cursor.execute ('LOAD DATA ' + g_strLocal + ' INFILE \"'+os.path.realpath(directory+'/w2_to_class_id.table')+'\" INTO TABLE w2ToClassId')

  print '(: load data: '+ os.path.realpath(directory +'/w1_to_class_id.table')
  cursor.execute ('LOAD DATA ' + g_strLocal + ' INFILE \"'+os.path.realpath(directory+'/w1_to_class_id.table')+'\" INTO TABLE w1ToClassId')


print "|: UPDATE DATABASE"

# Create option parser
parser = OptionParser()
parser.add_option("-s", dest="config", default="query-specification.xml", help=u"Angabe der Settings-Datei (*.xml)")
parser.add_option("-l", action="store_true", dest="local", default=False, help=u"Ob MySQL die Tabellen 'local' einlesen sollen")
(options, args) = parser.parse_args()

if options.local:
  g_strLocal="LOCAL"

### Prüfen der Parameter
if options.config==None:
  parser.error("missing config file")
  sys.exit(-1)
try:
  daten = file(options.config,'r')
except:
  parser.error("unknown settings file: " + options.config)
  sys.exit(-1)

#read specifications
mapConfig={}
fileConfig = file(options.config,'r')
for i in fileConfig.readlines():
  setting = i.rstrip('\n').split('\t')
  if len(setting) == 2:
    mapConfig[setting[0]] = setting[1]

### Parameter aus der Konfigurationsdatei prüfen
if 'TablePath' not in mapConfig:
  parser.error("missing table path in config file")
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

#create database
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






