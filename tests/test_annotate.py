from pathlib import Path

import conllu
import dwdsmor
import pytest
import spacy

import wordprofile.preprocessing.cli.annotate as anno

TEST_DIR = Path(__file__).parent


@pytest.fixture
def short_conll_file():
    return TEST_DIR / "testdata" / "short.conll"


@pytest.fixture
def multiple_docs_conll_file():
    return TEST_DIR / "testdata" / "four_docs.conll"


@pytest.fixture(scope="module")
def parser():
    return anno.setup_spacy_pipeline(accurate=False)


@pytest.fixture(scope="module")
def lemmatizer():
    return dwdsmor.lemmatizer()


@pytest.fixture
def phrasal_verbs_conll():
    return conllu.parse((TEST_DIR / "testdata" / "phrasal_verbs.conll").read_text())


def test_conversion_to_spacy_doc(parser, short_conll_file):
    with open(short_conll_file) as fh:
        sentences = list(conllu.parse_incr(fh))
    sentence = sentences[0]
    result = anno.convert_to_spacy_doc(parser, sentence)
    assert isinstance(result, spacy.tokens.Doc)
    assert len(result) == 13
    assert (
        result.text
        == "Sehr geehrter Herr Präsident Palinkás, meine sehr verehrten Damen und Herren , "
    )


def test_add_token_annotation_to_conll_sentence(short_conll_file, parser):
    with open(short_conll_file) as fh:
        sentences = conllu.parse(fh.read())
    doc = next(anno.annotate(parser, sentences[3:4]))
    assert [(tok["form"], tok["upos"], tok["head"], tok["deprel"]) for tok in doc] == [
        ("Damals", "ADV", 2, "advmod"),
        ("ging", "VERB", 0, "ROOT"),
        ("eine", "DET", 5, "det"),
        ("ganze", "ADJ", 5, "amod"),
        ("Epoche", "NOUN", 2, "nsubj"),
        ("zu", "ADP", 7, "case"),
        ("Ende", "NOUN", 2, "obl"),
        (".", "PUNCT", 2, "punct"),
    ]


def test_space_after(short_conll_file):
    with open(short_conll_file) as fh:
        sentences = conllu.parse(fh.read())
    spaces = [anno.is_space_after(tok) for tok in sentences[7]]
    assert spaces == [True, True, False, False, True, True, True, False, True, True]


def test_ner_model_added_as_component_to_nlp_pipeline():
    nlp = anno.setup_spacy_pipeline(accurate=False)
    assert nlp.has_pipe("wikiner")


def test_named_entity_annotation_added_to_tokens(parser, short_conll_file):
    with open(short_conll_file) as fh:
        sentences = conllu.parse(fh.read())
    result = next(anno.annotate(parser, sentences))
    assert result[4]["misc"]["NE"] == "PER"


def test_lemmatization_updates_lemma(lemmatizer):
    sentence = conllu.TokenList(
        [
            conllu.Token(
                id=1,
                form="Am",
                lemma="",
                upos="ADP",
                xpos="APPR_ART",
                head=2,
                deprel="case",
                feats={
                    "AdpType": "Prep",
                    "Case": "Dat",
                    "Definite": "Def",
                    "Gender": "Masc, Neut",
                    "Number": "Sing",
                },
                misc={},
            ),
            conllu.Token(
                id=2,
                form="Abend",
                lemma="",
                upos="NOUN",
                xpos="NN",
                head=3,
                deprel="obl",
                feats={
                    "Gender": "Masc",
                    "Number": "Sing",
                },
                misc={},
            ),
            conllu.Token(
                id=3,
                form="erreichen",
                lemma="",
                upos="VERB",
                xpos="VVFIN",
                head=0,
                deprel="ROOT",
                feats={
                    "Mood": "Ind",
                    "Number": "Plur",
                    "Person": "3",
                    "Tense": "Pres",
                    "VerbForm": "Fin",
                },
                misc={},
            ),
            conllu.Token(
                id=4,
                form="die",
                lemma="",
                upos="DET",
                xpos="ART",
                head=5,
                deprel="det",
                feats={
                    "Case": "Nom",
                    "Definite": "Def",
                    "Number": "Plur",
                    "PronType": "Art",
                },
                misc={},
            ),
            conllu.Token(
                id=5,
                form="Regenschauer",
                lemma="",
                upos="NOUN",
                xpos="NN",
                head=3,
                deprel="nsubj",
                feats={"Gender": "Masc", "Number": "Plur"},
                misc={},
            ),
            conllu.Token(
                id=6,
                form="ihren",
                lemma="",
                upos="DET",
                xpos="PPOSAT",
                head=8,
                deprel="det",
                feats={
                    "Case": "Acc",
                    "Gender": "Masc",
                    "Gender[psor]": "Fem",
                    "Number": "Sing",
                    "Number[psor]": "Sing",
                    "Person": "3",
                    "Poss": "Yes",
                    "PronType": "Prs",
                },
                misc={},
            ),
            conllu.Token(
                id=7,
                form="jährlichen",
                lemma="",
                upos="ADJ",
                xpos="ADJA",
                head=8,
                deprel="amod",
                feats={
                    "Case": "Acc",
                    "Degree": "Pos",
                    "Gender": "Masc",
                    "Number": "Sing",
                },
                misc={},
            ),
            conllu.Token(
                id=8,
                form="Höhepunkt",
                lemma="",
                upos="NOUN",
                xpos="NN",
                head=3,
                deprel="obj",
                feats={"Gender": "Masc", "Number": "Sing"},
                misc={},
            ),
        ]
    )
    anno.lemmatize(lemmatizer, sentence)
    result = [tok["lemma"] for tok in sentence]
    assert result == [
        "an",
        "Abend",
        "erreichen",
        "die",
        "Regenschauer",
        "ihre",
        "jährlich",
        "Höhepunkt",
    ]


def test_lemma_not_updated_if_pos_not_matching(lemmatizer):
    sentence = conllu.TokenList(
        [
            conllu.Token(
                id=1,
                form="erreichen",
                lemma="",
                upos="VERB",
                xpos="NN",
                head=0,
                deprel="ROOT",
                feats={
                    "Mood": "Ind",
                    "Number": "Plur",
                    "Person": "3",
                    "Tense": "Pres",
                    "VerbForm": "Fin",
                },
                misc={},
            ),
        ]
    )
    anno.lemmatize(lemmatizer, sentence)
    assert sentence[0]["lemma"] == ""


def test_lemma_not_update_if_unk_to_dwdsmor(lemmatizer):
    sentence = conllu.TokenList(
        [
            conllu.Token(
                id=1,
                form="unbeing",
                lemma="",
                upos="ADJ",
                xpos="ADJA",
                head=0,
                deprel="ROOT",
                feats={},
                misc={},
            ),
        ]
    )
    anno.lemmatize(lemmatizer, sentence)
    assert sentence[0]["lemma"] == ""


def test_lemmatization_makes_use_of_morph_information(lemmatizer):
    sentence = conllu.TokenList(
        [
            conllu.Token(
                id=1,
                form="getestet",
                lemma="",
                upos="VERB",
                xpos="VVPP",
                head=0,
                deprel="ROOT",
                feats={"Aspect": "Perf", "VerbForm": "Part"},
                misc={},
            ),
            conllu.Token(
                id=1,
                form="getestet",
                lemma="",
                upos="ADJ",
                xpos="ADJA",
                head=0,
                deprel="ROOT",
                feats={"Degree": "Pos"},
                misc={},
            ),
        ]
    )
    anno.lemmatize(lemmatizer, sentence)
    assert sentence[0]["lemma"] == "testen"
    assert sentence[0]["lemma"] != sentence[1]["lemma"]


def test_lemmatize_phrasal_verb_correct_lemma_added(phrasal_verbs_conll):
    expected_lemmas = ["bereithalten", "stattfinden", "naheliegen", "ankommen"]
    for i, sent in enumerate(phrasal_verbs_conll):
        anno.collapse_phrasal_verbs(sent)
        for token in sent:
            if token["deprel"] == "ROOT":
                assert token["lemma"] == expected_lemmas[i]


def test_lemmatize_phrasal_verb_index_of_particle_added_to_lemma(
    phrasal_verbs_conll,
):
    expected_prt_index = [11, 14, 4, 21]
    for i, sent in enumerate(phrasal_verbs_conll):
        anno.collapse_phrasal_verbs(sent)
        for token in sent:
            if token["deprel"] == "ROOT":
                assert expected_prt_index[i] == token["misc"].get("Compound:prt", 0)


def test_collapse_lemma_of_phrasal_verbs():
    sentence = conllu.TokenList(
        [
            conllu.Token(
                id=1,
                form="Denn",
                lemma="denn",
                upos="CCONJ",
                head=4,
                deprel="cc",
                misc={},
            ),
            conllu.Token(
                id=2,
                form="die",
                lemma="d",
                upos="DET",
                head=3,
                deprel="det",
                misc={},
            ),
            conllu.Token(
                id=3,
                form="Läuterung",
                lemma="Läuterung",
                upos="NOUN",
                head=4,
                deprel="nsubj",
                misc={},
            ),
            conllu.Token(
                id=4,
                form="setzt",
                lemma="setzen",
                upos="VERB",
                head=0,
                deprel="ROOT",
                misc={},
            ),
            conllu.Token(
                id=5,
                form="überlicherweise",
                lemma="überlicherweise",
                upos="ADJ",
                head=4,
                deprel="advmod",
                misc={},
            ),
            conllu.Token(
                id=6,
                form="erst",
                lemma="erst",
                upos="ADV",
                head=7,
                deprel="advmod",
                misc={},
            ),
            conllu.Token(
                id=7,
                form="später",
                lemma="spät",
                upos="ADJ",
                head=4,
                deprel="advmod",
                misc={},
            ),
            conllu.Token(
                id=8,
                form="ein",
                lemma="ein",
                upos="ADP",
                head=4,
                deprel="compound:prt",
                misc={},
            ),
        ]
    )
    anno.collapse_phrasal_verbs(sentence)
    assert sentence[3] == conllu.Token(
        id=4,
        form="setzt",
        lemma="einsetzen",
        upos="VERB",
        head=0,
        deprel="ROOT",
        misc={"Compound:prt": 8},
    )


def test_particle_not_collapsed_if_prt_not_adp():
    sentence = [
        conllu.Token(
            id=1,
            form="Opposition",
            lemma="Opposition",
            upos="NOUN",
            head=2,
            deprel="nsubj",
            misc={},
        ),
        conllu.Token(
            id=2,
            form="läuft",
            lemma="laufen",
            upos="VERB",
            head=0,
            deprel="ROOT",
            misc={},
        ),
        conllu.Token(
            id=3,
            form="Sturm",
            lemma="Sturm",
            upos="NOUN",
            head=2,
            deprel="compound:prt",
            misc={},
        ),
    ]
    anno.collapse_phrasal_verbs(sentence)
    assert sentence[1] == conllu.Token(
        id=2,
        form="läuft",
        lemma="laufen",
        upos="VERB",
        head=0,
        deprel="ROOT",
        misc={},
    )


def test_particle_not_collapsed_if_head_not_verb():
    sentence = [
        conllu.Token(
            id=1,
            form="Pauli",
            lemma="Pauli",
            upos="PROPN",
            head=2,
            deprel="nsubj",
            misc={},
        ),
        conllu.Token(
            id=2,
            form="folgt",
            lemma="folgen",
            upos="VERB",
            head=0,
            deprel="ROOT",
            misc={},
        ),
        conllu.Token(
            id=3,
            form="Ministerpräsident",
            lemma="Ministerpräsident",
            upos="NOUN",
            head=0,
            deprel="ROOT",
            misc={},
        ),
        conllu.Token(
            id=4,
            form="Günther",
            lemma="Günther",
            upos="PROPN",
            head=3,
            deprel="flat:name",
            misc={},
        ),
        conllu.Token(
            id=5,
            form="Beckstein",
            lemma="Beckstein",
            upos="PROPN",
            head=3,
            deprel="flat:name",
            misc={},
        ),
        conllu.Token(
            id=6,
            form="nach",
            lemma="nach",
            upos="ADP",
            head=3,
            deprel="compound:prt",
            misc={},
        ),
    ]
    anno.collapse_phrasal_verbs(sentence)
    assert sentence[2] == conllu.Token(
        id=3,
        form="Ministerpräsident",
        lemma="Ministerpräsident",
        upos="NOUN",
        head=0,
        deprel="ROOT",
        misc={},
    )


def test_case_normalization_and_phrasal_verb_lemmatization(lemmatizer):
    token_list = conllu.TokenList(
        [
            conllu.Token(
                id=1,
                form="Test",
                lemma="Test",
                upos="NOUN",
                xpos="NN",
                feats={},
                head=2,
                deprel="nsubj",
                deps=None,
                misc={"SpaceAfter": "Yes"},
            ),
            conllu.Token(
                id=2,
                form="Schlägt",
                lemma="Schlagen",
                upos="VERB",
                xpos="VVFIN",
                feats={},
                head=0,
                deprel="ROOT",
                deps=None,
                misc={"SpaceAfter": "Yes"},
            ),
            conllu.Token(
                id=3,
                form="fehl",
                lemma="fehl",
                upos="ADP",
                xpos="PTKVZ",
                feats={},
                head=2,
                deprel="compound:prt",
                deps=None,
                misc={"SpaceAfter": "No"},
            ),
        ]
    )
    anno.lemmatize(lemmatizer, token_list)
    anno.collapse_phrasal_verbs(token_list)
    assert token_list[1]["lemma"] == "fehlschlagen"


def test_verb_ignored_if_sein_during_phrasal_verb_lemmatisation():
    sentence = [
        conllu.Token(
            id=1,
            form="Dann",
            lemma="dann",
            upos="ADV",
            head=3,
            deprel="advmod",
            misc={},
        ),
        conllu.Token(
            id=2,
            form="ist",
            lemma="sein",
            upos="AUX",
            head=2,
            deprel="parataxis",
            misc={},
        ),
        conllu.Token(
            id=3,
            form="es",
            lemma="es",
            upos="PRON",
            head=2,
            deprel="nsubj",
            misc={},
        ),
        conllu.Token(
            id=4,
            form="mit",
            lemma="mit",
            upos="ADP",
            head=5,
            deprel="case",
            misc={},
        ),
        conllu.Token(
            id=5,
            form="der",
            lemma="d",
            upos="DET",
            head=6,
            deprel="det",
            misc=False,
        ),
        conllu.Token(
            id=6,
            form="Heimlichkeit",
            lemma="Heimlichkeit",
            upos="NOUN",
            head=2,
            deprel="obl",
            misc={},
        ),
        conllu.Token(
            id=7,
            form="vorbei",
            lemma="vorbei",
            upos="ADP",
            head=2,
            deprel="compound:prt",
            misc={},
        ),
    ]
    anno.collapse_phrasal_verbs(sentence)
    assert sentence[1]["lemma"] == "sein"
    assert sentence[1]["misc"] == {}


@pytest.mark.xfail
def test_wrong_lemma_from_data_replaced_after_phrasal_verb_concatenation(lemmatizer):
    sentence = [
        conllu.Token(
            id=1,
            form="Schwaben",
            lemma="Schwaben",
            upos="PROPN",
            xpos="NE",
            feats={},
            head=2,
            deprel="nsubj",
            deps=None,
            misc={},
        ),
        conllu.Token(
            id=2,
            form="fällt",
            lemma="fällen",
            upos="VERB",
            xpos="VVFIN",
            feats={},
            head=0,
            deprel="ROOT",
            deps=None,
            misc={},
        ),
        conllu.Token(
            id=3,
            form="oft",
            lemma="oft",
            upos="ADV",
            xpos="ADV",
            feats={},
            head=3,
            deprel="advmod",
            deps=None,
            misc={},
        ),
        conllu.Token(
            id=4,
            form="hinten",
            lemma="hinten",
            upos="ADV",
            xpos="ADV",
            feats={},
            head=2,
            deprel="advmod",
            deps=None,
            misc={},
        ),
        conllu.Token(
            id=5,
            form="heraus",
            lemma="heraus",
            upos="ADV",
            xpos="ADV",
            feats={},
            head=2,
            deprel="compound:prt",
            deps=None,
            misc={},
        ),
    ]
    anno.lemmatize(lemmatizer, sentence)
    anno.collapse_phrasal_verbs(sentence)
    assert sentence[1]["lemma"] == "herausfallen"


def test_phrasal_verb_with_recht_as_particle_not_concatenated():
    sentences = [
        [
            conllu.Token(
                id=1,
                form="Hat",
                lemma="haben",
                upos="AUX",
                head=0,
                deprel="ROOT",
                misc={},
            ),
            conllu.Token(
                id=2,
                form="er",
                lemma="er",
                upos="PRON",
                head=1,
                deprel="nsubj",
                misc={},
            ),
            conllu.Token(
                id=3,
                form="doch",
                lemma="doch",
                upos="ADV",
                head=1,
                deprel="advmod",
                misc={},
            ),
            conllu.Token(
                id=4,
                form="recht",
                lemma="recht",
                upos="ADJ",
                head=1,
                deprel="compound:prt",
                misc={},
            ),
        ],
        [
            conllu.Token(
                id=1,
                form="VGH",
                lemma="VGH",
                upos="PROPN",
                head=2,
                deprel="nsubj",
                misc={},
            ),
            conllu.Token(
                id=2,
                form="gab",
                lemma="geben",
                upos="VERB",
                head=0,
                deprel="ROOT",
                misc={},
            ),
            conllu.Token(
                id=3,
                form="dem",
                lemma="d",
                upos="DET",
                head=4,
                deprel="det",
                misc={},
            ),
            conllu.Token(
                id=4,
                form="Landratsamt",
                lemma="Landratsamt",
                upos="NOUN",
                head=2,
                deprel="obj",
                misc={},
            ),
            conllu.Token(
                id=5,
                form="recht",
                lemma="recht",
                upos="ADP",
                head=2,
                deprel="compound:prt",
                misc={},
            ),
        ],
        [
            conllu.Token(
                id=1,
                form="Recht",
                lemma="recht",
                upos="ADP",
                head=2,
                deprel="compound:prt",
                misc={},
            ),
            conllu.Token(
                id=2,
                form="hat",
                lemma="haben",
                upos="VERB",
                head=0,
                deprel="ROOT",
                misc={},
            ),
            conllu.Token(
                id=3,
                form="sie",
                lemma="sie",
                upos="PRON",
                head=2,
                deprel="nsubj",
                misc={},
            ),
        ],
    ]
    for sent in sentences:
        anno.collapse_phrasal_verbs(sent)
    assert sentences[0][0]["lemma"] == "haben"
    assert sentences[1][1]["lemma"] == "geben"
    assert sentences[2][1]["lemma"] == "haben"


def test_sentence_initial_particle_of_phrasal_verbs_normalized():
    sentence = [
        conllu.Token(
            id=1,
            form="Hinzu",
            lemma="hinzu",
            upos="ADP",
            head=2,
            deprel="compound:prt",
            misc={},
        ),
        conllu.Token(
            id=2,
            form="kommen",
            lemma="kommen",
            upos="VERB",
            head=0,
            deprel="ROOT",
            misc={},
        ),
        conllu.Token(
            id=3,
            form="unerklärliche",
            lemma="unerklärlich",
            upos="ADJ",
            head=4,
            deprel="amod",
            misc={},
        ),
        conllu.Token(
            id=4,
            form="Gliederschmerzen",
            lemma="Gliederschmerz",
            upos="NOUN",
            head=2,
            deprel="nsuj",
            misc={},
        ),
    ]
    anno.collapse_phrasal_verbs(sentence)
    assert sentence[1] == conllu.Token(
        id=2,
        form="kommen",
        lemma="hinzukommen",
        upos="VERB",
        head=0,
        deprel="ROOT",
        misc={"Compound:prt": 1},
    )


def test_particles_with_adj_and_adv_upos_concatenated_in_phrasal_verb_lemmatisation():
    sentences = [
        [
            conllu.Token(
                id=1,
                form="Der",
                lemma="d",
                upos="DET",
                head=2,
                deprel="det",
                misc={},
            ),
            conllu.Token(
                id=2,
                form="Fahrer",
                lemma="Fahrer",
                upos="NOUN",
                head=3,
                deprel="nsubj",
                misc={},
            ),
            conllu.Token(
                id=3,
                form="fuhr",
                lemma="fahren",
                upos="VERB",
                head=0,
                deprel="ROOT",
                misc={},
            ),
            conllu.Token(
                id=4,
                form="an",
                lemma="an",
                upos="ADP",
                head=6,
                deprel="case",
                misc={},
            ),
            conllu.Token(
                id=5,
                form="dem",
                lemma="d",
                upos="DET",
                head=6,
                deprel="det",
                misc={},
            ),
            conllu.Token(
                id=6,
                form="Polizisten",
                lemma="Polizist",
                upos="NOUN",
                head=3,
                deprel="obl",
                misc={},
            ),
            conllu.Token(
                id=7,
                form="vorbei",
                lemma="vorbei",
                upos="ADV",
                head=3,
                deprel="compound:prt",
                misc={},
            ),
        ],
        [
            conllu.Token(
                id=1,
                form="Die",
                lemma="d",
                upos="DET",
                head=2,
                deprel="det",
                misc={},
            ),
            conllu.Token(
                id=2,
                form="Tür",
                lemma="Tür",
                upos="NOUN",
                head=3,
                deprel="nsubj",
                misc={},
            ),
            conllu.Token(
                id=3,
                form="steht",
                lemma="stehen",
                upos="VERB",
                head=0,
                deprel="ROOT",
                misc={},
            ),
            conllu.Token(
                id=4,
                form="offen",
                lemma="offen",
                upos="ADJ",
                head=3,
                deprel="compound:prt",
                misc={},
            ),
        ],
    ]
    for sent in sentences:
        anno.collapse_phrasal_verbs(sent)
    assert sentences[0][2]["lemma"] == "vorbeifahren"
    assert sentences[1][2]["lemma"] == "offenstehen"


def test_lemmatization_of_contracted_adp(lemmatizer):
    prepositions = [
        ("am", "an"),
        ("Am", "an"),
        ("aufs", "auf"),
        ("beim", "bei"),
        ("fürs", "für"),
        ("hinters", "hinter"),
        ("hinterm", "hinter"),
        ("im", "in"),
        ("ins", "in"),
        ("übers", "über"),
        ("überm", "über"),
        ("ums", "um"),
        ("unterm", "unter"),
        ("unters", "unter"),
        ("vorm", "vor"),
        ("vors", "vor"),
        ("vom", "von"),
        ("zum", "zu"),
        ("zur", "zu"),
        # not covered by DWDSmor open
        # ("ans", "an"),
        # ("hintern", "hinter"),
        # ("übern", "über"),
        # ("untern", "unter"),
    ]
    for prep, lemma in prepositions:
        token_list = conllu.TokenList(
            [
                conllu.Token(
                    id=1,
                    form=prep,
                    lemma=prep,
                    upos="ADP",
                    xpos="APPR_ART",
                    feats={},
                    head="",
                    deprel="",
                    deps=None,
                    misc={},
                ),
            ]
        )
        anno.lemmatize(lemmatizer, token_list)
        assert token_list == [
            conllu.Token(
                id=1,
                form=prep,
                lemma=lemma,
                upos="ADP",
                xpos="APPR_ART",
                feats={},
                head="",
                deprel="",
                deps=None,
                misc={},
            )
        ]
