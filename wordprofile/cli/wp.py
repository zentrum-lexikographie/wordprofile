# This is a simple word profile client that is developed for usage tests
# It can instantiate a word profile and ask for basic functionality such as
#  * relation information,
#  * hits/matches, and
#  * word profile comparison
import json
import logging
import xmlrpc.client
from argparse import ArgumentParser


from wordprofile.apps.xmlrpc_api import WordprofileXMLRPC
from wordprofile.cli.utils.cmp import compare_lemmas
from wordprofile.cli.utils.hit import get_hits
from wordprofile.cli.utils.mwe_rel import get_mwe_free
from wordprofile.cli.utils.rel import get_relation
from wordprofile.utils import configure_logger

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
rel_parser.add_argument("-s", dest="start", type=int, default=0, help="Startpunkt der Relationstupel (default=0)")
rel_parser.add_argument("-n", dest="number", type=int, default=20, help="Anzahl der Relationstupel (default=20)")
rel_parser.add_argument("-f", dest="min_freq", type=int, default=0, help="Minimaler Frequenzwert (default=0)")
rel_parser.add_argument("-m", dest="min_stat", type=int, default=-9999, help="Minimaler Statistikwert (default=-9999)")
rel_parser.add_argument("-r", dest="relations", nargs="*",
                        help="Gewünschten Relationen in einer Liste (SUBJA,SUBJP,OBJA,OBJD,OBJI,GMOD,ATTR,KON,PP,etc.)")
rel_parser.add_argument("-o", dest="order", default="logDice",
                        help="Angabe der Ordnung (frequency,log_dice,mi_log_freq,mi3) (default=log_dice)")
rel_parser.add_argument("-v", action="store_true", dest="variations", default=False,
                        help="Einbeziehung von alternativen Schreibungen zu einem Eingabelemma")

mwe_rel_parser = subparsers.add_parser("mwe-rel", help="collocation relations")
mwe_rel_parser.add_argument("-l", dest="LemmaList", default="", type=str, help="die Eingabelemmata")
mwe_rel_parser.add_argument("-p", dest="pos_tag", default="", help="Substantiv,Verb,Adjektiv,Adverb")
mwe_rel_parser.add_argument("-s", dest="start", type=int, default=0, help="Startpunkt der Relationstupel (default=0)")
mwe_rel_parser.add_argument("-n", dest="number", type=int, default=20, help="Anzahl der Relationstupel (default=20)")
mwe_rel_parser.add_argument("-f", dest="min_freq", type=int, default=0, help="Minimaler Frequenzwert (default=0)")
mwe_rel_parser.add_argument("-m", dest="min_stat", type=int, default=-9999, help="Minimaler Statistikwert (default=-9999)")
mwe_rel_parser.add_argument("-r", dest="relations", nargs="*",
                            help="Gewünschten Relationen in einer Liste (SUBJA,SUBJP,OBJA,OBJD,OBJI,GMOD,ATTR,KON,PP,etc.)")
mwe_rel_parser.add_argument("-o", dest="order", default="logDice",
                            help="Angabe der Ordnung (frequency,log_dice,mi_log_freq,mi3) (default=log_dice)")

hit_parser = subparsers.add_parser("hit")
hit_parser.add_argument("-i", dest="info", default='', help="die Texttreffer-ID")
hit_parser.add_argument("-s", dest="start", type=int, default=0, help="Trefferstart")
hit_parser.add_argument("-n", dest="number", type=int, default=20, help="Trefferanzahl (default=20)")
hit_parser.add_argument("--ct", action="store_true", dest="context", default=False,
                        help="anzeigen der Contexte (rechter, linker Satz)")

status_parser = subparsers.add_parser("status")
info_parser = subparsers.add_parser("info")

cmp_parser = subparsers.add_parser("cmp")
cmp_parser.add_argument("--lemma1", type=str, required=True, help="das Eingabewort")
cmp_parser.add_argument("--lemma2", type=str, required=True, help="das Eingabewort")
cmp_parser.add_argument("--number", type=int, default=20, help="Anzahl der Relationstupel (default=20)")
cmp_parser.add_argument("--nbest", type=int, default=-1,
                        help="Die Anzahl der zu vergleichenden Relationstupel beider Wörter von vornherein einschränken")
cmp_parser.add_argument("--min_freq", type=int, default=0, help="Minimaler Frequenzwert")
cmp_parser.add_argument("--min_stat", type=float, default=0, help="Minimaler Statistikwert")
cmp_parser.add_argument("-r", "--relations", nargs="*",
                        help="Angabe der gewünschten Relationen (SUBJA,SUBJP,OBJA,OBJD,OBJI,GMOD,ATTR,KON,PP)")
cmp_parser.add_argument("-o", "--order", default="logDice",
                        help="Angabe der Ordnung (frequency,log_dice,mi_log_freq,mi3) (default=log_dice)")
# parser.add_argument("--is",action="store_true", dest="intersection", default=False, help=u"Schnitt berechen")
cmp_parser.add_argument("--operation", default="adiff",
                        help="Operation (adiff,rmax), Default: adiff")  # diff,adiff,max,min,rmax,avg,havg,gavg

args = parser.parse_args()

logger = configure_logger(logging.getLogger('wordprofile'))

if args.xmlrpc:
    wp: WordprofileXMLRPC = xmlrpc.client.ServerProxy("http://{}:{}".format(args.hostname, args.port))
else:
    wp = WordprofileXMLRPC(args.hostname, args.user, "", args.database, args.port, args.spec)

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
elif args.subcommand == "cmp":
    compare_lemmas(wp, args)
