#!/usr/bin/python
# Das Client-Programm fragt eine Wortprofil-MySQL-Datenbank über einen XMLRPC-Server ab und liefert Texttreffer
# zu einer Texttreffer-Id.
# Beispielaufruf:
# python wp_hit.py -x http://localhost:8080 -i 76575 -n 20

import getpass
import logging
import xmlrpc.client
from argparse import ArgumentParser

from wordprofile.pprint.drawConcord import draw_concord
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
tool_parser.add_argument("-i", dest="info", default=-1, help="die Texttreffer-ID")
tool_parser.add_argument("-s", dest="start", default=0, help="Trefferstart")
tool_parser.add_argument("-n", dest="number", default=20, help="Trefferanzahl (default=20)")
tool_parser.add_argument("-x", dest="host", default="http://localhost:9999",
                         help="host default=http://services.dwds.de:9999")
tool_parser.add_argument("-u", action="store_true", dest="internal_user", default=False,
                         help="interner Benutzer (mit Rechten)")
tool_parser.add_argument("--ct", action="store_true", dest="context", default=False,
                         help="anzeigen der Contexte (rechter, linker Satz)")
tool_parser.add_argument("--br", dest="width", default=140, help="Breite der Anzeige (default=140)")
tool_parser.add_argument("--sc", action="store_true", dest="score", default=False,
                         help="primär nach dem Sentence-Score sortieren")
tool_parser.add_argument("-a", action="store_false", dest="dateDesc", default=True, help="Datum aufsteigend")
tool_parser.add_argument("-c", dest="corpus", default="", help="einzelner Korpus, in dem gesucht werden soll")

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

mapRelInfo = wp.get_concordances_and_relation({
    "InfoId": args.info,
    "Start": args.start,
    "Number": args.number,
    "Subcorpus": args.corpus,
    "DateDesc": args.dateDesc,
    "UseScore": args.score,
    "UseContext": args.context,
    "InternalUser": args.internal_user
})

concords = []
for ctr, i in enumerate(mapRelInfo['Tuples']):
    strBiblCorpus = i['Bibl']['Corpus']
    strBiblDate = i['Bibl']['Date']
    strBiblTextclass = i['Bibl']['TextClass']
    strBiblOrig = i['Bibl']['Orig']
    strBiblScan = i['Bibl']['Scan']
    strBiblAvail = str(i['Bibl']['Avail'])
    strBiblPage = i['Bibl']['Page']
    strScore = str(i['Score'])

    strSentence = i['ConcordLine']
    strLeft = ""
    strRight = ""
    if i['ConcordLeft'] != "":
        strLeft = '\033[0;34m' + i['ConcordLeft'] + '\033[0m '
    if i['ConcordRight'] != "":
        strRight = ' \033[0;34m' + i['ConcordRight'] + '\033[0m '

    strMeta = "%i) %s | %s | %s | %s | %s | %s | %s | %s" % (
        ctr + 1, strBiblCorpus, strBiblDate, strBiblTextclass, strBiblOrig, strBiblScan, strBiblAvail, strBiblPage,
        strScore)
    concords.append((strLeft + strSentence + strRight, strMeta))

print("\033[32;1m" + "Relation: " + "\033[m" + mapRelInfo['Relation'])
print("\033[32;1m" + "Lemma1: " + "\033[m" + mapRelInfo['Lemma1'])
print("\033[32;1m" + "Lemma2: " + "\033[m" + mapRelInfo['Lemma2'])
print("\033[32;1m" + "Description: " + "\033[m" + mapRelInfo['Description'])
draw_concord(concords, False, args.width)
