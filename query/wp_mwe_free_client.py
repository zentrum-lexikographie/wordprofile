#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

  Das Client-Programm fragt eine Wortprofil-MySQL-Datenbank über einen XMLRPC-Server ab und liefert MWE-Kookkurrenzen zu einer Lemmaliste.
  Um die syntaktische Zugehörigkeiten innerhalb der Lemmaliste erfassen zu können, müssen die Lemmaformen eine bestimmte Ordnung haben.

  Möglichliche Abfragen (nach Wortarten als Regex) sind folgend:

  *Nominalphrase:
    Adverb* Adjektiv* Substantiv (Präposition Substantiv)?

  *Nominalphrase als Subjekt:
    Adverb* Adjektiv* Substantiv (Präposition Substantiv)? Verb

  *Nominalphrase als Objekt:
    Verb Adverb* Adjektiv* Substantiv (Präposition Substantiv)?

  *Verb:
    Verb Adverb* (Präposition Substantiv)?


  Beispiele sind:
    schön,Mann
    jung,Frau,mit,Haar
    liegen,auf,Rasen
 

  Beispielaufruf:
  python wp_mwe_free_client.py -x http://localhost:8080 -l "jung,Frau,mit,Haar" -n 20

"""
#(Adverb* Adjektiv* Substantiv)? (Präposition Substantiv)? (Verb (Präposition Substantiv)? Adverb* (Adjektiv* Substantiv)? (Präposition Substantiv)?)?*


import sys
sys.path.append('./moduls')
sys.path.append('./xmlrpc/moduls')

import xmlrpclib
from drawTable import *
import getopt
import codecs
from optparse import OptionParser

### Komandozeilenoptionen einlesen
parser = OptionParser()
parser.add_option("-l", dest="LemmaList", default=None, help=u"die kommagetrennte Lemma-Eingabeliste (jung,Frau,mit,Haar)")
parser.add_option("-s", dest="start", default=0, help=u"Startpunkt der Relationstupel (default=0)")
parser.add_option("-n", dest="number", default=20, help=u"Anzahl der Relationstupel (default=20)")
parser.add_option("-f", dest="min_freq", default=0, help=u"Minimaler Frequenzwert (default=0)")
parser.add_option("-m", dest="min_stat", default=-9999, help=u"Minimaler Statistikwert (default=-9999)")
parser.add_option("-x", dest="host", default=None, help=u"Hostrechner (z.B. http://services.dwds.de:8049)")
parser.add_option("-r", dest="relation", default="", help=u"Angabe der gewünschten Relationen in einer Liste (SUBJA,SUBJP,OBJA,OBJD,OBJI,GMOD,ATTR,KON,PP)")
parser.add_option("-o", dest="order", default="logDice", help=u"Angabe der Ordnung (logDice,frequency) (default=logDice)")
parser.add_option("--cs",action="store_true", dest="case_sensitive", default=False, help=u"Case-sensitive Abfrage")
parser.add_option("--sf",action="store_true", dest="surface", default=False, help=u"Verwenden der Oberflächenform statt der Lemmaform")
parser.add_option("--esf",action="store_true", dest="extended_surface_form", default=False, help=u"Verwenden der erweiterten")
parser.add_option("-b",action="store_true", dest="examples", default=False, help=u"Ausgeben von Beispielabfragen")
parser.add_option("-v",action="store_true", dest="variations", default=False, help=u"Generieren von alternativen Schreibungen zu einem Eingabewort")

(options, args) = parser.parse_args()

### Abfragebeispiele
if options.examples==True:
  print "Grundlegende Abfolge: Subjekt Verb Objekt"
  print "Beispiele:"
  print "* jung,Frau,mit,Messer"
  print "* Frau,lieben,Mann"
  print "* jung,Frau,lieben,heute,alt,Mann"
  print "* jung,Frau,lieben,in,Nacht,alt,Mann"
  print "* jung,Frau,mit,Messer,lieben,in,Nacht,alt,Mann,mit,Gitarre"
  print "* lieben,schön,Mann"
  print "* schön,Frau,lieben"
  sys.exit(0)

### Komandozeilenoptionen prüfen
if len(args) > 0:
  parser.error("incorrect number of arguments")

if options.LemmaList==None:
  parser.error("missing input lemma list")

if options.host==None:
  parser.error("missing host")

### XMLRPC-Client erstellen
s = xmlrpclib.ServerProxy(options.host)
#Print list of available methods
#print "methods:", s.system.listMethods()

mapParam={}
listPart=[]
listPartBase = options.LemmaList.split(',')
for i in listPartBase:
  listPart.append(i)

### Abfrageoptionen für die Lemmainformationen erstellen
mapParam["Parts"] = listPart
mapParam["CaseSensitive"] = int(options.case_sensitive)
mapParam["UseVariations"] = int(options.variations)

#Lemma-Informationen zu den einzelnen Lemmaformen ermitteln
vLemmaList = s.get_lemma_and_pos_by_list( mapParam )

### abzufragende Relationen ermitteln
listRel=[]
if options.relation != "":
  listRel = options.relation.split(',')
  if listRel != []:
    listRel = listRel

### Abfrageoptionen für die MWE-Kookkurrenzinformationen erstellen
mapParam["Parts"]=vLemmaList
mapParam["Start"] = int(options.start)
mapParam["Number"] = int(options.number)
mapParam["OrderBy"] = options.order
#mapParam["MinFreq"] = int(options.min_freq)
#mapParam["MinStat"] = int(options.min_stat)
mapParam["Relations"] = listRel
mapParam["ExtendedSurfaceForm"] = int(options.extended_surface_form)

### MWE-Kookkurrenzinformationen vom Wortprofilserver abfragen
RelInfo = s.get_mwe_relations_by_list(mapParam)

vParts = RelInfo['parts']
RelList = RelInfo['data']

if len(RelList)==0:
  print "|: keine entsprechenden MWE-Kookkurrenzen enthalten"

iRelCount=1
### Durchgehen der Relationen
for l in RelList:
  print l
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

    ### Durchgehen der MWE-Kookkurrenzen
    iCounter = 1
    for i in listTuples:        
        listPrint.append([str(iCounter),i['POS'],i[strForm],i['Score']['Frequency'],i['Score']['logDice'],i['ConcordId'],i['ConcordNo'],i['ConcordNoAccessible'],i['HasMwe']])
        iCounter+=1

    ### Ausgeben der Kookkurrenzen als Tabelle
    listHeader = ['Rank','POS',strForm,'Frequency','logDice','ConcordId','No','*No','HasMwe']
    print calculate_table(listHeader,listPrint)

