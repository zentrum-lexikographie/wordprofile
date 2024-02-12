import re
from collections.abc import Iterator

from wordprofile.datatypes import DBToken, Match
from wordprofile.extract import extract_matches

RE_GK_NORM_ERROR = re.compile(r"^[^-]+-[a-zäüö]+$")
INVALID_CHARS = re.compile(r"[^\u0000-\uD7FF\uE000-\uFFFF]|\\", re.UNICODE)


def remove_invalid_chars(unicode_string):
    return INVALID_CHARS.sub("", unicode_string)


def is_valid_token(tok: DBToken) -> bool:
    return not any(
        [
            len(tok.surface) < 2,
            not tok.surface[0].isalpha(),
            not tok.surface[-1].isalpha(),
            any(c.isdigit() for c in tok.lemma),
            any(c in "\"'@§!?;#*/&<>()_" for c in tok.surface),
            RE_GK_NORM_ERROR.match(tok.lemma),
        ]
    )


def valid_match(match: Match) -> bool:
    """
    Validates matches by specified criteria (surface form, special symbols,
    digits, valid characters in expected positions, length).
    """
    # TODO filter inconsistent relations
    #  - 0 is marked by parser
    return is_valid_token(match.head) and is_valid_token(match.dep)


def extract_matches_from_doc(parses: list[list[DBToken]]) -> Iterator[Match]:
    """
    Extracts valid matches from a given document (list of token sequences).
    """
    return filter(valid_match, extract_matches(parses))


# TODO: Lemma Repair To Be Removed
def load_lemma_repair_files() -> dict[str, dict[str, str]]:
    """
    Load static repair mapping files into dict.

    These mappings are used to repair the poor lemmatizer output (already
    known problems). The files have tab-separated csv format.
    Each line contains a mapping of the form:
        <bad lemma>\t<correct lemma>
    """
    word_classes_repair = {}
    files = [
        ("ADJ", "spec/lemma_repair_adjektiv.csv"),
        ("NOUN", "spec/lemma_repair_substantiv.csv"),
        ("VERB", "spec/lemma_repair_verb.csv"),
    ]
    for word_class, path in files:
        word_class_repair = {}
        for line in open(path, "r"):
            entry = line.strip().split("\t")
            if len(entry) == 2:
                if entry[0] not in word_class_repair:
                    word_class_repair[entry[0]] = entry[1]
        word_classes_repair[word_class] = word_class_repair
    return word_classes_repair


LEMMA_REPAIR = load_lemma_repair_files()


def repair_lemma(lemma: str, lemma_tag: str) -> str:
    if lemma_tag in LEMMA_REPAIR:
        return LEMMA_REPAIR[lemma_tag].get(lemma, lemma)
    return lemma


# REMOVE END


def sent_filter_length(sentence: list[DBToken]) -> bool:
    return 3 <= len(sentence) <= 100


def sent_filter_endings(sentence: list[DBToken]) -> bool:
    return not sentence[-1].surface in [":", ","] or len(sentence) >= 5


def sent_filter_tags(sentence: list[DBToken]) -> bool:
    return any(t.tag in ["NOUN", "VERB", "AUX"] for t in sentence)


def sent_filter_invalid_tags(sentence: list[DBToken]) -> bool:
    return sum(1 for t in sentence if t.tag in {"X", "SYM"}) < min(
        10, len(sentence) / 3
    )


def sentence_is_valid(s: list[DBToken]) -> bool:
    return all(
        [
            sent_filter_length(s),
            sent_filter_tags(s),
            sent_filter_endings(s),
            sent_filter_invalid_tags(s),
        ]
    )
