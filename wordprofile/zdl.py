import re
from typing import List, Dict

from wordprofile.datatypes import DBToken, Match
from wordprofile.extract import extract_matches


RE_GK_NORM_ERROR = re.compile(r'^[^-]+-[a-zäüö]+$')


def is_valid_token(tok: DBToken):
    return not any([
        len(tok.surface) < 2,
        not tok.surface[0].isalpha(),
        not tok.surface[-1].isalpha(),
        any(c.isdigit() for c in tok.lemma),
        any(c in '"\'@§!?;#*/&<>()_' for c in tok.surface),
        RE_GK_NORM_ERROR.match(tok.lemma)
    ])


def valid_match(match: Match):
    """
    Validates matches by specified criteria (surface form, special symbols, length).
    """
    # TODO filter inconsistent relations
    #  - 0 is marked by parser
    return is_valid_token(match.head) and is_valid_token(match.dep)


def extract_matches_from_doc(parses: List[List[DBToken]]):
    """
    Extracts valid matches from a given document (list of token sequences).
    """
    matches = []
    for match in filter(valid_match, extract_matches(parses)):
        matches.append(match)
    return matches


def load_lemma_repair_files() -> Dict[str, Dict[str, str]]:
    """
    Load static repair mapping files into dict.

    These mappings are used to repair the poor lemmatizer output (already known problems).
    The files have tab-separated csv format. Each line contains a mapping of the form:
        <bad lemma>\t<correct lemma>
    """
    word_classes_repair = {}
    files = [
        ('ADJ', 'spec/lemma_repair_adjektiv.csv'),
        ('NOUN', 'spec/lemma_repair_substantiv.csv'),
        ('VERB', 'spec/lemma_repair_verb.csv'),
    ]
    for word_class, path in files:
        word_class_repair = {}
        for line in open(path, 'r'):
            line = line.strip().split('\t')
            if len(line) == 2:
                if line[0] not in word_class_repair:
                    word_class_repair[line[0]] = line[1]
        word_classes_repair[word_class] = word_class_repair
    return word_classes_repair


LEMMA_REPAIR = load_lemma_repair_files()


def repair_lemma(lemma: str, lemma_tag: str) -> str:
    if lemma_tag in LEMMA_REPAIR:
        return LEMMA_REPAIR[lemma_tag].get(lemma, lemma)
    return lemma


def sent_filter_length(sentence: List[DBToken]) -> bool:
    return 3 <= len(sentence) <= 100


def sent_filter_endings(sentence: List[DBToken]) -> bool:
    return not sentence[-1].surface in [":", ","] or len(sentence) >= 5


def sent_filter_lower_start(sentence: List[DBToken]) -> bool:
    return not sentence[0].surface.islower() or sentence[0].tag == 'PRON'


def sent_filter_tags(sentence: List[DBToken]) -> bool:
    return any(t.tag in ["NOUN", "VERB", "AUX"] for t in sentence)


def sent_filter_invalid_tags(sentence: List[DBToken]) -> bool:
    return sum(1 for t in sentence if t.tag in {'X', 'SYM'}) < 10


def sentence_is_valid(s: List[DBToken]) -> bool:
    return all([
        sent_filter_length(s),
        sent_filter_tags(s),
        sent_filter_endings(s),
        sent_filter_invalid_tags(s)
    ])
