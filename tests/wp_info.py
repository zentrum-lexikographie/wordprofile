#!/usr/bin/python
# Das Client-Programm fragt eine Wortprofil-MySQL-Datenbank über einen XMLRPC-Server ab und liefert Informationen
# über die verwendeten Korpora, Anzahl an Lemmaformen, Kookkurrenzen, Texttreffern und Sätzen.
# Des Weiteren liefert es Informationen über die Schwellwerte, die beider Wortprofilberechnung
# verwendet wurden.
import getpass
import xmlrpc.client
from argparse import ArgumentParser

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

args = parser.parse_args()

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

result = wp.get_info()

# Projektinformationen
print("\033[32;1mproject:\033[m")
print("author:", result['author'])
print("creation date:", result['creation_date'])
print("spec version:", result['spec_file_version'])
print("spec file:", result['spec_file'])

# verwendete Korpora
listKorpora = result['used_corpora']
print("\033[32;1mcorpora:\033[m")
print(",".join(listKorpora))

# Zahlen über Gößen
print("\033[32;1mglobal info:\033[m")
print("NoOfLemmas:", result['lemma_size'])
print("NoOfCooccurrences:", result['relation_size'])
print("NoOfSentences:", result['sentence_size'])
print("NoOfHits:", result['info_size'])

# relationsbezogene Kookkurrenzinformationen
print("\033[32;1mcooccurrence info:\033[m")
for i in list(result['cooccurrence_info'].items()):
    print(i[0] + ":", i[1])

# Schwellwerte
print("\033[32;1mglobal threshold info:\033[m")
print("LemmaCut:", result['lemma_cut'])
print("\033[32;1mrelation threshold info:\033[m")
for i in list(result['threshold'].items()):
    print(i[0] + ":", i[1])
