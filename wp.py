#!/usr/bin/python
# This is a simple word profile client that is developed for usage tests
# It can instantiate a word profile and ask for basic functionality such as
#  * relation information,
#  * hits/matches, and
#  * word profile comparison

import getpass
import logging
import xmlrpc.client
from argparse import ArgumentParser

from wordprofile.apps.xmlrpc import WordprofileXMLRPC
from wordprofile.cli.cmp import compare_lemmas
from wordprofile.cli.hit import get_hits
from wordprofile.cli.info import get_wordprofile_info
from wordprofile.cli.rel import get_relation

parser = ArgumentParser()

subparsers = parser.add_subparsers(dest="subcommand")
db_parser = parser.add_argument_group("server arguments")
db_parser.add_argument("--user", type=str, help="database username")
db_parser.add_argument("--database", type=str, help="database name")
db_parser.add_argument("--hostname", default="localhost", type=str, help="XML-RPC hostname")
db_parser.add_argument("--passwd", action="store_true", help="ask for database password")
db_parser.add_argument("--port", default=8086, type=int, help="XML-RPC port")
db_parser.add_argument('--spec', type=str, help="Angabe der Settings-Datei (*.xml)")
db_parser.add_argument('--xmlrpc', action="store_true", help="Angabe der Settings-Datei (*.xml)")

rel_parser = subparsers.add_parser("rel", help="collocation relations")
rel_parser.add_argument("-l", dest="lemma", default=None, help="das Eingabelemma")
rel_parser.add_argument("-p", dest="pos_tag", default="", help="Substantiv,Verb,Adjektiv,Adverb")
rel_parser.add_argument("-s", dest="start", default=0, help="Startpunkt der Relationstupel (default=0)")
rel_parser.add_argument("-n", dest="number", default=20, help="Anzahl der Relationstupel (default=20)")
rel_parser.add_argument("-f", dest="min_freq", default=0, help="Minimaler Frequenzwert (default=0)")
rel_parser.add_argument("-m", dest="min_stat", default=-9999, help="Minimaler Statistikwert (default=-9999)")
rel_parser.add_argument("-c", dest="corpus", default="", help="Angabe des korpusnamen (zeit,kern,21jhd,etc.)")
rel_parser.add_argument("-r", dest="relations", nargs="*",
                        help="Gewünschten Relationen in einer Liste (SUBJA,SUBJP,OBJA,OBJD,OBJI,GMOD,ATTR,KON,PP,etc.)")
rel_parser.add_argument("-o", dest="order", default="logDice",
                        help="Angabe der Ordnung (frequency,log_dice,mi_log_freq,mi3) (default=log_dice)")
rel_parser.add_argument("--cs", action="store_true", dest="case_sensitive", default=False,
                        help="Case-sensitive Abfrage")
rel_parser.add_argument("--sf", action="store_true", dest="surface", default=False,
                        help="Verwenden der Oberflächenform statt der Lemmaform")
rel_parser.add_argument("-v", action="store_true", dest="variations", default=False,
                        help="Einbeziehung von alternativen Schreibungen zu einem Eingabelemma")

hit_parser = subparsers.add_parser("hit")
hit_parser.add_argument("-i", type=int, dest="info", default=-1, help="die Texttreffer-ID")
hit_parser.add_argument("-s", type=int, dest="start", default=0, help="Trefferstart")
hit_parser.add_argument("-n", type=int, dest="number", default=20, help="Trefferanzahl (default=20)")
hit_parser.add_argument("-x", dest="host", default="http://localhost:9999",
                        help="host default=http://services.dwds.de:9999")
hit_parser.add_argument("-u", action="store_true", dest="internal_user", default=False,
                        help="interner Benutzer (mit Rechten)")
hit_parser.add_argument("--ct", action="store_true", dest="context", default=False,
                        help="anzeigen der Contexte (rechter, linker Satz)")
hit_parser.add_argument("--br", dest="width", default=140, help="Breite der Anzeige (default=140)")
hit_parser.add_argument("--sc", action="store_true", dest="score", default=False,
                        help="primär nach dem Sentence-Score sortieren")
hit_parser.add_argument("-a", action="store_false", dest="dateDesc", default=True, help="Datum aufsteigend")
hit_parser.add_argument("-c", dest="corpus", default="", help="einzelner Korpus, in dem gesucht werden soll")

status_parser = subparsers.add_parser("status")
info_parser = subparsers.add_parser("info")

cmp_parser = subparsers.add_parser("cmp")
cmp_parser.add_argument("--lemma1", type=str, required=True, help="das Eingabewort")
cmp_parser.add_argument("--lemma2", type=str, required=True, help="das Eingabewort")
cmp_parser.add_argument("--number", default=20, help="Anzahl der Relationstupel (default=20)")
cmp_parser.add_argument("--nbest", default=-1,
                        help="Die Anzahl der zu vergleichenden Relationstupel beider Wörter von vornherein einschränken")
cmp_parser.add_argument("--min_freq", type=int, default=0, help="Minimaler Frequenzwert")
cmp_parser.add_argument("--min_stat", type=float, default=0, help="Minimaler Statistikwert")
cmp_parser.add_argument("-c", "--corpus", default="", help="Angabe des korpus (zeit,kern,21jhd)")
cmp_parser.add_argument("-r", "--relations", nargs="*",
                        help="Angabe der gewünschten Relationen (SUBJA,SUBJP,OBJA,OBJD,OBJI,GMOD,ATTR,KON,PP)")
cmp_parser.add_argument("-o", "--order", default="logDice",
                        help="Angabe der Ordnung (frequency,log_dice,mi_log_freq,mi3) (default=log_dice)")
# parser.add_argument("--is",action="store_true", dest="intersection", default=False, help=u"Schnitt berechen")
cmp_parser.add_argument("--operation", default="adiff",
                        help="Operation (adiff,rmax), Default: adiff")  # diff,adiff,max,min,rmax,avg,havg,gavg
cmp_parser.add_argument("--case-sensitive", action="store_true", default=False, help="Case-sensitive Abfrage")
cmp_parser.add_argument("-sf", "--surface", action="store_true", default=False,
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

if args.xmlrpc:
    wp: WordprofileXMLRPC = xmlrpc.client.ServerProxy("http://{}:{}".format(args.hostname, args.port))
else:
    print('user: ' + args.user)
    print('db: ' + args.database)
    if args.passwd:
        db_password = getpass.getpass("db password: ")
    else:
        db_password = args.user
    wp = WordprofileXMLRPC(args.hostname, args.user, db_password, args.database, args.port, args.spec)

if args.subcommand == "status":
    response = wp.status()
    print("|: status: ", response)
elif args.subcommand == "info":
    get_wordprofile_info(wp)
elif args.subcommand == "rel":
    get_relation(wp, args)
elif args.subcommand == "hit":
    get_hits(wp, args)
elif args.subcommand == "cmp":
    compare_lemmas(wp, args)
