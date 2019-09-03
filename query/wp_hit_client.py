#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

  Das Client-Programm fragt eine Wortprofil-MySQL-Datenbank über einen XMLRPC-Server ab und liefert Texttreffer zu einer Texttreffer-Id.

  Beispielaufruf:
  python wp_con_client.py -x http://localhost:8080 -i 1671#2#428#4#11112#15#207136 -n 20

"""

import sys
import xmlrpc.client
from optparse import OptionParser

from moduls.drawConcord import draw_concord

parser = OptionParser()
parser.add_option("-i", dest="info", default=-1, help="die Texttreffer-ID")
parser.add_option("-s", dest="start", default=0, help="Trefferstart")
parser.add_option("-n", dest="number", default=20, help="Trefferanzahl (default=20)")
parser.add_option("-x", dest="host", default="http://localhost:9999", help="host default=http://services.dwds.de:9999")
parser.add_option("-u", action="store_true", dest="internal_user", default=False,
                  help="interner Benutzer (mit Rechten)")
parser.add_option("--ct", action="store_true", dest="context", default=False,
                  help="anzeigen der Contexte (rechter, linker Satz)")
parser.add_option("--br", dest="width", default=140, help="Breite der Anzeige (default=140)")
parser.add_option("--sc", action="store_true", dest="score", default=False,
                  help="primär nach dem Sentence-Score sortieren")
parser.add_option("-a", action="store_false", dest="dateDesc", default=True, help="Datum aufsteigend")
parser.add_option("-c", dest="corpus", default="", help="einzelner Korpus, in dem gesucht werden soll")
parser.add_option("--out", dest="file", default="", help="Ausgabedatei")

(options, args) = parser.parse_args()

### Komandozeilenoptionen prüfen
if options.info == -1:
    parser.error("): missing info id")
    sys.exit(-1)

strInfo = options.info
strFile = options.file

### XMLRPC-Client erstellen
s = xmlrpc.client.ServerProxy(options.host)
# Print list of available methods
# print "methods:", s.system.listMethods()

### Parametermap erstellen
mapParam = {}
mapParam["InfoId"] = strInfo
mapParam["Start"] = int(options.start)
mapParam["Number"] = int(options.number)
mapParam["Subcorpus"] = options.corpus
mapParam["DateDesc"] = int(options.dateDesc)
mapParam["UseScore"] = int(options.score)
mapParam["UseContext"] = int(options.context)
mapParam["InternalUser"] = int(options.internal_user)
iConcordId = mapParam["InfoId"]

### Abfrage der Texttreffer zusammen mit groben Relationsinformationen
mapRelInfo = s.get_concordances_and_relation(mapParam)

listConcord = []
iCounter = 1

### für jeden Texttreffer
for i in mapRelInfo['Tuples']:

    ### Metainformationen
    strBiblCorpus = i['Bibl']['Corpus'].encode('utf8')
    strBiblDate = i['Bibl']['Date'].encode('utf8')
    strBiblTextclass = i['Bibl']['TextClass'].encode('utf8')
    strBiblOrig = i['Bibl']['Orig'].encode('utf8')
    strBiblScan = i['Bibl']['Scan'].encode('utf8')
    strBiblAvail = str(i['Bibl']['Avail'])
    strBiblPage = i['Bibl']['Page'].encode('utf8')
    strScore = str(i['Score'])

    ### Satzinformation
    strSentence = i['ConcordLine']
    strLeft = ""
    strRight = ""
    if i['ConcordLeft'] != "":
        strLeft = '\033[0;34m' + i['ConcordLeft'] + '\033[0m '
    if i['ConcordRight'] != "":
        strRight = ' \033[0;34m' + i['ConcordRight'] + '\033[0m '

    if strFile == "":
        ### wenn die Informationen direkt ausgegeben werden sollen
        strMeta = "%i) %s | %s | %s | %s | %s | %s | %s | %s" % (
            iCounter, strBiblCorpus, strBiblDate, strBiblTextclass, strBiblOrig, strBiblScan, strBiblAvail, strBiblPage,
            strScore)
        listConcord.append((strLeft + strSentence + strRight, strMeta))
    else:
        ### wenn die Informationen in eine Datei geschrieben werden sollen (ohne Meta-Informationen)
        listConcord.append((iCounter, strLeft + strSentence + strRight))

    iCounter = iCounter + 1

if strFile == "":

    ### Ausgeben der groben Relationsinformationen
    print("\033[32;1m" + "Relation: " + "\033[m" + mapRelInfo['Relation'])
    print("\033[32;1m" + "Lemma1: " + "\033[m" + mapRelInfo['Lemma1'])
    print("\033[32;1m" + "Lemma2: " + "\033[m" + mapRelInfo['Lemma2'])
    print("\033[32;1m" + "Description: " + "\033[m" + mapRelInfo['Description'])

    ### Ausgeben der Texttreffertabelle
    draw_concord(listConcord, False, int(options.width))
else:
    ### Schreiben der Texttrefferinformationen
    myOut = open(strFile, 'w', encoding='utf-8')
    for i in listConcord:
        myOut.write(str(i[0]))
        myOut.write('\t')
        myOut.write(i[1])
        myOut.write('\n')
    myOut.close()
