import argparse
import multiprocessing
import os
from glob import glob

import graphviz
import nltk

from wordprofile.datatypes import TabsDocument

argparser = argparse.ArgumentParser()
argparser.add_argument("--files", type=str, help="path pattern interpreted by glob", required=True)
argparser.add_argument("--jobs", help="", type=int, default=1)
args = argparser.parse_args()


def get_conll_fmt(doc: TabsDocument):
    sents = []
    for sent in doc.sentences:
        ws = []
        for w_i, w in enumerate(sent.to_conll(doc.index)):
            ws.append("{}\t{}\t{}\t{}".format(w.surface, w.tag, w.head, w.rel))
        sents.append("\n".join(ws))
    return sents


def visualize_document(doc_path):
    doc = TabsDocument.from_conll(doc_path)
    print("path:", doc.meta["basename"])
    path = os.path.join("..", "vis", doc.meta["basename"])
    os.makedirs(path, exist_ok=True)
    for s_i, sent in enumerate(get_conll_fmt(doc)):
        dg = nltk.DependencyGraph(sent)
        try:
            s = graphviz.Source(dg.to_dot())
            s.render(filename=os.path.join(path, str(s_i)),
                     format="png",
                     view=False, cleanup=True, quiet=True)
        except graphviz.backend.CalledProcessError:
            pass


def main():
    print('|: pattern: ' + args.files)
    files = glob(args.files)
    print('|: Found documents: ', len(files))
    print("Create MPPool with #njobs:", args.jobs)
    with multiprocessing.Pool(args.jobs) as pool:
        pool.map(visualize_document, files, chunksize=8)


if __name__ == '__main__':
    main()
