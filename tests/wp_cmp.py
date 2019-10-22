#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
  Das Client-Programm fragt eine Wortprofil-MySQL-Datenbank über einen XMLRPC-Server ab und vergleicht zwei Eingabelemmata. 
  Das Vergleichsergebnis wird in Tabellenform und farblich gekennzeichnet ausgegeben.

  Beispielaufruf:
  python wp_cmp_client.py  --l1 Mann --l2 Frau
"""
import getpass
import logging
import sys
from argparse import ArgumentParser

from wordprofile.pprint.drawTable import calculate_table
from wp_server import WortprofilQuery

parser = ArgumentParser()
parser.add_argument("--user", type=str, help="database username", required=True)
parser.add_argument("--database", type=str, help="database name", required=True)
parser.add_argument("--hostname", default="localhost", type=str, help="XML-RPC hostname")
parser.add_argument("--passwd", action="store_true", help="ask for database password")
parser.add_argument("--port", default=8086, type=int, help="XML-RPC port")
parser.add_argument('--spec', type=str, required=True, help="Angabe der Settings-Datei (*.xml)")
parser.add_argument("--l1", dest="lemma1", type=str, required=True, help="das Eingabewort")
parser.add_argument("--l2", dest="lemma2", type=str, required=True, help="das Eingabewort")
parser.add_argument("-n", dest="number", default=20, help="Anzahl der Relationstupel (default=20)")
parser.add_argument("-b", dest="nbest", default=-1,
                    help="Die Anzahl der zu vergleichenden Relationstupel beider Wörter von vornherein einschränken")
parser.add_argument("-f", dest="min_freq", default=-9999, help="Minimaler Frequenzwert (default=-9999)")
parser.add_argument("-m", dest="min_stat", default=-9999, help="Minimaler Statistikwert (default=-9999)")
parser.add_argument("-x", dest="host", default=None, help="Hostrechner (z.B. http://services.dwds.de:8049)")
parser.add_argument("-c", dest="corpus", default="", help="Angabe des korpus (zeit,kern,21jhd)")
parser.add_argument("-r", dest="relation", default="",
                    help="Angabe der gewünschten Relationen in einer Liste (SUBJA,SUBJP,OBJA,OBJD,OBJI,GMOD,ATTR,KON,PP)")
parser.add_argument("-o", dest="order", default="log_dice",
                    help="Angabe der Ordnung (frequency,log_dice,mi_log_freq,mi3) (default=log_dice)")
# parser.add_argument("--is",action="store_true", dest="intersection", default=False, help=u"Schnitt berechen")
parser.add_argument("--op", dest="operation", default="adiff",
                    help="Operation (adiff,rmax), Default: adiff")  # diff,adiff,max,min,rmax,avg,havg,gavg
parser.add_argument("--cs", action="store_true", dest="case_sensitive", default=False, help="Case-sensitive Abfrage")
parser.add_argument("--sf", action="store_true", dest="surface", default=False,
                    help="Verwenden der Oberflächenform statt der Lemmaform")

args = parser.parse_args()

logger = logging.getLogger('wordprofile')
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)

print('user: ' + args.user)
print('db: ' + args.database)
if args.passwd:
    db_password = getpass.getpass("db password: ")
else:
    db_password = args.user
s = WortprofilQuery(args.hostname, args.user, db_password, args.database, args.port, args.spec)


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


# Abfrageoptionen für die Lemmainformationen erstellen
mapParam = {}
mapParam["Word1"] = args.lemma1
mapParam["Word2"] = args.lemma2
mapParam["Subcorpus"] = args.corpus
mapParam["CaseSensitive"] = args.case_sensitive

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
    if args.relation != "":
        listRel = args.relation.split(',')
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
    mapParam["Number"] = int(args.number)
    mapParam["OrderBy"] = args.order
    mapParam["MinFreq"] = 5
    mapParam["MinStat"] = 0
    mapParam["Subcorpus"] = ""
    if args.nbest != -1:
        mapParam["NBest"] = int(args.nbest)
    mapParam["Operation"] = args.operation

    # Wortvergleich abfragen
    RelList = s.get_diff(mapParam)

    # Durchgehen der Relationen
    iRelCount = 1
    for k in RelList:
        listTuples = k['Tuples']
        print()
        print("\033[32;1m " + str(iRelCount) + ". " + k['Relation'] + ": " + "\033[m" + k['Description'])

        listPrint = []
        # Durchgehen der Kookkurrenzvergleiche
        for j in listTuples:
            # Nur Wort 1
            if j['Position'] == "left":
                listArg = []
                listArg.append(yellow(j["Lemma"]))
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
                listArg.append(cyan(j["Lemma"]))
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
                listArg.append(red(j["Lemma"]))
                listArg.append(red(j['Score']['AScomp']))
                listArg.append(red(j['Score']['Frequency1']))
                listArg.append(red(j['Score']['Frequency2']))
                listArg.append(red(j['Score']['Rank1']))
                listArg.append(red(j['Score']['Rank2']))
                listArg.append(red(j['Score']['Assoziation1']))
                listArg.append(red(j['Score']['Assoziation2']))
                listPrint.append(listArg)

        # Ausgeben des Vergleiches als Tabelle
        listHeader = ["Lemma", 'Score', 'Frequency1', 'Frequency2', 'Rank1', 'Rank2', 'Association1', 'Association2']
        print(calculate_table(listHeader, listPrint))

else:
    print("): Wort nicht enthalten")
