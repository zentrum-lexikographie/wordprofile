import datetime

import wordprofile.formatter as form
from wordprofile.datatypes import Concordance, MweConcordance


def test_highlighting_of_single_word_concordance():
    sentence = Concordance(
        sentence="Man\x02könne\x02Fahrgäste\x02schließlich\x02nicht\x02zwingen\x01,\x02sich\x02zu\x02waschen\x01.",
        token_position_1=1,
        token_position_2=6,
        prep_position=0,
        corpus="corpus",
        date=datetime.date.fromisoformat("2024-01-01"),
        textclass="tc",
        orig="",
        avail="",
        page="",
        file="",
        scan="",
        score=5,
        sentence_left="",
        sentence_right="",
    )
    result = form.format_concordances([sentence])[0]
    assert (
        result["ConcordLine"]
        == "_&Man&_ könne Fahrgäste schließlich nicht _&zwingen&_, sich zu waschen."
    )


def test_highlighting_of_single_word_concordance_with_prep():
    sentence = Concordance(
        sentence="Man\x02könne\x02Fahrgäste\x02schließlich\x02nicht\x02zwingen\x01,\x02sich\x02zu\x02waschen\x01.",
        token_position_1=3,
        token_position_2=6,
        prep_position=5,
        corpus="corpus",
        date=datetime.date.fromisoformat("2024-01-01"),
        textclass="tc",
        orig="",
        avail="",
        page="",
        file="",
        scan="",
        score=5,
        sentence_left="",
        sentence_right="",
    )
    result = form.format_concordances([sentence])[0]
    assert (
        result["ConcordLine"]
        == "Man könne _&Fahrgäste&_ schließlich _&nicht&_ _&zwingen&_, sich zu waschen."
    )


def test_highlighting_of_mwe_concordance():
    sentence = MweConcordance(
        sentence="Man\x02könne\x02Fahrgäste\x02schließlich\x02nicht\x02zwingen\x01,\x02sich\x02zu\x02waschen\x01.",
        token1_position_1=3,
        token1_position_2=6,
        prep1_position=4,
        token2_position_1=9,
        token2_position_2=8,
        prep2_position=0,
        corpus="corpus",
        date=datetime.date.fromisoformat("2024-01-01"),
        textclass="tc",
        orig="",
        avail="",
        page="",
        file="",
        scan="",
        score=5,
        sentence_left="",
        sentence_right="",
    )
    result = form.format_concordances([sentence])[0]
    assert (
        result["ConcordLine"]
        == "Man könne _&Fahrgäste&_ _&schließlich&_ nicht _&zwingen&_, _&sich&_ _&zu&_ waschen."
    )
