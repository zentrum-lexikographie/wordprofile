#!/usr/bin/env python

import argparse
import logging
import multiprocessing
import sys
from glob import glob

import pymongo
from imsnpars.nparser import options
from imsnpars.tools import utils
from wordprofile.parsing import get_parser, parse_file
from wordprofile.zdl import read_tabs_format

sys.setrecursionlimit(200)

parsers = {}

lformat = '[%(levelname)s] %(asctime)s %(name)s# %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=lformat)


# TODO refactor parser generation - too complicated right now
def build_parser_from_args(cmd_args=None):
    argParser = argparse.ArgumentParser(description="""IMS BiLSTM Parser""", add_help=False)

    db_args = argParser.add_argument_group('database')
    db_args.add_argument("--database", type=str, help="database name", required=True)
    db_args.add_argument("--drop", action="store_true", help="clears document database")
    db_args.add_argument("--skip", action="store_true", help="skips documents already inserted in db")

    parserArgs = argParser.add_argument_group('parser')
    parserArgs.add_argument("--parser", help="which parser to use", choices=["GRAPH", "TRANS"], required=True)
    parserArgs.add_argument("--jobs", help="", type=int, default=1)
    parserArgs.add_argument("--normalize", help="normalize the words", type=bool, required=False, default=True)

    # files
    filesArgs = argParser.add_argument_group('files')
    filesArgs.add_argument("--src", help="source file", type=str, required=True)
    filesArgs.add_argument("--list", help="input file consists of whitespace separated input output files",
                           action="store_true", required=False)
    filesArgs.add_argument("--dest", help="source file", type=str, required=False)
    filesArgs.add_argument("--model", help="load model from the file", type=str, required=True)

    # parse for the first time to only get the parser name
    args, _ = argParser.parse_known_args(cmd_args)

    # parse the second time to get all the args
    options.addParserCmdArguments(args.parser, argParser)
    args = argParser.parse_args(cmd_args)

    opts = utils.NParserOptions()
    options.fillParserOptions(args, opts)
    opts.load(args.model + ".args")
    opts.logOptions()

    return args, opts


def process_files_parallel(mongo_db_keys, srcs, args, options, basenames):
    parser = get_parser(args, options)
    mongo_db_client = pymongo.MongoClient(mongo_db_keys[0])
    mongo_db = mongo_db_client[mongo_db_keys[1]]
    result = []
    for src_i, src in enumerate(srcs):
        meta_data, _ = read_tabs_format(src, meta_only=True)
        if args.skip and meta_data['basename'] in basenames:
            logging.info("({}) - SKIP - document already in db".format(meta_data['basename']))
        else:
            try:
                meta_data, parses = parse_file(parser, src, options.normalize)
                parses = [[dict(token._asdict()) for token in sentence] for sentence in parses]
                logging.info("({}) - parsed document".format(meta_data['basename']))
                meta_data["sentences"] = parses
                result.append(meta_data)
            except RecursionError:
                logging.warning("Skip parse: maximum recursion depth exceeded")
    try:
        mongo_db["documents"].insert_many(result)
        logging.info("Inserted documents: {}".format(len(result)))
    except Exception as e:
        logging.warning(e)
    mongo_db_client.close()


def drop_documents(mongo_db_keys):
    mongo_db_client = pymongo.MongoClient(mongo_db_keys[0])
    mongo_db = mongo_db_client[mongo_db_keys[1]]
    mongo_db["documents"].drop()
    mongo_db["documents"].drop_indexes()
    mongo_db["documents"].create_index([("basename", pymongo.HASHED)])
    mongo_db_client.close()


def get_basenames(mongo_db_keys):
    mongo_db_client = pymongo.MongoClient(mongo_db_keys[0])
    mongo_db = mongo_db_client[mongo_db_keys[1]]
    return set(mongo_db["documents"].find().distinct('basename'))


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def main():
    args, options = build_parser_from_args()

    logging.info('|: db: ' + args.database)
    mongo_db_keys = ("mongodb://localhost:27017/", args.database)
    if args.drop:
        drop_documents(mongo_db_keys)
    src_files = glob(args.src)

    if len(src_files) == 0:
        raise FileNotFoundError("No files found for parsing!")

    basenames = get_basenames(mongo_db_keys)
    files = [(mongo_db_keys, src, args, options, basenames) for src in chunks(src_files, 25)]
    logging.info("Create MPPool with #njobs:", args.jobs)
    with multiprocessing.Pool(args.jobs) as pool:
        pool.starmap(process_files_parallel, files, chunksize=10)


if __name__ == '__main__':
    main()
