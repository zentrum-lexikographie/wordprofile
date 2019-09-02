#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

  Das Client-Programm fragt eine Wortprofil-MySQL-Datenbank über einen XMLRPC-Server ab und liefert Kookkurrenzen zu einem Eingabelemma.

  Beispielaufruf:
  python wp_rel_client.py -x http://localhost:8080 -l Mann -o MiLogFreq -n 20

"""

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
parser.add_option("-l", dest="lemma", default=None, help=u"das Eingabelemma")
parser.add_option("-p", dest="pos_tag", default="", help=u"Substantiv,Verb,Adjektiv,Adverb")
parser.add_option("-s", dest="start", default=0, help=u"Startpunkt der Relationstupel (default=0)")
parser.add_option("-n", dest="number", default=20, help=u"Anzahl der Relationstupel (default=20)")
parser.add_option("-f", dest="min_freq", default=0, help=u"Minimaler Frequenzwert (default=0)")
parser.add_option("-m", dest="min_stat", default=-9999, help=u"Minimaler Statistikwert (default=-9999)")
parser.add_option("-c", dest="corpus", default="", help=u"Angabe des korpusnamen (zeit,kern,21jhd,etc.)")
parser.add_option("-x", dest="host", default=None, help=u"Hostrechner (z.B. http://localhost:8080)")
parser.add_option("-r", dest="relation", default="", help=u"Gewünschten Relationen in einer Liste (SUBJA,SUBJP,OBJA,OBJD,OBJI,GMOD,ATTR,KON,PP,etc.)")
parser.add_option("-o", dest="order", default="logDice", help=u"Angabe der Ordnung (MiLogFreq,logDice,MI3,logLike,TScore) (default=logDice)")
parser.add_option("--cs",action="store_true", dest="case_sensitive", default=False, help=u"Case-sensitive Abfrage")
parser.add_option("--sf",action="store_true", dest="surface", default=False, help=u"Verwenden der Oberflächenform statt der Lemmaform")
parser.add_option("--esf",action="store_true", dest="extended_surface_form", default=False, help=u"Verwenden der erweiterten Oberflächenform")
parser.add_option("-v",action="store_true", dest="variations", default=False, help=u"Einbeziehung von alternativen Schreibungen zu einem Eingabelemma")
parser.add_option("--out", dest="file", default="", help=u"Ausgabedatei")

(options, args) = parser.parse_args()

### Komandozeilenoptionen prüfen
if len(args) > 0:
  parser.error("incorrect number of arguments")

if options.lemma==None:
  parser.error("missing input lemma")

if options.host==None:
  parser.error("missing host")

strPosTag = options.pos_tag
strFile = options.file

### XMLRPC-Client erstellen
s = xmlrpclib.ServerProxy(options.host)
#Print list of available methods
#print "methods:", s.system.listMethods()

### Abfrageoptionen für die Lemmainformationen erstellen
mapParam={}
mapParam["Word"] = options.lemma
mapParam["Subcorpus"] = options.corpus
mapParam["CaseSensitive"] = int(options.case_sensitive)
mapParam["UseVariations"] = int(options.variations)

### Lemmainformationen vom Wortprofilserver abfragen
mapping = s.get_lemma_and_pos(mapParam)

#mapParam={}
#mapParam["RelId"] ="1671#2#18"
#print s.get_cooccurrences(mapParam)

### Wenn das Lemma enthalten ist
if len(mapping) > 0:  

  mapSelect={}
  if strPosTag == "":
    ### Ermitteln der Wortart (evtl. über Tastatureingabe)
    if len(mapping) == 1:
      mapSelect = mapping[0]
      print "\033[32;1m"+"(1) "+"\033[m" + mapSelect["Lemma"] + " [" + mapSelect["POS"]+"]"
    else:
      print "\033[32;1m"+"Grundform Wählen:"+"\033[m"
      data = "999"
      while True:
        iCounter=1
        for i in mapping:
          print "\033[32;1m"+"("+str(iCounter)+") "+"\033[m" + i["Lemma"] + " [" + i["POS"]+"]"
          iCounter = iCounter+1
        data = sys.stdin.readline()

        if int(data) > len(mapping) or int(data) < 0:
          continue

        mapSelect = mapping[int(data)-1]
        break
  else:
    for i in mapping:
      if i["POS"]==strPosTag:
        mapSelect = i

  if mapSelect=={}:
    print "): keine Kookkurrenzen für die Wortart vorhanden"
    sys.exit(-1)

  ### Ausgeben von Meta-Informationen
  print "\033[32;1m"+"Anzahl an Relationen mit Doppelten:"+"\033[m",mapSelect["Frequency"]
  print "\033[32;1m"+"Anzahl an Relationen ohne Doppelte:"+"\033[m",mapSelect["Count"]
  print "\033[32;1m"+"mögliche Relationen :"+"\033[m",mapSelect["Relations"]

  ### abzufragende Relationen ermitteln
  listRel=[]
  if options.relation != "":
    listRel = options.relation.split(',')
    if listRel != []:
      listRel = listRel
  if listRel==[]:
    listRel = mapSelect['Relations']


  ### Abfrageoptionen für die Kookkurrenzinformationen erstellen
  mapParam={}
  mapParam["LemmaId"] = mapSelect["LemmaId"]
  mapParam["PosId"] = mapSelect["PosId"]
  mapParam["Start"] = int(options.start)
  mapParam["Number"] = int(options.number)
  mapParam["OrderBy"] = options.order
  mapParam["MinFreq"] = int(options.min_freq)
  mapParam["MinStat"] = int(options.min_stat)
  mapParam["Subcorpus"] = options.corpus
  mapParam["Relations"] = listRel
  mapParam["ExtendedSurfaceForm"] = int(options.extended_surface_form)

  ### Kookkurrenzinformationen vom Wortprofilserver abfragen
  RelList = s.get_relations(mapParam)

  strOrder=options.order

  if options.surface or options.extended_surface_form:
    strForm = "Form"
  else:
    strForm = "Lemma"

  ### wenn daas Ergebnis nicht in eine Datei geschrieben werden soll
  iCounter=1
  if strFile=="":

    ### Durchgehen der Relationen
    iRelCount=1
    for k in RelList:
      listTuples = k['Tuples']
      print
      if 'RelId' in k:      
        print "\033[32;1m "+str(iRelCount)+". "+k['Relation']+" ("+k['RelId']+"): "+"\033[m"+k['Description']
      else:
        print "\033[32;1m "+str(iRelCount)+". "+k['Relation']+": "+"\033[m"+k['Description']

      listPrint = []
      
      ### Aufsammeln der Kookkurrrenzen
      iCounter = 1
      bMWE=False
      for i in listTuples: 

        if 'HasMwe' in i:
          bMWE=True
          listPrint.append([str(iCounter),i['POS'],i[strForm],i['Score']['Frequency'],i['Score'][strOrder],i['ConcordId'],i['ConcordNo'],i['ConcordNoAccessible'],i['HasMwe']])
        else:
          listPrint.append([str(iCounter),i['POS'],i[strForm],i['Score']['Frequency'],i['Score'][strOrder],i['ConcordId'],i['ConcordNo'],i['ConcordNoAccessible']])

        iCounter+=1

      ### Ausgeben der Kookkurrenzen als Tabelle
      if bMWE:
        listHeader = ['Rank','POS',strForm,'Frequency',strOrder,'Hit/MWE-ID','No','*No','HasMwe']
      else:
        listHeader = ['Rank','POS',strForm,'Frequency',strOrder,'Hit/MWE-ID','No','*No']
      print calculate_table(listHeader,listPrint)
      iRelCount+=1

  else:

    ### Schreiben der Kookkurrenzen in eine Datei
    myOut = codecs.open(strFile,'w','utf8')
    myOut.write('Rang\tLemma\tFrequenz\tLogDice\tMiLogFreq\tTrefferId\n')
    for k in RelList:
      listTuples = k['Tuples']
      iCounter = 1
      for i in listTuples:
        myOut.write(str(iCounter))
        myOut.write('\t')
        myOut.write(i[strForm])
        myOut.write('\t')
        myOut.write(i['POS'])
        myOut.write('\t')
        myOut.write(str(i['Score']['Frequency']))
        myOut.write('\t')
        myOut.write(str(i['Score']['logDice']))
        myOut.write('\t')
        myOut.write(str(i['Score']['MiLogFreq']))
        myOut.write('\t')
        myOut.write(str(i['ConcordId']))
        myOut.write('\n')

        iCounter+=1

    myOut.close()

else:
  print "): Lemma nicht enthalten"

