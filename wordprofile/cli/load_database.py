import logging
import os
import sys
from argparse import ArgumentParser

from sqlalchemy import create_engine

from wordprofile.wpse.create import (
    create_indices,
    create_statistics,
    init_word_profile_tables,
)
from wordprofile.wpse.processing import load_files_into_db


def main():
    lformat = "[%(levelname)s] %(asctime)s # %(message)s"
    logging.basicConfig(
        stream=sys.stdout, level=logging.DEBUG, format=lformat, datefmt="%H:%M:%S"
    )
    logger = logging.getLogger(__name__)

    parser = ArgumentParser()
    parser.add_argument("source", help="temporary storage path")
    parser.add_argument("--user", type=str, help="database username")
    parser.add_argument("--db", type=str, help="database name")
    args = parser.parse_args()

    wp_user = args.user or os.environ["WP_USER"]
    wp_db = args.db or os.environ["WP_DB"]
    db_password = os.environ.get("WP_PASSWORD", wp_user)
    logger.info("USER: %s" % wp_user)
    logger.info("DB: %s" % wp_db)
    logger.info("init database")
    engine = create_engine(
        "mysql+pymysql://{}:{}@localhost".format(wp_user, db_password)
    )
    init_word_profile_tables(engine, wp_db)
    engine = create_engine(
        "mysql+pymysql://{}:{}@localhost/{}?charset=utf8mb4&local_infile=1".format(
            wp_user, db_password, wp_db
        )
    )
    logger.info("CREATE indices")
    load_files_into_db(engine, args.source)
    create_indices(engine)
    logger.info("CREATE word profile stats")
    create_statistics(engine)


if __name__ == "__main__":
    main()
