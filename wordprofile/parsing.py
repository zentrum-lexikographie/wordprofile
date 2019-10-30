import multiprocessing

from imsnpars.nparser import builder

from wordprofile.zdl import read_tabs_format, tokenized_sentence_to_conll_token, conll_token_to_tokenized_sentence

parsers = {}


def get_parser_prediction(parser, sentence):
    parser._NDependencyParser__renewNetwork()
    instance = parser._NDependencyParser__reprBuilder.buildInstance(sentence)
    tree = parser._NDependencyParser__predict_tree(instance)
    for pos, tok in enumerate(sentence):
        tok.setHeadPos(tree.getHead(pos))
        tok.dep = tree.getLabel(pos)
    return sentence


def parse_file(parser, src, use_normalizer=False):
    normalizer = builder.buildNormalizer(use_normalizer)
    meta_data, test_data = read_tabs_format(src)
    parser_data = map(lambda s: tokenized_sentence_to_conll_token(s, normalizer), test_data)
    parses = map(lambda s: get_parser_prediction(parser, s), parser_data)
    parses_converted = list(map(lambda xs: conll_token_to_tokenized_sentence(*xs), zip(test_data, parses)))
    return meta_data, parses_converted


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
