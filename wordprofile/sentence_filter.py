import re
from collections.abc import Iterator

from wordprofile.datatypes import Match, WPToken
from wordprofile.extract import extract_matches

RE_GK_NORM_ERROR = re.compile(r"^([^-]+-)+[a-zäüöß]+$")
INVALID_CHARS = re.compile(r"[^\u0000-\uD7FF\uE000-\uFFFF]|\\", re.UNICODE)


def remove_invalid_chars(unicode_string):
    return INVALID_CHARS.sub("", unicode_string) or "_"


def is_valid_token(tok: WPToken) -> bool:
    return not any(
        [
            len(tok.surface) < 2,
            not tok.surface[0].isalpha(),
            not tok.surface[-1].isalpha(),
            any(c.isdigit() for c in tok.lemma),
            any(c in "\"'@§!?;#*/&<>()_" for c in tok.surface),
            any(c in "\"'@§!?;#*/&<>()_" for c in tok.lemma),
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


def extract_matches_from_doc(parses: list[list[WPToken]]) -> Iterator[Match]:
    """
    Extracts valid matches from a given document (list of token sequences).
    """
    return filter(valid_match, extract_matches(parses))


def sent_filter_length(sentence: list[WPToken]) -> bool:
    return 3 <= len(sentence) <= 100


def sent_filter_endings(sentence: list[WPToken]) -> bool:
    if not sentence:
        return False
    return not sentence[-1].surface in [":", ","] or len(sentence) >= 5


def sent_filter_tags(sentence: list[WPToken]) -> bool:
    return any(t.tag in ["NOUN", "VERB", "AUX"] for t in sentence)


def sent_filter_invalid_tags(sentence: list[WPToken]) -> bool:
    return sum(1 for t in sentence if t.tag in {"X", "SYM"}) < min(
        10, len(sentence) / 3
    )


def sentence_is_valid(s: list[WPToken]) -> bool:
    return all(
        [
            sent_filter_length(s),
            sent_filter_tags(s),
            sent_filter_endings(s),
            sent_filter_invalid_tags(s),
        ]
    )
