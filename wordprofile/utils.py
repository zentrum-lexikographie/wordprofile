#!/usr/bin/python3

import logging

def chunks(lst, n):
    """Yield successive n-sized chunks from lst.
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def configure_logger(logger, level=logging.DEBUG, log_file=None):
    handler = logging.FileHandler(log_file) if log_file else logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter('[%(levelname)s] %(asctime)s - %(funcName)s - %(message)s')
    )
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger
