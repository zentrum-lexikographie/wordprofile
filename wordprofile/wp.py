#!/usr/bin/python

import logging
import math
from collections import defaultdict
from typing import List

from wordprofile.formatter import format_comparison, format_concordances, format_cooccs, format_lemma_pos
from wordprofile.wpse.OrthVariations import generate_orth_variations
from wordprofile.wpse.wpse_mysql import WpSeMySql
from wordprofile.wpse.wpse_spec import WpSeSpec

logger = logging.getLogger('wordprofile')


class Wordprofile:
    def __init__(self, db_host, db_user, db_passwd, db_name, wp_spec_file):
        logger.info("start init ...")
        self.wp_spec = WpSeSpec(wp_spec_file)
        self.wp_db = WpSeMySql(db_host, db_user, db_passwd, db_name)
        logger.info("init complete")

    def __get_ordered_relation_ids(self, relations, pos):
        """
        Gets relation ids sorted by the specified ordering
        """
        relation_order = self.wp_spec.mapRelOrder.get(pos, self.wp_spec.listRelOrder)
        ordered_rels = [i for i in relation_order if i in relations]
        return ordered_rels

    def get_lemma_and_pos(self, word: str, pos: str = '', use_external_variations: bool = True):
        """
        Die Methode ermöglicht es, zu einem gegebenen Wort die Wortprofil-Lemma/POS-IDs zu ermitteln (evtl. mehrere Part-Of-Speech Lesarten ).
        *Eingabe ist die Lemma/Oberflächen-Form eines Wortes in UTF-8 ( 'Word') (z.B. Laufen, Baum, Haus, schön, ...) zusammen mit der optionalen Angabe eines Subkorpus ( 'Subcorpus') (z.B. zeit, kern, 21jhd, ...). Zudem ist parametrisiert, ob caseinsensitiv abgefragt werden soll ( 'CaseSensitive') oder ob eine interne Liste mit abweichenden Schreibweisen verwendet werden soll ( 'UseVariations'). Diese Parameter werden über einen Dictionary übergeben:
        mapParam = {'Word':<string>, 'Subcorpus':<string>, 'CaseSensitive':<bool=0>, 'UseVariations':<bool=0>}
        hiervon sind obligatorisch: 'Word'
        *Rückgabe ist eine Liste aus: Lemmaform ( 'Lemma'), part-of-speech ( 'POS'), Lemma-ID ( 'LemmaId'), POS-ID ( 'PosId'), Anzahl der Relationen mit Doppelten ( 'Frequency'), Anzahl Relationen ohne Doppelte ( 'Count') und Liste aller möglichen Relationen ( 'Relations'), die nach Relevanz geordnet sind. Die Listeneinträge sind als dictionary abgelegt.
        """
        results = self.wp_db.get_lemma_and_pos(word, pos)
        # evtl. Variationen in der Schreibweise berücksichtigen
        if not results and use_external_variations and word in self.wp_spec.mapVariation:
            word = self.wp_spec.mapVariation[word]
            results = self.wp_db.get_lemma_and_pos(word, pos)
        # evtl. automatisch generierte Variationen der Schreibweisen berücksichtigen
        if not results and use_external_variations:
            for word in generate_orth_variations(word):
                results = self.wp_db.get_lemma_and_pos(word, pos)
                if results:
                    break
        return format_lemma_pos(results)

    def get_lemma_and_pos_diff(self, lemma1: str, lemma2: str, use_variations: bool = True):
        """
        Die Methode ermöglicht es, zu einem gegebenen Wort die Wortprofil-Lemma/POS-IDs zu ermitteln (evtl. mehrere Part-Of-Speech Lesarten ).
        mapParam = {'Word1':<string>, 'Word2':<string>, 'Subcorpus':<string>, 'CaseSensitive':<bool=False>}
        hiervon sind obligatorisch: 'Word1' und 'Word2'
        *Eingabe ist die Lemma/Oberflächen-Form des ersten Wortes in UTF-8 ('Word1') und des zweiten Vergleichswortes in UTF-8 ('Word2') (z.B. Laufen, Baum, Haus, schön, ...) zusammen mit der optionalen Angabe eines Subkorpus ( 'Subcorpus') (z.B. zeit, kern, 21jhd, ...). Zudem ist parametrisiert, ob caseinsensitiv abgefragt werden soll ( 'CaseSensitive'). Diese Parameter werden über einen Dictionary übergeben
        *Rückgabe ist eine Liste aus: erster Lemmaform ('Lemma1'), zweiter Lemmaform ('Lemma2'), erster Lemma-ID ('LemmaId1'), zweiter Lemma-ID ('LemmaId2'), part-of-speech ('POS'), POS-ID ('PosId'), Anzahl der Relationen mit Doppelten für das erste Wort ('Frequency1') und für das zweite Wort ('Frequency2'), Anzahl Relationen ohne Doppelte für das erte Wort ('Count1') und für das zweite Wort ('Count2') und Liste aller möglichen Relationen für beide Wörter ('Relations'), die nach Relevanz geordnet sind. Die Listeneinträge sind als dictionary abgelegt:
        [ {'Lemma1':<string>,'Lemma2':<string>,'POS':<string>,'LemmaId1':<int>,'LemmaId2':<int>,'PosId':<int>,'Frequency1':<int>,'Frequency2':<int>,'Count1':<int>,'Count2':<int>,'Relations:<Liste aus Strings>} , ... ]
        """
        list1 = self.get_lemma_and_pos(lemma1, use_external_variations=use_variations)
        list2 = self.get_lemma_and_pos(lemma2, use_external_variations=use_variations)
        # nur Lemmata mit der gleichen Wortart sind vergleichbar
        results = []
        for i in list1:
            for j in list2:
                if i['POS'] == j['POS']:
                    relations = list(set(i['Relations']) | set(j['Relations']))
                    results.append({
                        'LemmaId1': i['Lemma'],
                        'LemmaId2': j['Lemma'],
                        'POS': i['POS'],
                        'PosId': i['POS'],
                        'Frequency1': i['Frequency'],
                        'Frequency2': j['Frequency'],
                        'Relations': relations
                    })
        return results

    def get_relations(self, lemma: str, lemma2: str, pos: str, pos2: str = '', relations: List[str] = (),
                      start: int = 0, number: int = 20, order_by: str = 'log_dice', min_freq: int = 0,
                      min_stat: int = -1000):
        """
        Die Methode ermöglicht es, anhand einer Wortprofil-Lemma-ID und POS-ID Wortprofilrelationen abzufragen.
        *Eingabe ist ein Dictionary aus Parametern. Zu der Wortprofil-Lemma-ID ('LemmaId') und POS-ID ('PosId') sind wetere Parameter: ab dem wievielten Eintrag die Tupel zu den einzelnen Relationen zürückgegeben werden sollen ('Start'), wieviele Einträge zurückgegeben werden sollen ('Number'), nach welcher Statistik ('Frequency','MiLogFreq','MI3','logDice','AScore','logLike') sortiert werden soll ('OrderBy'), die minimal erlaubte Frequenz ('MinFreq'), der minimal erlaubte Statistikwert ('MinStat'), evtl. Angabe eines Subcorpus in dem gesucht werden soll ('Subcorpus') und bezüglich welcher Relationen abgefragt werden soll ('Relations')
        mapParam = {'LemmaId':<int>,'PosId':<int>,'Start':<int=0>,'Number':<int=20>,'OrderBy':<string='logDice'>,'MinFreq':<int=-inf>,'MinStat':<float=-inf>,'Subcorpus':<string>,'Relations':<stringlist=[]>}
        hiervon sind obligatorisch: 'LemmaId', 'PosId'
        *Rückgabe ist eine Liste aus einzelnen Relationsinformationen (als Dictionary), mit kurzem Relationsnamen ('Relation'), mit einer eindeutigen Relation-Id ('RelId'), einer kurzen Relationsbeschreibung ('Description') und den Kookkurrenztupeln ('Tuples'):
        [ {'Relation':<string>',RelId':<string>,'Description':<string>,'Tuples'<list>}, ... ]
       Die Kookkurrenztupel ('Tuples') zu einer syntaktischen Relation sind als Liste abgelegt. Ein Kookkurrenztupel enthält folgende Information: syntaktische Relation ('Relation'), Snippet ('Snippet'), Lemma des Kookkurrenzpartners ('Lemma'), Oberflächenform des Kookkurrenzpartners ('Form'), part-of-speech des Dependenten ('POS'), statistic Score ( 'Score'), Concordanz-ID für die Abfrage von MWE-Relationen und Konkordanzen ('ConcordId'), ob es MWEs zu der Kookkurrrenz gibt ('HasMwe' mit den Werten 0 oder 1),Anzahl der Belege ('ConcordNo'). Die Information 'Score' ist komplex und besteht aus einem Dictionary mit einem Eintrag für 'MiLogFreq', für 'logDice', für 'Frequency', für 'MI3', für 'AScore', für 'logLike'. Zudem wird die Gesamtanzahl der möglichen Belege zurückgegeben ('ConcordNo') und die Anzahl der anzeigbaren Belege ('ConcordNoAccessible'). Die Listeneinträge sind als dictionary abgelegt:
        [ {'Relation':<string>,'Snippet':<string>,'Lemma':<string>,'Form':<string>,'POS':<string>,'Score':{'MiLogFreq':<float>,'logDice':<float>,'Frequency':<int>},'ConcordId':<int>,'MweId':<string>,'ConcordNo':<int>,'ConcordNoAccessible':<int>}, ... ]
        Wenn der Wert von 'ConcordNo' der 0 entspricht gibt es aus rechtlichen Gründen keine Texttreffer. Dann ist 'ConcordNoAccessible' auch 0.
        """
        ordered_relations = self.__get_ordered_relation_ids(relations, pos)
        results = []
        for relation in ordered_relations:
            cooccs = self.wp_db.get_relation_tuples(lemma, lemma2, pos, pos2, start, number,
                                                    order_by, min_freq, min_stat, relation)
            # Meta-Informationen
            description = self.wp_spec.mapRelDesc.get(relation, self.wp_spec.strRelDesc)
            # ID (komplex) für die Relation+Kookkurenzen erstellen
            hit_id = "{}#{}#{}".format(lemma, pos, relation)
            results.append({
                'Relation': relation,
                'Description': description,
                'Tuples': format_cooccs(cooccs),
                'RelId': hit_id
            })
        return results

    # def get_cooccurrences(self, hit_id: str, start: int = 0, number: int = 20, order_by: str = 'log_dice', min_freq: int = 0, min_stat: int = -1000):
    #     """
    #     Die Methode ermöglicht es, anhand einer Relations-ID Kookkurrenzen für eine bestimmte Relation abzufragen
    #     (für normale Relationen und MWE-Relationen).
    #     *Eingabe ist ein Dictionary aus Parametern. Zu der Relations-ID ('RelId') sind wetere Parameter: ab dem
    #     wievielten Eintrag die Tupel zürückgegeben werden sollen ( 'Start'), wieviele Einträge zurückgegeben werden
    #     sollen ( 'Number'), nach welcher Statistik ( 'Frequency','MiLogFreq','MI3','logDice','AScore','logLike')
    #     sortiert werden soll ( 'OrderBy'), die minimal erlaubte Frequenz ( 'MinFreq'), der minimal erlaubte
    #     Statistikwert ( 'MinStat'), evtl. Angabe eines Subkorpus in dem gesucht werden soll ( 'Subcorpus')
    #     mapParam = {'RelId':<string>,'Start':<int=0>,'Number':<int=20>,'OrderBy':<string='logDice'>,
    #                 'MinFreq':<int=-inf>,'MinStat':<float=-inf>,'Subcorpus':<string>}
    #     hiervon sind obligatorisch: 'RelId'
    #     *Rückgabe ist eine Liste aus Kookkurrenztupeln. Ein Kookkurrenztupel enthält folgende Information: syntaktische
    #     Relation ('Relation'), Snippet ('Snippet'), Lemma des Kookkurrenzpartners ('Lemma'), Oberflächenform des
    #     Kookkurrenzpartners ('Form'), part-of-speech des Dependenten ('POS'), statistic Score ( 'Score'),
    #     Concordanz-ID ('ConcordId'), ob es MWEs zu der Kookkurrrenz gibt ('HasMwe' mit den Werten 0 oder 1), Anzahl der
    #     Belege ('ConcordNo'). Die Information 'Score' ist komplex und besteht aus einem Dictionary mit einem Eintrag
    #     für 'MiLogFreq', für 'logDice', für 'Frequency', für 'MI3', für 'AScore', für 'logLike'. Zudem wird die
    #     Gesamtanzahl der möglichen Belege zurückgegeben ('ConcordNo') und die Anzahl der anzeigbaren Belege
    #     ('ConcordNoAccessible'). Die Listeneinträge sind als dictionary abgelegt:
    #     [ {'Relation':<string>,'Snippet':<string>,'Lemma':<string>,'Form':<string>,'POS':<string>,
    #        'Score':{'MiLogFreq':<float>,'logDice':<float>,'Frequency':<int>},'ConcordId':<int>,'MweId':<string>,
    #        'ConcordNo':<int>,'ConcordNoAccessible':<int>}, ... ]
    #     """
    #     lemma, pos, rel = hit_id.split("#")[:3]
    #     cooccs = self.wp_db.get_relation_tuples(lemma, "", pos, "", start, number, order_by, min_freq,
    #                                             min_stat, rel)
    #     cooccs = self.__format_cooccs(cooccs)
    #     return cooccs

    def get_diff(self, lemma1: str, lemma2: str, pos: str, relations: List[str], number: int = 20,
                 order_by: str = 'log_dice', min_freq: int = 0, min_stat: int = -1000, operation: str = 'adiff',
                 use_intersection: bool = False, nbest: int = 0):
        """
        Die Methode ermöglicht es, anhand zweier Wortprofil-Lemma-IDs ('LemmaId1', 'LemmaId2')
        mit POS-ID ('POS') vergleichende Wortprofilrelationen abzufragen.
        *Eingabe ist ein Dictionary aus Parametern. Zu der Wortprofil-Lemma-IDs ('LemmaId1', 'LemmaId2') und der POS-ID ('POS') sind wetere Parameter: ab dem wievielten Eintrag die DiffTupel zu den einzelnen Relationen zürückgegeben werden sollen ('Start'), wieviele Einträge zurückgegeben werden sollen ('Number'), nach welcher Statistik ('Frequency','MiLogFreq','MI3','logDice') sortiert werden soll ('OrderBy'), die minimal erlaubte Frequenz ('MinFreq'), der minimal erlaubte Statistikwert ('MinStat'), evtl. Angabe eines Subcorpus in dem gesucht werden soll ('Subcorpus') und bezüglich welchee Relationen abgefragt werden soll (bei keiner Angabe in allen) ('Relations'). Zudem kann die Vergleichsoperation angegeben werden ('Operation'). Möglich sind 'adiff' (Wortprofil-Unterschiede), 'rmax' (Wortprofil-Gemeinsamkeiten) und experimentell 'diff', 'sum', 'min', 'max',  'avg', 'havg' und 'havg'. Über die Option 'NBest' kann bestimmt werden, dass nur n viele Tupel für Wort 1 und n viele Tupel für Wort 2 berücksichtigt werden sollen.
        mapParam = {'LemmaId1':<int>,'LemmaId2':<int>,'PosId':<int>,'Start':<int=0>,'Number':<int=20>,'OrderBy':<string='logDice'>,'MinFreq':<int=-inf>,'MinStat':<float=-inf>,'Subcorpus':<string>,'Relations':<stringlist>,'Operation':<string>,'NBest':<int=inf>}
        Hiervon sind obligatorisch: 'LemmaId1', 'LemmaId2', 'PosId' und 'Relations'
        *Rückgabe ist eine Liste aus einzelnen Relationsinformationen (als Dictionary), mit kurzem Relationsnamen ('Relation'), einer kurzen Relationsbeschreibung ('Description') und den Diff-Kookkurrenztupeln ('Tuples'):
        [ {'Relation':<string>,'Description':<string>,'Tuples'<list>}, ... ]
        Die Diff-Kookkurrenztupel ('Tuples') zu einer syntaktischen Relation sind als Liste abgelegt. Ein DiffKookkurrenztupel? enthält folgende Information: syntaktische Relation ( 'Relation'), Lemmaform des Kookkurrenzpartners ( 'Lemma'), Oberflächenform des Kookkurrenzpartners ( 'Form'), part-of-speech des Kookkurenzpartners ( 'POS'), statistic Score ( 'Score'), Concordanz-ID fürs erste word ('ConcordId1') und fürs zweite Wort ('ConcordId2'), die Farbe/Position im Diff ('Position' mit 'left', 'center' und 'right'). Die Information 'Score' ist komplex und besteht aus einem Dictionary mit einem Eintrag für 'Frequenzy1' und 'Frequenzy2' und für 'Rank1' und 'Rank2' und für 'Assoziation1' und 'Assoziation2' jeweils für Wort1 und Wort2 und dem Vergleichscore 'AScomp'. Zudem wird die Gesamtanzahl der möglichen Belege zurückgegeben ('ConcordNo1', 'ConcordNo2') und die Anzahl der anzeigbaren belege ('ConcordNoAccessible2', 'ConcordNoAccessible2'). Die Listeneinträge sind als dictionary abgelegt:
        [ {'Relation':<string>,'Form':<string>,'POS':<string>,'Score':{'Frequency1':<integer>,'Frequency2':<integer>,'Rank1':<integer>,'Rank2':<integer>,'Assoziation1':<float>,'Assoziation2':<float>,'AScomp':<float>},'ConcordId1':<int>,'ConcordId2':<int>,'ConcordNo1':<int>,'ConcordNo2':<int>,'ConcordNoAccessible1':<int>,'ConcordNoAccessible2':<int>,'Position':<string>}, ... ]
        Wenn keine ConcordId? vorhanden ist, wird '0' zurückgegeben.
        """
        ordered_relations = self.__get_ordered_relation_ids(relations, pos)
        relations = []
        for rel in ordered_relations:
            diffs = self.wp_db.get_relation_tuples_diff(lemma1, lemma2, pos, rel, order_by, min_freq, min_stat)
            diffs = self.__calculate_diff(lemma1, lemma2, diffs, number, nbest, use_intersection, operation)
            relations.append({
                'Relation': rel,
                'Description': self.wp_spec.mapRelDesc.get(rel, self.wp_spec.strRelDesc),
                'Tuples': format_comparison(diffs)
            })
        return relations

    def __calculate_diff(self, lemma1_id, lemma2_id, diffs, number, nbest, use_intersection, operation):
        """
        Berechnung des Vergleiches zweier Wortprofile
        Über die Vergleichsfunktionen lassen sich zwei Wörter anhand ihrer Wortprofile vergleichen.
        Terminologie:
            WP₁ - Menge der Kookkurrenzpartner bezüglich des Wortprofils des ersten Vergleichswortes
            WP₂ - Menge der Kookkurrenzpartner bezüglich des Wortprofils des zweiten Vergleichswortes
            s1/1 - liefert den Assoziationswert (standardmäßig logDice) zu einem Kookkurrenzpartner K ∊ WP₁ oder den Wert 0 für K ∉ WP₁
            s2/1 - liefert den Assoziationswert (standardmäßig logDice) zu einem Kookkurrenzpartner K ∊ WP₂ oder den Wert 0 für K ∉ WP₂
            r1/1 - liefert den Rang eines Kookkurenzpartners (standardmäßig nach logDice) K ∊ WP₁
            r2/1 - liefert den Rang eines Kookkurenzpartners (standardmäßig nach logDice) K ∊ WP₂
            L - die Maximale Anzahl an Kookurrenzpartnern die für eine grammatische Relation angezeigt werden soll
        Union:
            1. calculate absolute difference (adiff) for all pairs: |s₁(K)-s₂(K)| for all K ∊ WP₁ ∪ WP₂
            2. sort and choose nbest
            3. calculate true difference (diff) for all pairs: s₁(K)-s₂(K) for all K ∊ WP₁ ∪ WP₂
            4. sort again
        Intersect:
            1. compute max rank (rmax) for all pairs: max(r₁(K),r₂(K)) for all K ∊ WP₁ ∩ WP₂
            2. sort and choose nbest
        """
        diffs_grouped = defaultdict(dict)
        lemma1_ctr = lemma2_ctr = 0
        for i, c in enumerate(diffs):
            if nbest and lemma1_ctr > nbest and lemma2_ctr > nbest:
                break
            if c.Lemma1 == lemma1_id:
                if not nbest or lemma1_ctr <= nbest:
                    diffs_grouped[c.Lemma2]['coocc_1'] = c
                    diffs_grouped[c.Lemma2]['rank_1'] = i
                    diffs_grouped[c.Lemma2]['pos'] = c.Pos1
                lemma1_ctr += 1
            elif c.Lemma1 == lemma2_id:
                if not nbest or lemma2_ctr <= nbest:
                    diffs_grouped[c.Lemma2]['coocc_2'] = c
                    diffs_grouped[c.Lemma2]['rank_2'] = i
                    diffs_grouped[c.Lemma2]['pos'] = c.Pos1
                lemma2_ctr += 1
            else:
                raise ValueError("Unexpected lemma")
        # for intersection, only a subset is used further
        if use_intersection:
            diffs_grouped = [d for d in diffs_grouped.values() if 'coocc_1' in d and 'coocc_2' in d]
        else:
            diffs_grouped = list(diffs_grouped.values())
        # compute score based on occurring cooccs
        for d in diffs_grouped:
            if 'coocc_1' in d and 'coocc_2' in d:
                d['score'] = self.__diff_operation(operation, d['coocc_1'].LogDice, d['coocc_2'].LogDice, d['rank_1'],
                                                   d['rank_2'])
            elif 'coocc_1' in d:
                d['score'] = self.__diff_operation(operation, d['coocc_1'].LogDice, 0, d['rank_1'], 0)
            elif 'coocc_2' in d:
                d['score'] = self.__diff_operation(operation, 0, d['coocc_2'].LogDice, 0, d['rank_2'])
        # final sort and cut after nbest cooccs
        if operation in ["adiff", "ardiff"]:
            diffs_grouped.sort(key=lambda x: math.fabs(x['score']), reverse=True)
            diffs_grouped = diffs_grouped[:number]
            diffs_grouped.sort(key=lambda x: x['score'], reverse=True)
        elif operation == "rmax":
            diffs_grouped.sort(key=lambda x: x['score'])
            diffs_grouped = diffs_grouped[:number]
        else:
            diffs_grouped.sort(key=lambda x: x['score'], reverse=True)
            diffs_grouped = diffs_grouped[:number]
        return diffs_grouped

    def __diff_operation(self, strOperation, Sa, Sb, Ra, Rb):
        """
        Berechnen der Nummerischen Diff-Operation (Wert, der den Kookkurrenztupeln zugewiesen wird)
        Gegeben sind der Statistikwert des ersten Lemmas (Sa) und des zweiten Lemmas (Sb). Des Weiteren
        seigegeben der Rank des ersten Lemma (Ra) und des zweiten Lemma (Rb).
        möglich sind:
        """
        if strOperation == "diff":
            iScore = Sa - Sb
        elif strOperation == "adiff":
            iScore = math.fabs(Sa - Sb)
        elif strOperation == "max":
            iScore = max(Sa, Sb)
        elif strOperation == "rmax":
            iScore = max(Ra, Rb)
        elif strOperation == "avg":
            iScore = (Sa + Sb) / 2
        else:
            raise ValueError("Unknown operation")

        return iScore

    def get_relation_by_info_id(self, coocc_id: int):
        """
        Die Funktion ermöglicht es, anhand einer Concordanz-ID ('InfoId') eine Relation abzufragen.
        mapParam = {'InfoId':<int>}
        hiervon sind obligatorisch: 'InfoId'
        *Rückgabe ist ein Dictionary aus: syntaktischer Relation ('Relation'), Lemmaform von W1 ('Lemma1'), Lemmaform von W2 ('Lemma2'), POS-Tag von W1 ('POS1'), POS-Tag von W2 ('POS2'), Oberflächenform von W1 ('Form1'), Oberflächenform von W2 ('Form2'):
        {'Relation':<string>,'Lemma1':<string>,'Lemma2':<string>,'POS1':<string>,'POS2':<string>,'Form1':<string>,'Form2':<string>}
        """
        coocc_info = self.wp_db.get_relation_by_id(coocc_id)
        if coocc_info.rel in self.wp_spec.mapRelDescDetail:
            description = self.wp_spec.mapRelDescDetail[coocc_info.rel]
            description = description.replace('$1', coocc_info.lemma1)
            description = description.replace('$2', coocc_info.lemma2)
        else:
            description = ""
        return {'Description': description, 'Relation': coocc_info.rel,
                'Lemma1': coocc_info.lemma1, 'Lemma2': coocc_info.lemma2,
                'POS1': coocc_info.pos1, 'POS2': coocc_info.pos2}

    def get_concordances_and_relation(self, coocc_id: int, use_context: bool = False, start_index: int = 0,
                                      result_number: int = 20):
        """
        Diese Methode ist ein Mix aus 'get_concordances' und 'get_relation_by_info_id'.
        Die Eingabe gleicht der Eingabe bei der Methode 'get_concordances'
        Rückgabe ist ein Dictionary mit: Relationsbeschreibung ('Description', z.B.: Mann ist Subjekt von laufen), Lemmaform von W1 ( 'Lemma1'), Lemmaform von W2 ( 'Lemma2'), POS-Tag von W1 ( 'POS1'), POS-Tag von W2 ( 'POS2'), Oberflächenform von W1 ( 'Form1'), Oberflächenform von W2 ( 'Form2') und einer Liste mit Konkordanz-Informationen ( 'Tuples') die dem Format der Rückgabe von 'get_concordances' entspricht:
        {'Relation':<string>,'Description':<string>,'Lemma1':<string>,'Lemma2':<string>,'POS1':<string>,'POS2':<string>,'Form1':<string>,'Form2':<string>,'Tuples':[ {'Bibl': {'Corpus':<string>,'Date':<string>,'TextClass':<string>,'Orig':<string>* ,'Scan':<string> ,'Page':<string>}, 'ConcordLine':<string>, 'ConcordLeft':<string>, 'ConcordRight':<string>} , ... ]}
        """
        relation = self.get_relation_by_info_id(coocc_id)
        relation['Tuples'] = self.get_concordances(coocc_id, use_context, start_index, result_number)
        return relation

    def get_concordances(self, coocc_id: int, use_context: bool = False, start_index: int = 0, result_number: int = 20):
        return format_concordances(self.wp_db.get_concordances(coocc_id, use_context, start_index, result_number))
