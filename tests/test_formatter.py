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
        prep="_",
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
        prep="_",
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
        prep="_",
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
        prep="_",
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
                prep="_",
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
                prep="_",
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
        prep="_",
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
        prep="_",
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


def test_defaults_for_comparison_formatting():
    diffs = [{"pos": "NOUN", "score": 0.0}]
    result = form.format_comparison(diffs)
    assert result == [
        {
            "POS": "Substantiv",
            "ConcordId1": None,
            "ConcordId2": None,
            "ConcordNoAccessible1": 0,
            "ConcordNoAccessible2": 0,
            "Score": {
                "AScomp": 0.0,
                "Frequency1": 0,
                "Frequency2": 0,
                "Assoziation1": 0.0,
                "Assoziation2": 0.0,
            },
        }
    ]


def test_formatting_of_comparison():
    diffs = [
        {
            "pos": "NOUN",
            "score": 6.26,
            "coocc_1": Coocc(
                id=-2,
                rel="OBJ",
                lemma1="Apfel",
                lemma2="vergleichen",
                form1="Äpfel",
                form2="verglichen",
                tag1="NOUN",
                tag2="VERB",
                freq=101,
                score=8.1,
                inverse=0,
                has_mwe=0,
                num_concords=100,
                prep="_",
            ),
            "coocc_2": Coocc(
                id=-3,
                rel="OBJ",
                lemma1="Birne",
                lemma2="vergleichen",
                form1="Birnen",
                form2="vergleichen",
                tag1="NOUN",
                tag2="VERB",
                freq=95,
                score=5.1,
                inverse=1,
                has_mwe=0,
                num_concords=90,
                prep="_",
            ),
        }
    ]
    result = form.format_comparison(diffs)[0]
    expected = {
        "POS": "Substantiv",
        "Position": "center",
        "Relation": "OBJ",
        "ConcordId1": -2,
        "ConcordId2": -3,
        "ConcordNoAccessible1": 100,
        "ConcordNoAccessible2": 90,
        "Lemma": "vergleichen",
        "Form": "verglichen",
        "Score": {
            "AScomp": 6.26,
            "Frequency1": 101,
            "Assoziation1": 8.1,
            "Frequency2": 95,
            "Assoziation2": 5.1,
        },
    }
    assert result == expected


def test_formatting_of_comparison_with_inverse_relation():
    diffs = [
        {
            "pos": "NOUN",
            "score": 6.26,
            "coocc_1": Coocc(
                id=-2,
                rel="OBJ",
                lemma1="Apfel",
                lemma2="vergleichen",
                form1="Äpfel",
                form2="verglichen",
                tag1="NOUN",
                tag2="VERB",
                freq=101,
                score=8.1,
                inverse=1,
                has_mwe=0,
                num_concords=100,
                prep="_",
            ),
            "coocc_2": Coocc(
                id=-3,
                rel="OBJ",
                lemma2="Apfel",
                lemma1="ernten",
                form1="Äpfel",
                form2="ernten",
                tag1="NOUN",
                tag2="VERB",
                freq=95,
                score=5.1,
                inverse=1,
                has_mwe=0,
                num_concords=90,
                prep="_",
            ),
        }
    ]
    result = form.format_comparison(diffs)[0]["Relation"]
    assert result == "~OBJ"


def test_formatting_of_relation_description_in_diff_comparison():
    diffs = [
        {
            "pos": "NOUN",
            "score": 6.26,
            "coocc_2": Coocc(
                id=-2,
                rel="OBJ",
                lemma1="Apfel",
                lemma2="vergleichen",
                form1="Äpfel",
                form2="verglichen",
                tag1="NOUN",
                tag2="VERB",
                freq=101,
                score=8.1,
                inverse=1,
                has_mwe=0,
                num_concords=100,
                prep="_",
            ),
        }
    ]
    result = form.format_comparison(diffs)[0]["Relation"]
    assert result == "~OBJ"


def test_formatting_lemma_pos_if_only_one_result(description_handler):
    db_result = [LemmaInfo(lemma="schnell", tag="ADJ", rel="ADV", freq=3, inv=0)]
    result = form.format_lemma_pos(db_result, description_handler.mapRelOrder)
    assert result == [
        {
            "Lemma": "schnell",
            "POS": "Adjektiv",
            "PosId": "Adjektiv",
            "Frequency": 3,
            "Relations": ["ADV"],
        }
    ]


def test_formatting_lemma_pos_no_result(description_handler):
    result = form.format_lemma_pos([], description_handler.mapRelOrder)
    assert result == []


def test_format_collocation_description(description_handler):
    description = description_handler.strRelDescDetail
    result = form.format_relation_description(
        Coocc(
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
            prep="_",
        ),
        description,
    )
    assert result == {
        "Description": "Gesetz tritt auf mit verabschieden",
        "Lemma1": "Gesetz",
        "Lemma2": "verabschieden",
    }


def test_format_collocation_description_with_preposition(description_handler):
    description = description_handler.strRelDescDetail
    result = form.format_relation_description(
        Coocc(
            id=-1,
            rel="PP",
            lemma1="Bier",
            lemma2="Oktoberfest",
            form1="Bier",
            form2="Oktoberfest",
            tag1="NOUN",
            tag2="NOUN",
            freq=10,
            score=10,
            inverse=0,
            has_mwe=0,
            num_concords=10,
            prep="auf",
        ),
        description,
    )
    assert result == {
        "Description": "Bier tritt auf mit auf Oktoberfest",
        "Lemma1": "Bier",
        "Lemma2": "auf Oktoberfest",
    }


def test_format_collocation_description_with_preposition_inverse(description_handler):
    description = description_handler.strRelDescDetail
    result = form.format_relation_description(
        Coocc(
            id=-1,
            rel="PP",
            lemma1="Entwicklung",
            lemma2="beitragen",
            form1="Entwicklung",
            form2="trägt",
            tag1="NOUN",
            tag2="VERB",
            freq=10,
            score=10,
            inverse=1,
            has_mwe=0,
            num_concords=10,
            prep="zu",
        ),
        description,
    )
    assert result == {
        "Description": "Entwicklung tritt auf mit beitragen zu",
        "Lemma1": "Entwicklung",
        "Lemma2": "beitragen zu",
    }


def test_format_lemma_with_preposition():
    result = form.format_lemma_with_preposition("Lemma", "prep", 0)
    assert result == "prep Lemma"


def test_format_lemma_with_preposition_inverse():
    result = form.format_lemma_with_preposition("Test", "prep", 1)
    assert result == "Test prep"


def test_default_preposition_not_added_to_lemma():
    result = form.format_lemma_with_preposition("Test", "_", 0)
    assert result == "Test"


def test_format_pp_relation(description_handler):
    collocation = Coocc(
        id=1,
        rel="PP",
        lemma1="Meer",
        lemma2="Welle",
        form1="Meer",
        form2="Wellen",
        tag1="NOUN",
        tag2="NOUN",
        freq=10,
        score=3.0,
        inverse=0,
        has_mwe=0,
        num_concords=10,
        prep="mit",
    )
    result = form.format_relations([collocation], description_handler)[0]
    assert result == {
        "Relation": "PP",
        "RelationDescription": "hat Präpositionalgruppe",
        "POS": "Substantiv",
        "Form": "mit Wellen",
        "Lemma": "mit Welle",
        "Score": {"Frequency": 10, "logDice": 3.0},
        "ConcordId": "1",
        "ConcordNoAccessible": 10,
        "HasMwe": 0,
    }


def test_format_pp_relation_inverse(description_handler):
    collocation = Coocc(
        id=1,
        rel="PP",
        lemma1="Meer",
        lemma2="Haus",
        form1="Meer",
        form2="Haus",
        tag1="NOUN",
        tag2="NOUN",
        freq=10,
        score=3.0,
        inverse=1,
        has_mwe=0,
        num_concords=10,
        prep="an",
    )
    formatted = form.format_relations([collocation], description_handler)
    assert formatted[0]["Form"] == "Haus an"
    assert formatted[0]["Lemma"] == "Haus an"


def test_format_relation_with_pp_mwe(description_handler):
    collocation = Coocc(
        id=1,
        rel="PP",
        lemma1="Meer-offen",
        lemma2="Zugang",
        form1="Meer-offenen",
        form2="Zugang",
        tag1="NOUN-ADJ",
        tag2="NOUN",
        freq=10,
        score=3.0,
        inverse=1,
        has_mwe=0,
        num_concords=10,
        prep="zu",
    )
    formatted = form.format_relations([collocation], description_handler, is_mwe=True)
    assert formatted[0]["Lemma"] == "Zugang zu"


def test_format_comparison_with_pp_first_lemma():
    diffs = [
        {
            "pos": "NOUN",
            "coocc_1": Coocc(
                id=1,
                rel="PP",
                lemma1="Meer",
                lemma2="Welle",
                form1="Meer",
                form2="Wellen",
                tag1="NOUN",
                tag2="NOUN",
                freq=10,
                score=3.0,
                inverse=0,
                has_mwe=0,
                num_concords=10,
                prep="mit",
            ),
        }
    ]
    formatted = form.format_comparison(diffs)
    assert formatted[0]["Lemma"] == "mit Welle"
    assert formatted[0]["Form"] == "mit Wellen"


def test_format_comparison_with_pp_second_lemma():
    diffs = [
        {
            "pos": "NOUN",
            "coocc_2": Coocc(
                id=1,
                rel="PP",
                lemma1="Meer",
                lemma2="Haus",
                form1="Meer",
                form2="Haus",
                tag1="NOUN",
                tag2="NOUN",
                freq=10,
                score=3.0,
                inverse=1,
                has_mwe=0,
                num_concords=10,
                prep="an",
            ),
        }
    ]
    formatted = form.format_comparison(diffs)
    assert formatted[0]["Lemma"] == "Haus an"
    assert formatted[0]["Form"] == "Haus an"
