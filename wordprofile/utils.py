#!/usr/bin/python3


def chunks(lst, n):
    """Yield successive n-sized chunks from lst.
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


tag_b2f = {
    'NOUN': 'Substantiv',
    'VERB': 'Verb',
    'ADV': 'Adverb',
    'ADJ': 'Adjektiv',
    'PROPN': 'Eigenname',
    'ADP': 'Adposition',
    '': '',
}
tag_f2b = {v: k for k, v in tag_b2f.items()}
