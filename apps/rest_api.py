#!/usr/bin/python3

import logging
import os
from argparse import ArgumentParser
from typing import List

import time
import uvicorn
from fastapi import FastAPI, Query

from wordprofile.wp import Wordprofile

parser = ArgumentParser()
parser.add_argument("--user", type=str, help="database username", required=True)
parser.add_argument("--database", type=str, help="database name", required=True)
parser.add_argument("--hostname", default="localhost", type=str, help="REST API hostname")
parser.add_argument("--db-hostname", default="localhost", type=str, help="Hostname of the wp database.")
parser.add_argument("--port", default=8086, type=int, help="REST API port")
parser.add_argument('--spec', type=str, required=True, help="Settings file (*.xml)")
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

wp_user = args.user or os.environ['WP_USER']
wp_db = args.database or os.environ['WP_DB']
db_password = os.environ.get('WP_PASSWORD', wp_user)
logger.info('user: ' + wp_user)
logger.info('db: ' + wp_db)

wp = Wordprofile(args.db_hostname, wp_user, db_password, wp_db, args.spec)
app = FastAPI()


@app.get("/")
@app.get("/status")
async def status():
    """Let icinga know the word profile is online.
    """
    return "OK"


@app.get("/meta")
async def meta():
    """Ask wordprofile for meta information such as table statistics.
    """
    return wp.get_info_stats()


@app.get("/info/lemma/")
async def get_lemma(lemma: str, pos: str = "", use_external_variations: bool = True):
    """Gets lemma information from word-profile.

    Args:
        lemma: Lemma of interest.
        pos: Pos tag of first lemma.
        use_external_variations: Whether to use variations for either lemmas if not found in database.

    Returns:
        List of lemma-pos combinations with stats and possible relations.
    """
    return wp.get_lemma_and_pos(lemma, pos, use_external_variations)


@app.get("/info/lemmas/")
async def get_lemma_and_pos_diff(lemma1: str, lemma2: str, use_variations: bool = True):
    """Get lemma pairs with common pos tags from word-profile.

    Args:
        lemma1: Lemma of interest.
        lemma2: Lemma for comparison.
        use_variations: Whether to use variations for either lemmas if not found in database.

    Returns:
        List of lemma1–lemma2 combinations with additional information such as frequency and relation.
    """

    return wp.get_lemma_and_pos_diff(lemma1, lemma2, use_variations)


@app.get("/rel/")
async def get_relations(lemma1: str, pos1: str, lemma2: str = '', pos2: str = '',
                        relations: List[str] = Query(["META"]),
                        start: int = 0, number: int = 20, order_by: str = 'log_dice', min_freq: int = 0,
                        min_stat: int = -1000):
    """Get collocations from word-profile.

    Args:
        lemma1: Lemma of interest, first collocate.
        pos1: Pos tag of first lemma.
        lemma2 (optional): Second collocate.
        pos2 (optional): Pos tag of second lemma.
        relations (optional): List of relation labels.
        start (optional): Number of collocations to skip.
        number (optional): Number of collocations to take.
        order_by (optional): Metric for ordering, frequency or log_dice.
        min_freq (optional): Filter collocations with minimal frequency.
        min_stat (optional): Filter collocations with minimal stats score.

    Return:
        List of selected collocations grouped by relation.
    """
    order_by = 'log_dice' if order_by.lower() == 'logdice' else 'frequency'
    return wp.get_relations(lemma1, pos1, lemma2, pos2, relations, start, number, order_by, min_freq, min_stat)


@app.get("/lemma/id/{coocc_id}")
async def get_relation_by_info_id(coocc_id: int):
    """Get collocation information for a specific collocation id.

    Args:
        coocc_id: collocation id.

    Returns:
        Dictionary with collocation information.
    """
    return wp.get_relation_by_info_id(coocc_id)


@app.get("/hits/{coocc_id}")
async def get_concordances_and_relation(coocc_id: int, use_context: bool = False, start_index: int = 0,
                                        result_number: int = 20):
    """Get collocation information and concordances for a specified collocation id.

    Args:
        coocc_id: Collocation id.
        use_context (optional): If true, returns surrounding sentences for matched collocation.
        start_index (optional): Collocation id.
        result_number (optional): Collocation id.

    Returns:
        Dictionary with collocation information and their concordances.
    """
    return wp.get_concordances_and_relation(coocc_id, use_context, start_index, result_number)


@app.get("/cmp/difference/")
async def get_diff(lemma1: str, lemma2: str, pos: str, relations: List[str] = Query(["META"]), number: int = 20,
                   order_by: str = 'log_dice', min_freq: int = 0, min_stat: int = -1000, operation: str = 'adiff',
                   use_intersection: bool = False, nbest: int = 0):
    """Get collocations of common POS from word-profile database and computes distances for comparison.

    Args:
        lemma1: Lemma of interest, first collocate.
        lemma2: Second collocate.
        pos: Pos tag for both lemmas.
        relations (optional): List of relation labels.
        number (optional): Number of collocations to take.
        order_by (optional): Metric for ordering, frequency or log_dice.
        min_freq (optional): Filter collocations with minimal frequency.
        min_stat (optional): Filter collocations with minimal stats score.
        operation (optional): Lemma distance metric.
        use_intersection (optional): If set, only the intersection of both lemma is computed.
        nbest (optional): Checks only the n highest scored lemmas.
    Return:
        List of collocation-diffs grouped by relation.
    """
    order_by = 'log_dice' if order_by.lower() == 'logdice' else 'frequency'
    return wp.get_diff(lemma1, lemma2, pos, relations, number, order_by, min_freq, min_stat, operation,
                       use_intersection, nbest)


@app.get("/cmp/intersection/")
async def get_intersection(lemma1: str, lemma2: str, pos: str, relations: List[str] = Query(["META"]), number: int = 20,
                           order_by: str = 'log_dice', min_freq: int = 0, min_stat: int = -1000, nbest: int = 0):
    """Redirection for get_diff that sets parameters for intersection computation.

    Args:
        lemma1: Lemma of interest, first collocate.
        lemma2: Second collocate.
        pos: Pos tag for both lemmas.
        relations (optional): List of relation labels.
        number (optional): Number of collocations to take.
        order_by (optional): Metric for ordering, frequency or log_dice.
        min_freq (optional): Filter collocations with minimal frequency.
        min_stat (optional): Filter collocations with minimal stats score.
        nbest (optional): Checks only the n highest scored lemmas.
    Return:
        List of collocation-diffs grouped by relation.
    """
    order_by = 'log_dice' if order_by.lower() == 'logdice' else 'frequency'
    return wp.get_diff(lemma1, lemma2, pos, relations, number, order_by, min_freq, min_stat, operation='rmax',
                       use_intersection=True, nbest=nbest)


if __name__ == '__main__':
    uvicorn.run("rest_api:app", host=args.hostname, port=args.port, log_level="debug", reload=True)
