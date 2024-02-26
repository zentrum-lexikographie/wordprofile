import logging
import os
from argparse import ArgumentParser

from wordprofile.utils import configure_logs_to_file
from wordprofile.wpse.processing import post_process_db_files


def main():
    logger = logging.getLogger(__name__)
    configure_logs_to_file(logging.INFO, "compute-statistics")

    parser = ArgumentParser()
    parser.add_argument("src", type=str, nargs="+", help="temporary storage path")
    parser.add_argument("--dest", type=str, help="temporary storage path")
    parser.add_argument(
        "--min-rel-freq", type=int, default=3, help="number of process jobs"
    )
    parser.add_argument("--mwe", action="store_true")
    args = parser.parse_args()
    os.makedirs(args.dest, exist_ok=True)
    post_process_db_files(
        args.src, args.dest, min_rel_freq=args.min_rel_freq, with_mwe=args.mwe
    )
    logger.info("DONE compute statistics.")


if __name__ == "__main__":
    main()
