import os
import sys
from glob import glob

import click

from wordprofile.preprocessing.pytabs.tabs import TabsDocument


@click.command()
@click.option(
    "-i",
    "--input",
    default="",
    type=str,
    help="Glob compatible path pattern for source files.",
)
@click.option(
    "-o",
    "--output",
    default="",
    type=str,
    help="Path to destination folder.",
)
@click.help_option("--help", "-h")
def main(input, output):
    """Tabs to Conllu conversion"""
    src_files = glob(input, recursive=True)
    if len(src_files) == 0:
        raise FileNotFoundError("No files found for conversion!")
    for src in src_files:
        doc = TabsDocument.from_tabs(src)
        if output:
            file_name = os.path.basename(src)
            file_name = file_name[: -len("tabs")] + "conllu"
            tgt_path = os.path.join(output, doc.meta["collection"], file_name)
            doc.save(tgt_path)
        else:
            sys.stdout.write(doc.as_conllu())
            sys.stdout.flush()


if __name__ == "__main__":
    main()
