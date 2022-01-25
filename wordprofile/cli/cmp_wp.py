# This is a simple word profile client that is developed for usage tests
# It is used to compare two running wordprofile instances based on their overlap
import asyncio
import logging
import xmlrpc.client
from argparse import ArgumentParser
from collections import defaultdict

import numpy as np
from tabulate import tabulate

from wordprofile.apps.xmlrpc_api import WordprofileXMLRPC


async def get_relation(wp, lemma, pos_tag, start, number, order, min_freq, min_stat, corpus, relations):
    mapping = wp.get_lemma_and_pos({
        "Word": lemma,
        "POS": pos_tag,
    })
    if len(mapping) != 1:
        return {}
    selection = mapping[0]

    relations = wp.get_relations({
        "Lemma": selection["Lemma"],
        "LemmaId": selection.get("LemmaId", ""),
        "POS": selection["POS"],
        "PosId": selection.get("PosId", ""),
        "Start": start,
        "Number": number,
        "OrderBy": order,
        "MinFreq": min_freq,
        "MinStat": min_stat,
        "Subcorpus": corpus,
        "Relations": relations or selection["Relations"],
    })
    table_items = defaultdict(list)
    for rel_ctr, relation in enumerate(relations):
        for coocc_ctr, coocc in enumerate(relation['Tuples']):
            if coocc['POS'] in ["Personalpronomen"]:
                continue
            if relation["Relation"] == "VZ" and not coocc['Lemma'].endswith(lemma):
                coocc["Lemma"] = coocc['Lemma'] + lemma
            table_items[relation['Relation']].append((
                coocc['POS'], coocc["Lemma"], round(coocc['Score'][order], 2)
            ))
    return dict(table_items)


def overlap_ratio(words1, words2, n=10):
    overlap = len(words1 & words2)
    return round(min(overlap * 100 / min(len(words1), n), 100), 2)


parser = ArgumentParser()
parser.add_argument("--host1", type=str, help="XML-RPC hostname")
parser.add_argument("--host2", type=str, help="XML-RPC hostname")

parser.add_argument("-s", dest="start", default=0, help="Startpunkt der Relationstupel (default=0)")
parser.add_argument("-k", dest="k", type=int, default=1000, help="Number of samples")
parser.add_argument("-n1", dest="number1", type=int, default=20, help="Anzahl der Relationstupel (default=20)")
parser.add_argument("-n2", dest="number2", type=int, default=20, help="Anzahl der Relationstupel (default=20)")
parser.add_argument("-f", dest="min_freq", default=0, help="Minimaler Frequenzwert (default=0)")
parser.add_argument("-m", dest="min_stat", default=-9999, help="Minimaler Statistikwert (default=-9999)")
parser.add_argument("-c", dest="corpus", default="", help="Angabe des korpusnamen (zeit,kern,21jhd,etc.)")
parser.add_argument("-r", dest="relations", nargs="*",
                    help="Gewünschten Relationen in einer Liste (SUBJA,SUBJP,OBJA,OBJD,OBJI,GMOD,ATTR,KON,PP,etc.)")
parser.add_argument("-o", dest="order", default="logDice",
                    help="Angabe der Ordnung (frequency,log_dice,mi_log_freq,mi3) (default=log_dice)")

args = parser.parse_args()

logger = logging.getLogger('wordprofile')
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)

wp1: WordprofileXMLRPC = xmlrpc.client.ServerProxy("http://{}".format(args.host1))
wp2: WordprofileXMLRPC = xmlrpc.client.ServerProxy("http://{}".format(args.host2))

pos_map = {
    'Verb': 'VERB',
    'Substantiv': 'NOUN',
    'Adverb': 'ADV',
    'Adjektiv': 'ADJ',
}

pos_map_inv = {v: k for k, v in pos_map.items()}

lemma_pos_candidates = list(map(lambda c: (c[0], pos_map_inv[c[1]]),
                                (line.strip().split(",") for line in
                                 open("docs/wp_cmp_eval/token_freqs.csv", "r").readlines())))
lemma_pos_candidates = sorted(lemma_pos_candidates, key=lambda x: x[0])

relations = {
    'ADV',
    'ATTR',
    'GMOD',
    'KOM',
    'KON',
    'OBJ',
    'PN',
    'PP',
    'PRED',
    'SUBJA',
    # 'SUBJP',
    'VZ',
    '~ADV',
    '~ATTR',
    '~GMOD',
    '~KOM',
    '~OBJ',
    '~PP',
    '~PRED',
    '~SUBJA',
    # '~SUBJP'
}


async def main():
    fh_all = open('eval/wp_all.txt', 'w')

    for rel in relations:
        print("Relation:", rel, file=fh_all)
        overlap_scores = []
        with open('eval/wp_{}.txt'.format(rel.lower().replace("~", "-")), 'w') as fh:
            for lemma, pos in lemma_pos_candidates:
                t_relation_cats_1 = asyncio.create_task(
                    get_relation(wp1, lemma, pos, args.start, args.number1, args.order,
                                 args.min_freq, args.min_stat, args.corpus, [rel]))
                t_relation_cats_2 = asyncio.create_task(
                    get_relation(wp2, lemma, pos_map.get(pos), args.start, args.number2, args.order,
                                 args.min_freq, args.min_stat, args.corpus, [rel]))
                relation_cats_1, relation_cats_2 = await asyncio.gather(t_relation_cats_1, t_relation_cats_2)

                for rel_cat in set(relation_cats_1.keys()) & set(relation_cats_2.keys()):
                    wps1 = relation_cats_1.get(rel_cat, [])
                    wps2 = relation_cats_2.get(rel_cat, [])
                    max_rel_no = max(len(wps1), len(wps2))
                    table_items = []
                    table_headers = ['POS (alt)', 'Lemma (alt)', 'Score (alt)', 'POS (neu)', 'Lemma (neu)',
                                     'Score (neu)']
                    wp1_lemmas = {lemma for pos, lemma, score in wps1}
                    wp2_lemmas = {lemma for pos, lemma, score in wps2}
                    common_lemmas = set()
                    for i in range(max_rel_no):
                        if i < len(wps1) and wps1[i][1] in wp2_lemmas:
                            common_lemmas.add(wps1[i][1])
                            continue
                        if i < len(wps2) and wps2[i][1] in wp1_lemmas:
                            common_lemmas.add(wps2[i][1])
                            continue
                        row = []
                        if i < len(wps1):
                            row.extend(wps1[i])
                        else:
                            row.extend([None, None, None])
                        if i < len(wps2):
                            row.extend(wps2[i])
                        else:
                            row.extend([None, None, None])
                        table_items.append(row)
                    overlap_prob = overlap_ratio(wp1_lemmas, wp2_lemmas, args.number1)
                    overlap_scores.append(overlap_prob)
                    print("  {}-{} both:{:5.2f}".format(lemma, pos, overlap_prob), file=fh_all)
                    print("{}-{} both:{:5.2f}".format(lemma, pos, overlap_prob), file=fh)
                    print("[{}]".format(", ".join(common_lemmas)), file=fh)
                    print(tabulate(table_items, headers=table_headers, tablefmt='fancy_grid'), file=fh)
                    print('', file=fh)
            print("Avg Overlap: {:5.2f}".format(np.mean(overlap_scores)), file=fh_all)
            print("Avg Overlap: {:5.2f}".format(np.mean(overlap_scores)), file=fh)


if __name__ == '__main__':
    asyncio.run(main())
