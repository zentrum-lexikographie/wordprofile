import glob
import os
import re
import sys
from datetime import date
from typing import Dict, List, Set

import click

from preprocessing.pytabs.tabs import TabsDocument


def collect_current_basenames(data_root: str, corpus_name: str) -> Set[str]:
    """
    Collect basenames from corpus.toc files in data_root.

    This will search for all .toc file for 'corpus' in 'data_root' and
    subordinate directories and return a set of the contained basenames.
    """
    current_basenames = set()
    toc_files = glob.glob(f"{data_root}/**/{corpus_name}.toc", recursive=True)
    for file in toc_files:
        with open(file) as toc:
            current_basenames.update({line.strip() for line in toc})
    return current_basenames


def map_tabs_file_to_basename(corpus_tabs_file: str) -> Dict[str, str]:
    file_basename_mapping = {}
    with open(corpus_tabs_file) as fp:
        for line in fp:
            match = re.match(r"corpus-tabs.d/([\w/\.-]+)\.tabs\n?$", line)
            if match:
                basename = match.group(1)
            else:
                basename = ""
            file_basename_mapping[line.strip()] = basename
    return file_basename_mapping


def filter_new_files(
    old_basenames: Set[str], file_basename_mapping: Dict[str, str]
) -> List[str]:
    return [
        file
        for file, basename in file_basename_mapping.items()
        if basename not in old_basenames
    ]


@click.command()
@click.option(
    "--corpus",
    "-c",
    required=True,
    type=str,
    help="Name of corpus. Used for detection of .toc files and naming of output files.",
)
@click.option(
    "--data-root",
    "-d",
    required=True,
    type=click.Path(exists=True, file_okay=False),
    help="""Path to directory containing existing data and .toc files.
    New data will be written to a subdirectory there.""",
)
@click.option(
    "--tabs-dump-path",
    "-t",
    required=True,
    type=click.Path(exists=True, file_okay=False),
    help="""Path to 'ddc_dump' directory that contains subdir with .tabs files and
    'corpus-tabs.files'.""",
)
@click.help_option("--help", "-h")
def main(
    corpus: str,
    data_root: str,
    tabs_dump_path: str,
):
    """
    Generate .conll file for corpus from .tabs files that are not contained
    in existing data.

    Existing basenames are read from .toc files, new basenames are extracted
    from list in 'corpus-tabs.files'.
    New data is written to a subdirectory of the existing data directory,
    using the current date as name. A .toc file with the new basenames is
    added there as well.
    """
    old_basenames = collect_current_basenames(data_root, corpus)
    corpus_tabs_file = os.path.join(tabs_dump_path, "corpus-tabs.files")
    new_file_basename_map = map_tabs_file_to_basename(corpus_tabs_file)
    files_to_process = filter_new_files(old_basenames, new_file_basename_map)
    if not files_to_process:
        return
    output_dir = date.today().isoformat()
    output_path = os.path.join(data_root, output_dir)
    os.makedirs(os.path.abspath(output_path), exist_ok=True)

    new_basenames = []
    with open(os.path.join(output_path, f"{corpus}.conll"), "w") as fp:
        for file in files_to_process:
            doc = TabsDocument.from_tabs(os.path.join(tabs_dump_path, file))
            fp.write(doc.as_conllu())
            new_basenames.append(doc.meta["basename"])

    with open(os.path.join(output_path, f"{corpus}.toc"), "w", encoding="utf-8") as fp:
        fp.write("\n".join(new_basenames))


if __name__ == "__main__":
    main()
