#!/usr/bin/python

import logging
import math
import xmlrpc.server
from functools import cmp_to_key

from wordprofile.wpse import deprecated
from wordprofile.wpse.OrthVariations import generate_orth_variations
from wordprofile.wpse.wpse_mysql import WpSeMySql
from wordprofile.wpse.wpse_spec import WpSeSpec

logger = logging.getLogger('wordprofile')


class WortprofilQuery(xmlrpc.server.SimpleXMLRPCRequestHandler):
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
        params = {
            "Word": "Mann",
            "Subcorpus": "",
            "CaseSensitive": True,
            "UseLemmatizer": False,
            "UseVariations": 1
        }
        mapping = self.get_lemma_and_pos(params)
        selection = {}
        for i in mapping:
            if i["POS"] == "NN":
                selection = i

        if selection == {}:
            return "Internal Server Error (get_lemma_and_pos)"

        # Parameter für die Kookkurrenzabfrage
        params["Lemma"] = selection["Lemma"]
        params["POS"] = selection["POS"]
        params["Start"] = 0
        params["Number"] = 10
        params["OrderBy"] = "logDice"
        params["Relations"] = selection["Relations"]
        relations = self.get_relations(params)
        if len(relations) == 0:
            return "Internal Server Error (get_relations)"

        return "OK"

    def get_info(self):
        raise NotImplementedError()

    def get_ordered_relation_ids(self, relations, pos):
        """
        Gets relation ids sorted by the specified ordering
        """
        relation_order = self.wp_spec.mapRelOrder.get(pos, self.wp_spec.listRelOrder)
        ordered_rels = [i for i in relation_order if i in relations]
        return ordered_rels

    @deprecated
    def get_lemma_and_pos_by_list(self, mapParam):
        """
        Die Methode ermöglicht es, zu einer liste von gegebenen Wörtern die Wortprofil-Lemma/POS-IDs für jedes der enthaltenen Wörter zu ermitteln (evtl. mehrere Part-Of-Speech Lesarten für ein Wort).
        *Eingabe ist eine Liste aus Lemma/Oberflächen-Formen mehrerer Wörter in UTF-8 ('Parts') (z.B. [Treffen,im,weiß,Haus]) zusammen mit der optionalen Angabe eines Subkorpus ('Subcorpus') (z.B. zeit, kern, 21jhd, ...). Zudem ist parametrisiert, ob caseinsensitiv abgefragt werden soll ( 'CaseSensitive') oder ob eine interne Liste mit abweichenden Schreibweisen verwendet werden soll ('UseVariations'). Diese Parameter werden über einen Dictionary übergeben
        dictParam = {'Parts':<list>, 'Subcorpus':<string>, 'CaseSensitive':<bool=1>, 'UseVariations':<bool=0>}
        hiervon sind obligatorisch: 'Parts'
        *Rückgabe ist eine Liste aus einer Liste von: Lemmaform ('Lemma'), part-of-speech ('POS'), Lemma-ID ('LemmaId'), POS-ID ('PosId'), Anzahl der Relationen mit Doppelten ('Frequency'), Anzahl Relationen ohne Doppelte ( 'Count') und Liste aller möglichen Relationen ('Relations'), die nach Relevanz geordnet sind. die Listeneinträge sind als dictionary abgelegt:
        [[ {'Lemma':<string>,'POS':<string>,'LemmaId':<int>,'PosId':<int>,'Frequency':<int>,'Count':<int>,'Relations:<Liste aus Strings>} , ... ], [ ... ], ... ]
        """
        listLemma = mapParam['Parts']
        if len(listLemma) < 1:
            return []
        bCaseSensitive = False
        if "CaseSensitive" in mapParam:
            bCaseSensitive = bool(mapParam["CaseSensitive"])

        listResult = []
        # Durchgehen der Lemmaliste
        for word in listLemma:
            # Ermitteln der Lemmainformationen
            mapParam["Word"] = word
            mapping = self.get_lemma_and_pos(mapParam)

            mappingNew = []
            for j in mapping:
                if (not bCaseSensitive or word[0].isupper()) and j['POS'] in ['Substantiv']:
                    mappingNew.append(j)
                elif (not bCaseSensitive or word[0].islower()) and j['POS'] in ['Verb', 'Adjektiv', 'Adverb']:
                    mappingNew.append(j)
                elif (not bCaseSensitive or word[0].islower()) and j['POS'] in ['Präposition']:
                    mappingNew = []
                    mappingNew.append(j)
                    break

            # TODO warum []???
            if mappingNew == []:
                return []

            listResult.append(mappingNew)

        return listResult

    def get_lemma_and_pos(self, params):
        """
        Die Methode ermöglicht es, zu einem gegebenen Wort die Wortprofil-Lemma/POS-IDs zu ermitteln (evtl. mehrere Part-Of-Speech Lesarten ).
        *Eingabe ist die Lemma/Oberflächen-Form eines Wortes in UTF-8 ( 'Word') (z.B. Laufen, Baum, Haus, schön, ...) zusammen mit der optionalen Angabe eines Subkorpus ( 'Subcorpus') (z.B. zeit, kern, 21jhd, ...). Zudem ist parametrisiert, ob caseinsensitiv abgefragt werden soll ( 'CaseSensitive') oder ob eine interne Liste mit abweichenden Schreibweisen verwendet werden soll ( 'UseVariations'). Diese Parameter werden über einen Dictionary übergeben:
        mapParam = {'Word':<string>, 'Subcorpus':<string>, 'CaseSensitive':<bool=0>, 'UseVariations':<bool=0>}
        hiervon sind obligatorisch: 'Word'
        *Rückgabe ist eine Liste aus: Lemmaform ( 'Lemma'), part-of-speech ( 'POS'), Lemma-ID ( 'LemmaId'), POS-ID ( 'PosId'), Anzahl der Relationen mit Doppelten ( 'Frequency'), Anzahl Relationen ohne Doppelte ( 'Count') und Liste aller möglichen Relationen ( 'Relations'), die nach Relevanz geordnet sind. Die Listeneinträge sind als dictionary abgelegt.
        """
        use_external_variations = bool(params.get('UseVariations', True))
        is_case_sensitive = bool(params.get("CaseSensitive", False))
        word = params.get("Word")
        pos = params.get("POS", "")

        results = self.wp_db.get_lemma_and_pos(word, pos, is_case_sensitive)

        # evtl. Variationen in der Schreibweise berücksichtigen
        if not results and use_external_variations and word in self.wp_spec.mapVariation:
            word = self.wp_spec.mapVariation[word]
            results = self.wp_db.get_lemma_and_pos(word, pos, is_case_sensitive)

        # evtl. automatisch generierte Variationen der Schreibweisen berücksichtigen
        if not results and use_external_variations:
            for word in generate_orth_variations(word):
                results = self.wp_db.get_lemma_and_pos(word, pos, is_case_sensitive)
                if results:
                    break

        return results

    @deprecated
    def get_lemma_and_pos_diff(self, params):
        """
        Die Methode ermöglicht es, zu einem gegebenen Wort die Wortprofil-Lemma/POS-IDs zu ermitteln (evtl. mehrere Part-Of-Speech Lesarten ).
        mapParam = {'Word1':<string>, 'Word2':<string>, 'Subcorpus':<string>, 'CaseSensitive':<bool=False>}
        hiervon sind obligatorisch: 'Word1' und 'Word2'
        *Eingabe ist die Lemma/Oberflächen-Form des ersten Wortes in UTF-8 ('Word1') und des zweiten Vergleichswortes in UTF-8 ('Word2') (z.B. Laufen, Baum, Haus, schön, ...) zusammen mit der optionalen Angabe eines Subkorpus ( 'Subcorpus') (z.B. zeit, kern, 21jhd, ...). Zudem ist parametrisiert, ob caseinsensitiv abgefragt werden soll ( 'CaseSensitive'). Diese Parameter werden über einen Dictionary übergeben
        *Rückgabe ist eine Liste aus: erster Lemmaform ('Lemma1'), zweiter Lemmaform ('Lemma2'), erster Lemma-ID ('LemmaId1'), zweiter Lemma-ID ('LemmaId2'), part-of-speech ('POS'), POS-ID ('PosId'), Anzahl der Relationen mit Doppelten für das erste Wort ('Frequency1') und für das zweite Wort ('Frequency2'), Anzahl Relationen ohne Doppelte für das erte Wort ('Count1') und für das zweite Wort ('Count2') und Liste aller möglichen Relationen für beide Wörter ('Relations'), die nach Relevanz geordnet sind. Die Listeneinträge sind als dictionary abgelegt:
        [ {'Lemma1':<string>,'Lemma2':<string>,'POS':<string>,'LemmaId1':<int>,'LemmaId2':<int>,'PosId':<int>,'Frequency1':<int>,'Frequency2':<int>,'Count1':<int>,'Count2':<int>,'Relations:<Liste aus Strings>} , ... ]
        """
        # Parameter
        params1 = {}
        params2 = {}
        params1["Word"] = params["Word1"]
        params2["Word"] = params["Word2"]
        bUseExternalVariations = 1
        if "UseVariations" in params:
            bUseExternalVariations = params["UseVariations"]
        if "Subcorpus" in params:
            params1["Subcorpus"] = params["Subcorpus"]
            params2["Subcorpus"] = params["Subcorpus"]
        if "CaseSensitive" in params:
            params1["CaseSensitive"] = params["CaseSensitive"]
            params2["CaseSensitive"] = params["CaseSensitive"]

        # Lemmainformationen zum ersten Lemma ermitteln
        list1 = self.get_lemma_and_pos(params1)
        if list1 == [] and bool(bUseExternalVariations):
            strLemma = params1['Word']
            if strLemma in self.wp_spec.mapVariation:
                params1['Word'] = self.wp_spec.mapVariation[strLemma]
                list1 = self.get_lemma_and_pos(params1)

        # Lemmainformationen zum zweiten Lemma ermitteln
        list2 = self.get_lemma_and_pos(params2)
        if list2 == [] and bool(bUseExternalVariations):
            strLemma = params2['Word']
            if strLemma in self.wp_spec.mapVariation:
                params2['Word'] = self.wp_spec.mapVariation[strLemma]
                list2 = self.get_lemma_and_pos(params2)

        # nur Lemmata mit der gleichen Wortart sind vergleichbar
        results = []
        for i in list1:
            for j in list2:
                if i['POS'] == j['POS']:
                    relations = list(set(i['Relations']) | set(j['Relations']))
                    results.append({
                        'Lemma1': i['Lemma'], 'Lemma2': j['Lemma'], 'POS': i['POS'],
                        'Frequency1': i['Frequency'], 'Frequency2': j['Frequency'],
                        'Relations': relations})
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

        ordered_relations = self.get_ordered_relation_ids(relations, pos)

        results = []
        for relation in ordered_relations:
            cooccs = self.wp_db.get_relation_tuples_check(lemma, lemma2, pos, pos2, start, number,
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
        subcorpus = params.get("Subcorpus", "")

        # Informationen aus der komplexen ID extrahieren
        lemma, pos, rel = hit_id.split("#")[:3]
        cooccs = self.wp_db.get_relation_tuples_check(lemma, -1, pos, -1, start, number, order_by, min_freq,
                                                      min_stat, rel)
        cooccs = self.__relation_tuples_2_strings(cooccs)
        return cooccs

    def __relation_tuples_2_strings(self, cooccs):
        """
        Methode, um IDs in den Kookkurenzlisten auf Strings abzubilden
        """
        results = []
        for coocc in cooccs:
            # evt. Lemma Reparieren
            lemma2 = self.wp_spec.mapLemmaRepair.get((coocc.Pos2, coocc.Lemma2), coocc.Lemma2)
            lemma1 = self.wp_spec.mapLemmaRepair.get((coocc.Pos2, coocc.Lemma1), coocc.Lemma1)
            pos1 = coocc.Pos1
            pos2 = coocc.Pos2

            # Lemma+Präposition formatieren
            if coocc.Prep not in ["-", ""]:
                if coocc.inverse:
                    lemma2 = lemma2 + ' ' + coocc.Prep
                else:
                    lemma2 = coocc.Prep + ' ' + lemma2

            # Informationen in einer Map bündeln
            result = {
                'Relation': "~" if coocc.inverse else "" + coocc.Rel,
                'POS': pos2,
                'PosId': pos2,
                'Lemma': lemma2,
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
        lemma1 = params["Lemma1"]
        lemma2 = params["Lemma2"]
        pos = params["POS"]
        cooccs = params["Relations"]
        # start = params.get("Start", 0)
        number = params.get("Number", 20)
        order_by = params.get("OrderBy", "logDice")
        order_by = 'log_dice' if order_by.lower() == 'logdice' else 'frequency'
        min_freq = params.get("MinFreq", -100000000)
        min_stat = params.get("MinStat", -100000000)
        # subcorpus = params.get("Subcorpus", "")

        operation = params.get("Operation", "adiff")
        use_intersection = params.get("Intersection", False)
        nbest = params.get("NBest", None)

        ordered_relations = self.get_ordered_relation_ids(cooccs, pos)
        diffs = self.wp_db.get_relation_tuples_diff(lemma1, lemma2, pos, ordered_relations, order_by,
                                                    min_freq, min_stat)
        cooccs = self.__gen_rel_cooccurrence_mapping(diffs)

        relations = []
        for rel in ordered_relations:
            if rel in cooccs:
                results = self.__calculate_diff(lemma1, lemma2, diffs, cooccs[rel], number, nbest,
                                                use_intersection, operation)
                results = self.__diff_relation_tuples_2_strings(diffs, results)

                relation_name = rel
                description = self.wp_spec.strRelDesc
                if relation_name in self.wp_spec.mapRelDesc:
                    description = self.wp_spec.mapRelDesc[relation_name]

                relations.append({'Relation': relation_name, 'Description': description, 'Tuples': results})

        return relations

    @deprecated
    def get_intersection(self, mapParam):
        """
        Indirekter aufruf von get_diff mit der Operation 'rmax'
        """
        mapParam['Operation'] = 'rmax'
        return self.get_diff(mapParam)

    @deprecated
    def __calculate_diff(self, lemma1_id, lemma2_id, diffs, cooccs_rel, number, nbest, use_intersection, operation):
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
        Wortprofil-Diff:
            Im ersten Schritt wird für alle K ∊ WP₁ ∪ WP₂ die absolute Differenz der jeweiligen Assoziationswerte berechnet:
            adiff(K) = |s₁(K)-s₂(K)|
            Anhand dieser absoluten Differenzwerte werden nun die Kookkurrenzpartner aufsteigend sortiert und nach dem Wert L abgeschnitten.
            Daraufhin wird die Differenz für die verbleibenden Kookkurrenzpartner berechnet:
            diff(K) = s₁(K)-s₂(K)
            Im letzten Schritt werden die Kookkurrenzpartner anhand dieser Differenzwerte aufsteigend sortiert.
        Wortprofil-Intersect:
            Zuerst wird für alle K ∊ WP₁ ∩ WP₂ der maximale Rang berechnet:
            rmax(K) = max(r₁(K),r₂(K))
            Danach werden diese Kookkurrenzpartner anhand der Maximalränge absteigend sortiert und nach dem Wert L abgeschnitten.
        """
        mapData = {}
        mapCenter = {}
        mapRank = {}

        # Prüfen, ob die Kookkurrenzpartner für beide Lemmata vorhanden sind
        iCountRank2 = 1
        for k in cooccs_rel:
            i = diffs[k]
            if i.Lemma1 == lemma2_id:
                if nbest == None or iCountRank2 <= nbest:
                    mapData[(i.Prep, i.Lemma2)] = (k, i)
                    mapRank[k] = iCountRank2
                iCountRank2 += 1

        iCountRank1 = 1
        for k in cooccs_rel:
            i = diffs[k]
            if i.Lemma1 == lemma1_id:
                if nbest == None or iCountRank1 <= nbest:
                    if (i.Prep, i.Lemma2) in mapData:
                        (iPos, myTuple) = mapData[(i.Prep, i.Lemma2)]
                        iRef1 = k
                        iRef2 = iPos
                        mapCenter[iRef1] = iRef2
                        mapCenter[iRef2] = -1
                    mapRank[k] = iCountRank1
                iCountRank1 += 1

        if use_intersection:
            # wenn der Schnitt berechnet werden soll
            results = []
            for i in mapCenter:
                iRef = mapCenter[i]
                if iRef != -1:
                    iRef1 = i
                    iRef2 = iRef
                    iRank1 = mapRank[iRef1]
                    iRank2 = mapRank[iRef2]

                    iScore = self.__diff_operation(operation, diffs[iRef1].Score, diffs[iRef2].Score,
                                                   iRank1, iRank2)
                    results.append((iRef1, iRef2, iRank1, iRank2, iScore))
        else:
            results = []
            for k in cooccs_rel:
                i = diffs[k]
                # für Lemma1 und Lemma2
                if k in mapCenter:
                    iRef = mapCenter[k]
                    if iRef == -1:
                        pass
                    else:
                        iRef1 = k
                        iRef2 = iRef
                        iRank1 = mapRank[iRef1]
                        iRank2 = mapRank[iRef2]

                        iScore = self.__diff_operation(operation, i.Score, diffs[iRef2].Score, iRank1, iRank2)

                        results.append((iRef1, iRef2, iRank1, iRank2, iScore))

                elif k in mapRank:
                    # für nur Lemma1
                    if i.Lemma1 == lemma1_id:
                        iRef1 = k
                        iRef2 = -1
                        iRank1 = mapRank[iRef1]
                        iRank2 = -1

                        iScore = self.__diff_operation(operation, i.Score, 0, iRank1, 0)

                    # für nur Lemma2
                    else:
                        iRef1 = -1
                        iRef2 = k
                        iRank1 = -1
                        iRank2 = mapRank[iRef2]

                        iScore = self.__diff_operation(operation, 0, diffs[iRef2].Score, 0, iRank2)

                    results.append((iRef1, iRef2, iRank1, iRank2, iScore))

        yScore = 4

        # Abschließendes Sortieren und Abschneiden
        lcmp = lambda idx: lambda i, j: (i[idx] > j[idx]) and -1 or (i[idx] < j[idx]) and 1 or 0
        abs_lcmp = lambda idx: lambda i, j: (math.fabs(i[idx]) > math.fabs(j[idx])) and -1 or (
                math.fabs(i[idx]) < math.fabs(j[idx])) and 1 or 0
        rcmp = lambda idx: lambda i, j: (i[idx] < j[idx]) and -1 or (i[idx] > j[idx]) and 1 or 0
        abs_rcmp = lambda idx: lambda i, j: (math.fabs(i[idx]) < math.fabs(j[idx])) and -1 or (
                math.fabs(i[idx]) > math.fabs(j[idx])) and 1 or 0

        if operation == "rmax":
            my_cmp = rcmp
        else:
            my_cmp = lcmp
        # TODO cmp was removed in Python3. Seems weird anyway...
        if operation == "adiff":
            results.sort(key=cmp_to_key(abs_lcmp(yScore)))
            results = results[0:number]
            results.sort(key=cmp_to_key(lcmp(yScore)))
        elif operation == "ardiff":
            results.sort(key=cmp_to_key(abs_lcmp(yScore)))
            results = results[0:number]
            results.sort(key=cmp_to_key(lcmp(yScore)))
        else:
            results.sort(key=cmp_to_key(my_cmp(yScore)))
            results = results[0:number]

        return results

    @deprecated
    def __diff_operation(self, strOperation, Sa, Sb, Ra, Rb):
        """
        Berechnen der Nummerischen Diff-Operation (Wert, der den Kookkurrenztupeln zugewiesen wird)
        Gegeben sind der Statistikwert des ersten Lemmas (Sa) und des zweiten Lemmas (Sb). Des Weiteren
        seigegeben der Rank des ersten Lemma (Ra) und des zweiten Lemma (Rb).
        möglich sind:
          diff, adiff, ardiff, sum, min, max, rmax, avg, havg, gavg
        """
        iScore = 0
        if strOperation == "diff":
            iScore = Sa - Sb
        elif strOperation == "adiff":
            iScore = Sa - Sb
        elif strOperation == "ardiff":
            if Ra == 0:
                iScore = -(1000000 - Rb)
            elif Rb == 0:
                iScore = (1000000 - Ra)
            else:
                iScore = (1000000 - Ra) - (1000000 - Rb)
        elif strOperation == "sum":
            iScore = Sa + Sb
        elif strOperation == "min":
            iScore = min(Sa, Sb)
        elif strOperation == "max":
            iScore = max(Sa, Sb)
        elif strOperation == "rmax":
            iScore = max(Ra, Rb)
        elif strOperation == "avg":
            iScore = (Sa + Sb) / 2
        elif strOperation == "havg":
            iAvg = (Sa + Sb) / 2
            if Sa <= 0.0 or Sb <= 0.0:
                iHAvg = 0.0
            else:
                iHAvg = (2 * (Sa * Sb)) / (Sa + Sb)
            iScore = (iHAvg + iAvg) / 2
        elif strOperation == "gavg":
            iScore = math.sqrt(Sa * Sb)

        return iScore

    @deprecated
    def __diff_relation_tuples_2_strings(self, diffs, db_results):
        """
        Methode, um IDs in den Diff-Kookkurenzlisten auf Strings abzubilden
        """
        yRef1 = 0
        yRef2 = 1
        yRank1 = 2
        yRank2 = 3
        yScore = 4

        listMapRes = []

        for i in db_results:
            localMap = {
                "POS": None
            }
            score = {
                'AScomp': i[yScore],
                'Rank1': i[yRank1],
                'Rank2': i[yRank2]
            }
            if i[yRef1] != -1:
                # Es gibt Kookkurenzen zum ersten Wort
                score['Frequency1'] = diffs[i[yRef1]].Frequency
                score['Assoziation1'] = diffs[i[yRef1]].Score
                localMap['ConcordId1'] = diffs[i[yRef1]].RelId

                iConcordNo1 = diffs[i[yRef1]].Frequency
                if diffs[i[yRef1]].Rel == "KON" and diffs[i[yRef1]].Lemma1 == \
                        diffs[i[yRef1]].Lemma2:
                    iConcordNo1 = iConcordNo1 / 2
                localMap['ConcordNo1'] = iConcordNo1
                localMap['Relation'] = diffs[i[yRef1]].Rel

                # Ids auf Strings mappen
                strLemma = diffs[i[yRef1]].Lemma2
                strPrep = diffs[i[yRef1]].Prep

                # evt. Lemma Reparieren
                strLemmaRepair = self.wp_spec.mapLemmaRepair.get((localMap['POS'], strLemma), None)
                if strLemmaRepair:
                    strLemma = strLemmaRepair

                # Lemma+Präposition formatieren
                if strPrep != "-":
                    if diffs[i[yRef1]].Rel.startswith("~"):
                        strLemma = strLemma + ' ' + strPrep
                    else:
                        strLemma = strPrep + ' ' + strLemma

                localMap['Lemma'] = strLemma
                localMap['POS'] = diffs[i[yRef1]].Pos2

                if i[yRef2] == -1:
                    localMap['Position'] = 'left'
                else:
                    localMap['Position'] = 'center'
            else:
                score['Frequency1'] = 0
                score['Assoziation1'] = 0.0
                localMap['ConcordId1'] = 0
                localMap['ConcordNo1'] = 0
                localMap['ConcordNoAccessible1'] = 0

            if i[yRef2] != -1:
                # Es gibt Kookkurenzen zum zweiten Wort
                score['Frequency2'] = diffs[i[yRef2]].Frequency
                score['Assoziation2'] = diffs[i[yRef2]].Score
                localMap['ConcordId2'] = diffs[i[yRef2]].RelId

                iConcordNo2 = diffs[i[yRef2]].Frequency
                if diffs[i[yRef2]].Rel == "KON" and diffs[i[yRef2]].Lemma1 == \
                        diffs[i[yRef2]].Lemma2:
                    iConcordNo2 = iConcordNo2 / 2
                localMap['ConcordNo2'] = iConcordNo2

                if i[yRef1] == -1:
                    localMap['Relation'] = diffs[i[yRef2]].Rel
                    # Ids auf Strings mappen
                    strLemma = diffs[i[yRef2]].Lemma2
                    strPrep = diffs[i[yRef2]].Prep

                    # Lemma+Präposition formatieren
                    if strPrep != "-":
                        if diffs[i[yRef2]].Rel.startswith("~"):
                            strLemma = strLemma + ' ' + strPrep
                        else:
                            strLemma = strPrep + ' ' + strLemma

                    localMap['Lemma'] = strLemma
                    localMap['POS'] = diffs[i[yRef2]].Pos2
                    localMap['Position'] = 'right'
            else:
                score['Frequency2'] = 0
                score['Assoziation2'] = 0.0
                localMap['ConcordId2'] = 0
                localMap['ConcordNo2'] = 0
                localMap['ConcordNoAccessible2'] = 0

            localMap['Score'] = score
            listMapRes.append(localMap)

        return listMapRes

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
            description = description.replace('$3', coocc_info.prep)
        else:
            description = ""
        return {'RelationId': coocc_info.rel_id, 'Description': description, 'Relation': coocc_info.rel,
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
        subcorpus = params.get("Subcorpus", "")
        is_internal_user = bool(params.get("InternalUser", False))
        start_index = params.get("Start", 0)
        result_number = params.get("Number", 20)
        return self.wp_db.get_concordances(coocc_id, use_context, subcorpus,
                                           is_internal_user,
                                           start_index, result_number)
