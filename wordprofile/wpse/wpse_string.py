import re

RE_HIT_DELIMITER = re.compile(r"[^\x01\x02]*[\x01\x02]")


def format_sentence(sent: str):
    """
    Formatieren eines Hit
    """
    if not sent:
        return ""
    return sent.replace('\x02', ' ').replace('\x01', '').strip()


def format_sentence_center(sent, pos1, pos2):
    """
    Formatieren eines Hit mit Highlighting der Keywords
    """
    if not sent:
        return ""
    # TODO: remove hack for leading delimiter from data
    if sent.startswith('\x02'):
        sent = sent[1:]
    tokens = RE_HIT_DELIMITER.findall(sent)
    for idx, token in enumerate(tokens):
        padding = ' ' if token[-1] == '\x02' else ''
        if idx == (pos1 - 1):
            tokens[idx] = "&&{}&&{}".format(token[:-1], padding)
        elif idx == (pos2 - 1):
            tokens[idx] = "_&{}&_{}".format(token[:-1], padding)
        else:
            tokens[idx] = "{}{}".format(token[:-1], padding)
    return ''.join(tokens)


# TODO further refactoring necessary: cryptic surface example!?!
def surface_mapping(surface, rel, prep, use_extended_surface_form=False):
    """
    Mapping eines (kryptischen) Oberflächenstring auf einen lesbaren Oberflächenstring
    """
    if rel == "KON":
        rel_type = 2
    elif rel.startswith("~"):
        rel_type = 1
    else:
        rel_type = 0
    if use_extended_surface_form:
        if rel_type == 1 and prep != "-" and prep != "":
            i = surface.find('<')
            if i != -1:
                surface = surface[0:i] + ' ' + prep + ' ' + surface[i + 1:]
                surface = surface.replace('<', ' ').replace('>', ' ').lstrip()
            else:
                surface = surface.replace('<', ' ').replace('>', ' ').lstrip()
                surface = surface + ' ' + prep
        elif rel_type != 1 and prep != "-":
            surface = surface.replace('<', ' ').replace('>', ' ').lstrip()
            surface = prep + ' ' + surface
        else:
            surface = surface.replace('<', ' ').replace('>', ' ').lstrip()
        return surface.replace('  ', ' ')
    else:
        i = surface.rfind('>')
        if i != -1:
            j = surface[i + 1:].rfind('<')
            if j != -1:
                surface = surface[i + 1:j + 1]
            else:
                surface = surface[i + 1:]
        else:
            j = surface[i + 1:].rfind('<')
            if j != -1:
                surface = surface[0:j + 1]

        if rel_type == 1 and prep != "-" and prep != "":
            return surface + ' ' + prep
        elif rel_type != 1 and prep != "-" and prep != "":
            return prep + ' ' + surface
        else:
            return surface
