import datetime
from typing import List, Tuple

from sqlalchemy import MetaData
from sqlalchemy.engine import Engine

from wordprofile.datatypes import Match, DBToken, TabsDocument
from wordprofile.wpse.db_tables import get_table_corpus_files, DBCorpusFile, get_table_concord_sentences, DBConcordance, \
    get_table_matches, SURFACE_TYPE, LEMMA_TYPE, DBMatch


def insert_bulk_corpus_file(engine: Engine, corpus_files):
    meta = MetaData()
    corpus_file_tb = get_table_corpus_files(meta)
    query = corpus_file_tb.insert()
    conn = engine.connect()
    conn.execute(query, corpus_files)
    conn.close()


def prepare_corpus_file(doc: TabsDocument) -> Tuple[str, DBCorpusFile]:
    """Converts a document into a DB entry.

    Args:
        doc: Meta information about document.

    Returns:
        A documents id (for later usage) and meta information in DB format.
    """
    doc_id = doc.meta['file_']
    return doc_id, DBCorpusFile(
        id=doc_id,
        corpus=doc.meta['collection'],
        file=doc.meta['basename'],
        orig=doc.meta['bibl'],
        scan=doc.meta['biblLex'],
        date=doc.meta['date_'],
        text_class=doc.meta['textClass'],
        available=doc.meta['collection'],
    )


def insert_bulk_concord_sentences(engine: Engine, concord_sentences):
    meta = MetaData()
    concord_sentences_tb = get_table_concord_sentences(meta)
    query = concord_sentences_tb.insert()
    conn = engine.connect()
    conn.execute(query, concord_sentences)
    conn.close()


def prepare_concord_sentences(doc_id: str, parses: List[List[DBToken]]) -> List[DBConcordance]:
    """Converts concordances into DB entries.

    Args:
        doc_id: document id
        parses: list of valid sentences

    Returns:
        List of concordances as database entries with encoded sentences.
    """
    return [DBConcordance(
        corpus_file_id=doc_id,
        sentence_id=sent_i + 1,
        sentence=''.join('{}{}'.format('' if tok_i == 0 else '\x01' if tok.misc == 0 else '\x02', tok.surface)
                         for tok_i, tok in enumerate(parse)),
        page='-'
    ) for sent_i, parse in enumerate(parses)]


def insert_bulk_matches(engine: Engine, matches: List[dict]):
    meta = MetaData()
    matches_tb = get_table_matches(meta)
    query = matches_tb.insert()
    conn = engine.connect()
    conn.execute(query, matches)
    conn.close()


def prepare_matches(doc_id: str, matches: List[Match]) -> List[DBMatch]:
    """Converts extracted matches into DB entries.

    Args:
        doc_id: document id
        matches: list of extracted matches for document

    Returns:
        List of corresponding database matches, length might be increased by additional matches generated for
        prepositions.
    """
    db_matches = []
    for m in matches:
        if (len(m.head.surface) > SURFACE_TYPE.length or len(m.dep.surface) > SURFACE_TYPE.length or
                len(m.head.lemma) > LEMMA_TYPE.length or len(m.dep.lemma) > LEMMA_TYPE.length):
            print("SKIP LOONG MATCH", doc_id, m)
            continue
        if m.prep:
            if (len(m.head.surface) + len(m.prep.surface) + 1 > SURFACE_TYPE.length or
                    len(m.dep.surface) + len(m.prep.surface) + 1 > SURFACE_TYPE.length or
                    len(m.head.lemma) + len(m.prep.surface) + 1 > LEMMA_TYPE.length or
                    len(m.dep.lemma) + len(m.prep.surface) + 1 > LEMMA_TYPE.length):
                print("SKIP LOONG MATCH", doc_id, m)
                continue
            db_matches.append(DBMatch(
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
                creation_date=datetime.datetime.now()
            ))
            db_matches.append(DBMatch(
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
                creation_date=datetime.datetime.now()
            ))
        else:
            db_matches.append(DBMatch(
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
                creation_date=datetime.datetime.now()
            ))
    return db_matches
