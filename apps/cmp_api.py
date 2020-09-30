#!/usr/bin/python3
import random
import xmlrpc.client
from argparse import ArgumentParser
from collections import defaultdict

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from xmlrpc_api import WordprofileXMLRPC

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
                    help="Angabe der Ordnung (frequency,log_dice) (default=log_dice)")

args = parser.parse_args()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

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
                                 open("../docs/wp_cmp_eval/token_freqs.csv", "r").readlines())))
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


def get_relation(wp, lemma, pos_tag, start, number, order, min_freq, min_stat, relations):
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
    if len(words1) == 0:
        return 100.00
    overlap = len(words1 & words2)
    return round(min(overlap * 100 / min(len(words1), n), 100), 2)


@app.get("/", response_class=HTMLResponse)
@app.get("/cmp", response_class=HTMLResponse)
async def cmp(request: Request):
    rel = random.choice(list(relations))
    lemma_src, pos_src = random.choice(lemma_pos_candidates)
    relation_cats_1 = get_relation(wp1, lemma_src, pos_src, args.start, args.number1, args.order,
                                   args.min_freq, args.min_stat, [rel])
    relation_cats_2 = get_relation(wp2, lemma_src, pos_map.get(pos_src), args.start, args.number2, args.order,
                                   args.min_freq, args.min_stat, [rel])

    wps1 = relation_cats_1.get(rel, [])
    wps2 = relation_cats_2.get(rel, [])
    table_headers = ['Lemma', 'POS', 'Score']
    wp1_lemmas = {lemma for pos, lemma, score in wps1}
    wp2_lemmas = {lemma for pos, lemma, score in wps2}
    wp1_rows = []
    wp2_rows = []
    for pos, lemma, score in wps1:
        if lemma not in wp2_lemmas:
            wp1_rows.append((lemma, pos, score))
    for pos, lemma, score in wps2:
        if lemma not in wp1_lemmas:
            wp2_rows.append((lemma, pos, score))
    overlap_prob = overlap_ratio(wp1_lemmas, wp2_lemmas, args.number1)
    return templates.TemplateResponse("index.html",
                                      {"request": request, "lemma": lemma_src, "pos": pos_src, "relation": rel,
                                       "overlap": overlap_prob,
                                       "common_lemmas": list(wp1_lemmas & wp2_lemmas),
                                       "header": table_headers, "wp1": wp1_rows, "wp2": wp2_rows})


if __name__ == '__main__':
    uvicorn.run("cmp_api:app", log_level="debug", reload=True)
