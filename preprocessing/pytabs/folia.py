import itertools
import logging
from multiprocessing import Pool
import os
from pathlib import Path

import bagit
import click
import coloredlogs
from lxml import etree

from .parser import parse, add_space_after


def _gather_source_files(sources, source_dir_pattern):
    for source in sources:
        source = Path(source)
        if source.is_dir():
            for f in source.glob(source_dir_pattern):
                yield f.as_posix()
        else:
            yield source.as_posix()


def gather_sources(sources, source_dir_pattern, source_file_limit):
    sources = _gather_source_files(sources, source_dir_pattern)
    if source_file_limit:
        sources = itertools.islice(sources, source_file_limit)
    sources = list(sources)
    sources.sort()
    return sources


XML_ID = '{http://www.w3.org/XML/1998/namespace}id'

FOLIA_NS = 'http://ilk.uvt.nl/folia'
FOLIA_NS_MAP = {None: FOLIA_NS}
FOLIA = '{' + FOLIA_NS + '}'


def tabs_files_to_folia(chunk):
    id, template, ci, files = chunk
    count_p = 0
    count_s = 0
    count_w = 0

    id_stack = [id, str(ci + 1)]

    doc = etree.fromstring(template)
    doc.set(XML_ID, '.'.join(id_stack))

    metadata = doc.find(FOLIA + 'metadata')
    if metadata is None:
        metadata = etree.Element(FOLIA + 'metadata', nsmap=FOLIA_NS_MAP)
        doc.insert(0, metadata)

    text = doc.find(FOLIA + 'text')
    if text is None:
        text = etree.SubElement(doc, FOLIA + 'text', nsmap=FOLIA_NS_MAP)
    id_stack += ['text', '1']
    text.set(XML_ID, '.'.join(id_stack))

    id_stack += ['part', '0']
    for fi, f in enumerate(files):
        id_stack[-1] = str(fi + 1)
        with Path(f).open() as f:
            sentences = add_space_after(parse(f))
            paragraphs = itertools.groupby(
                sentences, lambda s: s['metadata']['break'].get('p', {})
            )
            part_id = '.'.join(id_stack)
            metadata_id = 'metadata.' + part_id
            part = etree.SubElement(
                text, FOLIA + 'part', {XML_ID: part_id, 'metadata': metadata_id}
            )
            id_stack += ['p', '0']
            for pi, (_, paragraph) in enumerate(paragraphs):
                count_p += 1
                id_stack[-1] = str(pi + 1)
                p = etree.SubElement(
                    part, FOLIA + 'p', {XML_ID: '.'.join(id_stack)}
                )
                id_stack += ['s', '0']
                for si, sentence in enumerate(paragraph):
                    count_s += 1
                    id_stack[-1] = str(si + 1)
                    s = etree.SubElement(
                        p, FOLIA + 's', {XML_ID: '.'.join(id_stack)}
                    )
                    # write metadata of first sentence in file
                    if pi == 0 and si == 0:
                        part_metadata = etree.SubElement(
                            metadata,
                            FOLIA + 'submetadata',
                            {XML_ID: metadata_id, 'type': 'native'}
                        )
                        for k, v in sentence['metadata']['meta'].items():
                            el = etree.SubElement(
                                part_metadata,
                                FOLIA + 'meta',
                                {'id': k}
                            )
                            el.text = v
                    token_fields = sentence['token_fields']
                    tokens = sentence['tokens']
                    id_stack += ['w', '0']
                    for ti, token in enumerate(tokens):
                        count_w += 1
                        id_stack[-1] = str(ti + 1)
                        w = etree.SubElement(
                            s, FOLIA + 'w', {XML_ID: '.'.join(id_stack)}
                        )
                        for k, v in zip(token_fields, token):
                            if k == 'Token':
                                t = etree.SubElement(w, FOLIA + 't')
                                t.text = v
                            elif k == 'SpaceAfter' and v != '1':
                                w.set('space', 'no')
                            elif k == 'Pos':
                                etree.SubElement(
                                    w, FOLIA + 'pos', {'class': v}
                                )
                            elif k == 'Lemma':
                                etree.SubElement(
                                    w, FOLIA + 'lemma', {'class': v}
                                )
                    id_stack = id_stack[:-2]
                id_stack = id_stack[:-2]
            id_stack = id_stack[:-2]
    return (etree.tostring(doc), count_p, count_s, count_w)


def validate_destination(ctx, param, value):
    destination = Path(value)
    if destination.is_dir():
        raise click.BadParameter('destination must not exist')
    destination.mkdir(parents=True)
    return value


@click.command()
@click.option(
    '-d', '--destination',
    required=True,
    type=click.Path(file_okay=False, exists=False),
    callback=validate_destination,
    help='Target directory where converted files are written in FoLiA format'
)
@click.option(
    '--id',
    required=True,
    help='FoLiA document prefix ID'
)
@click.option(
    '-l', '--source-file-limit',
    type=int,
    help='Optional max. limit for the number of DDC/Tabs files to process'
)
@click.option(
    '-n', '--destination-chunk-size',
    default=1,
    type=int,
    help='Number of DDC/Tabs files/documents to be aggregated per FoLiA document'
)
@click.option(
    '-p', '--source-dir-pattern',
    default='**/*.tabs',
    help='Glob pattern for DDC/Tabs files in source directories'
)
@click.option(
    '--parallel',
    default=lambda: len(os.sched_getaffinity(0)),
    type=int,
    help='Number of parallel conversions'
)
@click.option(
    '-q', '--quiet',
    is_flag=True,
    default=False,
    help='Do not show progress'
)
@click.option(
    '-t', '--template',
    type=click.Path(exists=True, dir_okay=False),
    help='FoLiA template'
)
@click.argument(
    'sources',
    nargs=-1,
    type=click.Path(exists=True)
)
def main(sources, source_dir_pattern, source_file_limit,
         quiet, parallel, id, template,
         destination, destination_chunk_size):
    if template is not None:
        template = Path(template)
    else:
        template = (Path(__file__) / '..' / 'template.folia.xml').resolve()
    with template.open() as f:
        parser = etree.XMLParser(remove_blank_text=True)
        template = etree.tostring(etree.parse(f, parser), pretty_print=False)

    sources = gather_sources(sources, source_dir_pattern, source_file_limit)
    destination = Path(destination)

    chunks = [
        sources[offset:offset + destination_chunk_size]
        for offset in range(0, len(sources), destination_chunk_size)
    ]
    chunks = list([(id, template, ci, chunk) for ci, chunk in enumerate(chunks)])
    chunks_len = len(chunks)

    level = logging.WARN if quiet else logging.INFO
    coloredlogs.install(level)
    log = logging.getLogger()

    with Pool(parallel) as p:
        results = p.imap(tabs_files_to_folia, chunks)
        for ri, result in enumerate(results):
            ri += 1
            doc, count_p, count_s, count_w = result
            dest_file = destination / f'{id}-{ri:010d}.folia.xml'
            dest_file.write_bytes(doc)
            log.info(
                f'{ri:7d}/{chunks_len} - '
                f'{count_p:7d} <p/>, {count_s:7d} <s/>, {count_w:7d} <w/> - '
                f'{dest_file}'
            )
    bagit.make_bag(destination.as_posix(), processes=parallel)


if __name__ == '__main__':
    main()
