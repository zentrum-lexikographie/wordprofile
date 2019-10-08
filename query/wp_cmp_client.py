#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
  Das Client-Programm fragt eine Wortprofil-MySQL-Datenbank über einen XMLRPC-Server ab und vergleicht zwei Eingabelemmata. 
  Das Vergleichsergebnis wird in Tabellenform und farblich gekennzeichnet ausgegeben.

  Beispielaufruf:
  python wp_cmp_client.py -x http://localhost:8080 --l1 Mann --l2 Frau
"""

import sys
import xmlrpc.client
from optparse import OptionParser

from moduls.drawTable import calculate_table


def black(x):
    if isinstance(x, type(99)) or isinstance(x, type(9.9)):
        x = str(x)
    return "\033[30;1m" + x + "\033[1m"


def red(x):
    if isinstance(x, type(99)) or isinstance(x, type(9.9)):
        x = str(x)
    return "\033[31;1m" + x + "\033[1m"


def green(x):
    if isinstance(x, type(99)) or isinstance(x, type(9.9)):
        x = str(x)
    return "\033[32;1m" + x + "\033[1m"


def yellow(x):
    if isinstance(x, type(99)) or isinstance(x, type(9.9)):
        x = str(x)
    return "\033[33;1m" + x + "\033[1m"


def blue(x):
    if isinstance(x, type(99)) or isinstance(x, type(9.9)):
        x = str(x)
    return "\033[34;1m" + x + "\033[1m"


def magenta(x):
    if isinstance(x, type(99)) or isinstance(x, type(9.9)):
        x = str(x)
    return "\033[35;1m" + x + "\033[1m"


def cyan(x):
    if isinstance(x, type(99)) or isinstance(x, type(9.9)):
        x = str(x)
    return "\033[36;1m" + x + "\033[1m"


def white(x):
    if isinstance(x, type(99)) or isinstance(x, type(9.9)):
        x = str(x)
    return "\033[37;1m" + x + "\033[1m"


# Komandozeilenoptionen einlesen
parser = OptionParser()
parser.add_option("--l1", dest="lemma1", default=None, help="das Eingabewort")
parser.add_option("--l2", dest="lemma2", default=None, help="das Eingabewort")
parser.add_option("-n", dest="number", default=20, help="Anzahl der Relationstupel (default=20)")
parser.add_option("-b", dest="nbest", default=-1,
                  help="Die Anzahl der zu vergleichenden Relationstupel beider Wörter von vornherein einschränken")
parser.add_option("-f", dest="min_freq", default=-9999, help="Minimaler Frequenzwert (default=-9999)")
parser.add_option("-m", dest="min_stat", default=-9999, help="Minimaler Statistikwert (default=-9999)")
parser.add_option("-x", dest="host", default=None, help="Hostrechner (z.B. http://services.dwds.de:8049)")
parser.add_option("-c", dest="corpus", default="", help="Angabe des korpus (zeit,kern,21jhd)")
parser.add_option("-r", dest="relation", default="",
                  help="Angabe der gewünschten Relationen in einer Liste (SUBJA,SUBJP,OBJA,OBJD,OBJI,GMOD,ATTR,KON,PP)")
parser.add_option("-o", dest="order", default="LogDice",
                  help="Angabe der Ordnung (frequency,LogDice,MiLogFreq,MI3) (default=logDice)")
# parser.add_option("--is",action="store_true", dest="intersection", default=False, help=u"Schnitt berechen")
parser.add_option("--op", dest="operation", default="adiff",
                  help="Operation (adiff,rmax), Default: adiff")  # diff,adiff,max,min,rmax,avg,havg,gavg
parser.add_option("--cs", action="store_true", dest="case_sensitive", default=False, help="Case-sensitive Abfrage")
parser.add_option("--sf", action="store_true", dest="surface", default=False,
                  help="Verwenden der Oberflächenform statt der Lemmaform")

(options, args) = parser.parse_args()

# Komandozeilenoptionen prüfen
if len(args) > 0:
    parser.error("incorrect number of arguments")

if options.lemma1 == None or options.lemma2 == None:
    parser.error("missing input word pair")

# Komandozeilenoptionen prüfen
if options.host == None:
    parser.error("missing host")

s = xmlrpc.client.ServerProxy(options.host)

# Abfrageoptionen für die Lemmainformationen erstellen
mapParam = {}
mapParam["Word1"] = options.lemma1
mapParam["Word2"] = options.lemma2
mapParam["Subcorpus"] = options.corpus
mapParam["CaseSensitive"] = int(options.case_sensitive)

# Lemmainformationen vom Wortprofilserver abfragen
mapping = s.get_lemma_and_pos_diff(mapParam)

# Wenn die Lemmata enthalten sind
if len(mapping) > 0:

    # Ermitteln der Wortart (evtl. über Tastatureingabe)
    if len(mapping) == 1:
        mapSelect = mapping[0]
        print("\033[32;1m" + "(1) " + "\033[m" + yellow(mapSelect["Lemma1"]) + "/" + cyan(mapSelect["Lemma2"]) + " [" +
              mapSelect["POS"] + "]")
    else:
        print("\033[32;1m" + "Grundform Wählen:" + "\033[m")
        data = "999"
        while True:
            iCounter = 1
            for i in mapping:
                print("\033[32;1m" + "(" + str(iCounter) + ") " + "\033[m" + yellow(i["Lemma1"]) + "/" + cyan(
                    i["Lemma2"]) + " [" + i["POS"] + "]")
                iCounter = iCounter + 1
            data = sys.stdin.readline()

            if int(data) > len(mapping) or int(data) < 0:
                continue

            mapSelect = mapping[int(data) - 1]
            break

    # abzufragende Relationen ermitteln
    listRel = []
    if options.relation != "":
        listRel = options.relation.split(',')
        if listRel != []:
            listRel = listRel
    if listRel == []:
        listRel = mapping[0]["Relations"]

    # Abfrageoptionen für den Wortvergleich erstellen
    mapParam = {}
    mapParam["Lemma1"] = mapping[0]["Lemma1"]
    mapParam["Lemma2"] = mapping[0]["Lemma2"]
    mapParam["Pos"] = mapping[0]["POS"]
    mapParam["Relations"] = listRel
    mapParam["Number"] = int(options.number)
    mapParam["OrderBy"] = options.order
    mapParam["MinFreq"] = 5
    mapParam["MinStat"] = 0
    mapParam["Subcorpus"] = ""
    if options.nbest != -1:
        mapParam["NBest"] = int(options.nbest)
    mapParam["Operation"] = options.operation

    # Wortvergleich abfragen
    RelList = s.get_diff(mapParam)

    # Durchgehen der Relationen
    iRelCount = 1
    for k in RelList:
        listTuples = k['Tuples']
        print()
        print("\033[32;1m " + str(iRelCount) + ". " + k['Relation'] + ": " + "\033[m" + k['Description'])

        listPrint = []
        if options.surface:
            strForm = "Form"
        else:
            strForm = "Lemma"
        # Durchgehen der Kookkurrenzvergleiche
        for j in listTuples:
            # Nur Wort 1
            if j['Position'] == "left":
                listArg = []
                listArg.append(yellow(j[strForm]))
                listArg.append(yellow(j['Score']['AScomp']))
                listArg.append(yellow(j['Score']['Frequency1']))
                listArg.append(yellow(j['Score']['Frequency2']))
                listArg.append(yellow(j['Score']['Rank1']))
                listArg.append(yellow(j['Score']['Rank2']))
                listArg.append(yellow(j['Score']['Assoziation1']))
                listArg.append(yellow(j['Score']['Assoziation2']))
                listPrint.append(listArg)
            # Nur Wort 2
            elif j['Position'] == "right":
                listArg = []
                listArg.append(cyan(j[strForm]))
                listArg.append(cyan(j['Score']['AScomp']))
                listArg.append(cyan(j['Score']['Frequency1']))
                listArg.append(cyan(j['Score']['Frequency2']))
                listArg.append(cyan(j['Score']['Rank1']))
                listArg.append(cyan(j['Score']['Rank2']))
                listArg.append(cyan(j['Score']['Assoziation1']))
                listArg.append(cyan(j['Score']['Assoziation2']))
                listPrint.append(listArg)
            # Beide Wörter
            else:
                listArg = []
                listArg.append(red(j[strForm]))
                listArg.append(red(j['Score']['AScomp']))
                listArg.append(red(j['Score']['Frequency1']))
                listArg.append(red(j['Score']['Frequency2']))
                listArg.append(red(j['Score']['Rank1']))
                listArg.append(red(j['Score']['Rank2']))
                listArg.append(red(j['Score']['Assoziation1']))
                listArg.append(red(j['Score']['Assoziation2']))
                listPrint.append(listArg)

        # Ausgeben des Vergleiches als Tabelle
        listHeader = [strForm, 'Score', 'Frequency1', 'Frequency2', 'Rank1', 'Rank2', 'Association1', 'Association2']
        print(calculate_table(listHeader, listPrint))

else:
    print("): Wort nicht enthalten")
