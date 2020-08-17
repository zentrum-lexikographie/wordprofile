#!/usr/bin/python3

import hashlib
import logging
import multiprocessing
import os
from collections import defaultdict, namedtuple
from glob import glob
from multiprocessing.queues import Queue
from typing import List, Dict, Tuple, Union, Iterator

import math
from sqlalchemy import create_engine

from pytabs.tabs import TabsSentence, TabsDocument
from wordprofile.datatypes import DBToken
from wordprofile.formatter import RE_HIT_DELIMITER
from wordprofile.utils import chunks
from wordprofile.wpse.db_tables import remove_invalid_chars
from wordprofile.wpse.prepare import prepare_corpus_file, prepare_concord_sentences, prepare_matches
from wordprofile.zdl import repair_lemma, SIMPLE_TAG_MAP, sentence_is_valid, extract_matches_from_doc

Match = namedtuple("Match",
                   ["id", "collocation_id", "head_surface", "dep_surface", "head_pos", "dep_pos", "prep_pos",
                    "doc_id", "sent_id"])
match_dtypes = [int, int, str, str, int, int, int, int, int]
Colloc = namedtuple("Collocation",
                    ["id", "label", "lemma1", "lemma2", "lemma1_tag", "lemma2_tag", "inv", "frequency"])
colloc_dtypes = [int, str, str, str, str, str, int, int]


def convert_line(line, cls, dtypes) -> Union[Match, Colloc]:
    return cls(*[dtype(col) for dtype, col in zip(dtypes, line.strip().split('\t'))])


def convert_sentence(sentence: TabsSentence) -> List[DBToken]:
    """Convert sentence into list of token while performing normalization and filtering.

    If tags are not found in mapping, they are left empty and recognized later.
    """

    def normalize_caps(t: DBToken) -> DBToken:
        return DBToken(idx=t.idx,
                       surface=t.surface.lower() if t.tag in ["VV", "ADJ", "ADV", "APP"] else t.surface,
                       lemma=t.lemma.lower() if t.tag in ["VV", "ADJ", "ADV", "APP"] else t.lemma,
                       tag=t.tag, head=t.head, rel=t.rel, misc=t.misc)

    return [normalize_caps(DBToken(
        idx=i,
        surface=remove_invalid_chars(surface),
        lemma=repair_lemma(remove_invalid_chars(lemma),
                           SIMPLE_TAG_MAP.get(xpos, '')),
        tag=SIMPLE_TAG_MAP.get(xpos, ''),
        head=head,
        rel=rel,
        misc=int(misc)
    )) for i, surface, lemma, tag, xpos, _, head, rel, _, misc in sentence.tokens]


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
                     chunksize=7)
    logging.info('INDICES DONE')
    logging.info('STOP first queues and wait...')
    db_files_worker.stop()
    db_sents_worker.stop()
    match_convert_worker.stop()
    db_files_worker.join()
    db_sents_worker.join()
    match_convert_worker.join()
    logging.info('STOP final matches queue and wait...')
    db_matches_worker.stop()
    db_matches_worker.join()
    logging.info('ALL JOBS DONE')


def reindex_corpus_files(fin: str, fout: str):
    """Iterates over generated corpus file in replaces mongodb index by numeric index.
    """
    corpus_file_idx = {}
    with open(fin, 'r') as files_in, open(fout, 'w') as files_out:
        for c_i, line in enumerate(files_in):
            line = line.split('\t')
            corpus_file_idx[line[0]] = c_i
            files_out.write('\t'.join([str(c_i)] + line[1:]))
    return corpus_file_idx


def reindex_filter_concordances(fin, fout, corpus_file_idx):
    """Filters and removes duplicates from concordances and replaces corpus file index.
    """
    sent_hashes = defaultdict(list)
    sents_idx = []
    with open(fin, 'r') as sents_in, open(fout, 'w') as sents_out:
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
                    sents_idx.append((doc_id, sent_id))
    return set(sents_idx)


def filter_matches(fin, fout, corpus_file_idx, sents_idx, collocs):
    """Filter matches with any missing entry for corpus file, sentence, or collocation.
    """
    match_i = 0
    with open(fin, 'r') as matches_in, open(fout, 'w') as matches_out:
        for line in matches_in:
            match = line.strip().split('\t')
            match[6] = str(corpus_file_idx[match[6]])
            # check whether concordances and collocations still exist for match
            if int(match[0]) in collocs and tuple(match[6:8]) in sents_idx:
                match.insert(0, str(match_i))
                match_i += 1
                matches_out.write('\t'.join(match) + '\n')


def compute_collocation_scores(fout, collocs):
    """Computes collocation statistics and writes to file.
    """
    f12 = defaultdict(lambda: defaultdict(int))
    f1 = defaultdict(lambda: defaultdict(int))
    f2 = defaultdict(int)
    for c_id, c in collocs.items():
        w1 = c.lemma1 + "-" + c.lemma1_tag
        w2 = c.lemma2 + "-" + c.lemma2_tag
        f12[c.label][(w1, w2)] += c.frequency
        f12[c.label][(w2, w1)] += c.frequency
        f1[c.label][w1] += c.frequency
        f1[c.label][w2] += c.frequency
        f2[w1] += c.frequency
        f2[w2] += c.frequency

    with open(fout, 'w') as fout:
        for c_id, c in collocs.items():
            w1 = c.lemma1 + "-" + c.lemma1_tag
            w2 = c.lemma2 + "-" + c.lemma2_tag
            log_dice = 14 + math.log2(2 * max(1, f12[c.label][(w1, w2)]) / (max(1, f1[c.label][w1]) + max(1, f2[w2])))
            fout.write("{c.id}\t{c.label}\t{c.lemma1}\t{c.lemma2}\t{c.lemma1_tag}\t{c.lemma2_tag}\t"
                       "{c.inv}\t{c.frequency}\t{score}\n".format(c=c, score=log_dice))
            if c.label in ['SUBJ', 'SUBJA', 'SUBJP', 'OBJ', 'OBJA', 'OBJD', 'PRED', 'ADV', 'ATTR', 'GMOD', 'PP', 'KOM']:
                fout.write("-{c.id}\t{c.label}\t{c.lemma2}\t{c.lemma1}\t{c.lemma2_tag}\t{c.lemma1_tag}\t"
                           "1\t{c.frequency}\t{score}\n".format(c=c, score=log_dice))


def extract_mwe_from_collocs(match_fin, collocs):
    """Compute MWE from matches and collocations.
    """

    def read_collapsed_sentence_matches(fin) -> Iterator[List[Match]]:
        """Reads the matches file and returns successively Matches per sentences.
        """
        sent = []
        sent_curr = 0
        doc_curr = 0
        with open(fin, "r") as fh:
            for line in fh:
                m = convert_line(line, Match, match_dtypes)
                if m.doc_id == doc_curr and m.sent_id == sent_curr:
                    sent.append(m)
                else:
                    yield sent
                    sent = [m]
                    doc_curr = m.doc_id
                    sent_curr = m.sent_id

    def has_one_overlap(*pos: Tuple[int]):
        """Checks whether positions have one overlap.
        """
        return len(set(pos)) == len(pos) - 1

    mwe_groups = defaultdict(list)
    for sent in read_collapsed_sentence_matches(match_fin):
        for m_i, m1 in enumerate(sent):
            for m2 in sent[m_i + 1:]:
                if has_one_overlap(m1.head_pos, m2.head_pos, m1.dep_pos, m2.dep_pos) and (m1.prep_pos == m2.prep_pos):
                    c1 = collocs[m1.collocation_id]
                    c2 = collocs[m2.collocation_id]
                    if has_one_overlap(m1.head_pos, m2.head_pos, m2.dep_pos):
                        # m2 - m1.dep_surface
                        lemma = c1.lemma1 if c1.inv else c1.lemma2
                        tag = c1.lemma1_tag if c1.inv else c1.lemma2_tag
                        mwe_groups[(m2.collocation_id, m1.collocation_id, c1.label, lemma, tag)].append(
                            (m2.id, m1.id))
                    if has_one_overlap(m1.dep_pos, m2.head_pos, m2.dep_pos):
                        # m2 - m1.head_surface
                        lemma = c1.lemma2 if c1.inv else c1.lemma1
                        tag = c1.lemma2_tag if c1.inv else c1.lemma1_tag
                        mwe_groups[(m2.collocation_id, m1.collocation_id, c1.label, lemma, tag)].append(
                            (m2.id, m1.id))
                    if has_one_overlap(m2.head_pos, m1.head_pos, m1.dep_pos):
                        # m1 - m2.dep_surface
                        lemma = c2.lemma1 if c2.inv else c2.lemma2
                        tag = c2.lemma1_tag if c2.inv else c2.lemma2_tag
                        mwe_groups[(m1.collocation_id, m2.collocation_id, c2.label, lemma, tag)].append(
                            (m1.id, m2.id))
                    if has_one_overlap(m2.dep_pos, m1.head_pos, m1.dep_pos):
                        # m1 - m2.head_surface
                        lemma = c2.lemma2 if c2.inv else c2.lemma1
                        tag = c2.lemma2_tag if c2.inv else c2.lemma1_tag
                        mwe_groups[(m1.collocation_id, m2.collocation_id, c2.label, lemma, tag)].append(
                            (m1.id, m2.id))
    return mwe_groups


def compute_mwe_scores(mwe_fout, match_fout, mwe_groups):
    """Calculates Log Dice score
    """
    f12 = defaultdict(lambda: defaultdict(int))
    f1 = defaultdict(lambda: defaultdict(int))
    f2 = defaultdict(int)
    for mwe_id, ((w1, w2, label, lemma, tag), mwe_matches) in enumerate(mwe_groups.items()):
        frequency = len(mwe_matches)
        f12[label][(w1, w2)] += frequency
        f12[label][(w2, w1)] += frequency
        f1[label][w1] += frequency
        f1[label][w2] += frequency
        f2[w1] += frequency
        f2[w2] += frequency

    with open(mwe_fout, "w") as mwe_out, open(match_fout, "w") as mwe_map:
        for mwe_id, (mwe, mwe_matches) in enumerate(mwe_groups.items()):
            mwe_freq = len(mwe_matches)
            w1, w2, label, lemma, tag = mwe
            log_dice = 14 + math.log2(2 * max(1, f12[label][(w1, w2)]) / (max(1, f1[label][w1]) + max(1, f2[w2])))
            mwe_out.write("{}\n".format("\t".join(map(str, (mwe_id,) + mwe + (mwe_freq, log_dice)))))
            for m1_id, m2_id in mwe_matches:
                mwe_map.write("{}\n".format("\t".join(map(str, (mwe_id,) + (m1_id, m2_id)))))


def load_collocations(fin, min_rel_freq=3) -> Dict[int, Colloc]:
    """Load collocations from file and filter by frequency limit.
    """
    collocs = {}
    with open(fin, "r") as fin:
        for line in fin:
            c = convert_line(line, Colloc, colloc_dtypes)
            if c.frequency >= min_rel_freq:
                collocs[c.id] = c
    return collocs


def post_process_db_files(storage_path, min_rel_freq=3):
    """Post-processing of generated data files.

    Filter concordances that satisfy sentence form and remove duplicate sentences.
    Filter collocations with too little occurrences.
    Filter matches with respect to available concordances and collocations.
    """
    logging.info('REPLACE INDEX corpus files')
    corpus_file_idx = reindex_corpus_files(os.path.join(storage_path, 'corpus_files_stage'),
                                           os.path.join(storage_path, 'corpus_files'))
    logging.info('FILTER concordances')
    sents_idx = reindex_filter_concordances(os.path.join(storage_path, 'concord_sentences_stage'),
                                            os.path.join(storage_path, 'concord_sentences'), corpus_file_idx)
    logging.info('LOAD FILTERED collocations')
    collocs = load_collocations(os.path.join(storage_path, 'collocations_stage'), min_rel_freq)
    logging.info('FILTER matches')
    filter_matches(os.path.join(storage_path, 'matches_stage'), os.path.join(storage_path, 'matches'), corpus_file_idx,
                   sents_idx, collocs)
    logging.info('CALCULATE AND WRITE log dice scores')
    compute_collocation_scores(os.path.join(storage_path, 'collocations'), collocs)
    logging.info('MAKE MWE LVL 1')
    mwe_groups = extract_mwe_from_collocs(os.path.join(storage_path, 'matches'), collocs)
    logging.info('CALCULATE log dice mwe lvl 1')
    compute_mwe_scores(os.path.join(storage_path, 'mwe'), os.path.join(storage_path, 'mwe_match'), mwe_groups)


def load_files_into_db(db_engine_key, storage_path):
    """Load generated data files into their corresponding db tables.
    """
    engine = create_engine(db_engine_key)
    for tb_name in ['corpus_files', 'concord_sentences', 'collocations', 'matches', 'mwe', 'mwe_match']:
        engine.execute("LOAD DATA LOCAL INFILE '{}' INTO TABLE {};".format(
            os.path.join(storage_path, tb_name),
            tb_name
        ))
        logging.info('LOADED {}'.format(tb_name))
