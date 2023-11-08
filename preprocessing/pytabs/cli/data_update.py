import glob
from typing import Set, Dict


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


def map_basename_to_tabs_file(corpus_tabs_file: str) -> Dict[str, str]:
    pass


def filter_new_files():
    pass
