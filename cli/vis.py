import argparse
import multiprocessing
import os
import random

import graphviz
import nltk
import pymongo

argparser = argparse.ArgumentParser()
argparser.add_argument("--database", type=str, help="database name", required=True)
argparser.add_argument("--jobs", help="", type=int, default=1)
args = argparser.parse_args()


def get_conll_fmt(doc):
    sents = []
    for sent in doc:
        ws = []
        for w_i, w in enumerate(sent):
            ws.append("{}\t{}\t{}\t{}".format(w['surface'], w['upos'], w['head'], w['rel']))
        sents.append("\n".join(ws))
    return sents


def visualize_document(mongo_db_keys, doc_id):
    mongo_db = pymongo.MongoClient(mongo_db_keys[0])[mongo_db_keys[1]]
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
            # with open("../files.csv", "a") as fh:
            #     fh.write("{}\t{}\t{}\n".format(path, s_i, " ".join(w["surface"] for w in doc["sentences"][s_i])))
        except graphviz.backend.CalledProcessError:
            pass


def main():
    # lformat = '[%(levelname)s] %(asctime)s %(name)s# %(message)s'
    # logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=lformat)
    print('|: db: ' + args.database)
    mongo_db_keys = ("mongodb://localhost:27017/", args.database)

    mongo_db = pymongo.MongoClient(mongo_db_keys[0])[mongo_db_keys[1]]
    document_ids = mongo_db["documents"].find({"sentences": {"$ne": []}}).distinct('_id')
    print('|: Found documents: ', len(document_ids))
    random.shuffle(document_ids)
    files = [(mongo_db_keys, doc_id) for doc_id in document_ids[:100]]

    print("Create MPPool with #njobs:", args.jobs)
    with multiprocessing.Pool(args.jobs) as pool:
        pool.starmap(visualize_document, files, chunksize=8)


if __name__ == '__main__':
    main()
