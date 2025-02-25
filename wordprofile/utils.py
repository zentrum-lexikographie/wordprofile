import logging
import os
from datetime import date


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def look_ahead(iterable):
    el = None
    for next_el in iterable:
        if el:
            yield (el, next_el)
        el = next_el
    if el:
        yield (el, None)


def configure_logger(logger, level=logging.DEBUG, log_file=None):
    handler = logging.FileHandler(log_file) if log_file else logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter("[%(levelname)s] %(asctime)s - %(funcName)s - %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger


tag_b2f = {
    "NOUN": "Substantiv",
    "VERB": "Verb",
    "ADV": "Adverb",
    "ADJ": "Adjektiv",
    "PROPN": "Eigenname",
    "ADP": "Adposition",
    "AUX": "Hilfsverb",
    "": "",
}
tag_f2b = {v: k for k, v in tag_b2f.items()}


def split_relation_inversion(relation):
    if relation.startswith("~"):
        relation = relation[1:]
        inv = 1
    else:
        inv = 0
    return relation, inv


def configure_logs_to_file(level=logging.INFO, log_file_identifier="wp-logs"):
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "log")
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(
            log_dir, f"{date.today().isoformat()}-{log_file_identifier}.log"
        ),
        level=level,
        format="%(asctime)s - %(levelname)s - %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
