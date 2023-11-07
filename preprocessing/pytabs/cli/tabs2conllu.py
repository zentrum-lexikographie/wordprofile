import os
import sys
from glob import glob

import click

from preprocessing.pytabs.tabs import TabsDocument


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
@click.option(
    "-x",
    "--remove-xml",
    is_flag=True,
    help="Removes invalid xml fragments from tokens.",
)
@click.option(
    "-v",
    "--remove-invalid-sentences",
    is_flag=True,
    help="Removes sentences that do not fit hard constraints.",
)
@click.help_option("--help", "-h")
def main(input, output, remove_xml, remove_invalid_sentences):
    """Tabs to Conllu conversion"""
    src_files = glob(input, recursive=True)
    if len(src_files) == 0:
        raise FileNotFoundError("No files found for conversion!")
    for src in src_files:
        doc = TabsDocument.from_tabs(src)
        if remove_xml:
            doc.remove_xml_tags_from_tabs()
        if remove_invalid_sentences:
            doc.remove_invalid_sentence()
        if output:
            file_name = os.path.basename(src)
            file_name = file_name[: -len("tabs")] + "conllu"
            tgt_path = os.path.join(output, doc.meta["collection"], file_name)
            doc.save(tgt_path, as_conll=True)
        else:
            sys.stdout.write(doc.as_conllu())
            sys.stdout.flush()


if __name__ == "__main__":
    main()
