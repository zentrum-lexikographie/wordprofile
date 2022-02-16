from xmlrpc.client import ServerProxy


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
