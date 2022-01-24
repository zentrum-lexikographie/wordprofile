#!/usr/bin/python3
# This is a simple word profile client that is developed for usage tests
# It can instantiate a word profile and ask for basic functionality such as
#  * relation information,
#  * hits/matches, and
#  * word profile comparison
import json
import logging
import os
import xmlrpc.client
from argparse import ArgumentParser

from .utils.cmp import compare_lemmas
from .utils.hit import get_hits
from .utils.info import get_wordprofile_info
from .utils.mwe_hit import get_mwe_hits
from .utils.mwe_rel import get_mwe_free
from .utils.rel import get_relation

from apps.xmlrpc_api import WordprofileXMLRPC

parser = ArgumentParser()

subparsers = parser.add_subparsers(dest="subcommand")
db_parser = parser.add_argument_group("server arguments")
db_parser.add_argument("--user", type=str, help="database username")
db_parser.add_argument("--database", type=str, help="database name")
db_parser.add_argument("--hostname", default="localhost", type=str, help="XML-RPC hostname")
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

mwe_rel_parser = subparsers.add_parser("mwe-rel", help="collocation relations")
mwe_rel_parser.add_argument("-l", dest="LemmaList", default="", type=str, help="die Eingabelemmata")
mwe_rel_parser.add_argument("-p", dest="pos_tag", default="", help="Substantiv,Verb,Adjektiv,Adverb")
mwe_rel_parser.add_argument("-s", dest="start", default=0, help="Startpunkt der Relationstupel (default=0)")
mwe_rel_parser.add_argument("-n", dest="number", default=20, help="Anzahl der Relationstupel (default=20)")
mwe_rel_parser.add_argument("-f", dest="min_freq", default=0, help="Minimaler Frequenzwert (default=0)")
mwe_rel_parser.add_argument("-m", dest="min_stat", default=-9999, help="Minimaler Statistikwert (default=-9999)")
mwe_rel_parser.add_argument("-r", dest="relations", nargs="*",
                            help="Gewünschten Relationen in einer Liste (SUBJA,SUBJP,OBJA,OBJD,OBJI,GMOD,ATTR,KON,PP,etc.)")
mwe_rel_parser.add_argument("-o", dest="order", default="logDice",
                            help="Angabe der Ordnung (frequency,log_dice,mi_log_freq,mi3) (default=log_dice)")

hit_parser = subparsers.add_parser("hit")
hit_parser.add_argument("-i", dest="info", default=-1, help="die Texttreffer-ID")
hit_parser.add_argument("-s", dest="start", default=0, help="Trefferstart")
hit_parser.add_argument("-n", dest="number", default=20, help="Trefferanzahl (default=20)")
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

hit_parser = subparsers.add_parser("mwe-hit")
hit_parser.add_argument("-i", dest="info", default=-1, help="die Texttreffer-ID")
hit_parser.add_argument("-s", dest="start", default=0, help="Trefferstart")
hit_parser.add_argument("-n", dest="number", default=20, help="Trefferanzahl (default=20)")
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
    wp_user = args.user or os.environ['WP_USER']
    wp_db = args.database or os.environ['WP_DB']
    db_password = os.environ.get('WP_PASSWORD', wp_user)
    logger.info('user: ' + wp_user)
    logger.info('db: ' + wp_db)
    wp = WordprofileXMLRPC(args.hostname, wp_user, db_password, wp_db, args.port, args.spec)

if args.subcommand == "status":
    response = wp.status()
    print("|: status: ", response)
elif args.subcommand == "info":
    info = wp.get_info()
    print(json.dumps(info, indent=4, sort_keys=True, default=str))
elif args.subcommand == "rel":
    get_relation(wp, args)
elif args.subcommand == "mwe-rel":
    get_mwe_free(wp, args)
elif args.subcommand == "hit":
    get_hits(wp, args)
elif args.subcommand == "mwe-hit":
    get_mwe_hits(wp, args)
elif args.subcommand == "cmp":
    compare_lemmas(wp, args)
