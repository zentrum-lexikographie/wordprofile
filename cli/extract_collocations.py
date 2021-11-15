import logging
import os
import sys
from argparse import ArgumentParser

from wordprofile.wpse.processing import process_files, extract_collocations


def main():
    lformat = '[%(levelname)s] %(asctime)s # %(message)s'
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=lformat, datefmt='%H:%M:%S')

    parser = ArgumentParser()
    parser.add_argument("--input", default="-", type=str, help="conll input file")
    parser.add_argument("--dest", help="temporary storage path")
    parser.add_argument("--njobs", type=int, default=1, help="number of process jobs")
    args = parser.parse_args()

    os.makedirs(args.dest, exist_ok=True)
    process_files(args.input, args.dest, args.njobs)
    logging.info(f'EXTRACT collocations from matches')
    extract_collocations(os.path.join(args.dest, 'matches'), os.path.join(args.dest, 'collocations'))
    logging.info(f'DONE {args.dest}')


if __name__ == '__main__':
    main()
