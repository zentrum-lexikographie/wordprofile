#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

  Das Client-Programm fragt eine Wortprofil-MySQL-Datenbank über einen XMLRPC-Server ab und liefert MWE-Kookkurrenzen zu einer komplexen Info-ID.

  Beispielaufruf:
  python wp_mwe_rel_client.py -x http://localhost:8080 -i 1671#2#1759#0#0#14#145083@1671#2#92#4#0#3#14736

"""

import sys
sys.path.append('./moduls')
sys.path.append('./xmlrpc/moduls')

import xmlrpclib
from drawTable import *
import getopt
from optparse import OptionParser

### Komandozeilenoptionen einlesen
parser = OptionParser()
parser.add_option("-i", dest="info", default=None, help=u"die InfoId")
parser.add_option("-n", dest="number", default=20, help=u"Anzahl der Relationstupel (default=20)")
parser.add_option("-s", dest="start", default=0, help=u"Ausgabe ab welchem Relationstupel (default=0)")
parser.add_option("-f", dest="min_freq", default=-9999, help=u"Minimaler Frequenzwert (default=-9999)")
parser.add_option("-m", dest="min_stat", default=-9999, help=u"Minimaler Statistikwert (default=-9999)")
parser.add_option("-x", dest="host", default=None, help=u"Hostrechner (z.B. http://services.dwds.de:8049)")
parser.add_option("-o", dest="order", default="logDice", help=u"Angabe der Ordnung (frequency,logDice) (default=logDice)")
parser.add_option("--sf",action="store_true", dest="surface", default=False, help=u"Verwenden der Oberflächenform statt der Lemmaform")

(options, args) = parser.parse_args()


### Komandozeilenoptionen prüfen
if len(args) > 0:
	parser.error("incorrect number of arguments")

if options.info==None:
	parser.error("missing infiId")

if options.host==None:
  parser.error("missing host")

### XMLRPC-Client erstellen
s = xmlrpclib.ServerProxy(options.host)
#Print list of available methods
#print "methods:", s.system.listMethods()

### Abfrageoptionen erstellen
mapParam={}
mapParam["ConcordId"] = options.info
mapParam["Number"] = int(options.number)
mapParam["Start"] = int(options.start)
mapParam["OrderBy"] = options.order
mapParam["MinFreq"] = options.min_freq
mapParam["MinStat"] = options.min_stat

### Wortprofilserver abfragen
RelInfo = s.get_mwe_relations(mapParam)
#RelInfo = s.get_mwe_relations_single(mapParam)

### Ausgeben der MWE-Bestandteile
vParts = RelInfo['parts']
print "\033[32;1mBestandteile:\033[m",vParts

### Durchgehen der syntaktischen Relationen
RelList = RelInfo['data']
iRelCount=1
for l in RelList:
  for k in RelList[l]:

    listTuples = k['Tuples']
    print
    if "RelId" in k:
      print "\033[32;1m "+str(iRelCount)+". "+k['Relation']+" "+l+" ("+k["RelId"]+"): "+"\033[m"+k['Description']
    else:
      print "\033[32;1m "+str(iRelCount)+". "+k['Relation']+" "+l+": "+"\033[m"+k['Description']

    listPrint=[]
    if options.surface:
      strForm = "Form"
    else:
      strForm = "Lemma"

    ### Einsammeln der MWE-Kookkurrrenzen
    iCounter = 1
    for i in listTuples:        
        listPrint.append([str(iCounter),i['POS'],i[strForm],i['Score']['Frequency'],i['Score']['logDice'],i['ConcordId'],i['ConcordNo'],i['ConcordNoAccessible'],i['HasMwe']])
        iCounter+=1

    ### Ausgeben der Kookkurrrenzen als Tabelle
    listHeader = ['Rank','POS',strForm,'Frequency','logDice','Hit/MWE-ID','No','*No','HasMwe']
    print calculate_table(listHeader,listPrint)



