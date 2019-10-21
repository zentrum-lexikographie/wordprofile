#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

  Das Client-Programm fragt eine Wortprofil-MySQL-Datenbank über einen XMLRPC-Server ab und liefert Kookkurrenzen zu einem Eingabelemma.

  Beispielaufruf:
  python wp_rel_client.py -x http://localhost:8080 -l Mann -o MiLogFreq -n 20

"""

import sys
import xmlrpc.client
from optparse import OptionParser

from wordprofile.pprint.drawTable import calculate_table

parser = OptionParser()
parser.add_option("-l", dest="lemma", default=None, help="das Eingabelemma")
parser.add_option("-p", dest="pos_tag", default="", help="Substantiv,Verb,Adjektiv,Adverb")
parser.add_option("-s", dest="start", default=0, help="Startpunkt der Relationstupel (default=0)")
parser.add_option("-n", dest="number", default=20, help="Anzahl der Relationstupel (default=20)")
parser.add_option("-f", dest="min_freq", default=0, help="Minimaler Frequenzwert (default=0)")
parser.add_option("-m", dest="min_stat", default=-9999, help="Minimaler Statistikwert (default=-9999)")
parser.add_option("-c", dest="corpus", default="", help="Angabe des korpusnamen (zeit,kern,21jhd,etc.)")
parser.add_option("-x", dest="host", default=None, help="Hostrechner (z.B. http://localhost:8080)")
parser.add_option("-r", dest="relation", default="",
                  help="Gewünschten Relationen in einer Liste (SUBJA,SUBJP,OBJA,OBJD,OBJI,GMOD,ATTR,KON,PP,etc.)")
parser.add_option("-o", dest="order", default="log_dice",
                  help="Angabe der Ordnung (frequency,log_dice,mi_log_freq,mi3) (default=log_dice)")
parser.add_option("--cs", action="store_true", dest="case_sensitive", default=False, help="Case-sensitive Abfrage")
parser.add_option("--sf", action="store_true", dest="surface", default=False,
                  help="Verwenden der Oberflächenform statt der Lemmaform")
parser.add_option("-v", action="store_true", dest="variations", default=False,
                  help="Einbeziehung von alternativen Schreibungen zu einem Eingabelemma")
parser.add_option("--out", dest="file", default="", help="Ausgabedatei")

(options, args) = parser.parse_args()

### Komandozeilenoptionen prüfen
if len(args) > 0:
    parser.error("incorrect number of arguments")

if options.lemma == None:
    parser.error("missing input lemma")

if options.host == None:
    parser.error("missing host")

strPosTag = options.pos_tag
strFile = options.file

### XMLRPC-Client erstellen
s = xmlrpc.client.ServerProxy(options.host)

### Abfrageoptionen für die Lemmainformationen erstellen
mapParam = {}
mapParam["Word"] = options.lemma
mapParam["Subcorpus"] = options.corpus
mapParam["CaseSensitive"] = int(options.case_sensitive)
mapParam["UseVariations"] = int(options.variations)

### Lemmainformationen vom Wortprofilserver abfragen
mapping = s.get_lemma_and_pos(mapParam)
print("mapping", mapping)

### Wenn das Lemma enthalten ist
if len(mapping) > 0:

    mapSelect = {}
    if strPosTag == "":
        ### Ermitteln der Wortart (evtl. über Tastatureingabe)
        if len(mapping) == 1:
            mapSelect = mapping[0]
            print("\033[32;1m" + "(1) " + "\033[m" + mapSelect["Lemma"] + " [" + mapSelect["POS"] + "]")
        else:
            print("\033[32;1m" + "Grundform Wählen:" + "\033[m")
            data = "999"
            while True:
                iCounter = 1
                for i in mapping:
                    print("\033[32;1m" + "(" + str(iCounter) + ") " + "\033[m" + i["Lemma"] + " [" + i["POS"] + "]")
                    iCounter = iCounter + 1
                data = sys.stdin.readline()

                if int(data) > len(mapping) or int(data) < 0:
                    continue

                mapSelect = mapping[int(data) - 1]
                break
    else:
        for i in mapping:
            if i["POS"] == strPosTag:
                mapSelect = i

    if mapSelect == {}:
        print("): keine Kookkurrenzen für die Wortart vorhanden")
        sys.exit(-1)

    ### Ausgeben von Meta-Informationen
    print("\033[32;1m" + "Anzahl an Relationen mit Doppelten:" + "\033[m", mapSelect["Frequency"])
    print("\033[32;1m" + "mögliche Relationen :" + "\033[m", mapSelect["Relations"])

    ### abzufragende Relationen ermitteln
    listRel = []
    if options.relation != "":
        listRel = options.relation.split(',')
        if listRel != []:
            listRel = listRel
    if listRel == []:
        listRel = mapSelect['Relations']

    ### Abfrageoptionen für die Kookkurrenzinformationen erstellen
    mapParam = {}
    mapParam["Lemma"] = mapSelect["Lemma"]
    mapParam["Pos"] = mapSelect["POS"]
    mapParam["Start"] = int(options.start)
    mapParam["Number"] = int(options.number)
    mapParam["OrderBy"] = options.order
    mapParam["MinFreq"] = int(options.min_freq)
    mapParam["MinStat"] = int(options.min_stat)
    mapParam["Subcorpus"] = options.corpus
    mapParam["Relations"] = listRel

    ### Kookkurrenzinformationen vom Wortprofilserver abfragen
    RelList = s.get_relations(mapParam)

    strOrder = options.order

    ### wenn daas Ergebnis nicht in eine Datei geschrieben werden soll
    iCounter = 1
    ### Durchgehen der Relationen
    iRelCount = 1
    for k in RelList:
        listTuples = k['Tuples']
        print()
        if 'RelId' in k:
            print("\033[32;1m " + str(iRelCount) + ". " + k['Relation'] + " (" + k['RelId'] + "): " + "\033[m" + k[
                'Description'])
        else:
            print("\033[32;1m " + str(iRelCount) + ". " + k['Relation'] + ": " + "\033[m" + k['Description'])

        listPrint = []

        ### Aufsammeln der Kookkurrrenzen
        iCounter = 1
        for i in listTuples:
            listPrint.append(
                [str(iCounter), i['POS'], i["Lemma"], i['Score']['Frequency'], i['Score'][strOrder],
                 i['ConcordId'], i['ConcordNo'], i['ConcordNoAccessible']])

            iCounter += 1

        ### Ausgeben der Kookkurrenzen als Tabelle
        listHeader = ['Rank', 'POS', "Lemma", 'Frequency', strOrder, 'Hit/MWE-ID', 'No', '*No']
        print(calculate_table(listHeader, listPrint))
        iRelCount += 1
else:
    print("): Lemma nicht enthalten")
