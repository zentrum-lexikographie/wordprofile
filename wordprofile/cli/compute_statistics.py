import logging
import os
import sys
from argparse import ArgumentParser

from wordprofile.utils import configure_logs_to_file
from wordprofile.wpse.processing import post_process_db_files


def parse_arguments(args):
    parser = ArgumentParser()
    parser.add_argument("src", type=str, nargs="+", help="Path to input data")
    parser.add_argument("--dest", type=str, help="Output path")
    parser.add_argument(
        "--min-rel-freq",
        type=int,
        default=3,
        help="Minimal frequency filter for aggregated collocations",
    )
    parser.add_argument("--mwe", action="store_true", help="Extract MWE collocations")
    return parser.parse_args(args)


def main(arguments: list):
    logger = logging.getLogger(__name__)
    configure_logs_to_file(level=logging.INFO, log_file_identifier="compute-statistics")
    args = parse_arguments(arguments)
    os.makedirs(args.dest, exist_ok=True)
    post_process_db_files(
        args.src, args.dest, min_rel_freq=args.min_rel_freq, with_mwe=args.mwe
    )
    logger.info("DONE compute statistics.")


if __name__ == "__main__":
    main(sys.argv[1:])
