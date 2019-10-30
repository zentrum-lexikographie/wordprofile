#!/usr/bin/env python

import argparse
import getpass
import logging
import multiprocessing
import sys
from glob import glob

from imsnpars.nparser import builder
from imsnpars.nparser import options
from imsnpars.tools import utils
from sqlalchemy import create_engine

from wordprofile.parsing import parse_file, get_parser
from wordprofile.wpse.db_tables import insert_concord_sentences, get_relation_id, insert_matches, \
    insert_corpus_file
from wordprofile.zdl import extract_matches_from_document


# TODO refactor parser generation - too complicated right now
def build_parser_from_args(cmd_args=None):
    argParser = argparse.ArgumentParser(description="""IMS BiLSTM Parser""", add_help=False)

    db_args = argParser.add_argument_group('database')
    db_args.add_argument("--user", type=str, help="database username", required=True)
    db_args.add_argument("--database", type=str, help="database name", required=True)
    db_args.add_argument("--passwd", action="store_true", help="ask for database password")

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
    argParser.add_argument('--help', action='help', default=argparse.SUPPRESS,
                           help=argparse._('show this help message and exit'))
    args = argParser.parse_args(cmd_args)

    opts = utils.NParserOptions()
    options.fillParserOptions(args, opts)
    opts.load(args.model + ".args")
    opts.logOptions()

    return args, opts


def process_files_parallel(db_engine_key, src, args, options):
    parser = get_parser(args, options)
    engine = create_engine(db_engine_key)
    meta_data, parses = parse_file(parser, src, options.normalize)
    print("({}) - parsed document".format(meta_data['basename']))
    corpus_file_id = insert_corpus_file(engine, meta_data)
    insert_concord_sentences(engine, corpus_file_id, parses)
    matches = extract_matches_from_document(parses)
    print("({}) - extracted matches".format(meta_data['basename']))
    matches = {get_relation_id(engine, ms[0]): ms for _, ms in matches.items() if ms}
    for relation_id, relation_matches in matches.items():
        insert_matches(engine, corpus_file_id, relation_id, relation_matches)
    print("({}) - inserted matches".format(meta_data['basename']))


def main():
    lformat = '[%(levelname)s] %(asctime)s %(name)s# %(message)s'
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=lformat)
    args, options = build_parser_from_args()

    print('|: user: ' + args.user)
    print('|: db: ' + args.database)
    if args.passwd:
        db_password = getpass.getpass("db password: ")
    else:
        db_password = args.user
    db_engine_key = 'mysql+pymysql://{}:{}@localhost/{}'.format(args.user, db_password, args.database)

    src_files = glob(args.src)

    if len(src_files) > 1:
        files = [(db_engine_key, src, args, options) for src in src_files]
        print("Create MPPool with #njobs:", args.jobs)
        with multiprocessing.Pool(args.jobs) as pool:
            pool.starmap(process_files_parallel, files, chunksize=3)
    else:
        engine = create_engine(db_engine_key)
        parser = builder.buildParser(options)
        parser.load(args.model)
        meta_data, parses = parse_file(parser, args.src, options.normalize)
        corpus_file_id = insert_corpus_file(engine, meta_data)
        insert_concord_sentences(engine, corpus_file_id, parses)
        matches = extract_matches_from_document(parses)
        matches = {get_relation_id(engine, ms[0]): ms for _, ms in matches.items() if ms}
        for relation_id, relation_matches in matches.items():
            insert_matches(engine, corpus_file_id, relation_id, relation_matches)


if __name__ == '__main__':
    main()
