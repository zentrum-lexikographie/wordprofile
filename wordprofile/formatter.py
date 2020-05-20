#!/usr/bin/python3

import re
from collections import defaultdict
from typing import List

from wordprofile.datatypes import Coocc, Concordance, LemmaInfo, MweConcordance

RE_HIT_DELIMITER = re.compile(r'([^\x01\x02]+)([\x01\x02])')


def format_lemma_pos(db_results: List[LemmaInfo]):
    """Converts lemma-pos items with their information (relations, frequencies) into output format
    """
    lemma_pos_mapping = defaultdict(list)
    for i in sorted(db_results, key=lambda x: x.freq, reverse=True):
        relation = "~" + i.rel if i.inv else i.rel
        lemma_pos_mapping[(i.lemma, i.tag)].append((relation, int(i.freq)))

    results = []
    for (lemma, pos), rel_freqs in lemma_pos_mapping.items():
        relations, frequencies = zip(*rel_freqs)
        if len(relations) > 1:
            relations = ('META',) + relations
        results.append({'Lemma': lemma, 'POS': pos, 'PosId': pos,
                        'Frequency': sum(frequencies), 'Relations': relations})
    return results


def format_cooccs(cooccs: List[Coocc]):
    """Converts co-occurrences into output format
    """
    results = []
    for coocc in cooccs:
        concord_no = coocc.Frequency
        if coocc.Rel == 'KON' and coocc.Lemma1 == coocc.Lemma2:
            concord_no = concord_no // 2
        results.append({
            'Relation': '~' if coocc.inverse else '' + coocc.Rel,
            'POS': coocc.Pos2,
            'PosId': coocc.Pos2,
            'Lemma': coocc.Lemma2,
            'Score': {
                'Frequency': coocc.Frequency // 2,
                #     'MiLogFreq': coocc.Score_MiLogFreq,
                #     'log_dice': coocc.Score_logDice,
                'logDice': coocc.LogDice,
                #     'MI3': coocc.Score_MI3,
            },
            'ConcordId': coocc.RelId,
            'ConcordNo': concord_no,
            'ConcordNoAccessible': concord_no
        })
    return results


def format_concordances(concords: List[Concordance]):
    """Converts concordances into output format
    """
    results = []
    for c in concords:
        sentence_left = format_sentence(c.sentence_left)
        sentence_right = format_sentence(c.sentence_right)
        sentence_main = format_sentence_and_highlight(c.sentence, c.token_position_1, c.token_position_2,
                                                      c.prep_position if c.prep_position > 0 else None)
        results.append({
            'Bibl': {
                'Corpus': c.corpus,
                'Date': c.date.strftime('%d-%m-%Y'),
                'TextClass': c.textclass,
                'Orig': c.orig.replace('#page#', c.page),
                'Scan': c.scan.replace('#page#', c.page),
                'Avail': c.avail,
                'Page': c.page,
                'File': c.file,
            },
            'ConcordLine': sentence_main,
            'ConcordLeft': sentence_left,
            'ConcordRight': sentence_right,
            'Score': c.score
        })
    return results


def format_mwe_concordances(concords: List[MweConcordance]):
    """Converts concordances into output format
    """
    results = []
    for c in concords:
        sentence_left = format_sentence(c.sentence_left)
        sentence_right = format_sentence(c.sentence_right)
        positions = list({c.token1_position_1, c.token1_position_2, c.prep1_position,
                          c.token2_position_1, c.token2_position_2, c.prep2_position})
        sentence_main = format_mwe_sentence_and_highlight(c.sentence, positions)
        results.append({
            'Bibl': {
                'Corpus': c.corpus,
                'Date': c.date.strftime('%d-%m-%Y'),
                'TextClass': c.textclass,
                'Orig': c.orig.replace('#page#', c.page),
                'Scan': c.scan.replace('#page#', c.page),
                'Avail': c.avail,
                'Page': c.page,
                'File': c.file,
            },
            'ConcordLine': sentence_main,
            'ConcordLeft': sentence_left,
            'ConcordRight': sentence_right,
            'Score': c.score
        })
    return results


def format_comparison(diffs):
    """Converts co-occurrence comparisons into output format
    """
    results = []
    for diff in diffs:
        # create result with common/default values
        coocc_diff = {
            'POS': diff['pos'],
            'ConcordId1': 0,
            'ConcordId2': 0,
            'ConcordNo1': 0,
            'ConcordNo2': 0,
            'ConcordNoAccessible1': 0,
            'ConcordNoAccessible2': 0,
            'Score': {
                'AScomp': diff.get('score'),
                'Rank1': diff.get('rank_1', -1),
                'Rank2': diff.get('rank_2', -1),
                'Frequency1': 0,
                'Assoziation1': 0.0,
                'Frequency2': 0,
                'Assoziation2': 0.0,
            }
        }
        # complete information for first coocc
        if 'coocc_1' in diff:
            coocc_diff['Score']['Frequency1'] = diff['coocc_1'].Frequency
            coocc_diff['Score']['Assoziation1'] = diff['coocc_1'].LogDice
            coocc_diff['ConcordId1'] = diff['coocc_1'].RelId
            concord_no = diff['coocc_1'].Frequency
            if diff['coocc_1'].Rel == "KON" and diff['coocc_1'].Lemma1 == diff['coocc_1'].Lemma2:
                concord_no = concord_no / 2
            coocc_diff['ConcordNo1'] = concord_no
            coocc_diff['Relation'] = diff['coocc_1'].Rel
            coocc_diff['Lemma'] = diff['coocc_1'].Lemma2
            coocc_diff['Form'] = diff['coocc_1'].Lemma2
            if 'coocc_2' in diff:
                coocc_diff['Position'] = 'left'
            else:
                coocc_diff['Position'] = 'center'
        # complete information for second coocc
        if 'coocc_2' in diff:
            coocc_diff['Score']['Frequency2'] = diff['coocc_2'].Frequency
            coocc_diff['Score']['Assoziation2'] = diff['coocc_2'].LogDice
            coocc_diff['ConcordId2'] = diff['coocc_2'].RelId
            concord_no = diff['coocc_2'].Frequency
            if diff['coocc_2'].Rel == "KON" and diff['coocc_2'].Lemma1 == diff['coocc_2'].Lemma2:
                concord_no = concord_no / 2
            coocc_diff['ConcordNo2'] = concord_no
            if 'coocc_1' not in diff:
                coocc_diff['Relation'] = diff['coocc_2'].Rel
                coocc_diff['Lemma'] = diff['coocc_2'].Lemma2
                coocc_diff['Form'] = diff['coocc_2'].Lemma2
                coocc_diff['Position'] = 'right'
        results.append(coocc_diff)
    return results


def format_sentence(sent: str) -> str:
    """Format of single concordance sentence.

    All special characters are removed from the concordance taken from the database.
    """
    if not sent:
        return ""
    return sent.replace('\x02', ' ').replace('\x01', '').strip()


def format_sentence_and_highlight(sent: str, pos1: int, pos2: int, pos3=None) -> str:
    """Format concordance sentence and highlight certain positions.
    """
    if not sent:
        return ""
    # TODO: remove hack for leading delimiter from data
    if sent.startswith('\x02'):
        sent = sent[1:]
    sent += '\x01'
    tokens = RE_HIT_DELIMITER.findall(sent)
    for idx, (token, delim) in enumerate(tokens):
        padding = ' ' if delim == '\x02' else ''
        if idx == (pos1 - 1):
            tokens[idx] = "&&{}&&{}".format(token, padding)
        elif idx == (pos2 - 1):
            tokens[idx] = "_&{}&_{}".format(token, padding)
        elif pos3 and idx == (pos3 - 1):
            tokens[idx] = "_&{}&_{}".format(token, padding)
        else:
            tokens[idx] = "{}{}".format(token, padding)
    return ''.join(tokens)


def format_mwe_sentence_and_highlight(sent: str, positions: List[int]) -> str:
    """Format concordance sentence and highlight certain positions.
    """
    if not sent:
        return ""
    # TODO: remove hack for leading delimiter from data
    if sent.startswith('\x02'):
        sent = sent[1:]
    sent += '\x01'
    tokens = RE_HIT_DELIMITER.findall(sent)
    for idx, (token, delim) in enumerate(tokens):
        padding = ' ' if delim == '\x02' else ''
        if (idx + 1) in positions:
            tokens[idx] = "&&{}&&{}".format(token, padding)
        else:
            tokens[idx] = "{}{}".format(token, padding)
    return ''.join(tokens)
