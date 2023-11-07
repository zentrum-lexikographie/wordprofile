import itertools
import re


def is_metadata_line(line):
    return line.startswith("%%$DDC")


METADATA_INDEXED_KEY = re.compile(r"^([^\[]+)(?:\[(\d+)\])?$")
METADATA_KEY_COMPONENT_SEP = re.compile(r"[:.]")

METADATA_CONTAINERS = set(["tokid", "meta", "index", "break"])


def parse_metadata_key(k):
    for comp in itertools.islice(METADATA_KEY_COMPONENT_SEP.split(k), 1, None):
        m = METADATA_INDEXED_KEY.match(comp)
        if m:
            yield m.group(1)
            idx = m.group(2)
            if idx:
                yield int(idx)
        else:
            yield comp


def parse_metadata(metadata):
    metadata_dict = {}
    for record in metadata:
        k, v = record.split("=", 1)
        k = k.lower()
        v = v.strip()
        if len(v) > 0:
            k = list(parse_metadata_key(k))
            container = metadata_dict
            for comp in k[:-1]:
                if comp not in container:
                    container[comp] = {}
                container = container[comp]
            container[k[-1]] = v
    return metadata_dict


def merge_metadata(prev_md, next_md):
    for k, v in next_md.items():
        if k in METADATA_CONTAINERS:
            prev_md[k] = merge_metadata(prev_md.get(k, {}), v)
        else:
            prev_md[k] = v
    return prev_md


def read_token_fields(metadata):
    token_fields = metadata.get("index", {})
    ks = list(token_fields.keys())
    ks.sort()
    for k in ks:
        yield token_fields[k].split(" ")[0]


def parse_tokens(tokens, token_fields):
    for token in tokens:
        fields = token.split("\t")
        yield fields


def parse_chunk(chunk, prev_metadata, prev_token_fields):
    metadata = []
    tokens = []
    for line in chunk:
        if is_metadata_line(line):
            metadata.append(line)
        else:
            tokens.append(line)

    metadata = merge_metadata(
        prev_metadata, parse_metadata(filter(is_metadata_line, metadata))
    )
    token_fields = prev_token_fields or list(read_token_fields(metadata))

    tokens = itertools.filterfalse(is_metadata_line, tokens)
    tokens = list(parse_tokens(tokens, token_fields))

    return {"metadata": metadata, "token_fields": token_fields, "tokens": tokens}


def parse(lines):
    lines = map(lambda l: l.strip(), lines)
    # partition lines by (non-)/empty lines
    chunks = [
        list(chunk)
        for is_sep, chunk in itertools.groupby(lines, lambda l: len(l) == 0)
        if not is_sep
    ]

    metadata = {}
    token_fields = []
    for chunk in chunks:
        sentence = parse_chunk(chunk, metadata, token_fields)
        metadata = sentence["metadata"]
        token_fields = sentence["token_fields"]
        yield sentence


def look_ahead(iterable):
    el = None
    for next_el in iterable:
        if el:
            yield (el, next_el)
        el = next_el
    if el:
        yield (el, None)


def is_space_before(token_fields, token):
    for k, v in zip(token_fields, token):
        if k == "WordSep":
            return v == "1"
    return False


def add_space_after(sentences):
    space_after = False
    for sentence, next_sentence in look_ahead(sentences):
        next_sentence_space_before = False
        if next_sentence:
            next_sentence_space_before = is_space_before(
                next_sentence["token_fields"], next_sentence["tokens"][0]
            )
        token_fields = sentence["token_fields"]
        if token_fields[-1] != "SpaceAfter":
            token_fields.append("SpaceAfter")
        for token, next_token in look_ahead(sentence["tokens"]):
            space_after = next_sentence_space_before
            if next_token:
                space_after = is_space_before(token_fields, next_token)
            token.append("1" if space_after else "0")
        yield sentence
