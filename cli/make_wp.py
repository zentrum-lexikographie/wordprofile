#!/usr/bin/python3

import getpass
import logging
import sys
from argparse import ArgumentParser

from sqlalchemy import create_engine

from wordprofile.wpse.create import init_word_profile_tables, create_collocations, create_statistics
from wordprofile.wpse.processing import create_indices, process_files, post_process_db_files, load_files_into_db


def main():
    lformat = '[%(levelname)s] %(asctime)s %(name)s# %(message)s'
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=lformat)

    parser = ArgumentParser()
    parser.add_argument("--user", type=str, help="database username")
    parser.add_argument("--maria-db", type=str, help="database name")
    parser.add_argument("--mongo-db", type=str, help="database name")
    parser.add_argument("--mongo-index", default='', help="database index")
    parser.add_argument("--create-index", action="store_true", help="create indices")
    parser.add_argument("--passwd", action="store_true", help="ask for database password")
    parser.add_argument("--init", action="store_true", help="ask for database init")
    parser.add_argument("--collocations", action="store_true", help="ask for wordprofile creation")
    parser.add_argument("--stats", action="store_true", help="ask for wordprofile creation")
    parser.add_argument("--tmp", default='/mnt/SSD/data/', help="temporary storage path")
    parser.add_argument("--chunk-size", default=2000, help="size of document chunks per process per corpus")
    args = parser.parse_args()

    logging.info('USER: ' + args.user)
    logging.info('DB: ' + args.maria_db)
    logging.info('MONGO-DB: ' + args.mongo_db)
    if args.passwd:
        db_password = getpass.getpass("db password: ")
    else:
        db_password = args.user
    if args.init:
        logging.info("init database")
        engine = create_engine('mysql+pymysql://{}:{}@localhost'.format(args.user, db_password))
        init_word_profile_tables(engine, args.maria_db)
    if args.mongo_index:
        db_engine_key = 'mysql+pymysql://{}:{}@localhost/{}?charset=utf8&local_infile=1'.format(args.user, db_password,
                                                                                                args.maria_db)
        mongo_db_keys = ("mongodb://localhost:27017/", args.mongo_db)
        process_files(mongo_db_keys, db_engine_key, args.mongo_index, args.tmp, args.chunk_size)
        post_process_db_files(args.tmp)
        load_files_into_db(db_engine_key, args.tmp)
    if args.collocations:
        logging.info("CREATE word profile collocations")
        db_engine_key = 'mysql+pymysql://{}:{}@localhost/{}'.format(args.user, db_password, args.maria_db)
        engine = create_engine(db_engine_key)
        create_collocations(engine)
    if args.create_index:
        logging.info("CREATE indices")
        db_engine_key = 'mysql+pymysql://{}:{}@localhost/{}'.format(args.user, db_password, args.maria_db)
        engine = create_engine(db_engine_key)
        create_indices(engine)
    if args.stats:
        logging.info("CREATE word profile stats")
        db_engine_key = 'mysql+pymysql://{}:{}@localhost/{}'.format(args.user, db_password, args.maria_db)
        engine = create_engine(db_engine_key)
        create_statistics(engine)
    logging.info("DONE")


if __name__ == '__main__':
    main()
