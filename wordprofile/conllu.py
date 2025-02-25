from conllu.parser import DEFAULT_FIELDS
from conllu.serializer import serialize_field


def is_space_after(token):
    return (token.get("misc") or {}).get("SpaceAfter", "Yes") != "No"


def token_text(token):
    return token.get("form", "") + (" " if is_space_after(token) else "")


def text(sentence):
    return "".join(token_text(t) for t in sentence)


def serialize(sentence):
    lines = []

    if sentence.metadata:
        for key, value in sentence.metadata.items():
            if value:
                line = f"# {key} = {value}"
            else:
                line = f"# {key}"
            lines.append(line)

    for token in sentence:
        line = '\t'.join(serialize_field(token.get(k)) for k in DEFAULT_FIELDS)
        lines.append(line)

    return '\n'.join(lines) + "\n\n"
