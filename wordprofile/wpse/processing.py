from __future__ import annotations

import hashlib
import logging
import math
import multiprocessing
import os
import re
import sys
from collections import Counter, defaultdict
from collections.abc import Callable, Iterator
from multiprocessing.queues import Queue
from typing import Any, Protocol, Union

import conllu
from conllu.models import Token, TokenList
from sqlalchemy import Connection, text

from wordprofile.datatypes import Colloc, CollocInstance, DBMatch, WPToken
from wordprofile.sentence_filter import (
    extract_matches_from_doc,
    remove_invalid_chars,
    repair_lemma,
    sentence_is_valid,
)
from wordprofile.wpse.prepare import (
    prepare_concord_sentences,
    prepare_corpus_file,
    prepare_matches,
)

logger = logging.getLogger(__name__)

COLLOC_INSTANCE_DTYPES = [int, int, str, str, int, int, str, int, int]


def convert_line(
    line: str, cls: Callable, dtypes: list[type]
) -> Union[CollocInstance, Colloc]:
    return cls(*[dtype(col) for dtype, col in zip(dtypes, line.strip().split("\t"))])


def convert_sentence(sentence: TokenList) -> list[WPToken]:
    """Convert sentence into list of token.

    Sentences are normalized and filtered during this process.
    If tags are not found in mapping, they are left empty.
    """

    prepositional_contract_map: dict[str, str] = {
        "am": "an",
        "aufs": "auf",
        "ans": "an",
        "beim": "bei",
        "fürs": "für",
        "im": "in",
        "ins": "in",
        "hinters": "hinter",
        "hinterm": "hinter",
        "ums": "um",
        "übers": "über",
        "überm": "über",
        "unterm": "unter",
        "unters": "unter",
        "untern": "unter",
        "vom": "von",
        "vorm": "vor",
        "vors": "vor",
        "zum": "zu",
        "zur": "zu",
    }

    def case_by_tag(w: str, tag: str) -> str:
        if tag in {"VERB", "ADJ", "ADV", "AUX"}:
            return w.lower()
        elif tag == "ADP":
            w = w.lower()
            return prepositional_contract_map.get(w, w)
        elif tag == "NOUN":
            return w[0].upper() + w[1:]
        else:
            return w

    def normalize_caps(t: WPToken) -> WPToken:
        return WPToken(
            idx=t.idx,
            surface=t.surface,
            lemma=case_by_tag(t.lemma, t.tag),
            tag=t.tag,
            head=t.head,
            rel=t.rel,
            misc=t.misc,
            morph=t.morph,
        )

    # this can *probably* be removed since spacy only returns "PROPN" anyway
    def entity_tag_conversion(token: Token) -> str:
        if token["misc"] and "NER" in token["misc"]:
            ner_tag = token["misc"]["NER"]
            if (
                ner_tag.endswith("PER")
                or ner_tag.endswith("LOC")
                or ner_tag.endswith("ORG")
            ):
                return "PROPN"
        return token["upos"]

    return collapse_phrasal_verbs(
        [
            normalize_caps(
                WPToken(
                    idx=token["id"],
                    surface=remove_invalid_chars(token["form"]),
                    # TODO remove lemma repair call
                    # ==> lemma=remove_invalid_chars(token['lemma']),
                    lemma=repair_lemma(
                        remove_invalid_chars(token["lemma"]), token["upos"]
                    ),
                    tag=entity_tag_conversion(token),
                    head=token["head"],
                    rel=token["deprel"],
                    misc=(
                        token["misc"].get("SpaceAfter") == "No"
                        if token["misc"]
                        else False
                    ),
                    morph=token.get("feats", None),
                )
            )
            for token in sentence
        ]
    )


def collapse_phrasal_verbs(sentence: list[WPToken]) -> list[WPToken]:
    for token in sentence:
        if token.surface == "recht":
            continue
        if token.rel == "compound:prt" and token.tag in {"ADP", "ADJ", "ADV"}:
            head = sentence[token.head - 1]
            if head.tag in {"VERB", "AUX"}:
                if head.lemma == "sein":
                    continue
                head.prt_pos = token.idx
                head.lemma = repair_lemma(f"{token.surface}{head.lemma}", "VERB")
    return sentence


class FileReaderQueue(Protocol):
    def get(self) -> Any:
        ...

    def put(self, item: Any) -> None:
        ...


class LemmaCounter:
    def __init__(self) -> None:
        self.freqs: Counter[str] = Counter()

    def count_token(self, parses: list[list[WPToken]]) -> None:
        lemmata = [
            "\t".join((tok.lemma, tok.tag))
            for sent in parses
            for tok in sent
            if tok.tag
            not in {
                "ADP",
                "PUNCT",
                "PRON",
                "DET",
                "CCONJ",
                "X",
                "SCONJ",
                "NUM",
                "PART",
                "INTJ",
                "PROPN",
            }
        ]
        self.freqs += Counter(lemmata)


class FileWorker(multiprocessing.Process):
    def __init__(
        self,
        path: str,
        fname: str,
        manager: multiprocessing.managers.SyncManager,
        flush_limit: int = 100,
    ) -> None:
        self.q = manager.Queue(maxsize=1000)
        self.path = path
        self.fname = fname
        self.flush_limit = flush_limit
        super().__init__()

    def run(self) -> None:
        logger.info("INIT queue, wait for jobs")
        flush_ctr = 0
        with open(os.path.join(self.path, self.fname), "w") as fh:
            while True:
                db_batch = self.q.get()
                if db_batch is None:
                    logger.info("{:10} - CLOSE queue".format(self.fname))
                    break
                try:
                    items = ["\t".join(map(str, x)) + "\n" for x in db_batch]
                    fh.writelines(items)
                    flush_ctr += 1
                    if flush_ctr >= self.flush_limit:
                        fh.flush()
                        flush_ctr = 0
                except Exception as e:
                    logger.exception(e)

    def stop(self) -> None:
        self.q.put(None)


class FileReader:
    def __init__(self, paths: list[str], queue: FileReaderQueue) -> None:
        self.q = queue
        self.paths = paths

    def _process_content(self, file_handle) -> None:
        conll_sentences = conllu.parse_incr(
            file_handle, fields=conllu.parser.DEFAULT_FIELDS
        )
        doc: list[TokenList] = []
        for sent in conll_sentences:
            if "DDC:meta.file_" in sent.metadata:
                if doc:
                    self.q.put(doc)
                doc = []
            doc.append(sent)
        self.q.put(doc)

    def run(self) -> None:
        logger.info("INIT queue, reading files")
        for file in self.paths:
            if file == "-":
                self._process_content(sys.stdin)
            else:
                with open(file, "r", encoding="utf-8") as fh:
                    self._process_content(fh)

    def stop(self, n_procs: int) -> None:
        for _ in range(n_procs):
            self.q.put(None)


def process_doc_file(
    file_reader_queue: Queue,
    db_files_queue: Queue,
    db_sents_queue: Queue,
    db_matches_queue: Queue,
    lemma_counters: multiprocessing.managers.ListProxy,
) -> None:
    """Extracts information from files and forwards to corresponding queue."""
    counter = LemmaCounter()
    while True:
        sentences: list[TokenList] = file_reader_queue.get()
        if not sentences:
            lemma_counters.append(counter)
            break
        try:
            doc_id, db_corpus_file = prepare_corpus_file(sentences[0].metadata)
            parses = list(filter(sentence_is_valid, map(convert_sentence, sentences)))
            db_concord_sentences = prepare_concord_sentences(doc_id, parses)
            counter.count_token(parses)
            matches = extract_matches_from_doc(parses)
            db_matches = prepare_matches(doc_id, matches)
            db_files_queue.put([db_corpus_file])
            db_sents_queue.put(db_concord_sentences)
            db_matches_queue.put(db_matches)
        except TypeError:
            logger.exception(
                "Type Conversion Error: invalid sentence parse in document: %s"
                % sentences[0].metadata.get("DDC:meta.file_")
            )
        except Exception:
            logger.exception(
                "Couldn't process document: %s"
                % sentences[0].metadata.get("DDC:meta.file_")
            )


def process_files(file_path: list[str], storage_path: str, njobs: int = 1) -> None:
    """Extract WP related information from given files.

    This method processes a given list of files in parallel.
    Workers are created for each result (corpus_files, concordances,
    matches, collocations) in relation to db tables. The file list is
    split into several chunks for parallel processing. The extracted
    results are sent to the workers.
    """
    mp_manager = multiprocessing.Manager()
    fr_queue = mp_manager.Queue(maxsize=2 * njobs)
    file_reader = FileReader(file_path, fr_queue)
    db_files_worker = FileWorker(storage_path, "corpus_files", mp_manager)
    db_sents_worker = FileWorker(
        storage_path, "concord_sentences", mp_manager, flush_limit=1000
    )
    db_matches_worker = FileWorker(
        storage_path, "matches", mp_manager, flush_limit=10000
    )
    db_files_worker.start()
    db_sents_worker.start()
    db_matches_worker.start()
    pool = []
    lemma_counters = mp_manager.list()
    for i in range(njobs):
        p = multiprocessing.Process(
            target=process_doc_file,
            args=(
                file_reader.q,
                db_files_worker.q,
                db_sents_worker.q,
                db_matches_worker.q,
                lemma_counters,
            ),
        )
        p.start()
        pool.append(p)
    file_reader.run()
    logger.info("STOP file reader queue...")
    file_reader.stop(njobs)
    logger.info("JOIN processes...")
    for p in pool:
        p.join()
    logger.info("STOP first queues and wait...")
    db_files_worker.stop()
    db_sents_worker.stop()
    db_files_worker.join()
    db_sents_worker.join()
    logger.info("STOP final matches queue and wait...")
    db_matches_worker.stop()
    db_matches_worker.join()
    logger.info("ALL JOBS DONE")
    save_lemma_counts_to_file(lemma_counters, storage_path)


def save_lemma_counts_to_file(
    lemma_counters: multiprocessing.managers.ListProxy,
    output_path: str,
) -> None:
    total: Counter[str] = Counter()
    for counter in lemma_counters:
        total += counter.freqs
    with open(os.path.join(output_path, "lemma_freqs"), "w") as fh:
        for lemma, freq in total.items():
            print("\t".join([lemma, str(freq)]), file=fh)


def reindex_corpus_files(fins: list[str], fout: str) -> dict[str, int]:
    """Iterates over generated corpus file and replaces index by numeric index."""
    corpus_file_idx = {}
    c_i = 0
    with open(fout, "w") as files_out:
        for fin in fins:
            with open(fin, "r") as files_in:
                for line in files_in:
                    tokens = line.split("\t")
                    corpus_file_idx[tokens[0]] = c_i
                    files_out.write("\t".join([str(c_i)] + tokens[1:]))
                    c_i += 1
    return corpus_file_idx


def reindex_concordances(
    fins: list[str],
    fout: str,
    corpus_file_idx: dict[str, int],
    fout_duplicate: str,
) -> set[tuple[str, str]]:
    """
    Filters and removes duplicates from concordances and replaces corpus
    file index.
    """

    def get_robust_hash(sentence: str) -> str:
        """Generates an md5 sentence hash.
        The sentence string is converted to lowercase and all symbols
        except letters are removed for robustness.
        """
        sentence = re.sub(r"[^a-z]", "", sentence.lower())
        return hashlib.md5(sentence.encode()).hexdigest()

    sent_hashes = set()
    sents_idx = []
    with open(fout, "w") as sents_out, open(fout_duplicate, "w") as dups_out:
        for fin in fins:
            logger.info("- %s" % fin)
            with open(fin, "r") as sents_in:
                for item in sents_in:
                    doc_corpus, sent_id, sentence = item.split("\t")
                    doc_id = str(corpus_file_idx[doc_corpus])
                    sent_hash = get_robust_hash(sentence)
                    # checks for duplicates based on sentence checksum (md5)
                    if sent_hash not in sent_hashes:
                        sent_hashes.add(sent_hash)
                        sents_out.write("\t".join([doc_id, sent_id, sentence]))
                        sents_idx.append((doc_id, sent_id))
                    else:
                        dups_out.write("\t".join([doc_corpus, sent_id, sentence]))
    return set(sents_idx)


def filter_transform_matches(
    fins: list[str],
    fout: str,
    corpus_file_idx: dict[str, int],
    sents_idx: set[tuple[str, str]],
    collocs: dict[int, Colloc],
) -> set[tuple[str, str]]:
    """
    Filter matches with any missing entry for corpus file, sentence,
    or collocation, then transform using collocation id.
    """
    relation_dict = dict()
    for c in collocs.values():
        relation_dict[
            "-".join([c.label, c.lemma1, c.lemma2, c.lemma1_tag, c.lemma2_tag, c.prep])
        ] = c.id

    valid_sentence_ids = set()
    match_i = 0
    with open(fout, "w") as matches_out:
        for fin in fins:
            logger.info("- %s" % fin)
            with open(fin, "r") as matches_in:
                for line in matches_in:
                    match = DBMatch.fromline(line)
                    match.corpus_file_id = str(corpus_file_idx[match.corpus_file_id])
                    # check whether concordances and collocations still exist for match
                    colloc_id = relation_dict.get(match.get_collocation_key())
                    if colloc_id is None:
                        continue
                    sentence_id = (match.corpus_file_id, str(match.sentence_id))
                    if sentence_id in sents_idx:
                        matches_out.write(
                            match.convert_to_database_entry(match_i, colloc_id) + "\n"
                        )
                        match_i += 1
                        valid_sentence_ids.add(sentence_id)
    return valid_sentence_ids


def compute_collocation_scores(
    fout: str,
    collocs: dict[int, Colloc],
    lemma_freqs: defaultdict[tuple[str, str], int],
) -> set[int]:
    """
    Computes logDice values and writes collocations to file.

    Collocations with negative logDice are not written to the final file
    but instead their ids are collected and returned.
    """
    with open(fout, "w") as f_out:
        inv_relations = {
            "SUBJA",
            "SUBJP",
            "OBJ",
            "OBJO",
            "PRED",
            "ADV",
            "ATTR",
            "GMOD",
            "PP",
            "KOM",
        }
        invalid_ids = set()
        for c_id, c in collocs.items():
            log_dice = 14 + math.log2(
                2
                * max(1, c.frequency)
                / (
                    max(1, lemma_freqs[(c.lemma1, c.lemma1_tag)])
                    + max(1, lemma_freqs[(c.lemma2, c.lemma2_tag)])
                )
            )
            if log_dice < 0:
                invalid_ids.add(c_id)
                continue
            f_out.write(
                "{c.id}\t{c.label}\t{c.lemma1}\t{c.lemma2}\t{c.lemma1_tag}\t{c.lemma2_tag}\t"
                "{c.prep}\t{c.inv}\t{c.frequency}\t{score}\n".format(
                    c=c, score=log_dice
                )
            )
            if c.label in inv_relations:
                f_out.write(
                    "-{c.id}\t{c.label}\t{c.lemma2}\t{c.lemma1}\t{c.lemma2_tag}\t{c.lemma1_tag}\t"
                    "{c.prep}\t1\t{c.frequency}\t{score}\n".format(c=c, score=log_dice)
                )
    return invalid_ids


def filter_invalid_collocations(
    collocations: dict[int, Colloc], invalid_ids: set[int]
) -> dict[int, Colloc]:
    return {
        col_id: col for col_id, col in collocations.items() if col_id not in invalid_ids
    }


def extract_mwe_from_collocs(
    match_fin: str, mwe_match_fout: str, collocs: dict[int, Colloc]
) -> tuple[dict[tuple, int], defaultdict[int, int]]:
    """
    Compute MWE from matches and collocations.

    MWE matches are stored directly on disk."""

    def read_collapsed_sentence_matches(fin: str) -> Iterator[list[CollocInstance]]:
        """Reads matches for collcations per sentences from file."""
        sent = []
        sent_curr = 0
        doc_curr = 0
        with open(fin, "r") as fh:
            for line in fh:
                m = convert_line(line, CollocInstance, COLLOC_INSTANCE_DTYPES)
                assert isinstance(m, CollocInstance)  # to make mypy happy for now
                if m.doc_id == doc_curr and m.sent_id == sent_curr:
                    sent.append(m)
                else:
                    yield sent
                    sent = [m]
                    doc_curr = m.doc_id
                    sent_curr = m.sent_id
            else:
                yield sent

    def has_one_overlap(*pos: tuple[int]) -> bool:
        """Checks whether positions have one overlap."""
        return len(set(pos)) == (len(pos) - 1)

    with open(mwe_match_fout, "w") as mwe_map:
        mwe_freqs: defaultdict[int, int] = defaultdict(lambda: 1)
        mwe_ids: dict[tuple, int] = {}
        for sent in read_collapsed_sentence_matches(match_fin):
            for m_i, m1 in enumerate(sent):
                for m2 in sent[m_i + 1 :]:
                    if has_one_overlap(
                        m1.head_pos, m2.head_pos, m1.dep_pos, m2.dep_pos
                    ):
                        if not (
                            m1.collocation_id in collocs
                            and m2.collocation_id in collocs
                        ):
                            continue
                        c1 = collocs[m1.collocation_id]
                        c2 = collocs[m2.collocation_id]
                        inverse = 0
                        if has_one_overlap(m1.head_pos, m2.head_pos, m2.dep_pos):
                            # m2 - m1.dep_surface
                            lemma = c1.lemma1 if c1.inv else c1.lemma2
                            tag = c1.lemma1_tag if c1.inv else c1.lemma2_tag
                            mwe_id = add_mwe_to_inventory(
                                mwe_freqs,
                                mwe_ids,
                                (
                                    m2.collocation_id,
                                    m1.collocation_id,
                                    c1.label,
                                    lemma,
                                    tag,
                                    inverse,
                                ),
                            )
                            mwe_map.write(
                                "{}\n".format(
                                    "\t".join(map(str, (mwe_id,) + (m2.id, m1.id)))
                                )
                            )
                        if has_one_overlap(m2.head_pos, m1.head_pos, m1.dep_pos):
                            # m1 - m2.dep_surface
                            lemma = c2.lemma1 if c2.inv else c2.lemma2
                            tag = c2.lemma1_tag if c2.inv else c2.lemma2_tag
                            mwe_id = add_mwe_to_inventory(
                                mwe_freqs,
                                mwe_ids,
                                (
                                    m1.collocation_id,
                                    m2.collocation_id,
                                    c2.label,
                                    lemma,
                                    tag,
                                    inverse,
                                ),
                            )
                            mwe_map.write(
                                "{}\n".format(
                                    "\t".join(map(str, (mwe_id,) + (m1.id, m2.id)))
                                )
                            )
                        inverse = 1
                        if has_one_overlap(m1.dep_pos, m2.head_pos, m2.dep_pos):
                            # m2 - m1.head_surface
                            lemma = c1.lemma2 if c1.inv else c1.lemma1
                            tag = c1.lemma2_tag if c1.inv else c1.lemma1_tag
                            mwe_id = add_mwe_to_inventory(
                                mwe_freqs,
                                mwe_ids,
                                (
                                    m2.collocation_id,
                                    m1.collocation_id,
                                    c1.label,
                                    lemma,
                                    tag,
                                    inverse if c1.label != "KON" else 0,
                                ),
                            )
                            mwe_map.write(
                                "{}\n".format(
                                    "\t".join(map(str, (mwe_id,) + (m2.id, m1.id)))
                                )
                            )
                        if has_one_overlap(m2.dep_pos, m1.head_pos, m1.dep_pos):
                            # m1 - m2.head_surface
                            lemma = c2.lemma2 if c2.inv else c2.lemma1
                            tag = c2.lemma2_tag if c2.inv else c2.lemma1_tag
                            mwe_id = add_mwe_to_inventory(
                                mwe_freqs,
                                mwe_ids,
                                (
                                    m1.collocation_id,
                                    m2.collocation_id,
                                    c2.label,
                                    lemma,
                                    tag,
                                    inverse if c2.label != "KON" else 0,
                                ),
                            )
                            mwe_map.write(
                                "{}\n".format(
                                    "\t".join(map(str, (mwe_id,) + (m1.id, m2.id)))
                                )
                            )
    return mwe_ids, mwe_freqs


def add_mwe_to_inventory(
    freqs: defaultdict[int, int],
    ids: dict[tuple, int],
    xs: tuple,
) -> int:
    mwe_id = ids.get(xs)
    if mwe_id is None:
        mwe_id = len(ids)
        ids[xs] = mwe_id
    else:
        freqs[mwe_id] += 1
    return mwe_id


def compute_mwe_scores(
    mwe_fout: str,
    mwe_ids,
    mwe_freqs,
    collocations: dict[int, Colloc],
    min_freq: int = 5,
) -> None:
    """Calculates Log Dice score for MWE"""

    with open(mwe_fout, "w") as mwe_out:
        for mwe, mwe_id in mwe_ids.items():
            mwe_freq = mwe_freqs[mwe_id]
            if mwe_freq < min_freq:
                continue
            c1, c2, label, lemma, tag, inv = mwe
            log_dice = 14 + math.log2(
                2
                * max(1, mwe_freq)
                / (
                    max(1, collocations[c1].frequency)
                    + max(1, collocations[c2].frequency)
                )
            )
            mwe_out.write(
                "{}\n".format(
                    "\t".join(map(str, (mwe_id,) + mwe + (mwe_freq, log_dice)))
                )
            )


def extract_collocations(match_fin: str, collocs_fout: str) -> None:
    """
    Iterates over all extracted matches and generates a collocation mapping.

    Collocations contain only lemmatized match information and, additionally,
    frequencies are counted for matches. The mapping is written to a file
    and used later for simplifying the matches information.
    """
    relation_dict: defaultdict[
        str, defaultdict[tuple[str, str, str, str, str], int]
    ] = defaultdict(lambda: defaultdict(int))
    with open(match_fin, "r") as fin:
        for line in fin:
            m = tuple(line.strip().split("\t"))
            rel, lemma1, lemma2, tag1, tag2, prep = m[0:6]
            relation_dict[rel][lemma1, lemma2, tag1, tag2, prep] += 1

    with open(collocs_fout, "w") as fh:
        for rel, cols_dict in relation_dict.items():
            for (lemma1, lemma2, tag1, tag2, prep), freq in cols_dict.items():
                fh.write(f"{rel}\t{lemma1}\t{tag1}\t{lemma2}\t{tag2}\t{prep}\t{freq}\n")


def extract_most_common_surface(match_fin: str, fout: str) -> None:
    """Generates a mapping from a lemma to its most common surface form."""
    common_surfaces: defaultdict[
        str, defaultdict[str, defaultdict[str, int]]
    ] = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    with open(match_fin, "r") as fin:
        for line in fin:
            m = tuple(line.strip().split("\t"))
            rel, lemma1, lemma2, tag1, tag2, _, form1, form2 = m[:8]
            common_surfaces[tag1][lemma1][form1] += 1
            common_surfaces[tag2][lemma2][form2] += 1

    with open(fout, "w") as fh:
        for tag in common_surfaces:
            for lemma in common_surfaces[tag]:
                surface, freq = sorted(
                    common_surfaces[tag][lemma].items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[0]
                fh.write(f"{lemma}\t{tag}\t{surface}\t{freq}\n")


def load_collocations(fins: list[str], min_rel_freq: int = 5) -> dict[int, Colloc]:
    """Load collocations from file and filter by frequency limit."""
    relation_dict: defaultdict[
        str, defaultdict[tuple[str, str, str, str, str], int]
    ] = defaultdict(lambda: defaultdict(int))
    for fin in fins:
        with open(fin, "r") as f_in:
            for line in f_in:
                m = tuple(line.strip().split("\t"))
                rel, (lemma1, tag1, lemma2, tag2, prep), freq = (
                    m[0],
                    m[1:6],
                    int(m[6]),
                )
                relation_dict[rel][(lemma1, lemma2, tag1, tag2, prep)] += freq
    collocs = {}
    c_id = 1
    for rel, cols_dict in relation_dict.items():
        for (lemma1, lemma2, tag1, tag2, prep), freq in cols_dict.items():
            if freq >= min_rel_freq:
                collocs[c_id] = Colloc(
                    c_id, rel, lemma1, lemma2, tag1, tag2, prep, 0, freq
                )
                c_id += 1
    return collocs


def compute_token_statistics(
    fins: list[str],
    fout: str,
    lemma_freqs: dict[tuple[str, str], int],
    min_freq: int = 5,
) -> None:
    logger.info("-- compute common surfaces")
    common_surfaces: dict[tuple[str, str], tuple[str, int]] = {}
    for fin in fins:
        with open(fin, "r") as f_in:
            for line in f_in:
                lemma, tag, surface, string_freq = tuple(line.strip().split("\t"))
                freq = int(string_freq)
                if len(parts := lemma.split()) == 2:
                    lemma_left, lemma_right = parts
                    surface_left, freq_left = common_surfaces.get(
                        (lemma_left, tag), ("", 0)
                    )
                    surface_right, freq_right = common_surfaces.get(
                        (lemma_right, tag), ("", 0)
                    )
                    if freq > freq_left:
                        common_surfaces[lemma_left, tag] = surface, freq
                    if freq > freq_right:
                        common_surfaces[lemma_right, tag] = surface, freq
                else:
                    common_surface, common_freq = common_surfaces.get(
                        (lemma, tag), ("", 0)
                    )
                    if freq > common_freq:
                        common_surfaces[lemma, tag] = surface, freq
    logger.info("-- write token stats with common surfaces")
    with open(fout, "w") as fh:
        for (lemma, tag), freq in filter(
            lambda x: x[1] >= min_freq, lemma_freqs.items()
        ):
            surface, surface_freq = common_surfaces.get((lemma, tag), ("", 0))
            if not surface:
                continue
            fh.write(f"{lemma}\t{tag}\t{freq}\t{surface}\t{surface_freq}\n")


def compute_stats(
    storage_paths: list[str],
    output_path: str,
    min_freq: int = 5,
    with_mwe: bool = False,
) -> None:
    "Aggregate data from subcorpora and compute collocations scores."
    # define output file paths
    corpus_file = os.path.join(output_path, "corpus_files")
    corpus_file_tmp = os.path.join(output_path, "corpus_files.tmp")
    concordance_file = os.path.join(output_path, "concord_sentences")
    concordance_file_tmp = os.path.join(output_path, "concord_sentences.tmp")
    duplicate_sents_file = os.path.join(output_path, "concord_sentences.duplicate")

    logger.info("REINDEX corpus files")
    corpus_file_idx = reindex_corpus_files(
        [os.path.join(p, "corpus_files") for p in storage_paths],
        corpus_file_tmp,
    )
    logger.info("DEDUPLICATE concordances")
    sents_idx = reindex_concordances(
        [os.path.join(p, "concord_sentences") for p in storage_paths],
        concordance_file_tmp,
        corpus_file_idx,
        duplicate_sents_file,
    )
    logger.info("LOAD FILTERED collocations")
    collocs = load_collocations(
        [os.path.join(p, "collocations") for p in storage_paths], min_freq
    )
    logger.info(
        "%d collocations with at least %d frequency collected."
        % (len(collocs), min_freq)
    )
    lemma_freqs = aggregate_lemma_frequencies(
        [os.path.join(p, "lemma_freqs") for p in storage_paths]
    )
    logger.info("CALCULATE AND WRITE log dice scores")
    invalid_collocation_ids = compute_collocation_scores(
        os.path.join(output_path, "collocations"), collocs, lemma_freqs
    )
    collocs = filter_invalid_collocations(collocs, invalid_collocation_ids)
    logger.info(
        "Removed %d collocations with negative logDice score."
        % len(invalid_collocation_ids)
    )
    logger.info("FILTER matches.")
    valid_sentence_ids = filter_transform_matches(
        [os.path.join(p, "matches") for p in storage_paths],
        os.path.join(output_path, "matches"),
        corpus_file_idx,
        sents_idx,
        collocs,
    )
    logger.info(
        "Found %d valid concordances (of %d)."
        % (len(valid_sentence_ids), len(sents_idx))
    )
    sents_idx = set()
    corpus_file_idx = {}
    logger.info("FILTER corpus files and sentences.")
    filter_corpus_files(corpus_file_tmp, corpus_file, valid_sentence_ids)
    filter_concordances(concordance_file_tmp, concordance_file, valid_sentence_ids)
    valid_sentence_ids = set()
    logger.info("Remove temporary files")
    os.remove(concordance_file_tmp)
    os.remove(corpus_file_tmp)

    logger.info("CALCULATE token statistics")
    compute_token_statistics(
        [os.path.join(p, "common_surfaces") for p in storage_paths],
        os.path.join(output_path, "token_freqs"),
        lemma_freqs,
        min_freq,
    )
    if with_mwe:
        logger.info("MAKE MWE LVL 1")
        mwe_ids, mwe_freqs = extract_mwe_from_collocs(
            os.path.join(output_path, "matches"),
            os.path.join(output_path, "mwe_match_full"),
            collocs,
        )
        # remove all MWE that don't appear in mwe_freqs, i.e. appear only once
        mwe_ids = {
            mwe: mwe_id for mwe, mwe_id in mwe_ids.items() if mwe_id in mwe_freqs
        }
        logger.info("CALCULATE log dice mwe lvl 1")
        compute_mwe_scores(
            os.path.join(output_path, "mwe"),
            mwe_ids,
            mwe_freqs,
            collocs,
            min_freq=min_freq,
        )
        collocs = {}
        mwe_ids = {}
        mwe_freqs_filtered = {
            mwe_id: freq for mwe_id, freq in mwe_freqs.items() if freq >= min_freq
        }
        filter_mwe_matches(output_path, mwe_freqs_filtered)
        # remove temporary file with MWE matches
        os.remove(os.path.join(output_path, "mwe_match_full"))


def filter_concordances(
    tmp_file: str, final_file: str, valid_sentence_ids: set[tuple[str, str]]
) -> None:
    with open(tmp_file) as fh:
        with open(final_file, "w") as fo:
            for line in fh:
                sent_id = tuple(line.strip().split("\t")[:2])
                if sent_id in valid_sentence_ids:
                    print(line, end="", file=fo)


def filter_corpus_files(
    tmp_file: str, final_file: str, valid_sentence_ids: set[tuple[str, str]]
) -> None:
    valid_doc_ids = {sent_id[0] for sent_id in valid_sentence_ids}
    with open(tmp_file) as fh:
        with open(final_file, "w") as fo:
            for line in fh:
                doc_id = line.strip().split("\t")[0]
                if doc_id in valid_doc_ids:
                    print(line, end="", file=fo)


def aggregate_lemma_frequencies(
    input_files: list[str],
) -> defaultdict[tuple[str, str], int]:
    lemma_frequencies: defaultdict[tuple[str, str], int] = defaultdict(int)
    for file in input_files:
        with open(file) as fh:
            for line in fh:
                lemma, tag, freq = line.strip().split("\t")
                lemma_frequencies[(lemma, tag)] += int(freq)
    return lemma_frequencies


def filter_mwe_matches(final_path: str, mwe_freqs: dict[int, int]) -> None:
    with open(os.path.join(final_path, "mwe_match_full")) as fh:
        with open(os.path.join(final_path, "mwe_match"), "w") as fo:
            for line in fh:
                mwe_id = int(line.strip().split("\t")[0])
                if mwe_id in mwe_freqs:
                    print(line, end="", file=fo)


def load_files_into_db(connection: Connection, storage_path: str) -> None:
    """Load generated data files into their corresponding db tables."""
    for tb_name in [
        "corpus_files",
        "concord_sentences",
        "collocations",
        "token_freqs",
        "matches",
        "mwe",
        "mwe_match",
    ]:
        tb_file = os.path.join(storage_path, tb_name)
        if not os.path.exists(tb_file):
            logger.warning("Local file '%s' does not exist." % tb_file)
        else:
            logger.info("LOAD DATA FILE: %s" % tb_name)
            if tb_name == "concord_sentences":
                query = f"""LOAD DATA LOCAL INFILE '{tb_file}' INTO TABLE {tb_name}
                (corpus_file_id, sentence_id, sentence);"""
            else:
                query = f"LOAD DATA LOCAL INFILE '{tb_file}' INTO TABLE {tb_name};"
            connection.execute(text(query))
