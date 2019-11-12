#!/usr/bin/python
# Das Client-Programm fragt einen Wortprofil-XMLRPC-Server ab und prüft, ob mit diesem alles in Ordnung ist.
# Wenn der Server abfragbar ist und alles in Ordnung ist, wird "OK" zurückgegeben, ansonsten eine Fehlermeldung.
#
# python wp_status.py -x http://localhost:8080
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

response = wp.status()
print("|: status: ", response)
