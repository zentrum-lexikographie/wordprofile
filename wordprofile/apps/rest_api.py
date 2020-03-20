#!/usr/bin/python
import getpass
import logging
import time
from argparse import ArgumentParser
from typing import List

import uvicorn
from fastapi import FastAPI

from wordprofile.wp import Wordprofile

parser = ArgumentParser()
parser.add_argument("--user", type=str, help="database username", required=True)
parser.add_argument("--database", type=str, help="database name", required=True)
parser.add_argument("--hostname", default="localhost", type=str, help="XML-RPC hostname")
parser.add_argument("--db-hostname", default="localhost", type=str, help="XML-RPC hostname")
parser.add_argument("--passwd", action="store_true", help="ask for database password")
parser.add_argument("--port", default=8086, type=int, help="XML-RPC port")
parser.add_argument('--spec', type=str, required=True, help="Angabe der Settings-Datei (*.xml)")
parser.add_argument('--log', dest='logfile', type=str,
                    default="./log/wp_" + time.strftime("%d_%m_%Y") + ".log",
                    help="Angabe der log-Datei (Default: log/wp_{date}.log)")
args = parser.parse_args()

logger = logging.getLogger('wordprofile')
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
fh = logging.FileHandler(args.logfile)
ch.setLevel(logging.DEBUG)
fh.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
fh.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)
logger.addHandler(fh)

logger = logging.getLogger('wordprofile')

logger.info('user: ' + args.user)
logger.info('db: ' + args.database)
if args.passwd:
    db_password = getpass.getpass("db password: ")
else:
    db_password = args.user

wp = Wordprofile(args.db_hostname, args.user, db_password, args.database, args.spec)
app = FastAPI()


@app.get("/")
@app.get("/status")
async def status():
    raise NotImplementedError()


@app.get("/lemma/{lemma}")
async def get_info():
    raise NotImplementedError()


@app.get("/rel/lemma/{lemma}")
async def get_lemma_and_pos(lemma: str, pos: str = "", use_external_variations: bool = True):
    """Return accessible information for lemma pos-tag pair.
    """
    return wp.get_lemma_and_pos(lemma, pos, use_external_variations)


@app.get("/cmp/lemma/{lemma}")
async def get_lemma_and_pos_diff(params):
    use_external_variations = bool(params.get('UseVariations', True))
    word_1 = params.get("Word1")
    word_2 = params.get("Word2")
    return wp.get_lemma_and_pos_diff(word_1, word_2, use_external_variations)


@app.get("/rel/")
async def get_relations(lemma: str, lemma2: str, pos: str, pos2: str = '', relations: List[str] = (),
                        start: int = 0, number: int = 20, order_by: str = 'log_dice', min_freq: int = 0,
                        min_stat: int = -1000):
    order_by = 'log_dice' if order_by.lower() == 'logdice' else 'frequency'
    return wp.get_relations(lemma, lemma2, pos, pos2, relations, start, number, order_by, min_freq, min_stat)


# @app.get("/lemma/{lemma}")
# async def get_cooccurrences(params):
#     hit_id = params["RelId"]
#     start = params.get("Start", 0)
#     number = params.get("Number", 20)
#     order_by = params.get("OrderBy", "logDice")
#     order_by = 'log_dice' if order_by.lower() == 'logdice' else 'frequency'
#     min_freq = params.get("MinFreq", -100000000)
#     min_stat = params.get("MinStat", -100000000)
#     return wp.get_cooccurrences(hit_id, start, number, order_by, min_freq, min_stat)


@app.get("/cmp/difference/")
async def get_diff(lemma1: str, lemma2: str, pos: str, cooccs: List[str], number: int = 20,
                   order_by: str = 'log_dice', min_freq: int = 0, min_stat: int = -1000, operation: str = 'adiff',
                   use_intersection: bool = False, nbest: int = 0):
    order_by = 'log_dice' if order_by.lower() == 'logdice' else 'frequency'
    return wp.get_diff(lemma1, lemma2, pos, cooccs, number, order_by, min_freq, min_stat, operation,
                       use_intersection, nbest)


@app.get("/cmp/similar/")
async def get_intersection(lemma1: str, lemma2: str, pos: str, cooccs: List[str], number: int = 20,
                           order_by: str = 'log_dice', min_freq: int = 0, min_stat: int = -1000, nbest: int = 0):
    return get_diff(lemma1, lemma2, pos, cooccs, number,
                    order_by, min_freq, min_stat, operation='rmax',
                    use_intersection=True, nbest=nbest)


@app.get("/lemma/id/{coocc_id}")
async def get_relation_by_info_id(coocc_id: int):
    return wp.get_relation_by_info_id(coocc_id)


@app.get("/hits/{coocc_id}")
async def get_concordances_and_relation(coocc_id: int, use_context: bool = False, start_index: int = 0,
                                        result_number: int = 20):
    relation = await get_relation_by_info_id(coocc_id)
    relation['Tuples'] = get_concordances(coocc_id, use_context, start_index, result_number)
    return relation


@app.get("/concords/{coocc_id}")
async def get_concordances(coocc_id: int, use_context: bool = False, start_index: int = 0, result_number: int = 20):
    return wp.get_concordances(coocc_id, use_context, start_index, result_number)


if __name__ == '__main__':
    uvicorn.run("rest_api:app", host=args.hostname, port=args.port, log_level="debug", reload=True)
