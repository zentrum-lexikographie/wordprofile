import argparse
import itertools
import json
import logging
import multiprocessing
import subprocess
import warnings

import conllu
import conllu.parser
import dwdsmor
import dwdsmor.tag.hdt
import py3langid as langid
import spacy
import spacy.tokens
import thinc.api
from cachetools import cached, LFUCache
from tqdm import tqdm

from .colloc import extract_collocs
from .conllu import is_space_after, serialize, text

warnings.simplefilter(action='ignore', category=FutureWarning)

logger = logging.getLogger(__name__)

spacy_model_packages = {
    "de_hdt_dist": (
        "de_hdt_dist @ https://huggingface.co/zentrum-lexikographie/de_hdt_dist/"
        "resolve/main/de_hdt_dist-any-py3-none-any.whl"
        "#sha256=dd54e4f75b249d401ed664c406c1a021ee6733bca7c701eb4500480d473a1a8a"
    ),
    "de_hdt_lg": (
        "de_hdt_lg @ https://huggingface.co/zentrum-lexikographie/de_hdt_lg/"
        "resolve/main/de_hdt_lg-any-py3-none-any.whl"
        "#sha256=44bd0b0299865341ee1756efd60670fa148dbfd2a14d0c1d5ab99c61af08236a"
    ),
    "de_wikinet_dist": (
        "de_wikiner_dist @ https://huggingface.co/zentrum-lexikographie/"
        "de_wikiner_dist/resolve/main/de_wikiner_dist-any-py3-none-any.whl"
        "#sha256=70e3bb3cdb30bf7f945fa626c6edb52c1b44aaccc8dc35ea0bfb2a9f24551f4f"
    ),
    "de_wikiner_lg": (
        "de_wikiner_lg @ https://huggingface.co/zentrum-lexikographie/"
        "de_wikiner_lg/resolve/main/de_wikiner_lg-any-py3-none-any.whl"
        "#sha256=8305ec439cad1247bed05907b97f6db4c473d859bc4083ef4ee0f893963c5b2e"
    ),
}


def spacy_model(model):
    try:
        return spacy.load(model)
    except OSError:
        assert model in spacy_model_packages, model
        logger.debug("Downloading spaCy model '%s'", model)
        subprocess.check_call(["pip", "install", "-qqq", spacy_model_packages[model]])
        return spacy.load(model)


def spacy_doc(nlp, s):
    return spacy.tokens.Doc(
        nlp.vocab,
        words=tuple(t["form"] for t in s),
        spaces=tuple(is_space_after(t) for t in s)
    )


def spacy_nlp(hdt, wikiner, sentences, batch_size=128, **kwargs):
    sents, hdt_sents, ner_sents = itertools.tee(sentences, 3)
    hdt_docs = (spacy_doc(hdt, s) for s in hdt_sents)
    ner_docs = (spacy_doc(wikiner, s) for s in ner_sents)
    hdt_docs = hdt.pipe(hdt_docs, batch_size=batch_size, **kwargs)
    ner_docs = wikiner.pipe(ner_docs, batch_size=batch_size, **kwargs)
    for s, hdt_doc, ner_doc in zip(sents, hdt_docs, ner_docs):
        for token, hdt_token in zip(s, hdt_doc):
            feats = conllu.parser.parse_dict_value(str(hdt_token.morph)) if hdt_token.morph else None
            is_root = hdt_token.dep_ == "ROOT"
            token.update({
                "upos": hdt_token.pos_,
                "xpos": hdt_token.tag_,
                "feats": feats,
                "head": 0 if is_root else hdt_token.head.i + 1,
                "deprel": "root" if is_root else hdt_token.dep_,
            })
        if ner_doc.ents:
            s.metadata["entities"] = json.dumps(tuple(
                (e.label_, *(i + 1 for i in range(e.start, e.end)))
                for e in ner_doc.ents
            ))
        yield s


def detect_language(sentence):
    lang, _prob = langid.classify(text(sentence))
    sentence.metadata["lang"] = lang
    return sentence


def collapse_phrasal_verbs(sentence):
    for token_index, token in enumerate(sentence):
        particle = token["form"].lower()
        if particle == "recht":
            continue
        if token["deprel"] != "compound:prt":
            continue
        if token["upos"] not in {"ADP", "ADJ", "ADV"}:
            continue
        head = sentence[token["head"] - 1]
        if not head or head["upos"] not in {"VERB", "AUX"}:
            continue
        verb = head["lemma"]
        if verb == "sein":
            continue
        head["misc"] = (head["misc"] or {}) | {
            "CompoundPrt": token_index + 1,
            "CompoundVerb": f"{particle}{verb}"
        }
    return sentence


def lemmatize(lemmatizer, sentence, cache_size=10000):
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
                    token_pos,
                    token_morph.get("Number"),
                    token_morph.get("Gender"),
                    token_morph.get("Case"),
                    token_morph.get("Person"),
                    token_morph.get("Tense"),
                    token_morph.get("Degree"),
                    token_morph.get("Mood"),
                    token_morph.get("VerbForm"),
            ).items()
        }
        dwdsmor_result = lemmatize(token_form, **token_criteria)
        if not dwdsmor_result:
            continue
        lemma = token["lemma"]
        dwdsmor_lemma = dwdsmor_result.analysis
        if lemma == dwdsmor_lemma:
            continue
        # make a POS match mandatory
        if dwdsmor_result.pos not in dwdsmor.tag.hdt.pos_map[token_pos]:
            continue
        token["lemma"] = dwdsmor_lemma
    return sentence


def post_annotate(sentence):
    print(sentence)
    sentence = collapse_phrasal_verbs(sentence)
    sentence = extract_collocs(sentence)
    sentence = detect_language(sentence)
    return sentence


def output(sentences, f, progress):
    for sentence in sentences:
        f.write(serialize(sentence))
        if progress is not None:
            progress.update(len(sentence))


arg_parser = argparse.ArgumentParser(description="Add linguistic annotations")
arg_parser.add_argument(
    "-c", "--concurrency", help="# of concurrent processes (none by default)",
    type=int, default="-1"
)
arg_parser.add_argument(
    "-f", "--fast", help="Use CPU-optimized model", action="store_true"
)
arg_parser.add_argument(
    "-g", "--gpu", help="ID of GPU to use (default = -1 aka. CPU)",
    type=int, default="-1"
)
arg_parser.add_argument(
    "-i", "--input-file", help="input CoNLL-U file to annotate",
    type=argparse.FileType("r"), default="-"
)
arg_parser.add_argument(
    "-o", "--output-file", help="output CoNLL-U file with (updated) annotations",
    type=argparse.FileType("w"), default="-"
)
arg_parser.add_argument(
    "-p", "--progress", help="Show progress", action="store_true"
)


def main():
    args = arg_parser.parse_args()
    if args.gpu >= 0:
        logger.info("Using GPU #%d", args.gpu)
        thinc.api.set_gpu_allocator("pytorch")
        thinc.api.require_gpu(args.gpu)
    spacy.prefer_gpu()
    logger.info("Loading spaCy models (%s)", "fast" if args.fast else "accurate")
    hdt = spacy_model("de_hdt_lg" if args.fast else "de_hdt_dist")
    wikiner = spacy_model("de_wikiner_lg" if args.fast else "de_wikiner_dist")
    logger.info("Loading DWDSmor lemmatizer")
    lemmatizer = dwdsmor.lemmatizer()
    sentences = conllu.parse_incr(args.input_file)
    progress = None
    if args.progress:
        progress = tqdm(
            desc="Annotating – POS, Deps, Lemma, NER, Collocations",
            unit=" tokens",
            unit_scale=True,
        )
    sentences = spacy_nlp(hdt, wikiner, sentences)
    sentences = (lemmatize(lemmatizer, s) for s in sentences)
    if args.concurrency < 0:
        sentences = (post_annotate(s) for s in sentences)
        output(sentences, args.output_file, progress)
    else:
        mp_ctx = multiprocessing.get_context("forkserver")
        with mp_ctx.Pool(args.concurrency) as p:
            sentences = p.imap(post_annotate, sentences, 1024)
            output(sentences, args.output_file, progress)


if __name__ == "__main__":
    main()
