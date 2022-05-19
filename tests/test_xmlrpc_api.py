from xmlrpc.client import ServerProxy, Fault

import pytest


def test_xmlrpc_api():
    wp = ServerProxy('http://localhost:8086/RPC2')
    lemmata_and_pos = wp.get_lemma_and_pos({
        'Word': 'haben',
        'POS': 'Verb'
    })
    for lemma_and_pos in lemmata_and_pos:
        assert wp.get_relations({
            'Lemma': lemma_and_pos['Lemma'],
            'POS': lemma_and_pos['POS'],
            'Relations': lemma_and_pos['Relations']
        })


def test_invalid_lemma():
    wp = ServerProxy('http://localhost:8086/RPC2')

    invalid_lemmas = [
        '(haben)',
        '"error"',
        "-1' OR (select/**/IFNULL(ASCII(SUBSTRING((SELECT/**/database()),3,1)),0)>122) AND 0008=0008 or 'SVLVDUiv'='",
    ]

    with pytest.raises(Fault):
        for lemma in invalid_lemmas:
            wp.get_lemma_and_pos({
                'Word': lemma,
                'POS': 'Verb'
            })
