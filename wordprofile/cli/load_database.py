import logging
from argparse import ArgumentParser

from wordprofile.db import open_db, load_db
from wordprofile.utils import configure_logs_to_file


def main():
    configure_logs_to_file(logging.INFO, "load-database")

    parser = ArgumentParser()
    parser.add_argument(
        "source", help="data source dir"
    )
    parser.add_argument(
        "--clear", help="Clear database before loading", action="store_true"
    )

    args = parser.parse_args()

    load_db(open_db(clear=args.clear), args.source)


if __name__ == "__main__":
    main()
