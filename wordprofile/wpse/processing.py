import hashlib
import logging
import math
import multiprocessing
import os
import re
import sys
import traceback
from collections import defaultdict, namedtuple
from multiprocessing.queues import Queue
from typing import List, Dict, Tuple, Union, Iterator, Set

import conllu
from conllu.models import TokenList

from wordprofile.datatypes import DBToken
from wordprofile.formatter import RE_HIT_DELIMITER2
from wordprofile.wpse.db_tables import remove_invalid_chars
from wordprofile.wpse.prepare import prepare_corpus_file, prepare_concord_sentences, prepare_matches
from wordprofile.zdl import repair_lemma, sentence_is_valid, extract_matches_from_doc

Match = namedtuple("Match",
                   ["id", "collocation_id", "head_surface", "dep_surface", "head_pos", "dep_pos", "prep_pos",
                    "doc_id", "sent_id"])
match_dtypes = [int, int, str, str, int, int, int, int, int]
Colloc = namedtuple("Colloc",
                    ["id", "label", "lemma1", "lemma2", "lemma1_tag", "lemma2_tag", "inv", "frequency"])
colloc_dtypes = [int, str, str, str, str, str, int, int]


def convert_line(line, cls, dtypes) -> Union[Match, Colloc]:
    return cls(*[dtype(col) for dtype, col in zip(dtypes, line.strip().split('\t'))])


def convert_sentence(sentence: TokenList) -> List[DBToken]:
    """Convert sentence into list of token while performing normalization and filtering.

    If tags are not found in mapping, they are left empty and recognized later.
    """

    def case_by_tag(w: str, tag: str) -> str:
        if tag in {"VERB", "ADJ", "ADV", "ADP", "AUX"}:
            return w.lower()
        elif tag == "NOUN":
            return w[0].upper() + w[1:]
        else:
            return w

    def normalize_caps(t: DBToken) -> DBToken:
        return DBToken(idx=t.idx,
                       surface=t.surface,
                       lemma=case_by_tag(t.lemma, t.tag),
                       tag=t.tag, head=t.head, rel=t.rel, misc=t.misc)

    return [normalize_caps(DBToken(
        idx=token['id'],
        surface=remove_invalid_chars(token['form']),
        lemma=repair_lemma(remove_invalid_chars(token['lemma']), token['upos']),
        tag=token['upos'],
        head=token['head'],
        rel=token['deprel'],
        misc=token['misc'].get('SpaceAfter') == 'No'
    )) for token in sentence]


class FileWorker(multiprocessing.Process):
    def __init__(self, path, fname, flush_limit=100):
        self.q = multiprocessing.Manager().Queue(maxsize=1000)
        self.path = path
        self.fname = fname
        self.flush_limit = flush_limit
        super().__init__()

    def run(self):
        logging.info('INIT queue, wait for jobs')
        flush_ctr = 0
        with open(os.path.join(self.path, self.fname), 'w') as fh:
            while True:
                db_batch = self.q.get()
                if db_batch is None:
                    logging.info('{:10} - CLOSE queue'.format(self.fname))
                    break
                try:
                    items = ["\t".join(map(str, x)) + "\n" for x in db_batch]
                    fh.writelines(items)
                    flush_ctr += 1
                    if flush_ctr >= self.flush_limit:
                        fh.flush()
                        flush_ctr = 0
                except Exception as e:
                    logging.warning(e)

    def stop(self):
        self.q.put(None)


class FileReader:
    def __init__(self, path, q_size=100):
        self.q = multiprocessing.Manager().Queue(maxsize=q_size)
        if path == "-":
            self.fh = sys.stdin
        else:
            self.fh = open(path)
        super().__init__()

    def run(self):
        logging.info(f'INIT queue, reading file')
        conll_sentences = conllu.parse_incr(self.fh, fields=conllu.parser.DEFAULT_FIELDS)
        doc = []
        for sent in conll_sentences:
            if "DDC:meta.file_" in sent.metadata:
                if doc:
                    self.q.put(doc)
                doc = []
            doc.append(sent)
        self.q.put(doc)

    def stop(self, n_procs: int):
        for _ in range(n_procs):
            self.q.put(None)


def process_doc_file(file_reader_queue: Queue, db_files_queue: Queue, db_sents_queue: Queue, db_matches_queue: Queue):
    """Extracts information from files and forwards to corresponding queue.
    """
    while True:
        sentences: TokenList = file_reader_queue.get()
        if not sentences:
            break
        try:
            doc_id, db_corpus_file = prepare_corpus_file(sentences[0].metadata)
            parses = list(filter(sentence_is_valid, map(convert_sentence, sentences)))
            db_concord_sentences = prepare_concord_sentences(doc_id, parses)
            matches = extract_matches_from_doc(parses)
            db_matches = prepare_matches(doc_id, matches)
            db_files_queue.put([db_corpus_file])
            db_sents_queue.put(db_concord_sentences)
            db_matches_queue.put(db_matches)
        except TypeError:
            logging.warning("Type Conversion Error: invalid sentence parse")
        except Exception as e:
            logging.warning(e)
            logging.warning(traceback.format_exc())


def is_valid_sentence(sentence: str):
    """Hard constraints for concordances.

    End with sentence delimiter, have a certain length, and start with uppercase letter.
    """
    s = RE_HIT_DELIMITER2.split(sentence.strip('\x01\x02'))
    return s[-1] in '.!?\'"' and 8 <= len(s) <= 25 and s[0][0].isupper()


def process_files(file_path: str, storage_path: str, njobs: int = 1):
    """Extract WP related information from given files.

    This method processed a given list of files in parallel.
    Workers are created for each result (corpus_files, concordances, matches, collocations) in relation to db tables.
    The file list is split into several chunks for parallel processing. The extracted results are sent to the workers.
    """
    file_reader = FileReader(file_path, q_size=2 * njobs)
    db_files_worker = FileWorker(storage_path, 'corpus_files')
    db_sents_worker = FileWorker(storage_path, 'concord_sentences', flush_limit=1000)
    db_matches_worker = FileWorker(storage_path, 'matches', flush_limit=10000)
    db_files_worker.start()
    db_sents_worker.start()
    db_matches_worker.start()
    pool = []
    for i in range(njobs):
        p = multiprocessing.Process(target=process_doc_file,
                                    args=(file_reader.q, db_files_worker.q, db_sents_worker.q, db_matches_worker.q))
        p.start()
        pool.append(p)
    file_reader.run()
    logging.info('STOP file reader queue...')
    file_reader.stop(njobs)
    logging.info('JOIN processes...')
    for p in pool:
        p.join()
    logging.info('STOP first queues and wait...')
    db_files_worker.stop()
    db_sents_worker.stop()
    db_files_worker.join()
    db_sents_worker.join()
    logging.info('STOP final matches queue and wait...')
    db_matches_worker.stop()
    db_matches_worker.join()
    logging.info('ALL JOBS DONE')


def reindex_corpus_files(fins: List[str], fout: str) -> Dict[str, int]:
    """Iterates over generated corpus file in replaces mongodb index by numeric index.
    """
    corpus_file_idx = {}
    c_i = 0
    with open(fout, 'w') as files_out:
        for fin in fins:
            with open(fin, 'r') as files_in:
                for line in files_in:
                    line = line.split('\t')
                    corpus_file_idx[line[0]] = c_i
                    files_out.write('\t'.join([str(c_i)] + line[1:]))
                    c_i += 1
    return corpus_file_idx


def reindex_filter_concordances(fins, fout, corpus_file_idx, fout_invalid, fout_duplicate) -> Set[Tuple[str, str]]:
    """Filters and removes duplicates from concordances and replaces corpus file index.
    """

    def get_robust_hash(sentence: str):
        """Generates an md5 sentence hash.
        The sentence string is lowered and all symbols except letters are removed for robustness.
        """
        sentence = re.sub(r"[^a-z]", "", sentence.lower())
        return hashlib.md5(sentence.encode()).hexdigest()

    sent_hashes = set()
    sents_idx = []
    with open(fout, 'w') as sents_out, open(fout_invalid, 'w') as invalids_out, open(fout_duplicate, 'w') as dups_out:
        for fin in fins:
            logging.info(f"- {fin}")
            with open(fin, 'r') as sents_in:
                for item in sents_in:
                    doc_corpus, sent_id, sentence, page = item.split('\t')
                    doc_id = str(corpus_file_idx[doc_corpus])
                    # checks whether sentence satisfies hard constraints
                    if is_valid_sentence(sentence):
                        sent_hash = get_robust_hash(sentence)
                        # checks for duplicates based on sentence checksum (md5)
                        if sent_hash not in sent_hashes:
                            sent_hashes.add(sent_hash)
                            sents_out.write("\t".join([doc_id, sent_id, sentence, page]))
                            sents_idx.append((doc_id, sent_id))
                        else:
                            dups_out.write("\t".join([doc_corpus, sent_id, sentence, page]))
                    else:
                        invalids_out.write("\t".join([doc_corpus, sent_id, sentence, page]))
    return set(sents_idx)


def filter_transform_matches(fins: List[str], fout: str, corpus_file_idx, sents_idx, collocs: Dict[int, Colloc]):
    """Filter matches with any missing entry for corpus file, sentence, or collocation,
    then transform using collocation id.
    """
    relation_dict = dict()
    for c in collocs.values():
        relation_dict['-'.join([c.label, c.lemma1, c.lemma2, c.lemma1_tag, c.lemma2_tag])] = c.id

    match_i = 0
    with open(fout, 'w') as matches_out:
        for fin in fins:
            logging.info(f"- {fin}")
            with open(fin, 'r') as matches_in:
                for line in matches_in:
                    match = line.strip().split('\t')
                    colloc_val = '-'.join(match[:5])
                    match[10] = str(corpus_file_idx[match[10]])
                    # check whether concordances and collocations still exist for match
                    colloc_id = relation_dict.get(colloc_val)
                    if colloc_id and tuple(match[10:12]) in sents_idx:
                        match = [str(match_i), str(colloc_id)] + match[5:]
                        matches_out.write('\t'.join(match) + '\n')
                        match_i += 1


def compute_collocation_scores(fout: str, collocs: Dict[int, Colloc]):
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
        inv_relations = {'SUBJ', 'SUBJA', 'SUBJP', 'OBJ', 'OBJA', 'OBJD', 'PRED', 'ADV', 'ATTR', 'GMOD', 'PP', 'KOM'}
        for c_id, c in collocs.items():
            w1 = c.lemma1 + "-" + c.lemma1_tag
            w2 = c.lemma2 + "-" + c.lemma2_tag
            log_dice = 14 + math.log2(2 * max(1, f12[c.label][(w1, w2)]) / (max(1, f1[c.label][w1]) + max(1, f2[w2])))
            fout.write("{c.id}\t{c.label}\t{c.lemma1}\t{c.lemma2}\t{c.lemma1_tag}\t{c.lemma2_tag}\t"
                       "{c.inv}\t{c.frequency}\t{score}\n".format(c=c, score=log_dice))
            if c.label in inv_relations:
                fout.write("-{c.id}\t{c.label}\t{c.lemma2}\t{c.lemma1}\t{c.lemma2_tag}\t{c.lemma1_tag}\t"
                           "1\t{c.frequency}\t{score}\n".format(c=c, score=log_dice))


def extract_mwe_from_collocs(match_fin: str, collocs: Dict[int, Colloc]):
    """Compute MWE from matches and collocations.
    """

    def read_collapsed_sentence_matches(fin: str) -> Iterator[List[Match]]:
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
        return len(set(pos)) == (len(pos) - 1)

    mwe_groups = defaultdict(list)
    for sent in read_collapsed_sentence_matches(match_fin):
        for m_i, m1 in enumerate(sent):
            for m2 in sent[m_i + 1:]:
                if has_one_overlap(m1.head_pos, m2.head_pos, m1.dep_pos, m2.dep_pos) and (m1.prep_pos == m2.prep_pos):
                    if not (m1.collocation_id in collocs and m2.collocation_id in collocs):
                        continue
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


def compute_mwe_scores(mwe_fout: str, match_fout: str, mwe_groups: Dict[Tuple, List[Tuple[int,int]]]):
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


def extract_collocations(match_fin: str, collocs_fout: str):
    """Iterates over all extracted matches and generates a collocation mapping.

    Collocations contain only lemmatized match information and, additionally, frequencies are counted for matches.
    The mapping is written to a file and used later for simplifying the matches information.
    """
    relation_dict = defaultdict(lambda: defaultdict(int))
    with open(match_fin, "r") as fin:
        for line in fin:
            m = tuple(line.strip().split('\t'))
            rel, lemma1, lemma2, tag1, tag2 = m[0:5]
            relation_dict[rel][lemma1, lemma2, tag1, tag2] += 1

    with open(collocs_fout, 'w') as fh:
        for rel, cols_dict in relation_dict.items():
            for (lemma1, lemma2, tag1, tag2), freq in cols_dict.items():
                fh.write(f'{rel}\t{lemma1}\t{tag1}\t{lemma2}\t{tag2}\t{freq}\n')


def extract_most_common_surface(match_fin: str, fout: str):
    """Iterates over all extracted matches and generates a mapping from a lemma to its most common surface form.
    """
    common_surfaces = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    with open(match_fin, "r") as fin:
        for line in fin:
            m = tuple(line.strip().split('\t'))
            rel, lemma1, lemma2, tag1, tag2, form1, form2 = m[:7]
            common_surfaces[tag1][lemma1][form1] += 1
            common_surfaces[tag2][lemma2][form2] += 1

    with open(fout, 'w') as fh:
        for tag in common_surfaces:
            for lemma in common_surfaces[tag]:
                surface, freq = sorted(common_surfaces[tag][lemma].items(), key=lambda x: x[1], reverse=True)[0]
                fh.write(f'{lemma}\t{tag}\t{surface}\t{freq}\n')


def load_collocations(fins: List[str], min_rel_freq: int = 3) -> Dict[int, Colloc]:
    """Load collocations from file and filter by frequency limit.
    """
    relation_dict = defaultdict(lambda: defaultdict(int))
    for fin in fins:
        with open(fin, "r") as fin:
            for line in fin:
                m = tuple(line.strip().split('\t'))
                rel, (lemma1, tag1, lemma2, tag2), freq = m[0], m[1:5], int(m[5])
                if freq >= min_rel_freq:
                    relation_dict[rel][(lemma1, lemma2, tag1, tag2)] += freq
    collocs = {}
    c_id = 0
    for rel, cols_dict in relation_dict.items():
        for (lemma1, lemma2, tag1, tag2), freq in cols_dict.items():
            collocs[c_id] = Colloc(c_id, rel, lemma1, lemma2, tag1, tag2, 0, freq)
            c_id += 1
    return collocs


def compute_token_statistics(fins: List[str], fout: str, collocs: Dict[int, Colloc]):
    logging.info("-- compute token frequencies")
    tokens_stats = defaultdict(int)
    for c in collocs.values():
        tokens_stats[c.lemma1, c.lemma1_tag] += c.frequency
        tokens_stats[c.lemma2, c.lemma2_tag] += c.frequency
    logging.info("-- compute common surfaces")
    common_surfaces = {}
    for fin in fins:
        with open(fin, "r") as fin:
            for line in fin:
                lemma, tag, surface, freq = tuple(line.strip().split('\t'))
                common_surface, common_freq = common_surfaces.get((lemma, tag), ('', 0))
                if int(freq) > common_freq:
                    common_surfaces[lemma, tag] = surface, freq
    logging.info("-- write token stats with common surfaces")
    with open(fout, 'w') as fh:
        for (lemma, tag), freq in tokens_stats.items():
            surface, surface_freq = common_surfaces[lemma, tag]
            fh.write(f'{lemma}\t{tag}\t{freq}\t{surface}\t{surface_freq}\n')


def post_process_db_files(storage_paths, final_path, min_rel_freq=3, with_mwe=False):
    """Post-processing of generated data files.

    Filter concordances that satisfy sentence form and remove duplicate sentences.
    Filter collocations with too little occurrences.
    Filter matches with respect to available concordances and collocations.
    """
    logging.info('REPLACE INDEX corpus files')
    corpus_file_idx = reindex_corpus_files([os.path.join(p, 'corpus_files') for p in storage_paths],
                                           os.path.join(final_path, 'corpus_files'))
    logging.info('FILTER concordances')
    sents_idx = reindex_filter_concordances([os.path.join(p, 'concord_sentences') for p in storage_paths],
                                            os.path.join(final_path, 'concord_sentences'), corpus_file_idx,
                                            os.path.join(final_path, 'concord_sentences.invalid'),
                                            os.path.join(final_path, 'concord_sentences.duplicate'))
    logging.info('LOAD FILTERED collocations')
    collocs = load_collocations([os.path.join(p, 'collocations') for p in storage_paths], min_rel_freq)
    logging.info('CALCULATE token statistics')
    compute_token_statistics([os.path.join(p, 'common_surfaces') for p in storage_paths],
                             os.path.join(final_path, 'token_freqs'), collocs)
    logging.info('FILTER TRANSFORM matches')
    filter_transform_matches([os.path.join(p, 'matches') for p in storage_paths], os.path.join(final_path, 'matches'),
                             corpus_file_idx, sents_idx, collocs)
    logging.info('CALCULATE AND WRITE log dice scores')
    compute_collocation_scores(os.path.join(final_path, 'collocations'), collocs)
    if with_mwe:
        logging.info('MAKE MWE LVL 1')
        mwe_groups = extract_mwe_from_collocs(os.path.join(final_path, 'matches'), collocs)
        logging.info('CALCULATE log dice mwe lvl 1')
        compute_mwe_scores(os.path.join(final_path, 'mwe'), os.path.join(final_path, 'mwe_match'), mwe_groups)


def load_files_into_db(engine, storage_path):
    """Load generated data files into their corresponding db tables.
    """
    for tb_name in ['corpus_files', 'concord_sentences', 'collocations', 'token_freqs', 'matches', 'mwe', 'mwe_match']:
        tb_file = os.path.join(storage_path, tb_name)
        if not os.path.exists(tb_file):
            logging.warning(f"Local file '{tb_file}' doe not exist.")
        else:
            logging.info('LOAD DATA FILE: {}'.format(tb_name))
            engine.execute("LOAD DATA LOCAL INFILE '{}' INTO TABLE {};".format(tb_file, tb_name))
