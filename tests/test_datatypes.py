import pytest

from wordprofile.datatypes import DBMatch


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
