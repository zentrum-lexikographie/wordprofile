#!/usr/bin/python
# Das Client-Programm fragt eine Wortprofil-MySQL-Datenbank über einen XMLRPC-Server ab und liefert Texttreffer
# zu einer Texttreffer-Id.
# Beispielaufruf:
# python wp_con_client.py -x http://localhost:8080 -i 1671#2#428#4#11112#15#207136 -n 20

import getpass
import logging
from argparse import ArgumentParser

from wordprofile.pprint.drawConcord import draw_concord
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

### Parametermap erstellen
mapParam = {}
mapParam["InfoId"] = args.info
mapParam["Start"] = args.start
mapParam["Number"] = args.number
mapParam["Subcorpus"] = args.corpus
mapParam["DateDesc"] = args.dateDesc
mapParam["UseScore"] = args.score
mapParam["UseContext"] = args.context
mapParam["InternalUser"] = args.internal_user
iConcordId = mapParam["InfoId"]

### Abfrage der Texttreffer zusammen mit groben Relationsinformationen
mapRelInfo = wp.get_concordances_and_relation(mapParam)

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

    ### wenn die Informationen direkt ausgegeben werden sollen
    strMeta = "%i) %s | %s | %s | %s | %s | %s | %s | %s" % (
        iCounter, strBiblCorpus, strBiblDate, strBiblTextclass, strBiblOrig, strBiblScan, strBiblAvail, strBiblPage,
        strScore)
    listConcord.append((strLeft + strSentence + strRight, strMeta))
    iCounter = iCounter + 1

### Ausgeben der groben Relationsinformationen
print("\033[32;1m" + "Relation: " + "\033[m" + mapRelInfo['Relation'])
print("\033[32;1m" + "Lemma1: " + "\033[m" + mapRelInfo['Lemma1'])
print("\033[32;1m" + "Lemma2: " + "\033[m" + mapRelInfo['Lemma2'])
print("\033[32;1m" + "Description: " + "\033[m" + mapRelInfo['Description'])

### Ausgeben der Texttreffertabelle
draw_concord(listConcord, False, args.width)
