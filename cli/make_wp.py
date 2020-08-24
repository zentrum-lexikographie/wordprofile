#!/usr/bin/python3

import logging
import os
import sys
from argparse import ArgumentParser

from sqlalchemy import create_engine

from wordprofile.wpse.create import init_word_profile_tables, create_statistics, create_indices
from wordprofile.wpse.processing import process_files, post_process_db_files, load_files_into_db


def main():
    lformat = '[%(levelname)s] %(asctime)s %(name)s# %(message)s'
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=lformat)

    parser = ArgumentParser()
    parser.add_argument("--user", type=str, help="database username")
    parser.add_argument("--db", type=str, help="database name")
    parser.add_argument("--input", default="-", type=str, help="conll input file")
    parser.add_argument("--create-wp", action="store_true", help="create wordprofile from tmp data")
    parser.add_argument("--tmp", default='/mnt/SSD/data/', help="temporary storage path")
    parser.add_argument("--njobs", type=int, default=1, help="size of document chunks per process per corpus")
    args = parser.parse_args()

    if args.input:
        os.makedirs(args.tmp, exist_ok=True)
        process_files(args.input, args.tmp, args.njobs)
        post_process_db_files(args.tmp)
    if args.create_wp:
        wp_user = args.user or os.environ['WP_USER']
        wp_db = args.db or os.environ['WP_DB']
        db_password = os.environ.get('WP_PASSWORD', wp_user)
        logging.info('USER: ' + wp_user)
        logging.info('DB: ' + wp_db)
        logging.info("init database")
        engine = create_engine('mysql+pymysql://{}:{}@localhost'.format(wp_user, db_password))
        init_word_profile_tables(engine, wp_db)
        engine = create_engine('mysql+pymysql://{}:{}@localhost/{}?charset=utf8&local_infile=1'.format(
            wp_user, db_password, wp_db))
        logging.info("CREATE indices")
        load_files_into_db(engine, args.tmp)
        create_indices(engine)
        logging.info("CREATE word profile stats")
        create_statistics(engine)
    logging.info("DONE")


if __name__ == '__main__':
    main()
