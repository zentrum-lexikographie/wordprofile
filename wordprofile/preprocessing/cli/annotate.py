import logging
import time
from datetime import datetime
from typing import Iterable, Iterator

import click
import conllu
import dwdsmor
import dwdsmor.tag.hdt
import spacy
import zdl_spacy
from cachetools import LFUCache, cached
from spacy.tokens import Doc

from wordprofile.utils import configure_logs_to_file

logger = logging.getLogger(__name__)


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
                    "lemma": nlp_token.lemma_,
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

    sep_indices = {
        t["head"]: t["id"] for t in sentence if t["deprel"] == "compound:prt"
    }
    for token_index, token in enumerate(sentence, 1):
        token_form = token["form"]
        token_pos = token["xpos"]
        token_morph = token.get("feats") or {}
        syninfo = (
            "SEP"
            if token_index in (sep_indices.keys() | sep_indices.values())
            else None
        )
        token_criteria = {
            k: frozenset(v) if v else None
            for k, v in dwdsmor.tag.hdt.criteria(
                pos=token_pos,
                number=token_morph.get("Number"),
                gender=token_morph.get("Gender"),
                case=token_morph.get("Case"),
                person=token_morph.get("Person")
                or ("UnmPers" if token_index in sep_indices.values() else None),
                tense=token_morph.get("Tense"),
                degree=token_morph.get("Degree"),
                mood=token_morph.get("Mood"),
                nonfinite=token_morph.get("VerbForm"),
                syninfo=syninfo,
            ).items()
        }
        dwdsmor_result = lemmatize(token_form, **token_criteria)
        if not dwdsmor_result:
            continue
        if token_index in sep_indices.values() and dwdsmor_result.syninfo is None:
            sep_indices.pop(token["head"])
        lemma = token["lemma"]
        dwdsmor_lemma = dwdsmor_result.analysis
        if lemma == dwdsmor_lemma and token_index not in sep_indices:
            continue
        # make a POS match mandatory except for verb particles
        if (
            dwdsmor_result.pos not in dwdsmor.tag.hdt.pos_map[token_pos]
            and token_index not in sep_indices.values()
        ):
            continue
        if token_index in sep_indices and dwdsmor_result.syninfo is not None:
            particle = sentence[sep_indices[token_index] - 1]
            particle_lemma = lemmatizer(
                particle["form"],
                pos="V",
                syninfo={"SEP"},
                person={"UnmPers"},
            )
            if particle["form"].lower() == "recht":
                particle_lemma = None
            if particle_lemma and particle_lemma.syninfo is not None:
                dwdsmor_lemma = f"{particle_lemma.analysis}{dwdsmor_lemma}"
                token["misc"] = (token["misc"] or {}) | {
                    "compound:prt": sep_indices[token_index]
                }
        token["lemma"] = dwdsmor_lemma


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
    nlp = zdl_spacy.load(
        model_type="dist" if not fast else "lg",
        ner=True,
        gpu_id=None if gpu < 0 else gpu,
    )
    lemmatizer = dwdsmor.lemmatizer("zentrum-lexikographie/dwdsmor-dwds")
    start = time.time()
    logger.info("Start time: %s" % datetime.fromtimestamp(start))
    for sentence in annotate(
        nlp,
        conllu.parse_incr(input, fields=conllu.parser.DEFAULT_FIELDS),
        batch_size=batch_size,
    ):
        lemmatize(lemmatizer, sentence)
        output.write(sentence.serialize())
    end = time.time()
    elapsed_time = end - start
    logger.info("End time: %s" % datetime.fromtimestamp(end))
    logger.info("Elapsed time: %f s" % elapsed_time)


if __name__ == "__main__":
    main()
