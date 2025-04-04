import logging
import subprocess
import time
from datetime import datetime
from typing import Iterable, Iterator

import click
import conllu
import dwdsmor
import dwdsmor.tag.hdt
import spacy
import thinc
from cachetools import LFUCache, cached
from spacy.tokens import Doc

from wordprofile.utils import configure_logs_to_file

logger = logging.getLogger(__name__)

ZDL_MODEL_PACKAGES = {
    "de_hdt_lg": (
        "de_hdt_lg @ https://huggingface.co/zentrum-lexikographie/de_hdt_lg/"
        "resolve/main/de_hdt_lg-any-py3-none-any.whl"
        "#sha256=44bd0b0299865341ee1756efd60670fa148dbfd2a14d0c1d5ab99c61af08236a"
    ),
    "de_wikiner_lg": (
        "de_wikiner_lg @ https://huggingface.co/zentrum-lexikographie/"
        "de_wikiner_lg/resolve/main/de_wikiner_lg-any-py3-none-any.whl"
        "#sha256=8305ec439cad1247bed05907b97f6db4c473d859bc4083ef4ee0f893963c5b2e"
    ),
    "de_hdt_dist": (
        "de_hdt_dist @ https://huggingface.co/zentrum-lexikographie/de_hdt_dist/"
        "resolve/main/de_hdt_dist-any-py3-none-any.whl"
        "#sha256=dd54e4f75b249d401ed664c406c1a021ee6733bca7c701eb4500480d473a1a8a"
    ),
    "de_wikiner_dist": (
        "de_wikiner_dist @ https://huggingface.co/zentrum-lexikographie/"
        "de_wikiner_dist/resolve/main/de_wikiner_dist-any-py3-none-any.whl"
        "#sha256=70e3bb3cdb30bf7f945fa626c6edb52c1b44aaccc8dc35ea0bfb2a9f24551f4f"
    ),
}


def is_space_after(token: conllu.Token):
    return (token.get("misc") or {}).get("SpaceAfter", "Yes") != "No"


def convert_to_spacy_doc(
    nlp: spacy.Language,
    sentence: conllu.models.TokenList,
) -> Doc:
    return spacy.tokens.Doc(
        nlp.vocab,
        words=[t["form"] for t in sentence],
        spaces=[is_space_after(t) for t in sentence],
    )


def spacy_model(model: str) -> spacy.Language:
    try:
        return spacy.load(model)
    except OSError:
        logger.debug("Downloading spaCy model '%s'", model)
        try:
            subprocess.run(
                ["pip", "install", "-qqq", ZDL_MODEL_PACKAGES[model]], check=True
            )
        except subprocess.CalledProcessError:
            logger.exception(
                "Couldn't install spaCy model %s, try manual installation.", model
            )
            raise
        return spacy.load(model)


def setup_spacy_pipeline(accurate: bool = True, gpu_id: int = -1) -> spacy.Language:
    if gpu_id >= 0:
        logger.info("Using GPU #%d", gpu_id)
        thinc.api.set_gpu_allocator("pytorch")
        thinc.api.require_gpu(gpu_id)
        spacy.prefer_gpu()
    nlp = spacy_model("de_hdt_dist" if accurate else "de_hdt_lg")
    ner = spacy_model("de_wikiner_dist" if accurate else "de_wikiner_lg")
    ner.replace_listeners(
        "transformer" if accurate else "tok2vec", "ner", ("model.tok2vec",)
    )
    nlp.add_pipe("ner", source=ner, name="wikiner")
    return nlp


def annotate(
    nlp: spacy.Language, sentences: Iterable[conllu.models.TokenList], batch_size=128
) -> Iterator[conllu.models.TokenList]:
    docs = nlp.pipe(
        ((convert_to_spacy_doc(nlp, sent), sent) for sent in sentences),
        batch_size=batch_size,
        as_tuples=True,
    )
    for doc, conll_sent in docs:
        for token, nlp_token in zip(conll_sent, doc):
            token.update(
                {
                    "upos": nlp_token.pos_,
                    "xpos": nlp_token.tag_,
                    "feats": nlp_token.morph.to_dict(),
                    "head": 0 if nlp_token.dep_ == "ROOT" else nlp_token.head.i + 1,
                    "deprel": nlp_token.dep_,
                }
            )
            if nlp_token.ent_iob not in {2, 0}:  # 0: not NE tagging, 2: outside NE
                misc = token.get("misc") if token.get("misc") else {}
                misc.update({"NamedEntity": nlp_token.ent_type_})
                token["misc"] = misc
        yield conll_sent


def lemmatize(
    lemmatizer: dwdsmor.automaton.Lemmatizer,
    sentence: conllu.models.TokenList,
    cache_size: int = 10000,
) -> None:
    @cached(LFUCache(cache_size))
    def lemmatize(form, **criteria):
        return lemmatizer(form, **criteria)

    for token in sentence:
        token_form = token["form"]
        token_pos = token["xpos"]
        token_morph = token["feats"] or {}
        token_criteria = {
            k: frozenset(v) if v else None
            for k, v in dwdsmor.tag.hdt.criteria(
                pos=token_pos,
                number=token_morph.get("Number"),
                gender=token_morph.get("Gender"),
                case=token_morph.get("Case"),
                person=token_morph.get("Person"),
                tense=token_morph.get("Tense"),
                degree=token_morph.get("Degree"),
                mood=token_morph.get("Mood"),
                nonfinite=token_morph.get("VerbForm"),
            ).items()
        }
        dwdsmor_result = lemmatize(token_form, **token_criteria)
        if not dwdsmor_result:
            continue
        lemma = token["lemma"]
        dwdsmor_lemma = dwdsmor_result.analysis
        if lemma == dwdsmor_lemma:
            dwdsmor_lemma = f"{dwdsmor_lemma}"
        else:
            dwdsmor_lemma = f"{dwdsmor_lemma}"
        # make a POS match mandatory
        if dwdsmor_result.pos not in dwdsmor.tag.hdt.pos_map[token_pos]:
            continue
        token["lemma"] = dwdsmor_lemma


def collapse_phrasal_verbs(sentence: conllu.models.TokenList) -> None:
    for token_index, token in enumerate(sentence, 1):
        particle = token["form"].lower()
        if particle == "recht":
            continue
        if token["deprel"] == "compound:prt" and token["upos"] in {"ADP", "ADJ", "ADV"}:
            head = sentence[token["head"] - 1]
            if head["upos"] in {"VERB", "AUX"}:
                verb = head["lemma"]
                if verb == "sein":
                    continue
                head["lemma"] = f"{particle}{verb}"
                head["misc"] = (head["misc"] or {}) | {"Compound:prt": token_index}


@click.command(
    help="Parse conll file and add linguistic annotations and lemmatisation."
)
@click.option(
    "-i",
    "--input",
    default="-",
    type=click.File("r"),
    help="Path to input file in conllu format.",
)
@click.option(
    "-o",
    "--output",
    default="-",
    type=click.File("w", encoding="utf-8"),
    help="Output file.",
)
@click.option(
    "--fast",
    "-f",
    is_flag=True,
    help="Use CPU-optimized models for faster processing. "
    "As default, GPU-optmized model group is used.",
)
@click.option(
    "--gpu",
    "-g",
    type=int,
    default=-1,
    help="ID of GPU to use, default -1 , i.e. using CPU.",
)
@click.option(
    "--batch-size",
    "-b",
    default=128,
    type=int,
    help="Batch size used by model during processing. Default is 128 (sentences).",
)
def main(input, output, fast, batch_size, gpu):
    configure_logs_to_file(log_file_identifier="annotate")
    input_file = input.name if input != "-" else "from stdin"
    logger.info(
        "Processing corpus %s on %s (batch size: %d)."
        % (input_file, f"gpu {gpu}" if gpu >= 0 else "cpu", batch_size)
    )
    nlp = setup_spacy_pipeline(not fast, gpu)
    lemmatizer = dwdsmor.lemmatizer("zentrum-lexikographie/dwdsmor-dwds")
    start = time.time()
    logger.info("Start time: %s" % datetime.fromtimestamp(start))
    for sentence in annotate(
        nlp,
        conllu.parse_incr(input, fields=conllu.parser.DEFAULT_FIELDS),
        batch_size=batch_size,
    ):
        lemmatize(lemmatizer, sentence)
        collapse_phrasal_verbs(sentence)
        output.write(sentence.serialize())
    end = time.time()
    elapsed_time = end - start
    logger.info("End time: %s" % datetime.fromtimestamp(end))
    logger.info("Elapsed time: %f s" % elapsed_time)


if __name__ == "__main__":
    main()
