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
    for m in matches:
        if (
            len(m.head.surface) > SURFACE_TYPE.length
            or len(m.dep.surface) > SURFACE_TYPE.length
            or len(m.head.lemma) > LEMMA_TYPE.length
            or len(m.dep.lemma) > LEMMA_TYPE.length
        ):
            logger.warning(f"SKIP LONG MATCH {doc_id} {m}")
            continue
        if m.prep:
            if (
                len(m.head.surface) + len(m.prep.surface) + 1 > SURFACE_TYPE.length
                or len(m.dep.surface) + len(m.prep.surface) + 1 > SURFACE_TYPE.length
                or len(m.head.lemma) + len(m.prep.surface) + 1 > LEMMA_TYPE.length
                or len(m.dep.lemma) + len(m.prep.surface) + 1 > LEMMA_TYPE.length
            ):
                logger.warning(f"SKIP LONG MATCH {doc_id[:7]}...{doc_id[-15:-8]} {m}")
                continue
            db_matches.append(
                DBMatch(
                    relation_label=m.relation,
                    head_lemma="{} {}".format(m.head.lemma, m.prep.lemma),
                    dep_lemma=m.dep.lemma,
                    head_tag=m.head.tag,
                    dep_tag=m.dep.tag,
                    head_surface="{} {}".format(m.head.surface, m.prep.surface),
                    dep_surface=m.dep.surface,
                    head_position=m.head.idx,
                    dep_position=m.dep.idx,
                    prep_position=m.prep.idx,
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
                    prep_position=m.prep.idx,
                    corpus_file_id=doc_id,
                    sentence_id=m.sid,
                )
            )
        else:
            db_matches.append(
                DBMatch(
                    relation_label=m.relation,
                    head_lemma=m.head.lemma,
                    dep_lemma=m.dep.lemma,
                    head_tag=m.head.tag,
                    dep_tag=m.dep.tag,
                    head_surface=m.head.surface,
                    dep_surface=m.dep.surface,
                    head_position=m.head.idx,
                    dep_position=m.dep.idx,
                    prep_position=0,
                    corpus_file_id=doc_id,
                    sentence_id=m.sid,
                )
            )
    return db_matches
