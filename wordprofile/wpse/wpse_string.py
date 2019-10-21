import re

from wordprofile.wpse import deprecated

RE_HIT_DELIMITER = re.compile(r"[^\x01\x02]*[\x01\x02]")


def format_sentence(sent: str):
    """
    Formatieren eines Hit
    """
    if not sent:
        return ""
    return sent.replace('\x02', ' ').replace('\x01', '')


def format_sentence_center(sent, pos1, pos2, pos3):
    """
    Formatieren eines Hit mit Highlighting der Keywords
    """
    if not sent:
        return ""
    tokens = RE_HIT_DELIMITER.findall(sent)
    for idx, token in enumerate(tokens):
        padding = ' ' if token[-1] == '\x02' else ''
        if idx == (pos1 - 1):
            tokens[idx] = "&&{}&&{}".format(token[:-1], padding)
        elif idx in [pos2 - 1, pos3 - 1]:
            tokens[idx] = "_&{}&_{}".format(token[:-1], padding)
        else:
            tokens[idx] = "{}{}".format(token[:-1], padding)
    return ''.join(tokens)


@deprecated
def format_sentence_center_mwe(strSent, listPosition):
    strWord = ""
    listWords = []
    iTokCount = 1
    for i in strSent:
        if i == '\x01' or i == '\x02':

            iCount = 0
            bSuccess = False
            for j in listPosition:
                if iTokCount == j:
                    if iCount == 0:
                        listWords.append('&&')
                        listWords.append(strWord)
                        listWords.append('&&')
                        bSuccess = True
                        break
                    else:
                        listWords.append('_&')
                        listWords.append(strWord)
                        listWords.append('&_')
                        bSuccess = True
                        break
                iCount += 1

            if not bSuccess:
                listWords.append(strWord)

            if i == '\x01':
                listWords.append('')
            if i == '\x02':
                listWords.append(' ')

            iTokCount += 1
            strWord = ""
        else:
            strWord += i

    listWords.append(strWord)

    return ''.join(listWords)


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
