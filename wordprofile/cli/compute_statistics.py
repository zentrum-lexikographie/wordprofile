import logging
import os
import sys
from argparse import ArgumentParser

from wordprofile.wpse.processing import post_process_db_files


def parse_arguments(args):
    parser = ArgumentParser()
    parser.add_argument("src", type=str, nargs="+", help="temporary storage path")
    parser.add_argument("--dest", type=str, help="temporary storage path")
    parser.add_argument(
        "--min-rel-freq", type=int, default=3, help="number of process jobs"
    )
    parser.add_argument("--mwe", action="store_true")
    return parser.parse_args(args)


def main(arguments: list):
    lformat = "[%(levelname)s] %(asctime)s # %(message)s"
    logging.basicConfig(
        stream=sys.stdout, level=logging.DEBUG, format=lformat, datefmt="%H:%M:%S"
    )
    args = parse_arguments(arguments)
    os.makedirs(args.dest, exist_ok=True)
    post_process_db_files(
        args.src, args.dest, min_rel_freq=args.min_rel_freq, with_mwe=args.mwe
    )


if __name__ == "__main__":
    main(sys.argv[1:])
