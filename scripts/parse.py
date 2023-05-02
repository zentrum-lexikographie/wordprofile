import bz2
import os
import re
import sys
from collections import OrderedDict

import click
import conllu
import torch
import trankit
from tqdm import tqdm


class Parser:

    def __init__(self, lang='german-hdt', tagbatch=12):
        tmp_stdout = sys.stdout
        sys.stdout = sys.stderr
        self.parser = trankit.Pipeline(lang, cache_dir=os.path.expanduser('~/.trankit/'))
        self.parser._tagbatchsize = tagbatch
        self.parser("Init")
        sys.stdout = tmp_stdout

    def __call__(self, sentences):
        sentences_in = [[token['form'] if token['form'] else '---' for token in sentence] for sentence in sentences]
        try:
            res = self.parser(sentences_in)
            for sent_i, sent in enumerate(sentences):
                words = res['sentences'][sent_i]['tokens']
                for tok_i, token in enumerate(sent):
                    ner_pred = words[tok_i].get('ner')
                    if ner_pred and ner_pred != 'O':
                        if token['misc']:
                            token['misc']['NER'] = words[tok_i].get('ner')
                        else:
                            token['misc'] = OrderedDict([('NER', words[tok_i].get('ner'))])
                    # stay with the original lemma for better compliance
                    token.update(
                        # lemma=words[tok_i].get('lemma', '_'),
                        upos=words[tok_i].get('upos', '_'),
                        xpos=words[tok_i].get('xpos', '_'),
                        feats=words[tok_i].get('feats', '_'),
                        head=words[tok_i].get('head', '_'),
                        deprel=words[tok_i].get('deprel', '_'),
                    )
        except RuntimeError as e:
            sys.stderr.write(f'Runtime Error: {e}')
        return sentences


def iter_conll_sentences(file_handle):
    chunk = []
    while True:
        line = file_handle.readline()
        if len(line) == 0:
            break
        if line == '\n':
            if chunk != '':
                yield ''.join(chunk)
                chunk.clear()
        else:
            chunk.append(line)


def group_sentences_to_documents(sentences):
    doc = []
    for sent in sentences:
        if "# DDC:meta.file_ =" in sent:
            if len(doc):
                yield '\n'.join(doc)
            doc = [sent]
        else:
            doc.append(sent)
    if len(doc):
        yield '\n'.join(doc)


def iter_doc_basenames(file_handle):
    for line in file_handle:
        if line.startswith("# DDC:meta.basename"):
            yield line[len("# DDC:meta.basename ="):].strip()


RE_META = re.compile(r"# DDC:meta\.(\w+) = (.*)")


def extract_meta_from_str(doc_str: str):
    return dict(m.groups() for m in RE_META.finditer(doc_str))


@click.command()
@click.option('-i', '--input', default='-', type=click.File('r'))
@click.option('-o', '--output', default='-', type=click.File('w'))
@click.option('-c', '--cont', default='.', type=click.Path())
@click.option('--lang', default='german-hdt', type=str)
@click.option('--tagbatch', default=12, type=int)
@click.option('--nthreads', default=1, type=int)
def main(input, output, cont, lang, tagbatch, nthreads):
    torch.set_num_threads(nthreads)
    parser = Parser(lang=lang, tagbatch=tagbatch)
    # We provide the field definition explicitly, so the parser does not seek
    # through the input stream, looking for a field declaration. The latter
    # will fail on piped stdin.
    if cont != '.':
        if cont.endswith('bz'):
            fh = bz2.open(cont, 'rt')
        elif cont.endswith('conll'):
            fh = open(cont, 'r')
        else:
            raise ValueError(f"Unknown file ending: {cont}")
        basenames = {base for base in tqdm(iter_doc_basenames(fh), desc="Basenames")}
        fh.close()
    else:
        basenames = {}
    print(f"Loaded basenames: {len(basenames)}", file=sys.stderr)

    for doc_str in tqdm(group_sentences_to_documents(iter_conll_sentences(input))):
        meta = extract_meta_from_str(doc_str)
        if meta['basename'] in basenames:
            continue
        doc = conllu.parse(doc_str, fields=conllu.parser.DEFAULT_FIELDS)
        for sentence in parser(doc):
            output.write(sentence.serialize())
        output.flush()


if __name__ == '__main__':
    main()
