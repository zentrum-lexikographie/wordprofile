#!/usr/bin/python

import logging
import math
from collections import defaultdict

from wordprofile.wpse import deprecated
from wordprofile.wpse.OrthVariations import generate_orth_variations
from wordprofile.wpse.wpse_mysql import WpSeMySql
from wordprofile.wpse.wpse_spec import WpSeSpec
from wordprofile.wpse.wpse_string import format_sentence, format_sentence_center

logger = logging.getLogger('wordprofile')


class Wordprofile:
    def __init__(self, db_host, db_user, db_passwd, db_name, db_port, wp_spec_file):
        logger.info("start init ...")
        self.wp_spec = WpSeSpec(wp_spec_file)
        self.wp_db = WpSeMySql(db_host, db_user, db_passwd, db_name)
        logger.info("init complete")

    def status(self):
        """
        Status-Function für "icinga". Es wird geprüft, ob der Server einwandfrei funktioniert.
        Hierzu werden Testweise Kookkurrenzen zu einem Wort abgefragt.
        """
        raise NotImplementedError()

    def get_info(self):
        raise NotImplementedError()

    def __get_ordered_relation_ids(self, relations, pos):
        """
        Gets relation ids sorted by the specified ordering
        """
        relation_order = self.wp_spec.mapRelOrder.get(pos, self.wp_spec.listRelOrder)
        ordered_rels = [i for i in relation_order if i in relations]
        return ordered_rels

    def get_lemma_and_pos(self, params):
        """
        Die Methode ermöglicht es, zu einem gegebenen Wort die Wortprofil-Lemma/POS-IDs zu ermitteln (evtl. mehrere Part-Of-Speech Lesarten ).
        *Eingabe ist die Lemma/Oberflächen-Form eines Wortes in UTF-8 ( 'Word') (z.B. Laufen, Baum, Haus, schön, ...) zusammen mit der optionalen Angabe eines Subkorpus ( 'Subcorpus') (z.B. zeit, kern, 21jhd, ...). Zudem ist parametrisiert, ob caseinsensitiv abgefragt werden soll ( 'CaseSensitive') oder ob eine interne Liste mit abweichenden Schreibweisen verwendet werden soll ( 'UseVariations'). Diese Parameter werden über einen Dictionary übergeben:
        mapParam = {'Word':<string>, 'Subcorpus':<string>, 'CaseSensitive':<bool=0>, 'UseVariations':<bool=0>}
        hiervon sind obligatorisch: 'Word'
        *Rückgabe ist eine Liste aus: Lemmaform ( 'Lemma'), part-of-speech ( 'POS'), Lemma-ID ( 'LemmaId'), POS-ID ( 'PosId'), Anzahl der Relationen mit Doppelten ( 'Frequency'), Anzahl Relationen ohne Doppelte ( 'Count') und Liste aller möglichen Relationen ( 'Relations'), die nach Relevanz geordnet sind. Die Listeneinträge sind als dictionary abgelegt.
        """
        use_external_variations = bool(params.get('UseVariations', True))
        word = params.get("Word")
        pos = params.get("POS", "")

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

        return results

    def get_lemma_and_pos_diff(self, params):
        """
        Die Methode ermöglicht es, zu einem gegebenen Wort die Wortprofil-Lemma/POS-IDs zu ermitteln (evtl. mehrere Part-Of-Speech Lesarten ).
        mapParam = {'Word1':<string>, 'Word2':<string>, 'Subcorpus':<string>, 'CaseSensitive':<bool=False>}
        hiervon sind obligatorisch: 'Word1' und 'Word2'
        *Eingabe ist die Lemma/Oberflächen-Form des ersten Wortes in UTF-8 ('Word1') und des zweiten Vergleichswortes in UTF-8 ('Word2') (z.B. Laufen, Baum, Haus, schön, ...) zusammen mit der optionalen Angabe eines Subkorpus ( 'Subcorpus') (z.B. zeit, kern, 21jhd, ...). Zudem ist parametrisiert, ob caseinsensitiv abgefragt werden soll ( 'CaseSensitive'). Diese Parameter werden über einen Dictionary übergeben
        *Rückgabe ist eine Liste aus: erster Lemmaform ('Lemma1'), zweiter Lemmaform ('Lemma2'), erster Lemma-ID ('LemmaId1'), zweiter Lemma-ID ('LemmaId2'), part-of-speech ('POS'), POS-ID ('PosId'), Anzahl der Relationen mit Doppelten für das erste Wort ('Frequency1') und für das zweite Wort ('Frequency2'), Anzahl Relationen ohne Doppelte für das erte Wort ('Count1') und für das zweite Wort ('Count2') und Liste aller möglichen Relationen für beide Wörter ('Relations'), die nach Relevanz geordnet sind. Die Listeneinträge sind als dictionary abgelegt:
        [ {'Lemma1':<string>,'Lemma2':<string>,'POS':<string>,'LemmaId1':<int>,'LemmaId2':<int>,'PosId':<int>,'Frequency1':<int>,'Frequency2':<int>,'Count1':<int>,'Count2':<int>,'Relations:<Liste aus Strings>} , ... ]
        """
        list1 = self.get_lemma_and_pos({
            "Word": params["Word1"],
            "UseVariations": bool(params.get('UseVariations', True))
        })
        list2 = self.get_lemma_and_pos({
            "Word": params["Word2"],
            "UseVariations": bool(params.get('UseVariations', True))
        })
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

    @deprecated
    def __gen_rel_cooccurrence_mapping(self, diffs):
        """
        Ermitteln eines Mapping von Relation-Id auf die Zeile innerhalb
        einer Liste von Kookkurenzinformationen (listData)
        """
        mapRelData = {}
        # Position der Relation-Information
        iCounter = 0
        for i in diffs:
            if i.Rel in mapRelData:
                mapRelData[i.Rel].append(iCounter)
            else:
                mapRelData[i.Rel] = [iCounter]
            iCounter += 1
        return mapRelData

    def get_relations(self, params):
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
        lemma = params["Lemma"]
        lemma2 = params.get("Lemma2", "")
        pos = params["POS"]
        pos2 = params.get("Pos2Id", "")
        relations = params.get("Relations", [])
        start = params.get("Start", 0)
        number = params.get("Number", 20)
        order_by = params.get("OrderBy", "logDice")
        order_by = 'log_dice' if order_by.lower() == 'logdice' else 'frequency'
        min_freq = params.get("MinFreq", -100000000)
        min_stat = params.get("MinStat", -100000000)

        ordered_relations = self.__get_ordered_relation_ids(relations, pos)
        results = []
        for relation in ordered_relations:
            cooccs = self.wp_db.get_relation_tuples(lemma, lemma2, pos, pos2, start, number,
                                                    order_by, min_freq, min_stat, relation)
            # IDs in den Kookkurenzlisten auf Strings abbilden
            cooccs = self.__relation_tuples_2_strings(cooccs)
            # Meta-Informationen
            description = self.wp_spec.mapRelDesc.get(relation, self.wp_spec.strRelDesc)
            # ID (komplex) für die Relation+Kookkurenzen erstellen
            hit_id = "{}#{}#{}".format(lemma, pos, relation)
            results.append({'Relation': relation, 'Description': description, 'Tuples': cooccs, 'RelId': hit_id})

        return results

    def get_cooccurrences(self, params):
        """
        Die Methode ermöglicht es, anhand einer Relations-ID Kookkurrenzen für eine bestimmte Relation abzufragen
        (für normale Relationen und MWE-Relationen).
        *Eingabe ist ein Dictionary aus Parametern. Zu der Relations-ID ('RelId') sind wetere Parameter: ab dem
        wievielten Eintrag die Tupel zürückgegeben werden sollen ( 'Start'), wieviele Einträge zurückgegeben werden
        sollen ( 'Number'), nach welcher Statistik ( 'Frequency','MiLogFreq','MI3','logDice','AScore','logLike')
        sortiert werden soll ( 'OrderBy'), die minimal erlaubte Frequenz ( 'MinFreq'), der minimal erlaubte
        Statistikwert ( 'MinStat'), evtl. Angabe eines Subkorpus in dem gesucht werden soll ( 'Subcorpus')
        mapParam = {'RelId':<string>,'Start':<int=0>,'Number':<int=20>,'OrderBy':<string='logDice'>,
                    'MinFreq':<int=-inf>,'MinStat':<float=-inf>,'Subcorpus':<string>}
        hiervon sind obligatorisch: 'RelId'
        *Rückgabe ist eine Liste aus Kookkurrenztupeln. Ein Kookkurrenztupel enthält folgende Information: syntaktische
        Relation ('Relation'), Snippet ('Snippet'), Lemma des Kookkurrenzpartners ('Lemma'), Oberflächenform des
        Kookkurrenzpartners ('Form'), part-of-speech des Dependenten ('POS'), statistic Score ( 'Score'),
        Concordanz-ID ('ConcordId'), ob es MWEs zu der Kookkurrrenz gibt ('HasMwe' mit den Werten 0 oder 1), Anzahl der
        Belege ('ConcordNo'). Die Information 'Score' ist komplex und besteht aus einem Dictionary mit einem Eintrag
        für 'MiLogFreq', für 'logDice', für 'Frequency', für 'MI3', für 'AScore', für 'logLike'. Zudem wird die
        Gesamtanzahl der möglichen Belege zurückgegeben ('ConcordNo') und die Anzahl der anzeigbaren Belege
        ('ConcordNoAccessible'). Die Listeneinträge sind als dictionary abgelegt:
        [ {'Relation':<string>,'Snippet':<string>,'Lemma':<string>,'Form':<string>,'POS':<string>,
           'Score':{'MiLogFreq':<float>,'logDice':<float>,'Frequency':<int>},'ConcordId':<int>,'MweId':<string>,
           'ConcordNo':<int>,'ConcordNoAccessible':<int>}, ... ]
        """
        hit_id = params["RelId"]
        start = params.get("Start", 0)
        number = params.get("Number", 20)
        order_by = params.get("OrderBy", "logDice")
        order_by = 'log_dice' if order_by.lower() == 'logdice' else 'frequency'
        min_freq = params.get("MinFreq", -100000000)
        min_stat = params.get("MinStat", -100000000)

        # Informationen aus der komplexen ID extrahieren
        lemma, pos, rel = hit_id.split("#")[:3]
        cooccs = self.wp_db.get_relation_tuples(lemma, "", pos, "", start, number, order_by, min_freq,
                                                min_stat, rel)
        cooccs = self.__relation_tuples_2_strings(cooccs)
        return cooccs

    def __relation_tuples_2_strings(self, cooccs):
        """
        Methode, um IDs in den Kookkurenzlisten auf Strings abzubilden
        """
        results = []
        for coocc in cooccs:
            result = {
                'Relation': "~" if coocc.inverse else "" + coocc.Rel,
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
                "ConcordId": coocc.RelId
            }

            # Berechnen der Frequenz und der Anzahl der Belege bei symmetrischen Relationen
            concord_no = coocc.Frequency
            # support_no = coocc.FreqBelege
            if coocc.Rel == "KON" and coocc.Lemma1 == coocc.Lemma2:
                concord_no = concord_no // 2
                # support_no = support_no / 2
            result['ConcordNo'] = concord_no
            # result['ConcordNoAccessible'] = support_no
            result['ConcordNoAccessible'] = concord_no
            results.append(result)
        return results

    def __format_concordances(self, concords):
        results = []
        for c in concords:
            sentence_left = format_sentence(c.sentence_left)
            sentence_right = format_sentence(c.sentence_right)
            if not c.sentence:
                logger.info("skip line: None in table!")
                continue
            bib_entry = {
                "Corpus": c.corpus,
                "Date": c.date.strftime("%d-%m-%Y"),
                "TextClass": c.textclass,
                "Orig": c.orig.replace('#page#', c.page),
                "Scan": c.scan.replace('#page#', c.page),
                "Avail": c.avail,
                "Page": c.page,
                "File": c.file,
            }
            sentence_main = format_sentence_center(c.sentence, c.token_position_1, c.token_position_2,
                                                   c.prep_position if c.prep_position > 0 else None)
            results.append({
                "Bibl": bib_entry,
                "ConcordLine": sentence_main,
                "ConcordLeft": sentence_left,
                "ConcordRight": sentence_right,
                "Score": c.score
            })
        return results

    def get_diff(self, params):
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
        lemma1 = params["LemmaId1"]
        lemma2 = params["LemmaId2"]
        pos = params["POS"]
        cooccs = params["Relations"]
        number = params.get("Number", 20)
        order_by = params.get("OrderBy", "logDice")
        order_by = 'log_dice' if order_by.lower() == 'logdice' else 'frequency'
        min_freq = params.get("MinFreq", -100000000)
        min_stat = params.get("MinStat", -100000000)

        operation = params.get("Operation", "adiff")
        use_intersection = params.get("Intersection", False)
        nbest = int(params.get("NBest", 0))

        ordered_relations = self.__get_ordered_relation_ids(cooccs, pos)
        relations = []
        for rel in ordered_relations:
            diffs = self.wp_db.get_relation_tuples_diff(lemma1, lemma2, pos, rel, order_by, min_freq, min_stat)
            diffs = self.__calculate_diff(lemma1, lemma2, diffs, number, nbest, use_intersection, operation)
            diffs = self.__format_comparison(diffs)
            relations.append({
                'Relation': rel,
                'Description': self.wp_spec.mapRelDesc.get(rel, self.wp_spec.strRelDesc),
                'Tuples': diffs
            })
        return relations

    def get_intersection(self, mapParam):
        """
        Indirekter aufruf von get_diff mit der Operation 'rmax'
        """
        mapParam['Operation'] = 'rmax'
        mapParam['Intersection'] = True
        return self.get_diff(mapParam)

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
                d['score'] = self.__diff_operation(operation, d['coocc_1'].LogDice, d['coocc_2'].LogDice, d['rank_1'], d['rank_2'])
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

    def __format_comparison(self, diffs):
        """
        Methode, um IDs in den Diff-Kookkurenzlisten auf Strings abzubilden
        """
        coocc_diffs = []
        for d in diffs:
            coocc_diff = {
                'POS': d['pos'],
                'ConcordId1': 0,
                'ConcordId2': 0,
                'ConcordNo1': 0,
                'ConcordNo2': 0,
                'ConcordNoAccessible1': 0,
                'ConcordNoAccessible2': 0,
                'Score': {
                    'AScomp': d.get('score'),
                    'Rank1': d.get('rank_1', -1),
                    'Rank2': d.get('rank_2', -1),
                    'Frequency1': 0,
                    'Assoziation1': 0.0,
                    'Frequency2': 0,
                    'Assoziation2': 0.0,
                }
            }
            if 'coocc_1' in d:
                # Es gibt Kookkurenzen zum ersten Wort
                coocc_diff['Score']['Frequency1'] = d['coocc_1'].Frequency
                coocc_diff['Score']['Assoziation1'] = d['coocc_1'].LogDice
                coocc_diff['ConcordId1'] = d['coocc_1'].RelId

                iConcordNo1 = d['coocc_1'].Frequency
                if d['coocc_1'].Rel == "KON" and d['coocc_1'].Lemma1 == d['coocc_1'].Lemma2:
                    iConcordNo1 = iConcordNo1 / 2
                coocc_diff['ConcordNo1'] = iConcordNo1
                coocc_diff['Relation'] = d['coocc_1'].Rel
                coocc_diff['Lemma'] = d['coocc_1'].Lemma2
                coocc_diff['Form'] = d['coocc_1'].Lemma2

                if 'coocc_2' in d:
                    coocc_diff['Position'] = 'left'
                else:
                    coocc_diff['Position'] = 'center'
            if 'coocc_2' in d:
                # Es gibt Kookkurenzen zum zweiten Wort
                coocc_diff['Score']['Frequency2'] = d['coocc_2'].Frequency
                coocc_diff['Score']['Assoziation2'] = d['coocc_2'].LogDice
                coocc_diff['ConcordId2'] = d['coocc_2'].RelId

                iConcordNo2 = d['coocc_2'].Frequency
                if d['coocc_2'].Rel == "KON" and d['coocc_2'].Lemma1 == d['coocc_2'].Lemma2:
                    iConcordNo2 = iConcordNo2 / 2
                coocc_diff['ConcordNo2'] = iConcordNo2
                if 'coocc_1' not in d:
                    coocc_diff['Relation'] = d['coocc_2'].Rel
                    coocc_diff['Lemma'] = d['coocc_2'].Lemma2
                    coocc_diff['Form'] = d['coocc_2'].Lemma2
                    coocc_diff['Position'] = 'right'
            coocc_diffs.append(coocc_diff)

        return coocc_diffs

    def get_relation_by_info_id(self, params):
        """
        Die Funktion ermöglicht es, anhand einer Concordanz-ID ('InfoId') eine Relation abzufragen.
        mapParam = {'InfoId':<int>}
        hiervon sind obligatorisch: 'InfoId'
        *Rückgabe ist ein Dictionary aus: syntaktischer Relation ('Relation'), Lemmaform von W1 ('Lemma1'), Lemmaform von W2 ('Lemma2'), POS-Tag von W1 ('POS1'), POS-Tag von W2 ('POS2'), Oberflächenform von W1 ('Form1'), Oberflächenform von W2 ('Form2'):
        {'Relation':<string>,'Lemma1':<string>,'Lemma2':<string>,'POS1':<string>,'POS2':<string>,'Form1':<string>,'Form2':<string>}
        """
        coocc_id = int(params.get("InfoId"))
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

    def get_concordances_and_relation(self, params):
        """
        Diese Methode ist ein Mix aus 'get_concordances' und 'get_relation_by_info_id'.
        Die Eingabe gleicht der Eingabe bei der Methode 'get_concordances'
        Rückgabe ist ein Dictionary mit: Relationsbeschreibung ('Description', z.B.: Mann ist Subjekt von laufen), Lemmaform von W1 ( 'Lemma1'), Lemmaform von W2 ( 'Lemma2'), POS-Tag von W1 ( 'POS1'), POS-Tag von W2 ( 'POS2'), Oberflächenform von W1 ( 'Form1'), Oberflächenform von W2 ( 'Form2') und einer Liste mit Konkordanz-Informationen ( 'Tuples') die dem Format der Rückgabe von 'get_concordances' entspricht:
        {'Relation':<string>,'Description':<string>,'Lemma1':<string>,'Lemma2':<string>,'POS1':<string>,'POS2':<string>,'Form1':<string>,'Form2':<string>,'Tuples':[ {'Bibl': {'Corpus':<string>,'Date':<string>,'TextClass':<string>,'Orig':<string>* ,'Scan':<string> ,'Page':<string>}, 'ConcordLine':<string>, 'ConcordLeft':<string>, 'ConcordRight':<string>} , ... ]}
        """
        relation = self.get_relation_by_info_id(params)
        relation['Tuples'] = self.get_concordances(params)
        return relation

    def get_concordances(self, params):
        """
        Die Methode ermöglicht es, anhand einer Concord-ID Texttreffer abzufragen.
        *Eingabe ist die Concordanz-ID ( 'InfoId') und ein Range von Belegen (Startpunkt ( 'Start') und Anzahl ( 'Number')) und die Angabe, ob nach Datum/Quality-Score absteigend sortiert werden soll ( 'DateDesc'), ob nach Quality-Score sortiert werden soll ('UseScore') und evtl. ein Subcorpus ( 'Subcorpus'). Über die Option 'UseContext' kann zudem angegeben werden ob zusätzlich ein lechter und linker Satz zurückgegeben werden soll. Des Weiteren kann über 'InternalUser' angegeben werden, ob rechtebehaftete Inhalte angezeigt werden. Diese Parameter werden über einen dictionary übergeben:
        mapParam = {'InfoId':<int/string>,'Start':<int=0>,'Number':<int=20> ,'InternalUser':<bool> ,'Subcorpus':<string> ,'UseScore':<bool=0> ,'UseContext':<bool=0> ,'DateDesc':<bool=1>}
        Hiervon sind obligatorisch: 'InfoId'

        *Rückgabe ist eine liste von Trefferinformationen. eine Trefferinformation ist ein Dictionary aus 'Bibl', 'ConcordLine', 'ConcordLeft' und 'ConcordRight' wobei 'Bibl' einen dictionary bibliographischer Einträge als wert hat ( 'Corpus','Date', 'TextClass', 'Orig', 'Scan','Page') und 'ConcordLine' den Beleg. Die Primäre Fundstelle im Beleg ist mit && (links) und && (rechts) markiert. Die sekundären Fundstellen sind mit _& (links) und &_(rechts) markiert.
        [ {'Bibl': {'Corpus':<string>,'Date':<string>,'TextClass':<string>,'Orig':<string> ,'Scan':<string> ,'Page':<string>}, 'ConcordLine':<string>, 'ConcordLeft':<string>, 'ConcordRight':<string>} , ... ]
        """
        coocc_id = int(params.get("InfoId"))
        use_context = bool(params.get("UseContext", False))
        start_index = params.get("Start", 0)
        result_number = params.get("Number", 20)
        return self.__format_concordances(self.wp_db.get_concordances(coocc_id, use_context,
                                                                      start_index, result_number))
