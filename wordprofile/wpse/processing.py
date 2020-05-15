#!/usr/bin/python3

import hashlib
import logging
import multiprocessing
import os
from collections import defaultdict, namedtuple
from glob import glob
from multiprocessing.queues import Queue
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine

from wordprofile.datatypes import DBToken, TabsDocument, TabsSentence
from wordprofile.formatter import RE_HIT_DELIMITER
from wordprofile.utils import chunks
from wordprofile.wpse.db_tables import remove_invalid_chars
from wordprofile.wpse.prepare import prepare_corpus_file, prepare_concord_sentences, prepare_matches
from wordprofile.zdl import repair_lemma, SIMPLE_TAG_MAP, sentence_is_valid, extract_matches_from_doc


def convert_sentence(sentence: TabsSentence) -> List[DBToken]:
    """Convert sentence into list of token while performing normalization and filtering.

    If tags are not found in mapping, they are left empty and recognized later.
    """
    return [DBToken(
        idx=i,
        surface=remove_invalid_chars(surface),
        lemma=repair_lemma(remove_invalid_chars(lemma),
                           SIMPLE_TAG_MAP.get(xpos, '')),
        tag=SIMPLE_TAG_MAP.get(xpos, ''),
        head=head,
        rel=rel,
        misc=bool(misc)
    ) for i, surface, lemma, tag, xpos, _, head, rel, _, misc in sentence.tokens]


def process_doc(doc_path: str):
    """Load single file into memory, extract and prepare information.
    """
    doc = TabsDocument.from_conll(doc_path)
    try:
        doc_id, db_corpus_file = prepare_corpus_file(doc)
        parses = list(filter(sentence_is_valid, map(convert_sentence, doc.sentences)))
        db_concord_sentences = prepare_concord_sentences(doc_id, parses)
        matches = extract_matches_from_doc(parses)
        db_matches = prepare_matches(doc_id, matches)
        return db_corpus_file, db_concord_sentences, db_matches
    except Exception as e:
        logging.warning(e)
        return None, [], []


def create_indices(engine: Engine):
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


def process_doc_files(doc_paths: List[str], db_files_queue: Queue, db_sents_queue: Queue, db_matches_queue: Queue):
    """Extracts information from files and forwards to corresponding queue.
    """
    db_corpus_files, db_concord_sentences, db_matches = zip(*map(process_doc, doc_paths))
    db_corpus_files = [x for x in db_corpus_files if x]
    db_concord_sentences = [x for sentences in db_concord_sentences for x in sentences]
    db_matches = [tuple(x) for file_matches in db_matches for x in file_matches]
    logging.info("PROCESSED documents {} {} {}".format(len(db_corpus_files),
                                                       len(db_concord_sentences), len(db_matches)))
    db_files_queue.put(db_corpus_files)
    db_sents_queue.put(db_concord_sentences)
    db_matches_queue.put(db_matches)


class ConverterFileWorker(multiprocessing.Process):
    def __init__(self, path, fname, q_match_out):
        self.path = path
        self.fname = fname
        self.q = multiprocessing.Manager().Queue(maxsize=100)
        self.q_match_out = q_match_out
        super().__init__()

    def run(self):
        relation_dict = defaultdict(dict)
        freq_dict = defaultdict(int)
        next_rel_id = 1
        logging.info('INIT queue, wait for jobs')
        while True:
            db_matches = self.q.get()
            logging.info("{:10} - GOT queue value. qsize={}".format(self.fname, self.q.qsize()))
            if not db_matches:
                logging.info('{:10} - CLOSE queue'.format(self.fname))
                with open(os.path.join(self.path, self.fname), 'w') as matches_rel:
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


def is_valid_sentence(sentence: str):
    """Hard constraints for concordances.

    End with sentence delimiter, have a certain length, and start with uppercase letter.
    """
    sentence += '\x01'
    s = [t for t, d in RE_HIT_DELIMITER.findall(sentence)]
    return s[-1] in '.!?\'"' and 8 <= len(s) <= 25 and s[0][0].isupper()


def process_files(files_path: str, storage_path: str, njobs: int = 1, chunk_size: int = 2000):
    """Extract WP related information from given files.

    This method processed a given list of files in parallel.
    Workers are created for each result (corpus_files, concordances, matches, collocations) in relation to db tables.
    The file list is split into several chunks for parallel processing. The extracted results are sent to the workers.
    """
    db_files_worker = FileWorker(storage_path, 'corpus_files_stage')
    db_sents_worker = FileWorker(storage_path, 'concord_sentences_stage')
    db_matches_worker = FileWorker(storage_path, 'matches_stage')
    db_files_worker.start()
    db_sents_worker.start()
    match_convert_worker = ConverterFileWorker(storage_path, 'collocations_stage', db_matches_worker.q)
    match_convert_worker.start()
    db_matches_worker.start()
    with multiprocessing.Pool(njobs) as pool:
        pool.starmap(process_doc_files, ((doc_paths, db_files_worker.q, db_sents_worker.q, match_convert_worker.q)
                                         for doc_paths in chunks(glob(files_path, recursive=True), chunk_size)),
                     chunksize=100)
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


def post_process_db_files(storage_path: str, min_rel_freq: int = 3):
    """Post-processing of generated data files.

    Filter concordances that satisfy sentence form and remove duplicate sentences.
    Filter collocations with too little occurrences.
    Filter matches with respect to available concordances and collocations.
    """
    logging.info('REPLACE INDEX corpus files')
    corpus_file_idx = {}
    with open(os.path.join(storage_path, 'corpus_files_stage'), 'r') as files_in, open(
            os.path.join(storage_path, 'corpus_files'), 'w') as files_out:
        for c_i, line in enumerate(files_in):
            line = line.split('\t')
            corpus_file_idx[line[0]] = c_i
            files_out.write('\t'.join([str(c_i)] + line[1:]))
    logging.info('FILTER concordances')
    with open(os.path.join(storage_path, 'concord_sentences_stage'), 'r') as sents_in, open(
            os.path.join(storage_path, 'concord_sentences'),
            'w') as sents_out:
        sent_hashes = defaultdict(list)
        for item in sents_in:
            doc_id, sent_id, sentence, page = item.split('\t')
            doc_id = str(corpus_file_idx[doc_id])
            # checks whether sentence satisfies hard constraints
            if is_valid_sentence(sentence):
                sent_hash = hashlib.md5(sentence.encode()).hexdigest()
                # checks for duplicates based on sentence checksum (md5)
                if sent_hash not in sent_hashes[doc_id]:
                    sent_hashes[doc_id].append(sent_hash)
                    sents_out.write("\t".join([doc_id, sent_id, sentence, page]))
    logging.info('FILTER collocations')
    with open(os.path.join(storage_path, 'collocations_stage'), 'r') as rel_in, open(
            os.path.join(storage_path, 'collocations'), 'w') as rel_out:
        for line in rel_in:
            if int(line.split('\t')[-1]) >= min_rel_freq:
                rel_out.write(line)
    logging.info('FILTER matches')
    sents_idxs = {tuple(line.split('\t')[:2]) for line in open(os.path.join(storage_path, 'concord_sentences'), 'r')}
    rel_idxs = {int(line.split('\t')[0]) for line in open(os.path.join(storage_path, 'collocations'), 'r')}
    with open(os.path.join(storage_path, 'matches_stage'), 'r') as matches_in, open(
            os.path.join(storage_path, 'matches'), 'w') as matches_out:
        match_i = 0
        for line in matches_in:
            match = line.split('\t')
            match[6] = str(corpus_file_idx[match[6]])
            # check whether concordances and collocations still exist for match
            if int(match[0]) in rel_idxs and tuple(match[6:8]) in sents_idxs:
                match.insert(0, str(match_i))
                match_i += 1
                matches_out.write('\t'.join(match))
    logging.info('CHECK MWE')
    Match = namedtuple("Match",
                       ["id", "collocation_id", "head_surface", "dep_surface", "head_pos", "dep_pos", "prep_pos",
                        "doc_id", "sent_id", "timestamp"])
    match_dtypes = [int, int, str, str, int, int, int, int, int, str]
    Colloc = namedtuple("Collocation",
                        ["id", "label", "lemma1", "lemma2", "lemma1_tag", "lemma2_tag", "inv", "frequency"])
    colloc_dtypes = [int, str, str, str, str, str, int, int]

    def convert_line(line, cls, dtypes):
        return cls(*[dtype(col) for dtype, col in zip(dtypes, line.strip().split('\t'))])

    collocs = {}
    with open(os.path.join(storage_path, 'collocations'), "r") as fin:
        for line in fin:
            c = convert_line(line, Colloc, colloc_dtypes)
            collocs[c.id] = c

    with open(os.path.join(storage_path, 'matches'), "r") as fin:
        sent = []
        sent_curr = 0
        doc_curr = 0
        mwe_groups = defaultdict(list)
        for line in fin:
            m = convert_line(line, Match, match_dtypes)
            if m.doc_id == doc_curr and m.sent_id == sent_curr:
                sent.append(m)
            else:
                if len(sent) > 1:
                    for m_i, m1 in enumerate(sent):
                        for m2 in sent[m_i + 1:]:
                            if len({m1.head_pos, m2.head_pos, m1.dep_pos, m2.dep_pos}) == 3 and (
                                    m1.prep_pos == m2.prep_pos):
                                c1 = collocs[m1.collocation_id]
                                c2 = collocs[m2.collocation_id]
                                if len({m1.head_pos, m2.head_pos, m2.dep_pos}) == 2:
                                    # m2 - m1.dep_surface
                                    lemma = c1.lemma1 if c1.inv else c1.lemma2
                                    tag = c1.lemma1_tag if c1.inv else c1.lemma2_tag
                                    mwe_groups[(m2.collocation_id, m1.collocation_id, c1.label, lemma, tag)].append(
                                        (m2.id, m1.id))
                                if len({m1.dep_pos, m2.head_pos, m2.dep_pos}) == 2:
                                    # m2 - m1.head_surface
                                    lemma = c1.lemma2 if c1.inv else c1.lemma1
                                    tag = c1.lemma2_tag if c1.inv else c1.lemma1_tag
                                    mwe_groups[(m2.collocation_id, m1.collocation_id, c1.label, lemma, tag)].append(
                                        (m2.id, m1.id))
                                if len({m2.head_pos, m1.head_pos, m1.dep_pos}) == 2:
                                    # m1 - m2.dep_surface
                                    lemma = c2.lemma1 if c2.inv else c2.lemma2
                                    tag = c2.lemma1_tag if c2.inv else c2.lemma2_tag
                                    mwe_groups[(m1.collocation_id, m2.collocation_id, c2.label, lemma, tag)].append(
                                        (m1.id, m2.id))
                                if len({m2.dep_pos, m1.head_pos, m1.dep_pos}) == 2:
                                    # m1 - m2.head_surface
                                    lemma = c2.lemma2 if c2.inv else c2.lemma1
                                    tag = c2.lemma2_tag if c2.inv else c2.lemma1_tag
                                    mwe_groups[(m1.collocation_id, m2.collocation_id, c2.label, lemma, tag)].append(
                                        (m1.id, m2.id))
                sent = [m]
                doc_curr = m.doc_id
                sent_curr = m.sent_id

    with open(os.path.join(storage_path, 'mwe'), "w") as mwe_out, \
            open(os.path.join(storage_path, 'mwe_match'), "w") as mwe_map:
        for mwe_id, (mwe, mwe_matches) in enumerate(mwe_groups.items()):
            mwe_out.write("{}\n".format("\t".join(map(str, (mwe_id,) + mwe + (len(mwe_matches),)))))
            for m1_id, m2_id in mwe_matches:
                mwe_map.write("{}\n".format("\t".join(map(str, (mwe_id,) + (m1_id, m2_id)))))


def load_files_into_db(db_engine_key: str, storage_path: str):
    """Load generated data files into their corresponding db tables.
    """
    engine = create_engine(db_engine_key)
    for tb_name in ['corpus_files', 'concord_sentences', 'collocations', 'matches', 'mwe', 'mwe_match']:
        engine.execute("LOAD DATA LOCAL INFILE '{}' INTO TABLE {};".format(
            os.path.join(storage_path, tb_name),
            tb_name
        ))
        logging.info('LOADED {}'.format(tb_name))
