#!/usr/bin/python3

import getpass
import logging
import os
from argparse import ArgumentParser

import sys
from sqlalchemy import create_engine

from wordprofile.wpse.create import init_word_profile_tables, create_statistics, create_indices
from wordprofile.wpse.processing import process_files, post_process_db_files, load_files_into_db


def main():
    lformat = '[%(levelname)s] %(asctime)s %(name)s# %(message)s'
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=lformat)

    parser = ArgumentParser()
    parser.add_argument("--user", type=str, help="database username")
    parser.add_argument("--maria-db", type=str, help="database name")
    parser.add_argument("--input", default="-", type=str, help="conll input file")
    parser.add_argument("--create-wp", action="store_true", help="create wordprofile from tmp data")
    parser.add_argument("--passwd", action="store_true", help="ask for database password")
    parser.add_argument("--tmp", default='/mnt/SSD/data/', help="temporary storage path")
    parser.add_argument("--chunk-size", type=int, default=2000, help="size of document chunks per process per corpus")
    parser.add_argument("--njobs", type=int, default=1, help="size of document chunks per process per corpus")
    args = parser.parse_args()

    if args.input:
        os.makedirs(args.tmp, exist_ok=True)
        process_files(args.input, args.tmp, args.njobs, args.chunk_size)
        post_process_db_files(args.tmp)
    if args.create_wp:
        logging.info('USER: ' + args.user)
        logging.info('DB: ' + args.maria_db)
        if args.passwd:
            db_password = getpass.getpass("db password: ")
        else:
            db_password = args.user
        logging.info("init database")
        engine = create_engine('mysql+pymysql://{}:{}@localhost'.format(args.user, db_password))
        init_word_profile_tables(engine, args.maria_db)
        engine = create_engine('mysql+pymysql://{}:{}@localhost/{}?charset=utf8&local_infile=1'.format(
            args.user, db_password, args.maria_db))
        logging.info("CREATE indices")
        load_files_into_db(engine, args.tmp)
        create_indices(engine)
        logging.info("CREATE word profile stats")
        create_statistics(engine)
    logging.info("DONE")


if __name__ == '__main__':
    main()
