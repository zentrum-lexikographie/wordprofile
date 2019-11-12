#!/usr/bin/python
# Das Client-Programm fragt eine Wortprofil-MySQL-Datenbank über einen XMLRPC-Server ab und liefert Kookkurrenzen zu 
# einem Eingabelemma.
# Beispielaufruf:
# python wp_rel.py -x http://localhost:8080 -l Mann -o MiLogFreq -n 20

import getpass
import logging
import sys
import xmlrpc.client
from argparse import ArgumentParser

from wordprofile.pprint.drawTable import calculate_table
from wp_server import WortprofilQuery

parser = ArgumentParser()

db_parser = parser.add_argument_group("server arguments")
db_parser.add_argument("--user", type=str, help="database username")
db_parser.add_argument("--database", type=str, help="database name")
db_parser.add_argument("--hostname", default="localhost", type=str, help="XML-RPC hostname")
db_parser.add_argument("--passwd", action="store_true", help="ask for database password")
db_parser.add_argument("--port", default=8086, type=int, help="XML-RPC port")
db_parser.add_argument('--spec', type=str, help="Angabe der Settings-Datei (*.xml)")
db_parser.add_argument('--xmlrpc', action="store_true", help="Angabe der Settings-Datei (*.xml)")

tool_parser = parser.add_argument_group("tool arguments")
tool_parser.add_argument("-l", dest="lemma", default=None, help="das Eingabelemma")
tool_parser.add_argument("-p", dest="pos_tag", default="", help="Substantiv,Verb,Adjektiv,Adverb")
tool_parser.add_argument("-s", dest="start", default=0, help="Startpunkt der Relationstupel (default=0)")
tool_parser.add_argument("-n", dest="number", default=20, help="Anzahl der Relationstupel (default=20)")
tool_parser.add_argument("-f", dest="min_freq", default=0, help="Minimaler Frequenzwert (default=0)")
tool_parser.add_argument("-m", dest="min_stat", default=-9999, help="Minimaler Statistikwert (default=-9999)")
tool_parser.add_argument("-c", dest="corpus", default="", help="Angabe des korpusnamen (zeit,kern,21jhd,etc.)")
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

if args.xmlrpc:
    wp = xmlrpc.client.ServerProxy("http://{}:{}".format(args.hostname, args.port))
else:
    print('user: ' + args.user)
    print('db: ' + args.database)
    if args.passwd:
        db_password = getpass.getpass("db password: ")
    else:
        db_password = args.user
    wp = WortprofilQuery(args.hostname, args.user, db_password, args.database, args.port, args.spec)

mapping = wp.get_lemma_and_pos({
    "Word": args.lemma,
    "Subcorpus": args.corpus,
    "CaseSensitive": args.case_sensitive,
    "UseVariations": args.variations
})
print("mapping", mapping)
if len(mapping) > 0:
    mapSelect = {}
    if args.pos_tag == "":
        # Ermitteln der Wortart (evtl. über Tastatureingabe)
        if len(mapping) == 1:
            mapSelect = mapping[0]
            print("\033[32;1m" + "(1) " + "\033[m" + mapSelect["Lemma"] + " [" + mapSelect["POS"] + "]")
        else:
            print("\033[32;1m" + "Grundform Wählen:" + "\033[m")
            data = "999"
            while True:
                iCounter = 1
                for coocc in mapping:
                    print("\033[32;1m" + "(" + str(iCounter) + ") " + "\033[m" + coocc["Lemma"] + " [" + coocc[
                        "POS"] + "]")
                    iCounter = iCounter + 1
                data = sys.stdin.readline()

                if int(data) > len(mapping) or int(data) < 0:
                    continue

                mapSelect = mapping[int(data) - 1]
                break
    else:
        for coocc in mapping:
            if coocc["POS"] == args.pos_tag:
                mapSelect = coocc

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

    relations = wp.get_relations({
        "Lemma": mapSelect["Lemma"],
        "Pos": mapSelect["POS"],
        "Start": args.start,
        "Number": args.number,
        "OrderBy": args.order,
        "MinFreq": args.min_freq,
        "MinStat": args.min_stat,
        "Subcorpus": args.corpus,
        "Relations": listRel
    })

    for rel_ctr, relation in enumerate(relations):
        print()
        if 'RelId' in relation:
            print("\033[32;1m " + str(rel_ctr + 1) + ". " + relation['Relation'] + " (" + relation[
                'RelId'] + "): " + "\033[m" + relation[
                      'Description'])
        else:
            print("\033[32;1m " + str(rel_ctr + 1) + ". " + relation['Relation'] + ": " + "\033[m" + relation[
                'Description'])

        table_items = []

        ### Aufsammeln der Kookkurrrenzen
        for coocc_ctr, coocc in enumerate(relation['Tuples']):
            table_items.append([
                str(coocc_ctr + 1), coocc['POS'], coocc["Lemma"], coocc['Score']['Frequency'],
                coocc['Score'][args.order], coocc['ConcordId']
            ])
        listHeader = ['Rank', 'POS', "Lemma", 'Frequency', args.order, 'Hit/MWE-ID']
        print(calculate_table(listHeader, table_items))
else:
    print("): Lemma nicht enthalten")
