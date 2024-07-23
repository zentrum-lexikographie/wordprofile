import datetime

import pytest

import wordprofile.formatter as form
from wordprofile.datatypes import Concordance, Coocc, LemmaInfo, MweConcordance
from wordprofile.wpse.wpse_spec import WpSeSpec


@pytest.fixture
def description_handler():
    return WpSeSpec()


def test_relation_not_modified_if_not_inverse(description_handler):
    collocation = Coocc(
        id=1,
        rel="GMOD",
        lemma1="",
        lemma2="",
        form1="",
        form2="",
        tag1="",
        tag2="",
        freq=10,
        score=3.0,
        inverse=0,
        has_mwe=0,
        num_concords=10,
    )
    result = form.format_relations([collocation], description_handler)[0]
    assert result["Relation"] == "GMOD"


def test_relation_retrieved_correctly_if_inverse(description_handler):
    collocation = Coocc(
        id=1,
        rel="GMOD",
        lemma1="",
        lemma2="",
        form1="",
        form2="",
        tag1="",
        tag2="",
        freq=10,
        score=3.0,
        inverse=1,
        has_mwe=0,
        num_concords=10,
    )
    result = form.format_relations([collocation], description_handler)[0]
    assert result["Relation"] == "~GMOD"


def test_correct_description_retrieved_if_not_inverse(description_handler):
    collocation = Coocc(
        id=1,
        rel="ATTR",
        lemma1="",
        lemma2="",
        form1="",
        form2="",
        tag1="",
        tag2="",
        freq=10,
        score=3.0,
        inverse=0,
        has_mwe=0,
        num_concords=10,
    )
    result = form.format_relations([collocation], description_handler)[0]
    assert result["RelationDescription"] == "hat Adjektivattribut"


def test_description_retrieved_correctly_if_inverse(description_handler):
    collocation = Coocc(
        id=1,
        rel="ATTR",
        lemma1="",
        lemma2="",
        form1="",
        form2="",
        tag1="",
        tag2="",
        freq=10,
        score=3.0,
        inverse=1,
        has_mwe=0,
        num_concords=10,
    )
    result = form.format_relations([collocation], description_handler)[0]
    assert result["RelationDescription"] == "ist Adjektivattribut von"


def test_highlighting_of_single_word_concordance():
    sentence = Concordance(
        sentence="Man\x02könne\x02Fahrgäste\x02schließlich\x02nicht\x02zwingen\x01,\x02sich\x02zu\x02waschen\x01.",
        token_position_1=1,
        token_position_2=6,
        extra_position="0",
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
        extra_position="5",
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
        extra1_position="4",
        token2_position_1=9,
        token2_position_2=8,
        extra2_position="0",
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


def test_formatting_of_context_sentences():
    sentence = "Denn\x02jetzt\x02kann\x02der\x02Chef\x02zuschauen\x01!\x02"
    result = form.format_sentence(sentence)
    assert result == "Denn jetzt kann der Chef zuschauen!"


def test_leading_delimiter_removed_of_highlighted_sentence():
    sentence = "\x01Denn\x02jetzt\x02kann\x02der\x02Chef\x02zuschauen\x01!\x01"
    result = form.format_sentence_and_highlight(sentence, [])
    assert result == "Denn jetzt kann der Chef zuschauen!"


def test_default_coocc_id_in_comparison():
    input_diffs = [
        {
            "coocc_1": Coocc(
                id=-1,
                rel="OBJ",
                lemma1="Gesetz",
                lemma2="verabschieden",
                form1="Gesetz",
                form2="verabschiedet",
                tag1="NOUN",
                tag2="VERB",
                freq=29,
                score=10.3,
                inverse=1,
                has_mwe=0,
                num_concords=29,
            ),
            "rank_1": 0,
            "pos": "NOUN",
            "score": 10.3,
        },
        {
            "coocc_2": Coocc(
                id=-2,
                rel="OBJ",
                lemma1="Recht",
                lemma2="einfordern",
                form1="Recht",
                form2="einfordern",
                tag1="NOUN",
                tag2="VERB",
                freq=7,
                score=8.1,
                inverse=1,
                has_mwe=0,
                num_concords=7,
            ),
            "rank_2": 16,
            "pos": "NOUN",
            "score": -8.1,
        },
    ]
    formatted = form.format_comparison(input_diffs)
    result = [(diff["ConcordId1"], diff["ConcordId2"]) for diff in formatted]
    assert result == [(-1, None), (None, -2)]


def test_format_lemma_pos(description_handler):
    db_result = [
        LemmaInfo(lemma="schnell", tag="ADV", rel="ADV", freq=3, inv=1),
        LemmaInfo(lemma="schnell", tag="ADV", rel="KON", freq=1, inv=0),
        LemmaInfo(lemma="schnell", tag="ADJ", rel="ATTR", freq=5, inv=1),
        LemmaInfo(lemma="schnell", tag="ADJ", rel="KON", freq=2, inv=0),
    ]
    result = form.format_lemma_pos(db_result, description_handler.mapRelOrder)
    assert result == [
        {
            "Lemma": "schnell",
            "POS": "Adjektiv",
            "PosId": "Adjektiv",
            "Frequency": 7,
            "Relations": ["META", "~ATTR", "KON"],
        }
    ]


def test_tuples_in_format_relation_contain_all_necessary_keys(description_handler):
    collocation = Coocc(
        id=12,
        rel="ATTR",
        lemma1="Fenster",
        lemma2="groß",
        form1="Fenster",
        form2="große",
        tag1="NOUN",
        tag2="ADJ",
        freq=10,
        score=3.0,
        inverse=0,
        has_mwe=0,
        num_concords=10,
    )
    result = form.format_relations([collocation], description_handler)[0]
    expected = {
        "ConcordId": "12",
        "ConcordNoAccessible": 10,
        "Relation": "ATTR",
        "RelationDescription": "hat Adjektivattribut",
        "POS": "Adjektiv",
        "Form": "große",
        "Lemma": "groß",
        "Score": {"logDice": 3.0, "Frequency": 10},
        "HasMwe": 0,
    }
    assert result == expected


def test_formatting_of_mwe_relation(description_handler):
    collocation = Coocc(
        id=17,
        rel="PP",
        lemma1="Ende-Jahrhundert",
        lemma2="ansteigen",
        form1="Ende-Jahrhundert",
        form2="angestiegen",
        tag1="NOUN-NOUN",
        tag2="VERB",
        freq=5,
        score=10.3,
        inverse=0,
        has_mwe=0,
        num_concords=5,
    )
    result = form.format_relations([collocation], description_handler, is_mwe=True)[0]
    expected = {
        "ConcordId": "#mwe17",
        "ConcordNoAccessible": 5,
        "Relation": "PP",
        "RelationDescription": "hat Präpositionalgruppe",
        "POS": "Verb",
        "Form": "angestiegen",
        "Lemma": "ansteigen",
        "Score": {"logDice": 10.3, "Frequency": 5},
        "HasMwe": 0,
    }
    assert result == expected


def test_format_concordances_contains_necessary_bibl_information():
    concordances = [
        Concordance(
            sentence="Auch\x02deshalb\x02habe\x02ich\x02Ihre\x02freundliche\x02Einladung\x02gern\x02angenommen\x01.",
            token_position_1=7,
            token_position_2=6,
            extra_position="-",
            corpus="corpus",
            date=datetime.date.fromisoformat("2024-01-01"),
            textclass="tc",
            orig="Quelle, 01.01.2024",
            avail="",
            page="",
            file="",
            scan="",
            score=5,
            sentence_left="",
            sentence_right="",
        )
    ]
    result = form.format_concordances(concordances)[0]
    expected = {
        "Bibl": {"Corpus": "corpus", "Orig": "Quelle, 01.01.2024"},
        "ConcordLine": "Auch deshalb habe ich Ihre _&freundliche&_ _&Einladung&_ gern angenommen.",
    }
    assert result == expected
