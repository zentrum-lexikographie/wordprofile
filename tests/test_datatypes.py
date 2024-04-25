import datetime

import pytest

from wordprofile.datatypes import Concordance, DBMatch, MweConcordance


def test_create_dbmatch_from_line():
    line = "ADV\tgestern\teinfallen\tADV\tVERB\tgestern\tfällt\t2\t1\t3-5\t1\t0\n"
    assert DBMatch.fromline(line) == DBMatch(
        "ADV",
        "gestern",
        "einfallen",
        "ADV",
        "VERB",
        "gestern",
        "fällt",
        2,
        1,
        "3-5",
        "1",
        0,
    )


def test_db_match_fromline_raises_error_if_not_enough_values():
    line = "ADV\tgestern\teinfallen\tADV\tVERB\n"
    with pytest.raises(ValueError):
        DBMatch.fromline(line)


def test_retrieval_of_collocation_key_for_db_match():
    match = DBMatch(
        "ADV",
        "gestern",
        "einfallen",
        "ADV",
        "VERB",
        "gestern",
        "fällt",
        2,
        1,
        "3-5",
        "1",
        0,
    )
    assert match.get_collocation_key() == "ADV-gestern-einfallen-ADV-VERB"


def test_conversion_of_db_match_to_database_entry():
    match = DBMatch(
        "ADV",
        "gestern",
        "einfallen",
        "ADV",
        "VERB",
        "gestern",
        "fällt",
        2,
        1,
        "3-5",
        "1",
        0,
    )
    assert (
        match.convert_to_database_entry(1, 2) == "1\t2\tgestern\tfällt\t2\t1\t3-5\t1\t0"
    )


def test_retrieval_of_highlighting_positions():
    conc = Concordance(
        sentence="",
        token_position_1=0,
        token_position_2=1,
        extra_position="-",
        corpus="",
        date=datetime.date.fromisoformat("2024-01-01"),
        textclass="",
        orig="",
        scan="",
        avail="",
        page="",
        file="",
        score=10,
        sentence_left="",
        sentence_right="",
    )
    result = conc.get_highlight_positions()
    assert result == [0, 1]


def test_retrieval_of_highlighting_positions_with_extra_positions():
    conc = Concordance(
        sentence="",
        token_position_1=2,
        token_position_2=1,
        extra_position="3-5",
        corpus="",
        date=datetime.date.fromisoformat("2024-01-01"),
        textclass="",
        orig="",
        scan="",
        avail="",
        page="",
        file="",
        score=10,
        sentence_left="",
        sentence_right="",
    )
    result = conc.get_highlight_positions()
    assert result == [1, 2, 3, 5]


def test_retrieval_of_highlighting_positions_mwe():
    conc = MweConcordance(
        sentence="",
        token1_position_1=0,
        token1_position_2=1,
        extra1_position="3-5",
        token2_position_1=7,
        token2_position_2=8,
        extra2_position="-",
        corpus="",
        date=datetime.date.fromisoformat("2024-01-01"),
        textclass="",
        orig="",
        scan="",
        avail="",
        page="",
        file="",
        score=10,
        sentence_left="",
        sentence_right="",
    )
    result = conc.get_highlight_positions()
    assert result == [0, 1, 3, 5, 7, 8]
