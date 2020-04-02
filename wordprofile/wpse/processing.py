import logging
import multiprocessing
import os
from collections import defaultdict
from typing import List, Dict

import pymongo
from sqlalchemy import create_engine

from wordprofile.datatypes import DBToken
from wordprofile.utils import chunks
from wordprofile.wpse.db_tables import remove_invalid_chars
from wordprofile.wpse.prepare import prepare_corpus_file, prepare_concord_sentences, prepare_matches
from wordprofile.zdl import repair_lemma, SIMPLE_TAG_MAP, sentence_is_valid, extract_matches_from_doc


def convert_sentence(sentence: List[Dict[str, str]]) -> List[DBToken]:
    return [DBToken(
        idx=i + 1,
        surface=remove_invalid_chars(token['surface']),
        lemma=repair_lemma(remove_invalid_chars(token['lemma']), SIMPLE_TAG_MAP.get(token['xpos'], '')),
        tag=SIMPLE_TAG_MAP.get(token['xpos'], ''),
        head=token['head'],
        rel=token['rel'],
        misc=bool(token['misc'])
    ) for i, token in enumerate(sentence)]


def process_doc(mongo_db_keys, mongo_index, doc_id):
    mongo_db = pymongo.MongoClient(mongo_db_keys[0])[mongo_db_keys[1]][mongo_index]
    doc = mongo_db.find_one({'_id': doc_id})
    try:
        doc_id, db_corpus_file = prepare_corpus_file(doc)
        parses = list(filter(sentence_is_valid, map(convert_sentence, doc["sentences"])))
        db_concord_sentences = prepare_concord_sentences(doc_id, parses)
        matches = extract_matches_from_doc(parses)
        db_matches = prepare_matches(doc_id, matches)
        return db_corpus_file, db_concord_sentences, db_matches
    except Exception as e:
        logging.warning(e)
        return None, [], []


def delete_indices(db_engine_key):
    engine = create_engine(db_engine_key)
    logging.info("DELETE indices for files, concordances, and matches")
    engine.execute("DROP INDEX IF EXISTS corpus_index ON corpus_files")
    engine.execute("DROP INDEX IF EXISTS concord_corpus_index ON concord_sentences")
    engine.execute("DROP INDEX IF EXISTS concord_corpus_sentence_index ON concord_sentences")
    engine.execute("DROP INDEX IF EXISTS matches_corpus_index ON matches")
    engine.execute("DROP INDEX IF EXISTS matches_corpus_sentence_index ON matches")
    engine.execute("DROP INDEX IF EXISTS matches_relation_label_index ON matches")


def create_indices(db_engine_key):
    engine = create_engine(db_engine_key)
    logging.info("CREATE INDEX indices for files, concordances, and matches")
    logging.info("CREATE INDEX corpus_index")
    engine.execute("CREATE UNIQUE INDEX corpus_index ON corpus_files (id);")
    logging.info("CREATE INDEX concord_corpus_index")
    engine.execute("CREATE INDEX concord_corpus_index ON concord_sentences (corpus_file_id);")
    logging.info("CREATE INDEX concord_corpus_sentence_index")
    engine.execute("CREATE UNIQUE INDEX concord_corpus_sentence_index "
                   "ON concord_sentences (corpus_file_id, sentence_id);")
    logging.info("CREATE INDEX matches_corpus_index")
    engine.execute("CREATE INDEX matches_corpus_index ON matches (corpus_file_id);")
    logging.info("CREATE INDEX matches_corpus_sentence_index")
    engine.execute("CREATE INDEX matches_corpus_sentence_index ON matches (corpus_file_id, sentence_id);")
    logging.info("CREATE INDEX matches_relation_label_index")
    engine.execute("CREATE INDEX matches_relation_label_index ON matches (collocation_id);")


def get_corpus_file_ids(mongo_db_keys, mongo_index, db_engine_key, filter_existing=True):
    mongo_db = pymongo.MongoClient(mongo_db_keys[0])[mongo_db_keys[1]][mongo_index]
    engine = create_engine(db_engine_key)
    if filter_existing:
        inserted_ids = {i[0] for i in engine.execute('SELECT id FROM corpus_files')}
        logging.info('LOAD corpus file ids: {}'.format(len(inserted_ids)))
    else:
        inserted_ids = {}
    document_ids = [i['_id'] for i in mongo_db.find({'sentence': {'$ne': []}}, {'_id': 1}) if
                    str(i['_id']) not in inserted_ids]
    logging.info("LOADED document ids for processing: {}".format(len(document_ids)))
    return document_ids


class FileWorker(multiprocessing.Process):
    def __init__(self, path, fname):
        self.q = multiprocessing.Manager().Queue(maxsize=100)
        self.path = path
        self.fname = fname
        super().__init__()

    def run(self):
        logging.info('INIT queue, wait for jobs')
        with open(os.path.join(self.path, self.fname), 'w') as fh:
            while True:
                db_batch = self.q.get()
                if not db_batch:
                    logging.info('{:10} - CLOSE queue'.format(self.fname))
                    break
                try:
                    items = ["\t".join(map(str, x)) + "\n" for x in db_batch]
                    logging.info(
                        "{:10} - GOT queue value ({}). qsize={}".format(self.fname, len(items), self.q.qsize()))
                    fh.writelines(items)
                except Exception as e:
                    logging.warning(e)

    def stop(self):
        self.q.put(None)


def process_files_index(mongo_db_keys, mongo_index, db_engine_key, db_files_queue, db_sents_queue, db_matches_queue):
    document_ids = get_corpus_file_ids(mongo_db_keys, mongo_index, db_engine_key, filter_existing=False)
    for doc_i, doc_ids in enumerate(chunks(document_ids, 2000)):
        with multiprocessing.Pool(3) as pool:
            db_corpus_files, db_concord_sentences, db_matches = zip(
                *pool.starmap(process_doc, [(mongo_db_keys, mongo_index, doc_id) for doc_id in doc_ids], chunksize=100)
            )
        db_corpus_files = [x for x in db_corpus_files if x]
        db_concord_sentences = [x for sentences in db_concord_sentences for x in sentences]
        db_matches = [tuple(x) for file_matches in db_matches for x in file_matches]
        logging.info("{:10} - PROCESSED documents {} {} {}".format(mongo_index, len(db_corpus_files),
                                                                   len(db_concord_sentences), len(db_matches)))
        db_files_queue.put(db_corpus_files)
        db_sents_queue.put(db_concord_sentences)
        db_matches_queue.put(db_matches)
    logging.info('{:10} - INDEX DONE'.format(mongo_index))


class ConverterFileWorker(multiprocessing.Process):
    def __init__(self, path, q_match_out):
        self.path = path
        self.q = multiprocessing.Manager().Queue(maxsize=100)
        self.q_match_out = q_match_out
        super().__init__()

    def run(self):
        relation_dict = defaultdict(dict)
        freq_dict = defaultdict(int)
        next_rel_id = 1
        fname = "relations"
        logging.info('INIT queue, wait for jobs')
        with open(os.path.join(self.path, fname), 'w') as matches_rel:
            while True:
                db_matches = self.q.get()
                logging.info("{:10} - GOT queue value. qsize={}".format(fname, self.q.qsize()))
                if not db_matches:
                    logging.info('{:10} - CLOSE queue'.format(fname))
                    for rel, cols_dict in relation_dict.items():
                        for cols, rel_id in cols_dict.items():
                            matches_rel.write('{}\t{}\t{}\t0\t{}\n'.format(
                                rel_id, rel, "\t".join(map(str, cols)), freq_dict[rel_id]))
                    break
                try:
                    for m_i, m in enumerate(db_matches):
                        rel, cols = m[0], m[1:5]
                        if cols in relation_dict[rel]:
                            rel_id = relation_dict[rel][cols]
                        else:
                            rel_id = next_rel_id
                            next_rel_id += 1
                            relation_dict[rel][cols] = rel_id
                        db_matches[m_i] = (rel_id,) + m[5:]
                        freq_dict[rel_id] += 1
                    self.q_match_out.put(db_matches)
                except Exception as e:
                    logging.warning(e)

    def stop(self):
        self.q.put(None)


def process_files(mongo_db_keys, db_engine_key, mongo_indices, storage_path):
    mongo_indices = [i.strip() for i in mongo_indices.split(",") if i.strip()]
    # delete_indices(db_engine_key)
    db_files_worker = FileWorker(storage_path, 'files')
    db_sents_worker = FileWorker(storage_path, 'sents')
    db_matches_worker = FileWorker(storage_path, 'matches')
    db_files_worker.start()
    db_sents_worker.start()
    match_convert_worker = ConverterFileWorker(storage_path, db_matches_worker.q)
    match_convert_worker.start()
    db_matches_worker.start()
    doc_ps = []
    for mongo_index in mongo_indices:
        logging.info('Start Process:{}'.format(mongo_index))
        p = multiprocessing.Process(target=process_files_index,
                                    args=(mongo_db_keys, mongo_index, db_engine_key,
                                          db_files_worker.q, db_sents_worker.q, match_convert_worker.q))
        p.start()
        doc_ps.append((mongo_index, p))

    for mongo_index, p in doc_ps:
        p.join()

    logging.info('INDICES DONE')
    db_files_worker.stop()
    db_sents_worker.stop()
    match_convert_worker.stop()
    db_matches_worker.stop()
    logging.info('PUT NONE to queue and wait...')
    db_files_worker.join()
    db_sents_worker.join()
    match_convert_worker.join()
    db_matches_worker.join()
    logging.info('ALL JOBS DONE')
    engine = create_engine(db_engine_key)
    engine.execute("LOAD DATA LOCAL INFILE '/mnt/SSD/data/files' INTO TABLE corpus_files;")
    logging.info('LOADED corpus_files')
    engine.execute("LOAD DATA LOCAL INFILE '/mnt/SSD/data/sents' INTO TABLE concord_sentences;")
    logging.info('LOADED concord_sentences')
    engine.execute("LOAD DATA LOCAL INFILE '/mnt/SSD/data/relations' INTO TABLE collocations;")
    logging.info('LOADED collocations')
    engine.execute("LOAD DATA LOCAL INFILE '/mnt/SSD/data/matches' INTO TABLE matches;")
    logging.info('LOADED matches')
