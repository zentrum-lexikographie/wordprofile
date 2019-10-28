#!/usr/bin/python
# Das Client-Programm fragt eine Wortprofil-MySQL-Datenbank über einen XMLRPC-Server ab und liefert Kookkurrenzen zu 
# einem Eingabelemma.
# Beispielaufruf:
# python wp_rel_client.py -x http://localhost:8080 -l Mann -o MiLogFreq -n 20

import getpass
import logging
import sys
from argparse import ArgumentParser

from wordprofile.pprint.drawTable import calculate_table
from wp_server import WortprofilQuery

parser = ArgumentParser()

db_parser = parser.add_argument_group("server arguments")
db_parser.add_argument("--user", type=str, help="database username", required=True)
db_parser.add_argument("--database", type=str, help="database name", required=True)
db_parser.add_argument("--hostname", default="localhost", type=str, help="XML-RPC hostname")
db_parser.add_argument("--passwd", action="store_true", help="ask for database password")
db_parser.add_argument("--port", default=8086, type=int, help="XML-RPC port")
db_parser.add_argument('--spec', type=str, required=True, help="Angabe der Settings-Datei (*.xml)")

tool_parser = parser.add_argument_group("tool arguments")
tool_parser.add_argument("-l", dest="lemma", default=None, help="das Eingabelemma")
tool_parser.add_argument("-p", dest="pos_tag", default="", help="Substantiv,Verb,Adjektiv,Adverb")
tool_parser.add_argument("-s", dest="start", default=0, help="Startpunkt der Relationstupel (default=0)")
tool_parser.add_argument("-n", dest="number", default=20, help="Anzahl der Relationstupel (default=20)")
tool_parser.add_argument("-f", dest="min_freq", default=0, help="Minimaler Frequenzwert (default=0)")
tool_parser.add_argument("-m", dest="min_stat", default=-9999, help="Minimaler Statistikwert (default=-9999)")
tool_parser.add_argument("-c", dest="corpus", default="", help="Angabe des korpusnamen (zeit,kern,21jhd,etc.)")
tool_parser.add_argument("-x", dest="host", default="", help="Hostrechner (z.B. http://localhost:8080)")
tool_parser.add_argument("-r", dest="relation", default="",
                         help="Gewünschten Relationen in einer Liste (SUBJA,SUBJP,OBJA,OBJD,OBJI,GMOD,ATTR,KON,PP,etc.)")
tool_parser.add_argument("-o", dest="order", default="log_dice",
                         help="Angabe der Ordnung (frequency,log_dice,mi_log_freq,mi3) (default=log_dice)")
tool_parser.add_argument("--cs", action="store_true", dest="case_sensitive", default=False,
                         help="Case-sensitive Abfrage")
tool_parser.add_argument("--sf", action="store_true", dest="surface", default=False,
                         help="Verwenden der Oberflächenform statt der Lemmaform")
tool_parser.add_argument("-v", action="store_true", dest="variations", default=False,
                         help="Einbeziehung von alternativen Schreibungen zu einem Eingabelemma")
tool_parser.add_argument("--out", dest="file", default="", help="Ausgabedatei")

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
wp = WortprofilQuery(args.hostname, args.user, db_password, args.database, args.port, args.spec)

### Abfrageoptionen für die Lemmainformationen erstellen
mapParam = {}
mapParam["Word"] = args.lemma
mapParam["Subcorpus"] = args.corpus
mapParam["CaseSensitive"] = args.case_sensitive
mapParam["UseVariations"] = args.variations

### Lemmainformationen vom Wortprofilserver abfragen
mapping = wp.get_lemma_and_pos(mapParam)
print("mapping", mapping)

### Wenn das Lemma enthalten ist
if len(mapping) > 0:

    mapSelect = {}
    if args.pos_tag == "":
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
            if i["POS"] == args.pos_tag:
                mapSelect = i

    if mapSelect == {}:
        print("): keine Kookkurrenzen für die Wortart vorhanden")
        sys.exit(-1)

    ### Ausgeben von Meta-Informationen
    print("\033[32;1m" + "Anzahl an Relationen mit Doppelten:" + "\033[m", mapSelect["Frequency"])
    print("\033[32;1m" + "mögliche Relationen :" + "\033[m", mapSelect["Relations"])

    ### abzufragende Relationen ermitteln
    listRel = []
    if args.relation != "":
        listRel = args.relation.split(',')
        if listRel != []:
            listRel = listRel
    if listRel == []:
        listRel = mapSelect['Relations']

    ### Abfrageoptionen für die Kookkurrenzinformationen erstellen
    mapParam = {}
    mapParam["Lemma"] = mapSelect["Lemma"]
    mapParam["Pos"] = mapSelect["POS"]
    mapParam["Start"] = args.start
    mapParam["Number"] = args.number
    mapParam["OrderBy"] = args.order
    mapParam["MinFreq"] = args.min_freq
    mapParam["MinStat"] = args.min_stat
    mapParam["Subcorpus"] = args.corpus
    mapParam["Relations"] = listRel

    ### Kookkurrenzinformationen vom Wortprofilserver abfragen
    RelList = wp.get_relations(mapParam)

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
                [str(iCounter), i['POS'], i["Lemma"], i['Score']['Frequency'], i['Score'][args.order],
                 i['ConcordId'], i['ConcordNo'], i['ConcordNoAccessible']])

            iCounter += 1

        ### Ausgeben der Kookkurrenzen als Tabelle
        listHeader = ['Rank', 'POS', "Lemma", 'Frequency', args.order, 'Hit/MWE-ID', 'No', '*No']
        print(calculate_table(listHeader, listPrint))
        iRelCount += 1
else:
    print("): Lemma nicht enthalten")
