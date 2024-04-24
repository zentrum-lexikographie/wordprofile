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
