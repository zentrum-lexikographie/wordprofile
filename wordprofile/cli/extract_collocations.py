import logging
import os
import sys
from argparse import ArgumentParser

from wordprofile.wpse.processing import (
    extract_collocations,
    extract_most_common_surface,
    process_files,
)


def main():
    lformat = "[%(levelname)s] %(asctime)s # %(message)s"
    logging.basicConfig(
        stream=sys.stdout, level=logging.DEBUG, format=lformat, datefmt="%H:%M:%S"
    )
    logger = logging.getLogger(__name__)
    parser = ArgumentParser()
    parser.add_argument(
        "--input",
        default="-",
        type=str,
        help="conll input file(s). As default stdin is used, if this option is not used.",
        nargs="*",
    )
    parser.add_argument("--dest", help="temporary storage path")
    parser.add_argument("--njobs", type=int, default=1, help="number of process jobs")
    args = parser.parse_args()
    os.makedirs(args.dest, exist_ok=True)
    process_files(args.input, args.dest, args.njobs)
    logger.info("EXTRACT collocations from matches")
    extract_collocations(
        os.path.join(args.dest, "matches"), os.path.join(args.dest, "collocations")
    )
    logger.info("EXTRACT most common surface form")
    extract_most_common_surface(
        os.path.join(args.dest, "matches"), os.path.join(args.dest, "common_surfaces")
    )
    logger.info("DONE %s" % args.dest)


if __name__ == "__main__":
    main()
