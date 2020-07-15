#!/usr/bin/python3

import multiprocessing
from typing import List

from imsnpars.nparser import builder
from imsnpars.tools.utils import ConLLToken as IMSConllToken
from wordprofile.datatypes import TabsToken

parsers = {}


def tokenized_sentence_to_conll_token(sentence: List[TabsToken], normalizer=None) -> List[IMSConllToken]:
    sentence_conll = []
    for token_i, token in enumerate(sentence):
        sentence_conll.append(
            IMSConllToken(tokId=token_i + 1,
                          orth=token.surface,
                          lemma=token.lemma,
                          pos=token.pos,
                          langPos=token.pos,
                          morph="",
                          headId=None,
                          dep=None,
                          norm=normalizer.norm(token.surface) if normalizer else None))
    return sentence_conll


def get_parser_prediction(parser, sentence):
    parser._NDependencyParser__renewNetwork()
    instance = parser._NDependencyParser__reprBuilder.buildInstance(sentence)
    tree = parser._NDependencyParser__predict_tree(instance)
    for pos, tok in enumerate(sentence):
        tok.setHeadPos(tree.getHead(pos))
        tok.dep = tree.getLabel(pos)
    return sentence


def parse_document(parser, doc, use_normalizer=False):
    normalizer = builder.buildNormalizer(use_normalizer)
    test_data = [sent.to_tabs_token(doc.index) for sent in doc.sentences]
    parser_data = map(lambda s: tokenized_sentence_to_conll_token(s, normalizer), test_data)
    parses = map(lambda s: get_parser_prediction(parser, s), parser_data)
    doc.add_column('Head', 'hd')
    doc.add_column('Deprel', 'rel')
    for tabs_sent, parse_sent in zip(doc.sentences, parses):
        tabs_sent.add_column([t.headId for t in parse_sent])
        tabs_sent.add_column([t.dep for t in parse_sent])
    return doc


def get_parser(args, options):
    global parsers
    pid = multiprocessing.current_process().name
    if pid in parsers:
        print("load parser from memory", pid)
        return parsers[pid]
    else:
        print("build and load new parser", pid)
        parser = builder.buildParser(options)
        parser.load(args.model)
        parsers[pid] = parser
        return parser
