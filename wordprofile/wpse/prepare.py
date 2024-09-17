import logging
from collections.abc import Iterable

from conllu.models import Metadata

from wordprofile.datatypes import DBConcordance, DBCorpusFile, DBMatch, Match, WPToken
from wordprofile.wpse.db_tables import LEMMA_TYPE, SURFACE_TYPE

logger = logging.getLogger(__name__)


def prepare_corpus_file(meta: Metadata) -> tuple[str, DBCorpusFile]:
    """Converts a document into a DB entry.

    Args:
        meta: Meta information about document.

    Returns:
        A documents id (for later usage) and meta information in DB format.
    """
    # TODO change document id; maybe corpus:basename works
    doc_id = str(meta.get("DDC:meta.file_"))
    return doc_id, DBCorpusFile(
        id=doc_id,
        corpus=meta.get("DDC:meta.collection"),
        file=meta.get("DDC:meta.basename"),
        orig=meta.get("DDC:meta.bibl"),
        scan=meta.get("DDC:meta.biblLex"),
        date=meta.get("DDC:meta.date_"),
        text_class=meta.get("DDC:meta.textClass"),
        available=meta.get("DDC:meta.collection"),
    )


def prepare_concord_sentences(
    doc_id: str, parses: list[list[WPToken]]
) -> list[DBConcordance]:
    """Converts concordances into DB entries.

    Sentence tokens are encoded such that whitespaces (misc=1) are
    encoded into \x01 and non-whitespaces (misc=0) are encoded into
    \x02, respectively.

    Args:
        doc_id: document id
        parses: list of valid sentences

    Returns:
        List of concordances as database entries with encoded sentences.
    """
    return [
        DBConcordance(
            corpus_file_id=doc_id,
            sentence_id=sent_i,
            sentence="".join(
                "{}{}".format(
                    tok.surface,
                    "" if tok == parse[-1] else "\x01" if tok.misc else "\x02",
                )
                for tok in parse
            ),
            page="-",
        )
        for sent_i, parse in enumerate(parses, 1)
    ]


def prepare_matches(doc_id: str, matches: Iterable[Match]) -> list[DBMatch]:
    """Converts extracted matches into DB entries.

    Args:
        doc_id: document id
        matches: iterable of extracted matches for document

    Returns:
        List of corresponding database matches, length might be increased
        by additional matches generated for prepositions.
    """
    db_matches = []
    max_surface_length = 50 if SURFACE_TYPE.length is None else SURFACE_TYPE.length
    max_lemma_length = 50 if LEMMA_TYPE.length is None else LEMMA_TYPE.length
    for m in matches:
        if (
            len(m.head.surface) > max_surface_length
            or len(m.dep.surface) > max_surface_length
            or len(m.head.lemma) > max_lemma_length
            or len(m.dep.lemma) > max_lemma_length
        ):
            logger.warning(f"SKIP LONG MATCH {doc_id} {m}")
            continue
        extra_pos = {m.dep.prt_pos, m.head.prt_pos}
        if m.prep:
            extra_pos.add(m.prep.idx)
            extra_positions = "-".join([str(idx) for idx in extra_pos if idx])
            if (
                len(m.head.surface) + len(m.prep.surface) + 1 > max_surface_length
                or len(m.dep.surface) + len(m.prep.surface) + 1 > max_surface_length
                or len(m.head.lemma) + len(m.prep.surface) + 1 > max_lemma_length
                or len(m.dep.lemma) + len(m.prep.surface) + 1 > max_lemma_length
            ):
                logger.warning(f"SKIP LONG MATCH {doc_id[:7]}...{doc_id[-15:-8]} {m}")
                continue
            db_matches.append(
                DBMatch(
                    relation_label=m.relation,
                    head_lemma=m.head.lemma,
                    dep_lemma=m.dep.lemma,
                    head_tag=m.head.tag,
                    dep_tag=m.dep.tag,
                    prep=m.prep.lemma,
                    head_surface=m.head.surface,
                    dep_surface=m.dep.surface,
                    head_position=m.head.idx,
                    dep_position=m.dep.idx,
                    extra_position=extra_positions if extra_positions else "-",
                    corpus_file_id=doc_id,
                    sentence_id=m.sid,
                )
            )
            db_matches.append(
                DBMatch(
                    relation_label=m.relation,
                    head_lemma=m.head.lemma,
                    dep_lemma="{} {}".format(m.prep.lemma, m.dep.lemma),
                    head_tag=m.head.tag,
                    dep_tag=m.dep.tag,
                    head_surface=m.head.surface,
                    dep_surface="{} {}".format(m.prep.surface, m.dep.surface),
                    head_position=m.head.idx,
                    dep_position=m.dep.idx,
                    extra_position=extra_positions,
                    corpus_file_id=doc_id,
                    sentence_id=m.sid,
                )
            )
        else:
            extra_positions = "-".join([str(idx) for idx in extra_pos if idx])
            db_matches.append(
                DBMatch(
                    relation_label=m.relation,
                    head_lemma=m.head.lemma,
                    dep_lemma=m.dep.lemma,
                    head_tag=m.head.tag,
                    dep_tag=m.dep.tag,
                    prep="_",
                    head_surface=m.head.surface,
                    dep_surface=m.dep.surface,
                    head_position=m.head.idx,
                    dep_position=m.dep.idx,
                    extra_position=extra_positions if extra_positions else "-",
                    corpus_file_id=doc_id,
                    sentence_id=m.sid,
                )
            )
    return db_matches
