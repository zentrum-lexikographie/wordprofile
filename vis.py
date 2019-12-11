import os
import random
import shutil

import graphviz
import nltk
import pymongo
from graphviz import Source


def get_conll_fmt(doc):
    sents = []
    for sent in doc:
        ws = []
        for w_i, w in enumerate(sent):
            if w['rel'] == "ROOT" and w['upos'][0] == '$':
                continue
            ws.append("{}\t{}\t{}\t{}".format(w['surface'], w['upos'], w['head'], w['rel']))
        sents.append("\n".join(ws))
    return sents


mongo_client = pymongo.MongoClient("mongodb://localhost:27017")
mongo_db = mongo_client["zdl2"]
document_ids = mongo_db["documents"].find({"sentences": {"$ne": []}}).distinct('_id')
random.shuffle(document_ids)
for doc_id in document_ids[:10]:
    with open("../files.csv", "a") as fh:
        doc = mongo_db["documents"].find_one({'_id': doc_id})
        print("path:", doc["basename"])
        path = os.path.join("..", "vis", doc["basename"])
        os.makedirs(path, exist_ok=True)
        for s_i, sent in enumerate(get_conll_fmt(doc["sentences"])):
            dg = nltk.DependencyGraph(sent)
            try:
                s = graphviz.Source(dg.to_dot())
                s.render(filename=os.path.join(path, str(s_i)),
                         format="png",
                         view=False, cleanup=True, quiet=True)
                fh.write("{}\t{}\t{}\n".format(path, s_i, " ".join(w["surface"] for w in doc["sentences"][s_i])))
            except graphviz.backend.CalledProcessError:
                pass
