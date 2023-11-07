import os
import sys
from glob import glob

import click

from pytabs.tabs import TabsDocument


@click.command()
@click.option('-i', '--input', 'source', default='', type=str)
@click.option('-o', '--output', 'destination', default='', type=str)
@click.option('-x', '--remove-xml', is_flag=True)
@click.option('-v', '--remove-invalid-sentences', is_flag=True)
def main(source, destination, remove_xml, remove_invalid_sentences):
    src_files = glob(source, recursive=True)
    if len(src_files) == 0:
        raise FileNotFoundError("No files found for conversion!")
    for src in src_files:
        doc = TabsDocument.from_tabs(src)
        if remove_xml:
            doc.remove_xml_tags_from_tabs()
        if remove_invalid_sentences:
            doc.remove_invalid_sentence()
        if destination:
            file_name = os.path.basename(src)
            file_name = file_name[:-len("tabs")] + "conllu"
            tgt_path = os.path.join(destination, doc.meta['collection'], file_name)
            doc.save(tgt_path, as_conll=True)
        else:
            sys.stdout.write(doc.as_conllu())
            sys.stdout.flush()


if __name__ == '__main__':
    main()
