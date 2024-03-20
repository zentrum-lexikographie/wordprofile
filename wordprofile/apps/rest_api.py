import http
import logging
import time
from argparse import ArgumentParser
from typing import List

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
app = FastAPI()
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
    """Ask wordprofile for meta information such as table statistics."""
    return wp.get_info_stats()


@app.get("/api/v1/tags", tags=["wp"])
async def get_lemma(lemma: str, pos: str = "", use_external_variations: bool = True):
    """Gets lemma information from word-profile.

    Args:
        lemma: Lemma of interest.
        pos: Pos tag of first lemma.
        use_external_variations (deprecated): Whether to use variations for either lemmas if not found in database.

    Returns:
        List of lemma-pos combinations with stats and possible relations.
    """
    return wp.get_lemma_and_pos(lemma, pos)


@app.get("/api/v1/cmp/tags", tags=["cmp"])
async def get_lemma_and_pos_diff(lemma1: str, lemma2: str, use_variations: bool = True):
    """Get lemma pairs with common pos tags from word-profile.

    Args:
        lemma1: Lemma of interest.
        lemma2: Lemma for comparison.
        use_variations (deprecated): Whether to use variations for either lemmas if not found in database.

    Returns:
        List of lemma1–lemma2 combinations with additional information such as frequency and relation.
    """

    return wp.get_lemma_and_pos_diff(lemma1, lemma2)


@app.get("/api/v1/list/tags", tags=["list"])
def get_lemma_and_pos_by_list(parts: List[str]):
    """For compatibility to old WP. Just pipes input to output."""
    return parts


@app.get("/api/v1/list/mwe", tags=["list"])
def get_mwe_relations_by_list(
    parts: List[str],
    relations: List[str] = Query([]),
    start: int = 0,
    number: int = 20,
    order_by: str = "logDice",
    min_freq: int = 0,
    min_stat: float = -1000.0,
):
    """Fetches mwe entries for a given list of lemmas.

    Args:
        parts (optional): List of lemmas.
        relations (optional): List of relation labels.
        start (optional): Number of collocations to skip.
        number (optional): Number of collocations to take.
        order_by (optional): Metric for ordering, frequency or log_dice.
        min_freq (optional): Filter collocations with minimal frequency.
        min_stat (optional): Filter collocations with minimal stats score.

    Return:
        Dictionary of mwe relations for specific collocation parts.
            <parts>: List of Lemma-POS pairs
            <data>: Relations specifically for parts of the input.
    """
    order_by = "log_dice" if order_by.lower() == "logdice" else "frequency"
    coocc_ids = wp.get_collocation_ids(parts[0], parts[1])
    return wp.get_mwe_relations(
        coocc_ids, relations, start, number, order_by, min_freq, min_stat
    )


@app.get("/api/v1/profile", tags=["wp"])
async def get_relations(
    lemma1: str,
    pos1: str,
    lemma2: str = "",
    pos2: str = "",
    relations: List[str] = Query([]),
    start: int = 0,
    number: int = 20,
    order_by: str = "logDice",
    min_freq: int = 0,
    min_stat: float = -1000.0,
):
    """Get collocations from word-profile.

    Args:
        lemma1: Lemma of interest, first collocate.
        pos1: Pos tag of first lemma.
        lemma2 (deprecated): Second collocate.
        pos2 (deprecated): Pos tag of second lemma.
        relations (optional): List of relation labels.
        start (optional): Number of collocations to skip.
        number (optional): Number of collocations to take.
        order_by (optional): Metric for ordering, frequency or log-dice.
        min_freq (optional): Filter collocations with minimal frequency.
        min_stat (optional): Filter collocations with minimal stats score.

    Return:
        List of selected collocations grouped by relation.
    """
    order_by = "log_dice" if order_by.lower() == "logdice" else "frequency"
    if len(relations) == 0:
        relations = wp.get_lemma_and_pos(lemma1, pos1)[0]["Relations"]
    return wp.get_relations(
        lemma1,
        pos1,
        lemma2,
        pos2,
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
    use_context: bool = False,
    start_index: int = 0,
    result_number: int = 20,
):
    """Get collocation information and concordances for a specified collocation id.

    Args:
        coocc_id: Collocation id.
        use_context (optional): If true, returns surrounding sentences for matched collocation.
        start_index (optional): Collocation id.
        result_number (optional): Collocation id.

    Returns:
        Dictionary with collocation information and their concordances.
    """
    return wp.get_concordances_and_relation(
        coocc_id, use_context, start_index, result_number
    )


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
    operation: str = "adiff",
    use_intersection: bool = False,
    nbest: int = 0,
):
    """Get collocations of common POS from word-profile database and computes distances for comparison.

    Args:
        lemma1: Lemma of interest, first collocate.
        lemma2: Second collocate.
        pos: Pos tag for both lemmas.
        relations (optional): List of relation labels.
        number (optional): Number of collocations to take.
        order_by (optional): Metric for ordering, frequency or log-dice.
        min_freq (optional): Filter collocations with minimal frequency.
        min_stat (optional): Filter collocations with minimal stats score.
        operation (optional): Lemma distance metric.
        use_intersection (optional): If set, only the intersection of both lemma is computed.
        nbest (optional): Checks only the n highest scored lemmas.
    Return:
        List of collocation-diffs grouped by relation.
    """
    order_by = "log_dice" if order_by.lower() == "logdice" else "frequency"
    if len(relations) == 0:
        relations = wp.get_lemma_and_pos_diff(lemma1, lemma2)[0]["Relations"]
    return wp.get_diff(
        lemma1,
        lemma2,
        pos,
        relations,
        number,
        order_by,
        min_freq,
        min_stat,
        operation,
        use_intersection,
        nbest,
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
    nbest: int = 0,
):
    """Redirection for get_diff that sets parameters for intersection computation.

    Args:
        lemma1: Lemma of interest, first collocate.
        lemma2: Second collocate.
        pos: Pos tag for both lemmas.
        relations (optional): List of relation labels.
        number (optional): Number of collocations to take.
        order_by (optional): Metric for ordering, frequency or log-dice.
        min_freq (optional): Filter collocations with minimal frequency.
        min_stat (optional): Filter collocations with minimal stats score.
        nbest (optional): Checks only the n highest scored lemmas.
    Return:
        List of collocation-diffs grouped by relation.
    """
    order_by = "log_dice" if order_by.lower() == "logdice" else "frequency"
    if len(relations) == 0:
        relations = wp.get_lemma_and_pos_diff(lemma1, lemma2)[0]["Relations"]
    return wp.get_diff(
        lemma1,
        lemma2,
        pos,
        relations,
        number,
        order_by,
        min_freq,
        min_stat,
        operation="rmax",
        use_intersection=True,
        nbest=nbest,
    )


@app.get("/api/v1/mwe/profile", tags=["mwe"])
def get_mwe_relations(
    coocc_id: int,
    relations: List[str] = Query([]),
    start: int = 0,
    number: int = 20,
    order_by: str = "logDice",
    min_freq: int = 0,
    min_stat: float = -1000.0,
):
    """Get collocation information and concordances for a specified MWE collocation id.

    Args:
        coocc_id: MWE collocation id.
        relations (optional): List of relation labels.
        start (optional): Collocation id.
        number (optional): Number of collocations to take.
        order_by (optional): Metric for ordering, frequency or log-dice.
        min_freq (optional): Filter collocations with minimal frequency.
        min_stat (optional): Filter collocations with minimal stats score.

    Returns:
        Dictionary with mwe relations for specific collocation id.
    """
    order_by = "log_dice" if order_by.lower() == "logdice" else "frequency"
    return wp.get_mwe_relations(
        [coocc_id], relations, start, number, order_by, min_freq, min_stat
    )


@app.get("/api/v1/mwe/hits", tags=["mwe"])
def get_mwe_concordances_and_relation(
    coocc_id: int,
    use_context: bool = False,
    start_index: int = 0,
    result_number: int = 20,
):
    """Get mwe collocation information and concordances for a specified collocation id.

    Args:
        coocc_id: Collocation id.
        use_context (optional): If true, returns surrounding sentences for matched collocation.
        start_index (optional): Collocation id.
        result_number (optional): Collocation id.

    Returns:
        Dictionary with collocation information and their concordances.
    """
    return wp.get_concordances_and_relation(
        coocc_id, use_context, start_index, result_number, is_mwe=True
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
