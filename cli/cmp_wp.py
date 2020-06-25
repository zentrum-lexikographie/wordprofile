#!/usr/bin/python3
# This is a simple word profile client that is developed for usage tests
# It is used to compare two running wordprofile instances based on their overlap

import logging
import random
import xmlrpc.client
from argparse import ArgumentParser
from collections import defaultdict

import numpy as np
from tabulate import tabulate

from apps.xmlrpc_api import WordprofileXMLRPC


def get_relation(wp, lemma, pos_tag, start, number, order, min_freq, min_stat, corpus, relations):
    """
    Args:
        wp:
        lemma:
        pos_tag:
        start:
        number:
        order:
        min_freq:
        min_stat:
        corpus:
        relations:
    """
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


def wp_jaccard_distance(wp1, wp2, n=10):
    """
    Args:
        wp1:
        wp2:
        n:
    """
    words1 = set(c[1] for c in wp1)
    words2 = set(c[1] for c in wp2)
    overlap = len(words1 & words2)
    both = len(words1 | words2)
    overlap_p = round(min(overlap * 100 / min(len(words1), n), 100), 2)
    jacc = round(min(overlap * 100 / min(both, n * 2), 100), 2)
    return overlap, both, overlap_p, jacc


parser = ArgumentParser()
subparsers = parser.add_subparsers(dest="subcommand")
db_parser = parser.add_argument_group("server arguments")
db_parser.add_argument("--host1", type=str, help="XML-RPC hostname")
db_parser.add_argument("--host2", type=str, help="XML-RPC hostname")

db_parser.add_argument("-s", dest="start", default=0, help="Startpunkt der Relationstupel (default=0)")
db_parser.add_argument("-k", dest="k", default=1000, help="Number of samples")
db_parser.add_argument("-n", dest="number", default=20, help="Anzahl der Relationstupel (default=20)")
db_parser.add_argument("-f", dest="min_freq", default=0, help="Minimaler Frequenzwert (default=0)")
db_parser.add_argument("-m", dest="min_stat", default=-9999, help="Minimaler Statistikwert (default=-9999)")
db_parser.add_argument("-c", dest="corpus", default="", help="Angabe des korpusnamen (zeit,kern,21jhd,etc.)")
db_parser.add_argument("-r", dest="relations", nargs="*",
                       help="Gewünschten Relationen in einer Liste (SUBJA,SUBJP,OBJA,OBJD,OBJI,GMOD,ATTR,KON,PP,etc.)")
db_parser.add_argument("-o", dest="order", default="logDice",
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
    'Verb': 'VV',
    'Substantiv': 'NN',
    'Adverb': 'ADV',
    'Adjektiv': 'ADJ',
}
pos_map_inv = {v: k for k, v in pos_map.items()}

lemma_pos_candidates = list(map(lambda c: (c[0], pos_map_inv[c[1]]),
                                (line.strip().split(",") for line in
                                 open("docs/wp_cmp_eval/token_freqs.csv", "r").readlines())))
lemma_pos_candidates = sorted(random.choices(lemma_pos_candidates, k=args.k), key=lambda x: x[0])

relations = ['ADV', 'ATTR', 'GMOD', '~GMOD', 'KOM', 'KON', 'OBJ', '~OBJ', 'PP', 'PRED', '~PRED', 'VZ']
# relations = ['VZ']

for rel in relations:
    print("Relation:", rel)
    scores = {
        'overlaps': [],
        'jacc_dists': []
    }
    with open('eval/wp_{}_cmp.txt'.format(rel.lower().replace("~", "-")), 'w') as fh:
        for lemma, pos in lemma_pos_candidates:
            relation_cats_1 = get_relation(wp1, lemma, pos, args.start, args.number, args.order,
                                           args.min_freq, args.min_stat, args.corpus, [rel])
            relation_cats_2 = get_relation(wp2, lemma, pos_map.get(pos), args.start, args.number, args.order,
                                           args.min_freq, args.min_stat, args.corpus, [rel])

            for rel_cat in set(relation_cats_1.keys()) & set(relation_cats_2.keys()):
                wps1 = relation_cats_1.get(rel_cat, [])
                wps2 = relation_cats_2.get(rel_cat, [])
                max_rel_no = max(len(wps1), len(wps2))
                table_items = []
                table_headers = ['POS (alt)', 'Lemma (alt)', 'Score (alt)', 'POS (neu)', 'Lemma (neu)', 'Score (neu)']
                for i in range(max_rel_no):
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
                overlap, both, overlap_prob, jacc_dist = wp_jaccard_distance(wps1, wps2)
                scores['overlaps'].append(overlap_prob)
                scores['jacc_dists'].append(jacc_dist)
                print("  {}-{} both:{:5.2f} jacc:{:5.2f}".format(lemma, pos, overlap_prob, jacc_dist))
                print("{}-{} both:{:5.2f} jacc:{:5.2f}".format(lemma, pos, overlap_prob, jacc_dist), file=fh)
                print(tabulate(table_items, headers=table_headers, tablefmt='fancy_grid'), file=fh)
                print('', file=fh)
        print("Avg Overlap: {:5.2f}, Avg JACC Dist: {:5.2f}".format(np.mean(scores['overlaps']),
                                                                    np.mean(scores['jacc_dists'])))
        print("Avg Overlap: {:5.2f}, Avg JACC Dist: {:5.2f}".format(np.mean(scores['overlaps']),
                                                                    np.mean(scores['jacc_dists'])),
              file=fh)
