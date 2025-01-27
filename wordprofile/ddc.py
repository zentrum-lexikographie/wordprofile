import argparse
import itertools
from pathlib import Path
import re

from conllu.models import Metadata, Token, TokenList

from .conllu import serialize, text


def metadata_val(line, prefix):
    prefix = f"%%$DDC:meta.{prefix}="
    if line.startswith(prefix):
        return line[len(prefix):].strip() or None


def parse(lines):
    lines = map(lambda line: line.strip(), lines)
    # partition lines by (non-)/empty lines
    chunks = (
        tuple(c)
        for is_c, c in itertools.groupby(lines, lambda line: len(line) > 0)
        if is_c
    )
    fields = None
    for chunk in chunks:
        metadata = list()
        tokens = list()
        for line in chunk:
            if line.startswith("%%$DDC"):
                metadata.append(line)
            else:
                tokens.append(line)
        corpus = None
        basename = None
        bibl = None
        date = None
        _fields = list()
        for line in metadata:
            corpus = metadata_val(line, "collection") or corpus
            basename = metadata_val(line, "basename") or basename
            bibl = metadata_val(line, "bibl") or bibl
            date = metadata_val(line, "date_") or date
            if line.startswith("%%$DDC:index["):
                _, vs = line.split("=", 1)
                _fields.append(vs.split(" ")[-1])
        fields = tuple(_fields) if _fields else fields
        assert fields is not None, "No DDC-tabs field declaration"
        tokens = tuple(dict(zip(fields, line.split('\t'))) for line in tokens)
        metadata = None
        if corpus:
            metadata = {
                "newdoc id": f"{corpus}:{basename}",
                "bibl": bibl,
                "date": date
            }
        yield (tokens, metadata)


def look_ahead(iterable):
    el = None
    for next_el in iterable:
        if el:
            yield (el, next_el)
        el = next_el
    if el:
        yield (el, None)


def as_conll(lines):
    sentences = parse(lines)
    for sentence, next_sentence in look_ahead(sentences):
        tokens, metadata = sentence
        next_tokens, _ = next_sentence or (None, None)
        t_next_sentence_token = next_tokens[0] if next_tokens else None
        token_list = []
        for ti, (t, t_next) in enumerate(look_ahead(tokens)):
            next_token = t_next or t_next_sentence_token
            no_space_after = next_token and next_token.get("ws", "1") == "0"
            token_list.append(Token({
                "id": ti + 1,
                "form": t.get("w") or "---",
                "lemma": t.get("l"),
                "xpos": t.get("p"),
                "misc": {"SpaceAfter": "No"} if no_space_after else None
            }))
        metadata = Metadata(metadata) if metadata else None
        yield TokenList(token_list, metadata)


_xml_frag = re.compile(r"</?[^>]+>")


def is_clean(sentence):
    return _xml_frag.search(text(sentence)) is None


arg_parser = argparse.ArgumentParser(description="Convert DDC-Tabs to CoNLL-U")
arg_parser.add_argument(
    "-o", "--output-file", help="output CoNLL-U file",
    type=argparse.FileType("w"), default="-"
)
arg_parser.add_argument(
    "-p", "--pattern", help="Glob pattern for DDC-Tabs files in dirs",
    default="**/*.tabs"
)
arg_parser.add_argument(
    "ddc_tabs_path", help="input DDC-Tabs dirs/files", type=Path, nargs="*"
)


def main():
    args = arg_parser.parse_args()
    for path in args.ddc_tabs_path:
        tabs_files = path.glob(args.pattern) if path.is_dir() else (path, )
        for tabs_file in sorted(tabs_files):
            with tabs_file.open("rt") as f:
                for sentence in as_conll(f):
                    if not is_clean(sentence):
                        if sentence.metadata:
                            sentence = TokenList(
                                [Token({"id": "1", "form": "---"})],
                                sentence.metadata
                            )
                        else:
                            continue
                    args.output_file.write(serialize(sentence))


if __name__ == "__main__":
    main()
