import http
import logging
import time
from argparse import ArgumentParser
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

import wordprofile.config as config
from wordprofile.utils import configure_logger
from wordprofile.wp import Wordprofile

parser = ArgumentParser()
parser.add_argument("--spec", type=str, help="Settings file", default=config.SPEC)
parser.add_argument(
    "--db-hostname", type=str, help="database host", default=config.DB_HOST
)
parser.add_argument("--db-name", type=str, help="database name", default=config.DB_NAME)
parser.add_argument(
    "--db-user", type=str, help="database username", default=config.DB_USER
)
parser.add_argument(
    "--db-password", type=str, help="database password", default=str(config.DB_PASSWORD)
)
parser.add_argument(
    "--http-hostname", type=str, help="REST API hostname", default=config.HTTP_HOSTNAME
)
parser.add_argument(
    "--http-port", type=int, help="REST API port", default=config.HTTP_PORT
)
parser.add_argument(
    "--workers", type=int, help="Number of Uvicorn workers", default=config.HTTP_WORKERS
)
parser.add_argument("--debug", action="store_true", help="Activate debug mode.")

args = parser.parse_args()

uvicorn_access = logging.getLogger("uvicorn.access")
uvicorn_access.disabled = True
logger = configure_logger(logging.getLogger("wordprofile"), logging.INFO)

wp = Wordprofile(
    args.db_hostname, args.db_user, args.db_password, args.db_name, args.spec
)
app = FastAPI(
    title="Wordprofile API",
    description="Wordprofile API allows retrieval of collocations and their concordances from Wortprofil database.",
)
app.mount("/static", StaticFiles(directory="wordprofile/apps/static"), name="static")
templates = Jinja2Templates(directory="wordprofile/apps/static")


@app.get("/", tags=["view"])
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/status", tags=["info"])
async def status():
    """Let icinga know the word profile is online."""
    return "OK"


@app.get("/api/v1/meta", tags=["info"])
async def meta():
    """
    Return meta information about wordprofile data(base).

    Information contains:
    - database table names, creation and update dates
    - frequencies for POS tags and relation labels
    - document count and time span of subcorpora
    """
    return wp.get_info_stats()


@app.get("/api/v1/tags", tags=["wp"])
async def get_lemma(lemma: str, pos: str = ""):
    """Gets lemma information from wordprofile.

    Args:
    - lemma: Lemma of interest.
    - pos (optional): POS tag of lemma. Default is empty string.

    Returns:
    - List of lemma-POS combinations with stats and possible relations.
    """
    return wp.get_lemma_and_pos(lemma, pos)


@app.get("/api/v1/cmp/tags", tags=["cmp"])
async def get_lemma_and_pos_diff(lemma1: str, lemma2: str):
    """Get lemma pairs with common POS tags from wordprofile.

    Args:
    - lemma1: Lemma of interest.
    - lemma2: Lemma for comparison.

    Returns:
    - List of lemma1–lemma2 combinations with additional information such as frequency and relation.
    """

    return wp.get_lemma_and_pos_diff(lemma1, lemma2)


@app.get("/api/v1/profile", tags=["wp"])
async def get_relations(
    lemma1: str,
    pos1: str,
    relations: List[str] = Query([]),
    start: int = 0,
    number: int = 20,
    order_by: str = "logDice",
    min_freq: int = 0,
    min_stat: float = -1000.0,
):
    """Get collocations from wordprofile.

    Args:
    - lemma1: Lemma of interest.
    - pos1: POS tag of lemma.
    - relations (optional): List of relation labels. If no relation labels are
        specified, all available relations for the lemma are evaluated.
    - start (optional): Number of collocations to skip. Default is 0.
    - number (optional): Number of collocations to take. Default is 20.
    - order_by (optional): Metric for ordering, frequency or logDice.
        Default is logDice.
    - min_freq (optional): Filter collocations with minimal frequency.
        Default is 0.
    - min_stat (optional): Filter collocations with minimal stats score.
        Default is -1000.0.

    Return:
    - List of selected collocations grouped by relation.
    """
    order_by = "log_dice" if order_by.lower() == "logdice" else "frequency"
    if len(relations) == 0:
        result = wp.get_lemma_and_pos(lemma1, pos1)
        if len(result) == 0:
            return []
        relations = result[0]["Relations"]
    return wp.get_relations(
        lemma1,
        pos1,
        relations,
        start,
        number,
        order_by,
        min_freq,
        min_stat,
    )


@app.get("/api/v1/hits", tags=["wp"])
async def get_concordances_and_relation(
    coocc_id: int,
    start_index: int = 0,
    result_number: int = 20,
):
    """Get collocation information and concordances for a specified collocation id.

    Args:
    - coocc_id: Collocation id.
    - start_index (optional): Number of concordances to skip. Default is 0.
    - result_number (optional): Number of concordances to return. Default is 20.

    Returns:
    - Dictionary with collocation information and their concordances.
    """
    return wp.get_concordances_and_relation(coocc_id, start_index, result_number)


@app.get("/api/v1/cmp/diff", tags=["cmp"])
async def get_diff(
    lemma1: str,
    lemma2: str,
    pos: str,
    relations: List[str] = Query([]),
    number: int = 20,
    order_by: str = "logDice",
    min_freq: int = 0,
    min_stat: float = -1000.0,
):
    """
    Get collocations for two lemmas with common POS from wordprofile
    database and compute distances for comparison. Distance is calculated
    as difference of logDice scores.

    Args:
    - lemma1: Lemma of interest.
    - lemma2: Comparison lemma.
    - pos: POS tag for both lemmas.
    - relations (optional): List of relation labels. If no relation labels
        are specified, all available relations for the lemma are evaluated.
    - number (optional): Number of collocations to return per relation.
        Default is 20.
    - order_by (optional): Metric for ordering, frequency or logDice.
        Default is logDice.
    - min_freq (optional): Filter collocations with minimal frequency.
        Default is 0.
    - min_stat (optional): Filter collocations with minimal stats score.
        Default is -1000.0.

    Return:
    - List of collocation-diffs grouped by relation.
    """
    order_by = "log_dice" if order_by.lower() == "logdice" else "frequency"
    if len(relations) == 0:
        result = wp.get_lemma_and_pos_diff(lemma1, lemma2)
        if len(result) == 0:
            return []
        relations = result[0]["Relations"]
    return wp.get_diff(
        lemma1,
        lemma2,
        pos,
        relations,
        number,
        order_by,
        min_freq,
        min_stat,
        operation="adiff",
        use_intersection=False,
    )


@app.get("/api/v1/cmp/intersection", tags=["cmp"])
async def get_intersection(
    lemma1: str,
    lemma2: str,
    pos: str,
    relations: List[str] = Query([]),
    number: int = 20,
    order_by: str = "logDice",
    min_freq: int = 0,
    min_stat: float = -1000.0,
):
    """
    Return intersection of collocations for two lemmas with common POS tag.
    Collocations are ranked by harmonic mean of logDice scores.

    Args:
    - lemma1: Lemma of interest.
    - lemma2: Comparison lemma.
    - pos: POS tag for both lemmas.
    - relations (optional): List of relation labels. If no relation labels
        are specified, all available relations for the lemma pair are
        evaluated.
    - number (optional): Number of collocations per relation to return.
        Default is 20.
    - order_by (optional): Metric used for comparison, frequency or logDice.
        Default is logDice.
    - min_freq (optional): Filter collocations with minimal frequency.
        Default is 0.
    - min_stat (optional): Filter collocations with minimal stats score.
        Default is -1000.0.

    Return:
    - List of collocation-diffs grouped by relation.
    """
    order_by = "log_dice" if order_by.lower() == "logdice" else "frequency"
    if len(relations) == 0:
        result = wp.get_lemma_and_pos_diff(lemma1, lemma2)
        if len(result) == 0:
            return []
        relations = result[0]["Relations"]
    return wp.get_diff(
        lemma1,
        lemma2,
        pos,
        relations,
        number,
        order_by,
        min_freq,
        min_stat,
        operation="hmean",
        use_intersection=True,
    )


@app.get("/api/v1/mwe/profile", tags=["mwe"])
def get_mwe_relations(
    coocc_id: Optional[int] = None,
    lemma1: str = "",
    lemma2: str = "",
    relations: List[str] = Query([]),
    number: int = 20,
    order_by: str = "logDice",
    min_freq: int = 0,
    min_stat: float = -1000.0,
):
    """Get collocations for MWE.

    For retrieval, either the collocation id can be used or two lemmata
    can be passed as strings.
    The coocc_id parameter has priority over the string search, so if both
    coocc_id and lemma1/lemma2 are passed, only coocc_id will be used for the
    query.

    Args:
    - coocc_id (optional): MWE's collocation id.
    - lemma1 (optional): First lemma of MWE.
    - lemma2 (optional): Second lemma of MWE.
    - relations (optional): List of relation labels. If no relation labels
        are specified, all available relations for the mwe are evaluated.
    - number (optional): Number of collocations to return per relation.
        Default is 20.
    - order_by (optional): Metric for ordering, frequency or logDice.
        Default is logDice.
    - min_freq (optional): Filter collocations with minimal frequency.
        Default is 0.
    - min_stat (optional): Filter collocations with minimal stats score.
        Default is -1000.0.

    Returns:
    - Dictionary with mwe relations for specific collocation id or pair
        of lemmata.
    """
    order_by = "log_dice" if order_by.lower() == "logdice" else "frequency"
    if coocc_id is None:
        coocc_ids = wp.get_collocation_ids(lemma1, lemma2)
    else:
        coocc_ids = [coocc_id]
    return wp.get_mwe_relations(
        coocc_ids, relations, number, order_by, min_freq, min_stat
    )


@app.get("/api/v1/mwe/hits", tags=["mwe"])
def get_mwe_concordances_and_relation(
    coocc_id: int,
    start_index: int = 0,
    result_number: int = 20,
):
    """
    Get MWE collocation information and concordances for a specified
    collocation id.

    Args:
    - coocc_id: Collocation id of MWE.
    - start_index (optional): Number of concordances to skip. Default is 0.
    - result_number (optional): Number of concordances to return.
        Default is 20.

    Returns:
    - Dictionary with collocation information and their concordances.
    """
    return wp.get_concordances_and_relation(
        coocc_id, start_index, result_number, is_mwe=True
    )


# Adapted from https://medium.com/@roy-pstr/fastapi-server-errors-and-logs-take-back-control-696405437983
@app.middleware("http")
async def log_process_time(request: Request, call_next):
    url = (
        f"{request.url.path}?{request.query_params}"
        if request.query_params
        else request.url.path
    )
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = "{0:.2f}".format(process_time)
    host = getattr(getattr(request, "client", None), "host", None)
    port = getattr(getattr(request, "client", None), "port", None)
    try:
        status_phrase = http.HTTPStatus(response.status_code).phrase
    except ValueError:
        status_phrase = ""
    logger.info(
        f'{host}:{port} - "{request.method} {url}" {response.status_code} {status_phrase} {formatted_process_time}ms'
    )
    return response


def main():
    uvicorn.run(
        "wordprofile.apps.rest_api:app",
        host=args.http_hostname,
        port=args.http_port,
        workers=args.workers,
        log_level="debug",
        reload=args.debug,
    )


if __name__ == "__main__":
    main()
