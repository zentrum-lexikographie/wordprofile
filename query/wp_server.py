#!/usr/bin/python

# Das Programm startet einen XMLRPC-Server und stellt bestimmte Funktionen bereit, die auf Daten
# einer Wortprofil-MySQL-Datenbank zugreifen
# *Es Können (MWE-)Kookkurrenzen abgefragt werden.
# *Es können Texttreffer Abgefragt werden.
# *Es können Wortprofile miteinander Verglichen werden.

import logging
import math
import sys
import time
import xmlrpc.server
from argparse import ArgumentParser
from collections import defaultdict, namedtuple

from moduls import deprecated
from moduls.OrthVariations import OrthVariations
from moduls.wpse_mysql import WpSeMySql
from moduls.wpse_spec import WpSeSpec
from moduls.wpse_string import format_sentence, format_sentence_center, format_sentence_center_mwe, \
    surface_mapping, intersect
from moduls.wpse_tree import WpSeTree


class CooccInfo:
    def __init__(self, info_id, lemma_id_1=0, lemma_id_2=0, pos_id_1=0, pos_id_2=0, prep_id=0, rel_id=0):
        self.iLemma1Id = lemma_id_1
        self.iLemma2Id = lemma_id_2
        self.iPos1Id = pos_id_1
        self.iPos2Id = pos_id_2
        self.iPrepId = prep_id
        self.iRelId = rel_id
        self.iInfoId = info_id


class WortprofilQuery(xmlrpc.server.SimpleXMLRPCRequestHandler):
    def __init__(self, CWpSpec):
        print("|: start init ...")
        # Generierung eines Parsebaums (geordnete Liste aus Dependent-Kopf-Relationen) aus einer Lemmaliste
        self.CWpTree = WpSeTree()
        # Einlesen der Spezifikationsdatei
        self.CWpSpec = CWpSpec
        # MySQL-Seitigen Grundfunktionen
        self.CWpMySQL = WpSeMySql(self.CWpSpec)
        if not self.CWpMySQL.check_connection():
            print("): MySQL-Verbindung fehlgeschlagen")
            sys.exit(-1)
        self.CWpMySQL.init_data()
        # Generiereung Orthographischer Variationen
        self.COrthVariations = OrthVariations()
        print("|: MWE-Depth = %i" % self.CWpMySQL.iMweDepth)

        if self.CWpMySQL.iMweDepth > 0 and len(self.CWpSpec.mapMweRelOrder) == 0:
            print("): Missing MWE-Specification")

        print("|: init complete")

    def status(self):
        """
        Status-Function für "icinga". Es wird geprüft, ob der Server einwandfrei funktioniert.
        Hierzu werden Testweise Kookkurrenzen zu einem Wort abgefragt.
        """
        if not self.CWpMySQL.connect():
            return "Can't connect to MySQL database (%s, %s)" % (self.CWpMySQL.strHost, self.CWpMySQL.strDatabase)

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
            if i["POS"] == "Substantiv":
                selection = i

        if selection == {}:
            return "Internal Server Error (get_lemma_and_pos)"

        # Parameter für die Kookkurrenzabfrage
        params["LemmaId"] = selection["LemmaId"]
        params["Lemma"] = selection["Lemma"]
        params["PosId"] = selection["PosId"]
        params["Start"] = 0
        params["Number"] = 10
        params["OrderBy"] = "logDice"
        params["Relations"] = selection["Relations"]
        params["ExtendedSurfaceForm"] = True

        # Kookkurrenzen abfragen
        relations = self.get_relations(params)
        if len(relations) == 0:
            return "Internal Server Error (get_relations)"

        # Der Server läuft einwandfrei
        return "OK"

    def get_info(self):
        for i in self.CWpMySQL.mapRelInfo:
            if self.CWpMySQL.mapRelInfo[i]['Name'] in self.CWpSpec.mapRelDesc:
                description = self.CWpSpec.mapRelDesc[self.CWpMySQL.mapRelInfo[i]['Name']]
            else:
                description = self.CWpSpec.strRelDesc
            self.CWpMySQL.mapRelInfo[i]['Description'] = description

        return {
            "used_corpora": self.CWpMySQL.vCorpusName,
            "lemma_size": self.CWpMySQL.mapTypeToValue.get('lemmaSize', None),
            "relation_size": self.CWpMySQL.mapTypeToValue.get('relationSize', None),
            "sentence_size": self.CWpMySQL.mapTypeToValue.get('sentenceSize', None),
            "info_size": self.CWpMySQL.mapTypeToValue.get('infoSize', None),
            "threshold": self.CWpMySQL.mapThresholdInfo,
            "mwe_depth": self.CWpMySQL.iMweDepth,
            "author": self.CWpMySQL.mapProjectInfo.get('Author', None),
            "creation_date": self.CWpMySQL.mapProjectInfo.get('CreationDate', None),
            "spec_file": self.CWpMySQL.mapProjectInfo.get('SpecFile', None),
            "spec_file_version": self.CWpMySQL.mapProjectInfo.get('SpecFileVersion', None),
            "lemma_cut": self.CWpMySQL.mapProjectInfo.get('LemmaCut', None),
            "cooccurrence_info": self.CWpMySQL.mapRelInfo,
        }

    @deprecated
    def gen_rel_ids_by_rel(self, listRel):
        """
        Ermitteln einer Liste von Relation-Ids
        anhand einer Liste von Relationen (String)
        """
        setRes = set()
        for i in listRel:
            if i in self.CWpMySQL.mapRelToId:
                setRes.add(self.CWpMySQL.mapRelToId[i])
        return list(setRes)

    def get_ordered_relation_ids(self, relations, pos):
        """
        Gets relation ids sorted by the specified ordering
        """
        relation_to_id = {}
        for r in relations:
            if r in self.CWpMySQL.mapRelToId:
                relation_to_id[r] = self.CWpMySQL.mapRelToId[r]

        relation_order = self.CWpSpec.mapRelOrder.get(pos, self.CWpSpec.listRelOrder)
        ordered_ids = [relation_to_id[i] for i in relation_order if i in relations]
        return ordered_ids

    @deprecated
    def gen_mwe_rel_ids_by_pos(self, strPOS):
        """
        Ermitteln einer Liste von Sortierten Relations-Ids
        anhand einer Wortkategorie
        """
        mapRelations = {}
        for i in self.CWpMySQL.mapRelToId:
            mapRelations[i] = self.CWpMySQL.mapRelToId[i]

        if strPOS in self.CWpSpec.mapMweRelOrder:
            listSort = self.CWpSpec.mapMweRelOrder[strPOS]
        else:
            listSort = self.CWpSpec.listMweRelOrder

        listSortId = []
        for i in listSort:
            if i in mapRelations:
                listSortId.append(mapRelations[i])
        return listSortId

    @deprecated
    def __gen_rel_pos_cooccurrence_mapping(self, listData):
        """
        Ermitteln eines Mapping von Relation-Id und Wortkategorie-Id auf die Zeile innerhalb
        einer Liste von Kookkurenzinformationen (listData)
        """
        mapRes = {}

        # Positionen von Relation, Lemmaform und Wortkategorie
        xRel = 0
        xLemma1 = 2
        xPos1 = 14

        iCounter = 0
        for i in listData:
            if (i[xLemma1], i[xPos1]) in mapRes:
                if i[xRel] in mapRes[(i[xLemma1], i[xPos1])]:
                    mapRes[(i[xLemma1], i[xPos1])][i[xRel]].append(iCounter)
                else:
                    mapRes[(i[xLemma1], i[xPos1])][i[xRel]] = [iCounter]
            else:
                mapDummy = {}
                mapDummy[i[xRel]] = [iCounter]
                mapRes[(i[xLemma1], i[xPos1])] = mapDummy

            iCounter += 1
        return mapRes

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

        results = self.__get_lemma_and_pos_base(word, pos, is_case_sensitive)

        # evtl. Variationen in der Schreibweise berücksichtigen
        if not results and use_external_variations and word in self.CWpSpec.mapVariation:
            word = self.CWpSpec.mapVariation[word]
            results = self.__get_lemma_and_pos_base(word, pos, is_case_sensitive)

        # evtl. automatisch generierte Variationen der Schreibweisen berücksichtigen
        if not results and use_external_variations:
            for word in self.COrthVariations.gen(word):
                results = self.__get_lemma_and_pos_base(word, pos, is_case_sensitive)
                if results:
                    break

        return results

    def __get_lemma_and_pos_base(self, word, pos, is_case_sensitive):
        """
        Basismethode zur Abfrage von Lemmainformationen
        """
        if not all(c.isalpha() or c == '-' for c in word):
            return []

        query = """
            SELECT LemmaId, PosId, Frequency, Count, RelationId FROM head_pos_rel_freq_test  
            WHERE head_pos_rel_freq_test.lemma LIKE '{}' {};
        """.format(
            word.lower(),
            " and POS='{}'".format(self.CWpMySQL.mapPosToId[pos]) if pos not in ["*", ""] else "")

        self.CWpMySQL.connect()
        self.CWpMySQL.execute(query)
        db_results = self.CWpMySQL.fetchall()
        self.CWpMySQL.disconnect()

        return self.__get_valid_sorted_lemmas(db_results, word, is_case_sensitive)

    def __get_valid_sorted_lemmas(self, head_pos_rel_freqs, word, is_case_sensitive):
        """
        Bei einer gegebenen Liste von Lemmainformationen werden Einträge gelöscht und die Einträge werden Sortiert.
        Hierbei wird Bezug auf die Großschreibung und auf die Wortarten Bezug genommen. So sind Großgeschriebene Worte
        eher Substantiv als Verb.
        """
        lemma_pos_mapping = defaultdict(list)
        for lemma_id, pos_id, frequency, count, relation_id in head_pos_rel_freqs:
            lemma_pos_mapping[(lemma_id, pos_id)].append((relation_id, frequency, count))

        # Erstellen einer map, die zu einer Wortart, die frequenteste Lemmainformation besitzt
        most_frequent_lemma = {}
        for (lemma_id, pos_id), relations in lemma_pos_mapping.items():
            frequency = sum(frequency for _, frequency, _ in relations)
            count = sum(count for _, _, count in relations)
            if pos_id not in most_frequent_lemma or most_frequent_lemma[pos_id][1] < frequency:
                most_frequent_lemma[pos_id] = (lemma_id, frequency, count, relations)
        pos_sorted = sorted(most_frequent_lemma.items(), key=lambda x: x[1][1], reverse=True)

        results = []
        for pos_id, (lemma_id, frequency, count, relations) in pos_sorted:
            pos = self.CWpMySQL.mapIdToPOS[pos_id]
            lemma = self.CWpMySQL.mmapIdToLem[lemma_id]
            relations = [self.CWpMySQL.mapIdToRel[relation_id] for (relation_id, frequency, count) in relations]

            # bei case-sensitiver Abfrage Groß-Kleinschreibung zu den Wortarten berücksichtigen
            if is_case_sensitive:
                if pos != "Substantiv" and lemma[0].isupper():
                    continue
                if pos == "Substantiv" and lemma[0].islower():
                    continue

            # Relevanz der einzelnen Informationen über die verschiedenen Ergebnislisten behandeln
            if word == lemma and word[0].isupper() and lemma[0].isupper():
                if pos == "Substantiv":
                    score = 1
                else:
                    score = 2
            elif word.lower() == lemma.lower():
                score = 3
            elif word[0].isupper() == lemma[0].isupper():
                score = 4
            else:
                score = 5
            results.append((score, {'LemmaId': lemma_id, 'PosId': pos_id, 'POS': pos, 'Lemma': lemma,
                                    'Frequency': frequency, 'Count': count, 'Relations': relations}))
        results = [r[1] for r in sorted(results, key=lambda x: x[0])]
        return results

    @deprecated
    def get_lemma_and_pos_diff(self, mapParam):
        """
        Die Methode ermöglicht es, zu einem gegebenen Wort die Wortprofil-Lemma/POS-IDs zu ermitteln (evtl. mehrere Part-Of-Speech Lesarten ).
        mapParam = {'Word1':<string>, 'Word2':<string>, 'Subcorpus':<string>, 'CaseSensitive':<bool=False>}
        hiervon sind obligatorisch: 'Word1' und 'Word2'
        *Eingabe ist die Lemma/Oberflächen-Form des ersten Wortes in UTF-8 ('Word1') und des zweiten Vergleichswortes in UTF-8 ('Word2') (z.B. Laufen, Baum, Haus, schön, ...) zusammen mit der optionalen Angabe eines Subkorpus ( 'Subcorpus') (z.B. zeit, kern, 21jhd, ...). Zudem ist parametrisiert, ob caseinsensitiv abgefragt werden soll ( 'CaseSensitive'). Diese Parameter werden über einen Dictionary übergeben
        *Rückgabe ist eine Liste aus: erster Lemmaform ('Lemma1'), zweiter Lemmaform ('Lemma2'), erster Lemma-ID ('LemmaId1'), zweiter Lemma-ID ('LemmaId2'), part-of-speech ('POS'), POS-ID ('PosId'), Anzahl der Relationen mit Doppelten für das erste Wort ('Frequency1') und für das zweite Wort ('Frequency2'), Anzahl Relationen ohne Doppelte für das erte Wort ('Count1') und für das zweite Wort ('Count2') und Liste aller möglichen Relationen für beide Wörter ('Relations'), die nach Relevanz geordnet sind. Die Listeneinträge sind als dictionary abgelegt:
        [ {'Lemma1':<string>,'Lemma2':<string>,'POS':<string>,'LemmaId1':<int>,'LemmaId2':<int>,'PosId':<int>,'Frequency1':<int>,'Frequency2':<int>,'Count1':<int>,'Count2':<int>,'Relations:<Liste aus Strings>} , ... ]
        """

        # Parameter
        mapParam1 = {}
        mapParam2 = {}
        mapParam1["Word"] = mapParam["Word1"]
        mapParam2["Word"] = mapParam["Word2"]
        bUseExternalVariations = 1
        if "UseVariations" in mapParam:
            bUseExternalVariations = mapParam["UseVariations"]
        if "Subcorpus" in mapParam:
            mapParam1["Subcorpus"] = mapParam["Subcorpus"]
            mapParam2["Subcorpus"] = mapParam["Subcorpus"]
        if "CaseSensitive" in mapParam:
            mapParam1["CaseSensitive"] = mapParam["CaseSensitive"]
            mapParam2["CaseSensitive"] = mapParam["CaseSensitive"]

        # Lemmainformationen zum ersten Lemma ermitteln
        list1 = self.get_lemma_and_pos(mapParam1)
        if list1 == [] and bool(bUseExternalVariations):
            strLemma = mapParam1['Word']
            if strLemma in self.CWpSpec.mapVariation:
                mapParam1['Word'] = self.CWpSpec.mapVariation[strLemma]
                list1 = self.get_lemma_and_pos(mapParam1)

        # Lemmainformationen zum zweiten Lemma ermitteln
        list2 = self.get_lemma_and_pos(mapParam2)
        if list2 == [] and bool(bUseExternalVariations):
            strLemma = mapParam2['Word']
            if strLemma in self.CWpSpec.mapVariation:
                mapParam2['Word'] = self.CWpSpec.mapVariation[strLemma]
                list2 = self.get_lemma_and_pos(mapParam2)

        # print(list1)
        # print(list2)

        # nur Lemmata mit der gleichen Wortart sind vergleichbar
        listResult = []
        for i in list1:
            for j in list2:
                if i['PosId'] == j['PosId']:
                    listRelations = intersect(i['Relations'], j['Relations'])
                    listResult.append(
                        {'Lemma1': i['Lemma'], 'Lemma2': j['Lemma'], 'LemmaId1': i['LemmaId'], 'LemmaId2': j['LemmaId'],
                         'PosId': i['PosId'], 'POS': i['POS'], 'Frequency1': i['Frequency'],
                         'Frequency2': j['Frequency'], 'Count1': i['Count'], 'Count2': j['Count'],
                         'Relations': listRelations})

        return listResult

    @deprecated
    def __gen_rel_cooccurrence_mapping(self, listData):
        """
        Ermitteln eines Mapping von Relation-Id auf die Zeile innerhalb
        einer Liste von Kookkurenzinformationen (listData)
        """
        mapRelData = {}
        # Position der Relation-Information
        xRel = 0
        iCounter = 0
        for i in listData:
            if i[xRel] in mapRelData:
                mapRelData[i[xRel]].append(iCounter)
            else:
                mapRelData[i[xRel]] = [iCounter]
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
        lemma_id = params["LemmaId"]
        lemma2_id = params.get("Lemma2Id", -1)
        pos_id = params["PosId"]
        pos2_id = params.get("Pos2Id", -1)
        relations = params.get("Relations", [])
        use_extended_surface_form = bool(params.get("ExtendedSurfaceForm", False))
        start = params.get("Start", 0)
        number = params.get("Number", 20)
        order_by = params.get("OrderBy", "logDice")
        min_freq = params.get("MinFreq", -100000000)
        min_stat = params.get("MinStat", -100000000)
        subcorpus = params.get("Subcorpus", "")

        ordered_relation_ids = self.get_ordered_relation_ids(relations, self.CWpMySQL.mapIdToPOS[pos_id])

        results = []
        for rel_id in ordered_relation_ids:
            cooccs = self.__get_relation_tuples_mwe_check(lemma_id, lemma2_id, pos_id, pos2_id, start, number,
                                                          order_by, min_freq, min_stat, subcorpus, rel_id)
            # IDs in den Kookkurenzlisten auf Strings abbilden
            cooccs = self.__relation_tuples_2_strings(lemma_id, pos_id, cooccs, use_extended_surface_form)
            # Meta-Informationen
            relation = self.CWpMySQL.mapIdToRel[rel_id]
            description = self.CWpSpec.mapRelDesc.get(relation, self.CWpSpec.strRelDesc)
            # ID (komplex) für die Relation+Kookkurenzen erstellen
            hit_id = "{}#{}#{}".format(lemma_id, pos_id, rel_id)

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
        min_freq = params.get("MinFreq", -100000000)
        min_stat = params.get("MinStat", -100000000)
        subcorpus = params.get("Subcorpus", "")

        # Prüfen, ob es sich um eine ID einer MWE-Relation handelt
        if hit_id.find('@') != -1:
            return self.get_mwe_cooccurrences(params)

        # Informationen aus der komplexen ID extrahieren
        lemma_id, pos_id, rel_id = [int(i) for i in hit_id.split("#")[:3]]
        cooccs = self.__get_relation_tuples_mwe_check(lemma_id, -1, pos_id, -1, start, number,
                                                      order_by, min_freq, min_stat, subcorpus, rel_id)
        cooccs = self.__relation_tuples_2_strings(lemma_id, pos_id, cooccs, False)

        return cooccs

    def __get_relation_tuples_mwe_check(self, lemma_id, lemma2_id, pos_id, pos2_id, start, number, order_by, min_freq,
                                        min_stat, subcorpus, relation_id):
        """
        Methode zum Abfragen der Kookkurrenztupeln zu einer liste von gegebenen Relation-IDs über die
        Wortprofil-MySQL-Datenbank
        """
        # Minimalfrequenz behandeln (MWE-Kookkurenzen einbezogen)
        str_min_freq = ""
        str_min_freq_mwe_check = ""
        if min_freq > 0:
            str_min_freq = " and (-relations.frequency)>=" + str(min_freq) + " "
            str_min_freq_mwe_check = " and (-ConditionalCheck_1.frequency)>=" + str(min_freq) + " "

        # Minimalstatistikwerte behandeln (MWE-Kookkurenzen einbezogen)
        str_min_stat = ""
        str_min_stat_mwe_check = ""
        if min_stat > -100000000:
            str_min_stat = " and (-relations." + order_by + ")>=" + str(min_stat) + " "
            str_min_stat_mwe_check = " and (-ConditionalCheck_1.logDice)>=" + str(min_stat) + " "

        # wenn es allgemein MWE-Relationen gibt
        if self.CWpMySQL.iMweDepth > 0:
            select_from_sql = """
            SELECT  
                function, prep, lemma1, lemma2, surfacePrep, surface1, surface2, POS2, -relations.frequency, 
                -freqBelege, -MiLogFreq, -relations.logDice, -MI3, info, 
                if(ConditionalCheck_1.id1!=CAST('None' as UNSIGNED) {} {} ,1,0) as MweId 
            FROM 
                {}relations USE INDEX(I_{}) LEFT JOIN ConditionalCheck_1 ON (relations.info=ConditionalCheck_1.id1) 
            """.format(
                str_min_freq_mwe_check, str_min_stat_mwe_check, subcorpus, order_by
            )
        else:
            select_from_sql = """
            SELECT  
                function, prep, lemma1, lemma2, surfacePrep, surface1, surface2, POS2, -relations.frequency, 
                -freqBelege, -MiLogFreq, -relations.logDice, -MI3, info, '0' 
            FROM 
                {}relations USE INDEX(I_{})
            """.format(
                subcorpus, order_by
            )

        # evtl. auch das zweite Wort in der Kookkurrenz einschränken
        if pos2_id == -1 or lemma2_id == -1:
            where_sql = "WHERE lemma1='{}' and POS1='{}' and function IN ({}) {} {} LIMIT {}, {};".format(
                lemma_id, pos_id, relation_id, str_min_freq, str_min_stat, start, number
            )
        else:
            where_sql = """WHERE lemma1='{}' and POS1='{}' and 
                                lemma2='{}' and POS2='{}' and 
                                function IN ({}) {} {} ORDER BY frequency;""".format(
                lemma_id, pos_id, lemma2_id, pos2_id, relation_id, str_min_freq, str_min_stat
            )

        # MySQL abfragen
        self.CWpMySQL.connect()
        self.CWpMySQL.execute(select_from_sql + where_sql)
        db_results = self.CWpMySQL.fetchall()
        self.CWpMySQL.disconnect()

        Coocc = namedtuple("Coocc", ["Rel", "Prep", "Lemma1", "Lemma2", "SurfacePrep", "Surface1", "Surface2", "POS",
                                     "Frequency", "FreqBelege", "Score_MiLogFreq", "Score_logDice", "Score_MI3", "Info",
                                     "ConditionalCheck"])
        return map(Coocc._make, db_results)

    @deprecated
    def __mwe_id_prefix(self, listRelData, listCooccRef):
        """
        Methode, um die MWE-Id aus den Kookkurrenzinformationen einer Relation zu extrahieren
        """
        xStrInfo = 16
        strMweId = ""
        for k in listCooccRef:
            i = listRelData[k]
            if strMweId == "":
                strMweId = i[xStrInfo]
            elif strMweId != i[xStrInfo]:
                return ""

        return strMweId

    def __relation_tuples_2_strings(self, lemma_id, pos_id, coocc_tuples, use_extended_surface_form):
        """
        Methode, um IDs in den Kookkurenzlisten auf Strings abzubilden
        """
        results = []
        for coocc in coocc_tuples:
            result = {}
            result['Relation'] = self.CWpMySQL.mapIdToRel[coocc.Rel]
            result['POS'] = self.CWpMySQL.mapIdToPOS[coocc.POS]
            lemma = self.CWpMySQL.mmapIdToLem.get(coocc.Lemma2)
            prep = self.CWpMySQL.mmapIdToLem.get(coocc.Prep)
            surface = self.CWpMySQL.mmapIdToSurf.get(coocc.Surface2)

            # Oberflächenform formatieren (z.B. bei erweiterten Oberflächenformen mit Kontext)
            surface = surface_mapping(surface, self.CWpMySQL.mapRelIdToType[coocc.Rel],
                                      prep,
                                      use_extended_surface_form)
            # evt. Lemma Reparieren
            lemma = self.CWpSpec.mapLemmaRepair.get((result['POS'], lemma), lemma)
            # Lemma+Präposition formatieren
            if prep not in ["-", ""]:
                if self.CWpMySQL.mapRelIdToType[coocc.Rel] == 1:
                    lemma = lemma + ' ' + prep
                else:
                    lemma = prep + ' ' + lemma

            # Informationen in einer Map bündeln
            result['Lemma'] = lemma
            result['Form'] = surface
            result['Score'] = {
                'Frequency': coocc.Frequency,
                'MiLogFreq': coocc.Score_MiLogFreq,
                'logDice': coocc.Score_logDice,
                'MI3': coocc.Score_MI3,
            }
            result["ConcordId"] = "{}#{}#{}#{}#{}#{}#{}".format(
                lemma_id, pos_id, coocc.Lemma2, coocc.POS, coocc.Prep, coocc.Rel, coocc.Info)

            # MWE-Zugänglichkeit
            if int(coocc.ConditionalCheck) == 0:
                result["HasMwe"] = 0
            else:
                result["HasMwe"] = 1

            # Berechnen der Frequenz und der Anzahl der Belege bei symmetrischen Relationen
            concord_no = coocc.Frequency
            support_no = coocc.FreqBelege
            if self.CWpMySQL.mapRelIdToType[coocc.Rel] == 2 and coocc.Lemma1 == coocc.Lemma2:
                concord_no = concord_no / 2
                support_no = support_no / 2
            result['ConcordNo'] = concord_no
            result['ConcordNoAccessible'] = support_no
            results.append(result)
        return results

    @deprecated
    def __mwe_relation_tuples_2_strings(self, listData, listCooccRef, mapParam, strInfoId):
        """
        Methode, um IDs in den MWE-Kookkurenzlisten auf Strings abzubilden
        hier wird im gegensatz zu '__relation_tuples_2_strings' mit einer
        Positionsliste (listCooccRef) für die Kookkurrenztupel (listData) gearbeitet
        """
        # Basis der neuen MWE-ID ist die alte MWE-ID (bzw. Treffer-ID)
        strMweId = mapParam["ConcordIdRemember"]

        # Parameter
        strOrder = "logDice"
        if "OrderBy" in mapParam:
            strOrder = mapParam["OrderBy"]
        bExtendedSurfaceForm = False
        if "ExtendedSurfaceForm" in mapParam:
            bExtendedSurfaceForm = bool(mapParam["ExtendedSurfaceForm"])

        # Positionen in den Kookkurrenztupeln
        # (0)rel,(1)prep,(2)lemma1,(3)lemma2,(4)surfacePrep,(5)surface1,(6)surface2,(7)POS2,(8)frequency,(9)freqBelege,(10)score_MiLogFrweq(11)score_logDice,(12)score_MI3,(13)info
        xRel = 0
        xPrep = 1
        xLemma1 = 2
        xLemma2 = 3
        xSurfacePrep = 4
        xSurface1 = 5
        xSurface2 = 6
        xPOS2 = 7
        xFrequency = 8
        xFreqBelege = 9
        xScore_MiLogFreq = 10
        xScore_logDice = 11
        xScore_MI3 = 12
        xInfo = 13
        xPOS1 = 14
        xConditionalCheck = 15

        xStrInfo = 16

        listMapRes = []

        # Durchgehen der Liste von Positionen der relevanten Daten
        for k in listCooccRef:
            i = listData[k]

            # Wenn eine MWE-ID gegeben ist (bei der MWE-free-Abfrage), ist diese die Basis der neuen MWE-ID
            if len(i) > 16:
                strMweId = i[xStrInfo]

            localMap = {}
            mapScore = {}

            # Ids auf Strings mappen
            localMap['Relation'] = self.CWpMySQL.mapIdToRel[i[xRel]]
            localMap['POS'] = self.CWpMySQL.mapIdToPOS[i[xPOS2]]
            strLemma = self.CWpMySQL.mmapIdToLem.get(i[xLemma2])
            strPrep = self.CWpMySQL.mmapIdToLem.get(i[xPrep])
            strSurface = self.CWpMySQL.mmapIdToSurf.get(i[xSurface2])
            strPrepSurface = strPrep

            # Oberflächenform formatieren (z.B. bei erweiterten Oberflächenformen mit Kontext)
            strSurface = surface_mapping(strSurface, self.CWpMySQL.mapRelIdToType[i[xRel]], strPrepSurface,
                                         bExtendedSurfaceForm)

            # evt. Lemma Reparieren
            strLemmaRepair = self.CWpSpec.mapLemmaRepair.get((localMap['POS'], strLemma), None)
            if strLemmaRepair != None:
                strLemma = strLemmaRepair.encode('utf8')

            # Lemma+Präposition formatieren
            if self.CWpMySQL.mapRelIdToType[i[xRel]] == 1 and strPrep != "-" and strPrep != "":
                strLemma = strLemma + ' ' + strPrep
            elif self.CWpMySQL.mapRelIdToType[i[xRel]] != 1 and strPrep != "-" and strPrep != "":
                strLemma = strPrep + ' ' + strLemma

            # Informationen in einer Map bündeln
            localMap['Lemma'] = strLemma
            localMap['Form'] = strSurface
            mapScore['Frequency'] = i[xFrequency]
            mapScore['MiLogFreq'] = i[xScore_MiLogFreq]
            mapScore['logDice'] = i[xScore_logDice]
            mapScore['MI3'] = i[xScore_MI3]
            localMap['Score'] = mapScore
            localMap["ConcordId"] = strMweId + "@" + str(i[xLemma1]) + "#" + str(i[xPOS1]) + "#" + str(
                i[xLemma2]) + "#" + str(i[xPOS2]) + "#" + str(i[xPrep]) + "#" + str(i[xRel]) + '#' + str(i[xInfo])

            # MWE-Zugänglichkeit
            if int(i[xConditionalCheck]) == 0:
                localMap["HasMwe"] = 0
            else:
                localMap["HasMwe"] = 1

            # Berechnen der Frequenz und der Anzahl der Belege bei symmetrischen Relationen
            iConcordNo = i[xFrequency]
            iFreqBelege = i[xFreqBelege]
            if self.CWpMySQL.mapRelIdToType[i[xRel]] == 2 and i[xLemma1] == i[xLemma2]:
                iConcordNo = iConcordNo / 2
                iFreqBelege = iFreqBelege / 2
            localMap['ConcordNo'] = iConcordNo
            localMap['ConcordNoAccessible'] = iFreqBelege

            # Zur Ergebnisliste hinzufügen
            listMapRes.append(localMap)

        return listMapRes

    @deprecated
    def get_diff(self, mapParam):
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
        listSortId = self.get_ordered_relation_ids(mapParam["Relations"], self.CWpMySQL.mapIdToPOS[mapParam["PosId"]])

        listData = self.get_relation_tuples_diff(mapParam, listSortId)

        mapRelData = self.__gen_rel_cooccurrence_mapping(listData)

        listResult = []
        for i in listSortId:
            if i in mapRelData:
                listTuples = self.__calculate_diff(i, listData, mapRelData[i], mapParam)
                listTuples = self.__diff_relation_tuples_2_strings(listData, listTuples, mapParam)

                strRel = self.CWpMySQL.mapIdToRel[i]
                strDesc = self.CWpSpec.strRelDesc
                if strRel in self.CWpSpec.mapRelDesc:
                    strDesc = self.CWpSpec.mapRelDesc[strRel]

                listResult.append({'Relation': strRel, 'Description': strDesc, 'Tuples': listTuples})

        return listResult

    @deprecated
    def get_intersection(self, mapParam):
        """
        Indirekter aufruf von get_diff mit der Operation 'rmax'
        """
        mapParam['Operation'] = 'rmax'
        return self.get_diff(mapParam)

    def __extract_coocc_info(self, info_id):
        """
        Extrahieren der Bestandteile einer Komplexen Treffer-Id bzw. Mwe-Id
        """
        coocc_infos = []
        for hit_mwe_id in info_id.split('@'):
            hit_mwe_id = [int(i) for i in hit_mwe_id.split('#')]
            if len(hit_mwe_id) == 1:
                coocc_info = CooccInfo(hit_mwe_id[0])
            else:
                coocc_info = CooccInfo(*(hit_mwe_id[-1:] + hit_mwe_id[:-1]))
            coocc_infos.append(coocc_info)
        return coocc_infos

    @deprecated
    def __extract_mwe_parts(self, strObj):
        """
        Extrahieren der Namens Bestandteile aus einer komplexen Treffer-Id bzw. MWE-Id
        """
        # (0)lemma1, (1)POS1, (2)lemma2, (3)POS2, (4)Prep, (5)Rel, (6)Info
        strBaseId = strObj
        # grobes aufspalten in die MWE-Bestandteile
        listMweId = strBaseId.split('@')
        iCount = 1
        vInfo = []
        for i in listMweId:
            listMweIdLocal = i.split('#')
            if iCount == 1:

                mapInfo = {}
                mapInfo['Lemma'] = self.CWpMySQL.mmapIdToLem.get(int(listMweIdLocal[0]))
                mapInfo['POS'] = self.CWpMySQL.mapIdToPOS[int(listMweIdLocal[1])]
                vInfo.append(mapInfo)

                mapInfo2 = {}
                mapInfo2['Lemma'] = self.CWpMySQL.mmapIdToLem.get(int(listMweIdLocal[2]))
                mapInfo2['POS'] = self.CWpMySQL.mapIdToPOS[int(listMweIdLocal[3])]
                vInfo.append(mapInfo2)

            else:

                mapInfo = {}
                mapInfo['Lemma'] = self.CWpMySQL.mmapIdToLem.get(int(listMweIdLocal[2]))
                mapInfo['POS'] = self.CWpMySQL.mapIdToPOS[int(listMweIdLocal[3])]
                vInfo.append(mapInfo)

            iCount += 1

        return vInfo

    @deprecated
    def __extract_mwe_info(self, strObj):
        """
        Extrahieren bestimmter Informationen aus einer komplexen Treffer-Id bzw. Mwe-Id:
        *Menge von Treffer-Ids
        *Abbildung von zweiter Lemmaform+Wortkategorie auf die möglichen Relation-Ids
        *Ein Treffer-Id-String durch '#' getrennt
        """
        # (0)lemma1, (1)POS1, (2)lemma2, (3)POS2, (4)Prep, (5)Rel, (6)Info
        strBaseId = strObj

        # grobes aufspalten in die MWE-Bestandteile
        listMweId = strBaseId.split('@')
        setId = set()
        mapLemCat = {}
        strInfoId = ""
        iCount = 1

        for i in listMweId:
            listMweIdLocal = i.split('#')
            if iCount == 1:
                setId.add(int(listMweIdLocal[6]))

                listRelId = self.gen_mwe_rel_ids_by_pos(self.CWpMySQL.mapIdToPOS[int(listMweIdLocal[1])])
                mapLemCat[(int(listMweIdLocal[0]), int(listMweIdLocal[1]))] = listRelId

                listRelId = self.gen_mwe_rel_ids_by_pos(self.CWpMySQL.mapIdToPOS[int(listMweIdLocal[3])])
                mapLemCat[(int(listMweIdLocal[2]), int(listMweIdLocal[3]))] = listRelId
            else:
                setId.add(int(listMweIdLocal[6]))

                listRelId = self.gen_mwe_rel_ids_by_pos(self.CWpMySQL.mapIdToPOS[int(listMweIdLocal[3])])
                mapLemCat[(int(listMweIdLocal[2]), int(listMweIdLocal[3]))] = listRelId

            iCount += 1

        # Treffer-Id-String durch '#' getrennt
        for i in setId:
            if strInfoId != "":
                strInfoId += "#"
            strInfoId += str(i)

        return (setId, mapLemCat, strInfoId)

    @deprecated
    def __extract_mwe_relation_info(self, strObj):
        """
        Extrahieren der Bestandteile einer Komplexen Relation-Id
        *Menge von Treffer-Ids
        *Abbildung von zweiter Lemmaform+Wortkategorie auf die möglichen Relation-Ids
        *Ein Treffer-Id-String durch '#' getrennt
        *Prefix der komplexen Treffer-Id bzw Mwe-Id
        """
        setId = set()
        mapLemCat = {}
        strInfoId = ""

        # grobes aufspalten in die MWE-Bestandteile
        listMweId = strObj.split('@')

        strMweId = strObj[0:strObj.rfind('@')]

        for i in range(0, len(listMweId)):
            listMweIdLocal = listMweId[i].split('#')
            if i == len(listMweId) - 1:
                # (0)lemma1, (1)POS1, (3)Rel
                mapLemCat[(int(listMweIdLocal[0]), int(listMweIdLocal[1]))] = [int(listMweIdLocal[2])]
            else:
                # (0)lemma1, (1)POS1, (2)lemma2, (3)POS2, (4)Prep, (5)Rel, (6)Info
                setId.add(int(listMweIdLocal[6]))

        # Treffer-Id-String durch '#' getrennt
        for i in setId:
            if strInfoId != "":
                strInfoId += "#"
            strInfoId += str(i)

        return (setId, mapLemCat, strInfoId, strMweId)

    @deprecated
    def get_mwe_relations_by_list(self, mapParam):
        """
        Die Methode ermöglicht es, anhand einer liste von Lemma-und-Pos-Informationen
        MWE-Wortprofilrelationen abzufragen.

        Eingabe ist ein Dictionary aus Parametern. Zu den Lemma-und-Pos-Informationen (Parts (Rückgabe von 'get_lemma_and_pos_by_list')) sind wetere Parameter: ab dem wievielten Eintrag die Tupel zu den einzelnen Relationen zurückgegeben werden sollen ( 'Start'), wie viele Einträge zurückgegeben werden sollen ( 'Number'), nach welcher Statistik ( 'Frequency','logDice') sortiert werden soll ( 'OrderBy'), die minimal erlaubte Frequenz ( 'MinFreq') und der minimal erlaubte Statistikwert ( 'MinStat').

        mapParam = {'Parts':<list>,'Start':<int=0>,'Number':<int=20>,'OrderBy':<string='logDice'>,'MinFreq':<int=-inf>,'MinStat':<float=-inf>}

        hiervon sind obligatorisch: 'Parts'

        *Die Rückgabe enthält einerseits die Information über die MWE-Bestandteile und andererseits je ein Wortprofil für die Wörter, die in dem MWE involviert sind, falls ein solches existiert. Konkret ist die Rückgabe ein Dictionary mit den Attributen 'parts', für die MWE-Bestandteile und 'data' für die Wortprofile zu den einzelnen Lemmaformen:

        {'parts':X,'data':Y }

        Die Informationen zu den MWE-Berstandteilen sind als Liste abgelegt. Die Reihenfolge der einzelnen Listenelemente entspricht hierbei der Abfragereihenfolge der MWE-Bestandteile. Die einzelnen Informationen sind als Dictionary angelegt und umfassen die Lemmaform 'Lemma' und die Wortkategorie 'POS':

        X = [{'Lemma':<string>,POS:<string>},'Lemma':<string>,POS:<string>}, ...]

        Einer Lemmaformen wird über ein Dictionary ein entsprechendes Wortprofil zugeordnet. Die Wortprofile haben hierbei die gleiche Gestallt wie in der Rückgabe von 'get_relations'. Hier ist ein Beispiel für einen MWE mit den Lemmaformen 'Hund' und 'lieben' gegeben:

        Y = {'Hund':[ {'Relation':<string>,'RelId':<string>,'Description':<string>,'Tuples'<list>}, ... ], 'lieben':[ {'Relation':<string>,'RelId':<string>,'Description':<string>,'Tuples'<list>}, ... ], ... }

        """
        mapParam["ConcordIdRemember"] = ""

        # eine Menge von binären Dependenzrelationen mit einer Sortierung, die die MWE-Wortprofilabfrage ermöglicht
        listInfo = self.CWpTree.lemma_and_pos_list_to_tree(mapParam['Parts'], self.CWpMySQL.mapRelToId,
                                                           self.CWpMySQL.mapRelIdToType)
        if len(listInfo) == 0:
            return {'data': [], 'parts': {}}

        # Abfragen der Kookkurrenzen
        listData = self.get_mwe_relations_by_list_base(mapParam, listInfo)

        # Mapping von den Relationen auf die Kookkurenzen erstellen
        mapRelDataRef = self.__gen_rel_pos_cooccurrence_mapping(listData)

        listResult = []
        vInfoVector = []

        # durchgehen der Relationen des Mapping
        mapResultPerLemma = {}
        strInfoPrefix = ""
        for j in mapRelDataRef:

            listLocalRelId = self.gen_mwe_rel_ids_by_pos(self.CWpMySQL.mapIdToPOS[j[1]])
            for i in listLocalRelId:
                if i in mapRelDataRef[j]:

                    # Ids innerhalb der Kookkurrenzinformatinen auf Strings abbilden
                    listTuples = self.__mwe_relation_tuples_2_strings(listData, mapRelDataRef[j][i], mapParam, "")

                    # Relation-Id zusammenbauen
                    strInfoPrefix = self.__mwe_id_prefix(listData, mapRelDataRef[j][i])
                    if strInfoPrefix != "":
                        strRelId = strInfoPrefix + "@" + str(j[0]) + '#' + str(j[1]) + '#' + str(i)
                    else:
                        strRelId = "undef"

                    strRel = self.CWpMySQL.mapIdToRel[i]
                    strDesc = self.CWpSpec.strRelDesc
                    if strRel in self.CWpSpec.mapRelDesc:
                        strDesc = self.CWpSpec.mapRelDesc[strRel]

                    strLem = self.CWpMySQL.mmapIdToLem.get(j[0])

                    if strLem in mapResultPerLemma:
                        mapResultPerLemma[strLem].append(
                            {'Relation': strRel, 'Description': strDesc, 'Tuples': listTuples, 'RelId': strRelId})
                    else:
                        mapResultPerLemma[strLem] = [
                            {'Relation': strRel, 'Description': strDesc, 'Tuples': listTuples, 'RelId': strRelId}]

        # Lemmabestandteile der Treffer-Id bzw. Mwe-Id ermitteln
        if strInfoPrefix != "":
            vParts = self.__extract_mwe_parts(strInfoPrefix)
        else:
            vParts = []

        mapKomplResult = {}
        mapKomplResult['data'] = mapResultPerLemma
        mapKomplResult['parts'] = vParts
        return mapKomplResult

    @deprecated
    def get_mwe_relations_by_list_parametric(self, mapParam):
        """
        Die Methode ermöglicht es, anhand einer liste von Lemma-und-Pos-Relation-Tupeln (Parts) MWE-Wortprofilrelationen abzufragen.

        Der Parameter 'Parts' kann hier beispielsweise so belegt werden: [{'Lemma2': 'Mann', 'Lemma1': 'lieben', 'Relation': 'SUBJA', 'POS2': 'Substantiv', 'Prep': '-', 'POS1': 'Verb'}, {'Lemma2': 'Frau', 'Lemma1': 'lieben', 'Relation': 'OBJ', 'POS2': 'Substantiv', 'Prep': '-', 'POS1': 'Verb'}]

        Hier steht '-' für nicht vorhanden.

        Ein anderes Beispiel mit Präposition ist:

        [{'Lemma2': 'Haus', 'Lemma1': 'wohnen', 'Relation': 'PP', 'POS2': 'Substantiv', 'Prep': 'in', 'POS1': 'Verb'}, {'Lemma2': 'sch\xc3\xb6n', 'Lemma1': 'Haus', 'Relation': 'ATTR', 'POS2': 'Adjektiv', 'Prep': '-', 'POS1': 'Substantiv'}]

        Wenn eine Relation unbestimmt sein soll, kann '*' verwendet werden:

        [{'Lemma2': 'Mann', 'Lemma1': 'sehen', 'Relation': '*', 'POS2': 'Substantiv', 'Prep': '-', 'POS1': 'Verb'}]

        Die Abfolge der Tupelelemente muss der Abfolge einer Sukzessiven sequenziellen Wortprofil-Mwe-Abfrage entsprechen.
        """
        listInfo = []
        listLemma = mapParam['Parts']
        if len(listLemma) < 1:
            return None

        # durch gehen der eingabeliste und extrahieren der Informationen
        for i in listLemma:
            mapParam["Word"] = i['Lemma1']
            mapParam["POS"] = i['POS1']
            # lemmainformationen für das erste Lemma ermitteln
            mapping1 = self.get_lemma_and_pos(mapParam)
            if mapping1 == []:
                return {'data': [], 'parts': {}}
            # lemmainformationen für das zweite Lemma ermitteln
            mapParam["Word"] = i['Lemma2']
            mapParam["POS"] = i['POS2']
            mapping2 = self.get_lemma_and_pos(mapParam)
            if mapping2 == []:
                return {'data': [], 'parts': {}}
            # id der Präposition ermitteln
            if 'Prep' in i:
                idPRep = self.CWpMySQL.get_prep_id(i['Prep'])
            else:
                idPRep = -1

            if i['Relation'] == "*":
                # unbestimmte Relation
                vRel = self.CWpTree.rellist_to_idlist_directed(mapping1[0]['Relations'], self.CWpMySQL.mapRelToId,
                                                               self.CWpMySQL.mapRelIdToType)
            else:
                # bestimmte Relation
                vRel = [self.CWpMySQL.mapRelToId[i['Relation']]]

            if len(mapping1) > 0 and len(mapping2) > 0:
                listInfo.append((mapping1[0], mapping2[0], vRel, idPRep))

        mapParam["ConcordIdRemember"] = ""

        if len(listInfo) < 1:
            return None

        # Mwe-Kookkurrenzen ermitteln
        listData = self.get_mwe_relations_by_list_base(mapParam, listInfo)

        # Mapping von den Relationen auf die Kookkurenzen erstellen
        mapRelDataRef = self.__gen_rel_pos_cooccurrence_mapping(listData)

        listResult = []
        vInfoVector = []

        mapResultPerLemma = {}

        # durchgehen der Relationen des Mapping
        for j in mapRelDataRef:

            listLocalRelId = self.gen_mwe_rel_ids_by_pos(self.CWpMySQL.mapIdToPOS[j[1]])
            for i in listLocalRelId:
                if i in mapRelDataRef[j]:

                    # Ids innerhalb der Kookkurrenzinformatinen auf Strings abbilden
                    listTuples = self.__mwe_relation_tuples_2_strings(listData, mapRelDataRef[j][i], mapParam, "")

                    # Relation-Id zusammenbauen
                    strInfoPrefix = self.__mwe_id_prefix(listData, mapRelDataRef[j][i])
                    if strInfoPrefix != "":
                        strRelId = strInfoPrefix + "@" + str(j[0]) + '#' + str(j[1]) + '#' + str(i)  # strInfoId
                    else:
                        strRelId = "undef"

                    strRel = self.CWpMySQL.mapIdToRel[i]
                    strDesc = self.CWpSpec.strRelDesc
                    if strRel in self.CWpSpec.mapRelDesc:
                        strDesc = self.CWpSpec.mapRelDesc[strRel]

                    strLem = self.CWpMySQL.mmapIdToLem.get(j[0])

                    if strLem in mapResultPerLemma:
                        mapResultPerLemma[strLem].append(
                            {'Relation': strRel, 'Description': strDesc, 'Tuples': listTuples, 'RelId': strRelId})
                    else:
                        mapResultPerLemma[strLem] = [
                            {'Relation': strRel, 'Description': strDesc, 'Tuples': listTuples, 'RelId': strRelId}]

        mapKomplResult = {}
        mapKomplResult['data'] = mapResultPerLemma
        mapKomplResult['parts'] = vInfoVector
        return mapKomplResult

    @deprecated
    def __get_mwe_rec_select(self, iStelligkeit):
        """
        Zusammenstellen einer MySQL Teilanfrage für die complexen IDs bei MWE-Abfragen (normale Version)
        """
        iMax = iStelligkeit + 1

        strConditionalRec = ""
        iCount = 1
        for i in range(1, iMax + 1):
            if i == 1:
                strCheckRec = ",myMweList" + str(iStelligkeit) + ".id" + str(i)
            elif i == iMax:
                strCheckRec = ",myMweList" + str(iStelligkeit) + ".id" + str(i - 1)
            else:
                strCheckRec = ",myMweList" + str(iStelligkeit) + ".id" + str(i - 1) + ",myMweList" + str(
                    iStelligkeit) + ".id" + str(i)

            if strConditionalRec != "":
                strConditionalRec += " , "
            if i == 1:
                strConditionalRec += "func_order_initial(idToConditional_" + str(
                    iStelligkeit) + ".mate" + strCheckRec + ")"
                pass
            elif i == iMax:
                strConditionalRec += "func_order_final(idToConditional_" + str(
                    iStelligkeit) + ".mate" + strCheckRec + ")"
                pass
            else:
                strConditionalRec += "func_order_middle(idToConditional_" + str(
                    iStelligkeit) + ".mate" + strCheckRec + ")"
                pass
            iCount += 1

        return strConditionalRec

    @deprecated
    def __get_mwe_rec_select_free(self, iStelligkeit):
        """
        Zusammenstellen einer MySQL Teilanfrage für die IDs bei MWE-Abfragen (Version für die freie Abfrage von MWEs)
        """
        iMax = iStelligkeit + 1

        strConditionalRec = ""
        iCount = 1
        for i in range(1, iMax + 1):
            if i == 1:
                strCheckRec = ",myMweList" + str(iStelligkeit) + ".id" + str(i)
            elif i == iMax:
                strCheckRec = ",myMweList" + str(iStelligkeit) + ".id" + str(i - 1)
            else:
                strCheckRec = ",myMweList" + str(iStelligkeit) + ".id" + str(i - 1) + ",myMweList" + str(
                    iStelligkeit) + ".id" + str(i)

            if strConditionalRec != "":
                strConditionalRec += " , "
            if i == 1:
                strConditionalRec += "func_order_initial(idToConditionalFree_" + str(
                    iStelligkeit) + ".mate" + strCheckRec + ")"
                pass
            elif i == iMax:
                strConditionalRec += "func_order_final(idToConditionalFree_" + str(
                    iStelligkeit) + ".mate" + strCheckRec + ")"
                pass
            else:
                strConditionalRec += "func_order_middle(idToConditionalFree_" + str(
                    iStelligkeit) + ".mate" + strCheckRec + ")"
                pass
            iCount += 1

        return strConditionalRec

    @deprecated
    def __get_mwe_rec_join_on(self, iStelligkeit):
        """
        Generieren einer Join-Bedingung, die die Kongruenz der IDs bei MWE-Abfragen realisiert (normale Version)
        """
        strJoinOn = ""
        iMax = iStelligkeit
        for i in range(1, iMax + 1):
            if strJoinOn != "":
                strJoinOn += " and "
            strJoinOn += "myMweList" + str(iStelligkeit) + ".id" + str(i) + " = idToConditional_" + str(
                iStelligkeit) + ".id" + str(i) + " "

        return strJoinOn

    @deprecated
    def __get_mwe_rec_join_on_free(self, iStelligkeit):
        """
        Generieren einer Join-Bedingung, die die Kongruenz der IDs bei MWE-Abfragen realisiert
        (Version für die freie Abfrage von MWEs)
        """
        strJoinOn = ""
        iMax = iStelligkeit
        for i in range(1, iMax + 1):
            if strJoinOn != "":
                strJoinOn += " and "
            strJoinOn += "myMweList" + str(iStelligkeit) + ".id" + str(i) + " = idToConditionalFree_" + str(
                iStelligkeit) + ".id" + str(i) + " "

        return strJoinOn

    @deprecated
    def get_mwe_relations_by_list_base(self, mapParam, listMweRec):
        """
        Abfragen der MySQL-Datenbank anhand einer Liste aus geordneten Dependenzrelationen (listMweRec).
        Hierbei werden MWE-Kookkurrenzen abgefragt.
        """
        iLemmaID = 0
        iPosID = 0
        iStart = 0
        iNumber = 20
        strOrderBy = "logDice"
        iMinFreq = -100000000
        iMinStat = -100000000
        strSubcorpus = ""
        listRelation = []

        iLemma2ID = -1
        iPos2ID = -1
        strHasMwe = ""

        # Informationen über das erste Element in listMweRec
        iLemmaID = listMweRec[0][0]["LemmaId"]
        iPosID = listMweRec[0][0]["PosId"]
        iLemma2ID = listMweRec[0][1]["LemmaId"]
        iPos2ID = listMweRec[0][1]["PosId"]
        iPrepId = listMweRec[0][3]

        # Parameter
        setRelations = set()
        if "Relations" in mapParam:
            for i in mapParam["Relations"]:
                setRelations.add(i)
        if "Start" in mapParam:
            iStart = mapParam["Start"]
        if "Number" in mapParam:
            iNumber = mapParam["Number"]
        if "OrderBy" in mapParam:
            strOrderBy = mapParam["OrderBy"]
        if "MinFreq" in mapParam:
            iMinFreq = mapParam["MinFreq"]
        if "MinStat" in mapParam:
            iMinStat = mapParam["MinStat"]
        if "Subcorpus" in mapParam:
            strSubcorpus = mapParam["Subcorpus"]

        strMinFreq = "0"
        if iMinFreq > 0:
            strMinFreq = str(iMinFreq)

        strMinStat = "-9999999"
        if iMinStat > -100000000:
            strMinStat = str(iMinStat)

        strRelIds = self.CWpMySQL.list_2_in(listMweRec[0][2])

        strWherePrep = ""
        if iPrepId != -1:
            strWherePrep = " and prep = \"%s\" " % (iPrepId)

        # zusammenbauen der MWE-ID für spätere Abfragen
        strInitialInfo = "CONCAT('%s#%s#%s#%s#',%s,'#',%s,'#',%s)" % (
            str(iLemmaID), str(iPosID), str(iLemma2ID), str(iPos2ID), "relations.prep", "relations.function",
            "relations.info")

        # mit Hilfe der Tabelle 'relations' die Treffer-Id ermitteln
        strCreate1 = "CREATE TEMPORARY TABLE myMweList1 LIKE tmpMweList1; "
        strIn1 = "INSERT INTO myMweList1 "
        strSelect1 = "SELECT  info, " + strInitialInfo + " "
        strFrom1 = "FROM relations USE INDEX(I_" + strOrderBy + ") "
        strWhere1 = "WHERE lemma1=\"%s\" and POS1=\"%s\" and lemma2=\"%s\" and POS2=\"%s\" and function IN %s %s;" % (
            listMweRec[0][0]["LemmaId"], listMweRec[0][0]["PosId"], listMweRec[0][1]["LemmaId"],
            listMweRec[0][1]["PosId"],
            strRelIds, strWherePrep)

        self.CWpMySQL.connect()
        self.CWpMySQL.execute("SET NAMES 'utf8';")
        self.CWpMySQL.execute(strCreate1)
        self.CWpMySQL.execute(strIn1 + strSelect1 + strFrom1 + strWhere1)  #

        # bei komplexeren MWEs, erweitern um die weiteren Komponenten
        iCount = 1
        for i in range(1, len(listMweRec)):
            strRecSelect = self.__get_mwe_rec_select_free(iCount)
            strRecJoinOn = self.__get_mwe_rec_join_on_free(iCount)
            strRelIds = self.CWpMySQL.list_2_in(listMweRec[i][2])

            iPrepId = listMweRec[i][3]
            strWherePrep = ""
            if iPrepId != -1:
                strWherePrep = " and prep = \"%s\" " % (iPrepId)

            # Zusammenbauen der MWE-ID für spätere Abfragen
            strInfo2 = "CONCAT(myMweList%i.info,'@',idToConditionalFree_%i.lemma1,'#',idToConditionalFree_%i.pos1,'#',idToConditionalFree_%i.lemma2,'#',idToConditionalFree_%i.pos2,'#',idToConditionalFree_%i.prep,'#',idToConditionalFree_%i.function,'#',idToConditionalFree_%i.mate)" % (
                iCount, iCount, iCount, iCount, iCount, iCount, iCount, iCount)

            # mit Hilfe der Tabelle 'tmpMweList' die Treffer-IDs ermitteln
            strCreate2 = "CREATE TEMPORARY TABLE myMweList" + str(iCount + 1) + " LIKE tmpMweList" + str(
                iCount + 1) + "; "
            strIn2 = "INSERT INTO myMweList" + str(iCount + 1) + " "
            strSelect2 = "SELECT  " + strRecSelect + ", " + strInfo2 + " "
            strFrom2 = "FROM myMweList" + str(iCount) + " STRAIGHT_JOIN idToConditionalFree_" + str(
                iCount) + " ON ( " + strRecJoinOn + " )"
            strWhere = " WHERE (lemma1=\"%s\" and POS1=\"%s\") and (lemma2=\"%s\" and POS2=\"%s\") and function IN %s %s " % (
                listMweRec[i][0]["LemmaId"], listMweRec[i][0]["PosId"], listMweRec[i][1]["LemmaId"],
                listMweRec[i][1]["PosId"], strRelIds, strWherePrep)

            self.CWpMySQL.execute(strCreate2)
            self.CWpMySQL.execute(strIn2 + strSelect2 + strFrom2 + strWhere)  #

            iCount += 1

        # weiteres Zusammenbauen der MWE-ID für spätere Abfragen
        strInfoCut = "CONCAT(myMweList%i.info,'@',idToConditional_%i.lemma,'#',idToConditional_%i.pos,'#0#',idToConditional_%i.function,'#',idToConditional_%i.mate)" % (
            iCount, iCount, iCount, iCount, iCount)

        strRecSelect = self.__get_mwe_rec_select(iCount)
        strRecJoinOn = self.__get_mwe_rec_join_on(iCount)
        strRecJoinOnFree = self.__get_mwe_rec_join_on_free(iCount)
        # Abschneiden nach den Schwellwerten für jede einzelne Relation
        strCreateCut = "CREATE TEMPORARY TABLE myMateCut LIKE tmpMweListCut_" + str(iCount + 1) + "; "
        strInCut = "INSERT INTO myMateCut "
        strSelectCut = " SELECT idToConditional_" + str(iCount) + ".mate,-idToConditional_" + str(
            iCount) + ".frequency,-idToConditional_" + str(iCount) + ".freqBelege,-idToConditional_" + str(
            iCount) + ".logDice,idToConditional_" + str(iCount) + ".function,idToConditional_" + str(
            iCount) + ".lemma,idToConditional_" + str(iCount) + ".POS, " + strRecSelect + ",  myMweList" + str(
            iCount) + ".info "
        strFromCut = "FROM myMweList" + str(iCount) + " STRAIGHT_JOIN idToConditional_" + str(
            iCount) + " USE INDEX(I_" + strOrderBy + ") ON ( " + strRecJoinOn + " )"
        strWhereCut = " WHERE idToConditional_" + str(iCount) + ".lemma=$LEMMA$ and idToConditional_" + str(
            iCount) + ".POS=$POS$ and idToConditional_" + str(
            iCount) + ".function=$FUNCTION$ and -idToConditional_" + str(
            iCount) + ".logDice>=" + strMinStat + " and -idToConditional_" + str(
            iCount) + ".frequency>=" + strMinFreq + " "
        strLimitCut = " LIMIT " + str(iStart) + "," + str(iNumber) + ";"

        self.CWpMySQL.execute(strCreateCut)

        mapDone = {}
        for i in listMweRec:
            if (i[0]["LemmaId"], i[0]["PosId"]) not in mapDone:
                for j in i[0]["Relations"]:
                    if len(setRelations) == 0 or j in setRelations:
                        strWhereCutDummy = strWhereCut.replace("$LEMMA$", str(i[0]["LemmaId"])).replace("$POS$", str(
                            i[0]["PosId"])).replace("$FUNCTION$", str(self.CWpMySQL.mapRelToId[j]))
                        self.CWpMySQL.execute(strInCut + strSelectCut + strFromCut + strWhereCutDummy + strLimitCut)
                mapDone[(i[0]["LemmaId"], i[0]["PosId"])] = True

            if (i[1]["LemmaId"], i[1]["PosId"]) not in mapDone:
                for j in i[1]["Relations"]:
                    if len(setRelations) == 0 or j in setRelations:
                        strWhereCutDummy = strWhereCut.replace("$LEMMA$", str(i[1]["LemmaId"])).replace("$POS$", str(
                            i[1]["PosId"])).replace("$FUNCTION$", str(self.CWpMySQL.mapRelToId[j]))
                        self.CWpMySQL.execute(strInCut + strSelectCut + strFromCut + strWhereCutDummy + strLimitCut)
                mapDone[(i[1]["LemmaId"], i[1]["PosId"])] = True

        # Ermitteln der Kookkurrrenzen, die zurückgegeben werden sollen
        strConditionalRecJoin = ""
        iCount2 = 1
        for i in range(0, iCount + 1):
            if strConditionalRecJoin != "":
                strConditionalRecJoin += " and "
            strConditionalRecJoin += "ConditionalCheck_" + str(iCount + 1) + ".id" + str(
                iCount2) + "=myMateCut.id" + str(iCount2)
            iCount2 += 1

        if self.CWpMySQL.iMweDepth > iCount:

            strMinFreqCheck = ""
            if iMinFreq > 0:
                strMinFreqCheck = " and (-ConditionalCheck_" + str(iCount + 1) + ".frequency)>=" + str(iMinFreq) + " "

            strMinStatCheck = ""
            if iMinStat > -100000000:
                strMinStatCheck = " and (-ConditionalCheck_" + str(iCount + 1) + ".logDice)>=" + str(iMinStat) + " "

            strSelect3 = """ SELECT relations.function,prep,lemma1,lemma2,surfacePrep,surface1,surface2,POS2,myMateCut.frequency,myMateCut.freqBelege,0,myMateCut.logDice,0,relations.info,POS1,
    if(ConditionalCheck_""" + str(
                iCount + 1) + """.id1!=CAST('None' as UNSIGNED) """ + strMinFreqCheck + strMinStatCheck + """,1,0),myMateCut.info """
            strFrom3 = """FROM myMateCut
                        STRAIGHT_JOIN relations FORCE INDEX(I_info) ON
                        (
                          relations.info=myMateCut.mate and
                          relations.function=myMateCut.function
                        )
                        LEFT JOIN ConditionalCheck_""" + str(iCount + 1) + """ FORCE INDEX(I_id) ON
                        (
                           """ + strConditionalRecJoin + """
                        )
                        """
        else:
            strSelect3 = " SELECT relations.function,relations.prep,lemma1,lemma2,surfacePrep,surface1,surface2,POS2,myMateCut.frequency,myMateCut.freqBelege,0,myMateCut.logDice,0,relations.info,POS1,'0',myMateCut.info "

            strFrom3 = """FROM myMateCut STRAIGHT_JOIN relations FORCE INDEX(I_info) ON
                        (
                          relations.info=myMateCut.mate and
                          relations.function=myMateCut.function
                        )
                        """

        self.CWpMySQL.execute(strSelect3 + strFrom3)

        listResult = self.CWpMySQL.fetchall()
        self.CWpMySQL.disconnect()

        return listResult

    @deprecated
    def get_mwe_relations(self, mapParam):
        """
        Die Methode ermöglicht es, anhand einer Concordanz-ID MWE-Wortprofilrelationen abzufragen.

        *Eingabe ist ein Dictionary aus Parametern. Zu der Concordanz-ID ( 'ConcordId') sind wetere Parameter: ab dem wievielten Eintrag die Tupel zu den einzelnen Relationen zurückgegeben werden sollen ( 'Start'), wie viele Einträge zurückgegeben werden sollen ( 'Number'), nach welcher Statistik ( 'Frequency','logDice') sortiert werden soll ( 'OrderBy'), die minimal erlaubte Frequenz ( 'MinFreq') und der minimal erlaubte Statistikwert ( 'MinStat'):
            mapParam = {'ConcordId':<string>,'Start':<int=0>,'Number':<int=20>,'OrderBy':<string='logDice'>,'MinFreq':<int=-inf>,'MinStat':<float=-inf>}

        hiervon sind obligatorisch: 'MweId'
        *Die Rückgabe enthält einerseits die Information über die MWE-Bestandteile und andererseits je ein Wortprofil für die Wörter, die in dem MWE involviert sind, falls ein solches existiert. Konkret ist die Rückgabe ein Dictionary mit den Attributen 'parts', für die MWE-Bestandteile und 'data' für die Wortprofile zu den einzelnen Lemmaformen:
        {'parts':X,'data':Y }
        Die Informationen zu den MWE-Berstandteilen sind als Liste abgelegt. Die Reihenfolge der einzelnen Listenelemente entspricht hierbei der Abfragereihenfolge der MWE-Bestandteile. Die einzelnen Informationen sind als Dictionary angelegt und umfassen die Lemmaform 'Lemma' und die Wortkategorie 'POS':
        X = [{'Lemma':<string>,POS:<string>},'Lemma':<string>,POS:<string>}, ...]
        Einer Lemmaformen wird über ein Dictionary ein entsprechendes Wortprofil zugeordnet. Die Wortprofile haben hierbei die gleiche Gestallt wie in der Rückgabe von 'get_relations'. Hier ist ein Beispiel für einen MWE mit den Lemmaformen 'Hund' und 'lieben' gegeben:
        Y = {'Hund':[ {'Relation':<string>,'RelId':<string>,'Description':<string>,'Tuples'<list>}, ... ], 'lieben':[ {'Relation':<string>,'RelId':<string>,'Description':<string>,'Tuples'<list>}, ... ], ... }
        """
        (setInfoId, mapLemCat, strInfoId) = self.__extract_mwe_info(mapParam["ConcordId"])

        # Komplexe Mwe-Id bzw. Treffer-Id in seine Bestandteile aufsplitten
        vInfoVector = self.__extract_mwe_parts(mapParam["ConcordId"])

        mapParam['ConcordIdRemember'] = mapParam['ConcordId']
        mapParam['ConcordId'] = strInfoId

        listRelations = []
        if 'Relations' in mapParam:
            listRelations = self.gen_rel_ids_by_rel(mapParam['Relations'])

        # Ermitteln Kookkurrenzen für alle syntaktischen Relationen
        listData = self.__get_relation_tuples_mwe(mapParam, listRelations, setInfoId)

        # Erstellen einer Map, die den Relationen die Kookkurrenzen zuordnet
        mapRelData = self.__gen_rel_pos_cooccurrence_mapping(listData)

        listResult = []

        # Durchgehen der Relationen
        mapResultPerLemma = {}
        for j in mapRelData:

            # Prüfen, ob zu der Wortkategorie die syntaktische Relation behandelt werden soll
            listLocalRelId = self.gen_mwe_rel_ids_by_pos(self.CWpMySQL.mapIdToPOS[j[1]])
            for i in listLocalRelId:
                if i in mapRelData[j]:
                    # IDs in den Kookkurrenz-Informationen auf Strings abbilden
                    listTuples = self.__mwe_relation_tuples_2_strings(listData, mapRelData[j][i], mapParam, strInfoId)

                    # komplexe Relation-Id zusammenbauen
                    strRelId = mapParam['ConcordIdRemember'] + "@" + str(j[0]) + '#' + str(j[1]) + '#' + str(
                        i)  # strInfoId

                    # Metainformationen
                    strRel = self.CWpMySQL.mapIdToRel[i]
                    strDesc = self.CWpSpec.strRelDesc
                    if strRel in self.CWpSpec.mapRelDesc:
                        strDesc = self.CWpSpec.mapRelDesc[strRel]

                    # Lemmaform ermitteln
                    strLem = self.CWpMySQL.mmapIdToLem.get(j[0])

                    # zum Ergebnis hinzufügen
                    if strLem in mapResultPerLemma:
                        mapResultPerLemma[strLem].append(
                            {'Relation': strRel, 'Description': strDesc, 'Tuples': listTuples, 'RelId': strRelId})
                    else:
                        mapResultPerLemma[strLem] = [
                            {'Relation': strRel, 'Description': strDesc, 'Tuples': listTuples, 'RelId': strRelId}]

        mapKomplResult = {}
        mapKomplResult['data'] = mapResultPerLemma
        mapKomplResult['parts'] = vInfoVector
        return mapKomplResult

    @deprecated
    def get_mwe_cooccurrences(self, mapParam):
        """
        Ermitteln der Kookkurrenzen zu einer komplexen MWE-Relation-Id
        """
        # Extrahieren der Bestandteile einer Komplexen Relation-Id
        strRelId = mapParam["RelId"]
        (setInfoId, mapLemCat, strInfoId, strMweId) = self.__extract_mwe_relation_info(strRelId)

        # ermitteln der Kookkurenzen
        mapParam['ConcordIdRemember'] = mapParam['RelId']
        mapParam['ConcordId'] = strMweId
        listData = self.__get_relation_tuples_mwe_single(mapParam, setInfoId, mapLemCat)

        # Mapping von den Relationen auf die Kookkurenzen erstellen
        mapRelData = self.__gen_rel_pos_cooccurrence_mapping(listData)

        listResult = []

        mapResultPerLemma = {}

        # Durchgehen der Relationen
        for j in mapRelData:
            # Durchgehen der entsprechenden Kookkurrenzen
            for i in mapRelData[j]:
                # IDs in den Kookkurrenz-Informationen auf Strings abbilden
                listTuples = self.__mwe_relation_tuples_2_strings(listData, mapRelData[j][i], mapParam, strInfoId)

        return listTuples

    @deprecated
    def __get_relation_tuples_mwe_single(self, mapParam, setInfoId, mapLemCat):
        """
        Ermitteln der Kookkurrenzen zu einer Menge von Treffer-Ids und einer Map von Lemma-Wortkategorie auf
        mögliche Relationen
        """
        iMinFreq = -100000000
        iMinStat = -100000000
        iNumber = 100000000
        iStart = 0

        # Parameter
        if "Start" in mapParam:
            iStart = mapParam["Start"]
        if "Number" in mapParam:
            iNumber = int(mapParam["Number"])
        strOrderBy = "logDice"
        if "OrderBy" in mapParam:
            strOrderBy = mapParam["OrderBy"]
        bReverse = False
        if "Reverse" in mapParam:
            bReverse = bool(mapParam["Reverse"])
        if "MinFreq" in mapParam:
            iMinFreq = mapParam["MinFreq"]
        if "MinStat" in mapParam:
            iMinStat = mapParam["MinStat"]

        # Schwellwerte
        strMinFreq = "0"
        if iMinFreq > 0:
            strMinFreq = str(iMinFreq)
        strMinStat = "-9999999"
        if iMinStat > -100000000:
            strMinStat = str(iMinStat)

        iMweStelligkeit = len(setInfoId)

        # Konstruieren der Where-Bedingung
        strWhereRec = ""
        strCheckRec = ""
        vCheckRec = []
        strConditionalRec = ""
        iCount = 1
        for i in sorted(setInfoId):
            if strWhereRec != "":
                strWhereRec += " and "
            strWhereRec += "idToConditional_" + str(iMweStelligkeit) + ".id" + str(iCount) + "=" + str(i) + " "
            vCheckRec.append(i)
            strCheckRec += "," + str(i)
            iCount += 1

        # Konstruieren der MWE-Bedingungen
        iCount = 1
        for i in range(0, len(setInfoId) + 1):
            if i == 0:
                strCheckRec = ',' + str(vCheckRec[i])
            elif i == len(setInfoId):
                strCheckRec = ',' + str(vCheckRec[i - 1])
            else:
                strCheckRec = ',' + str(vCheckRec[i - 1]) + ',' + str(vCheckRec[i])
            if strConditionalRec != "":
                strConditionalRec += " , "
            if i == 0:
                strConditionalRec += "func_order_initial" + "(idToConditional_" + str(
                    iMweStelligkeit) + ".mate" + strCheckRec + ")"
                pass
            elif i == len(setInfoId):
                strConditionalRec += "func_order_final" + "(idToConditional_" + str(
                    iMweStelligkeit) + ".mate" + strCheckRec + ")"
                pass
            else:
                strConditionalRec += "func_order_middle" + "(idToConditional_" + str(
                    iMweStelligkeit) + ".mate" + strCheckRec + ")"
                pass
            iCount += 1
        strConditionalRecJoin = ""
        iCount = 1
        for i in range(0, len(setInfoId) + 1):
            if strConditionalRecJoin != "":
                strConditionalRecJoin += " and "
            strConditionalRecJoin += "ConditionalCheck_" + str(iMweStelligkeit + 1) + ".id" + str(
                iCount) + "=myMateCut.id" + str(iCount)
            iCount += 1

        # Anhand der Mate-ConcordId die Passenden Kookkurenz-IDS finden
        strCreate1 = "CREATE TEMPORARY TABLE myMateCut LIKE tmpMateCut_" + str(iMweStelligkeit + 1) + "; "
        strIn1 = "INSERT INTO myMateCut "
        strSelect1 = " SELECT idToConditional_" + str(iMweStelligkeit) + ".mate,-idToConditional_" + str(
            iMweStelligkeit) + ".frequency,-idToConditional_" + str(
            iMweStelligkeit) + ".freqBelege,-idToConditional_" + str(
            iMweStelligkeit) + ".logDice,idToConditional_" + str(iMweStelligkeit) + ".function,idToConditional_" + str(
            iMweStelligkeit) + ".lemma,idToConditional_" + str(iMweStelligkeit) + ".POS," + strConditionalRec + ", 0 "
        strFrom1 = "FROM idToConditional_" + str(iMweStelligkeit) + " USE INDEX(I_" + strOrderBy + ") "
        strWhere1 = " WHERE " + strWhereRec + " and idToConditional_" + str(
            iMweStelligkeit) + ".lemma=$LEMMA$ and idToConditional_" + str(
            iMweStelligkeit) + ".POS=$POS$ and idToConditional_" + str(
            iMweStelligkeit) + ".function=$FUNCTION$ and -idToConditional_" + str(
            iMweStelligkeit) + ".logDice>=" + strMinStat + " and -idToConditional_" + str(
            iMweStelligkeit) + ".frequency>=" + strMinFreq + " "
        strLimit1 = " LIMIT " + str(iStart) + "," + str(iNumber) + ";"

        # Ermitteln der Kookkurrrenzen
        if self.CWpMySQL.iMweDepth > iMweStelligkeit:

            # Schwellwerte für den MWE-Check
            strMinFreqCheck = ""
            if iMinFreq > 0:
                strMinFreqCheck = " and (-ConditionalCheck_" + str(iMweStelligkeit + 1) + ".frequency)>=" + str(
                    iMinFreq) + " "
            strMinStatCheck = ""
            if iMinStat > -100000000:
                strMinStatCheck = " and (-ConditionalCheck_" + str(iMweStelligkeit + 1) + ".logDice)>=" + str(
                    iMinStat) + " "

            strSelect3 = """ SELECT relations.function,prep,lemma1,lemma2,surfacePrep,surface1,surface2,POS2,myMateCut.frequency,myMateCut.freqBelege,0,myMateCut.logDice,0,info,POS1,
    if(ConditionalCheck_""" + str(
                iMweStelligkeit + 1) + """.id1!=CAST('None' as UNSIGNED) """ + strMinFreqCheck + strMinStatCheck + """,1,0) """
            strFrom3 = """FROM myMateCut
                        STRAIGHT_JOIN relations FORCE INDEX(I_info) ON
                        (
                          relations.info=myMateCut.mate and
                          relations.function=myMateCut.function
                        )
                        LEFT JOIN ConditionalCheck_""" + str(iMweStelligkeit + 1) + """ FORCE INDEX(I_id) ON
                        (
                           """ + strConditionalRecJoin + """
                        )
                        """
        else:
            strSelect3 = " SELECT relations.function,prep,lemma1,lemma2,surfacePrep,surface1,surface2,POS2,myMateCut.frequency,myMateCut.freqBelege,0,myMateCut.logDice,0,info,POS1,'0' "
            strFrom3 = """FROM myMateCut STRAIGHT_JOIN relations FORCE INDEX(I_info) ON
                        (
                          relations.info=myMateCut.mate and
                          relations.function=myMateCut.function
                        )
                        """

        self.CWpMySQL.connect()
        self.CWpMySQL.execute("SET NAMES 'utf8';")

        self.CWpMySQL.execute(strCreate1)
        # ausfüren der MySQL-Abfrage für die verschiedenen Lemmaformen und Wortarten der Vorhergehenden komplexen MWE-ID (An bestehende Lemma wird angehängt)
        for i in mapLemCat:
            listRelId = mapLemCat[i]
            for j in listRelId:
                strWhereDummy = strWhere1.replace("$LEMMA$", str(i[0])).replace("$POS$", str(i[1])).replace(
                    "$FUNCTION$", str(j))
                self.CWpMySQL.execute(strIn1 + strSelect1 + strFrom1 + strWhereDummy + strLimit1)

        self.CWpMySQL.execute(strSelect3 + strFrom3)

        listResult = self.CWpMySQL.fetchall()

        self.CWpMySQL.disconnect()

        return listResult

    @deprecated
    def __get_relation_tuples_mwe(self, mapParam, listRelationId, setInfoId):
        """
        Ermitteln der Kookkurrenzen zu einer Menge von Relation-Ids und einer Menge von Treffer-Ids
        """
        iMinFreq = -100000000
        iMinStat = -100000000
        iNumber = 100000000
        iStart = 0

        iLemma2ID = -1
        iPos2ID = -1

        # Parameter
        if "Start" in mapParam:
            iStart = mapParam["Start"]
        if "Number" in mapParam:
            iNumber = int(mapParam["Number"])
        strOrder = "logDice"
        if "OrderBy" in mapParam:
            strOrder = mapParam["OrderBy"]
        bReverse = False
        if "Reverse" in mapParam:
            bReverse = bool(mapParam["Reverse"])
        if "MinFreq" in mapParam:
            iMinFreq = mapParam["MinFreq"]
        if "MinStat" in mapParam:
            iMinStat = mapParam["MinStat"]
        if "Lemma2Id" in mapParam:
            iLemma2ID = mapParam["Lemma2Id"]
        if "Pos2Id" in mapParam:
            iPos2ID = mapParam["Pos2Id"]
        if "HasMwe" in mapParam:
            strHasMwe = " and ConditionalCheck_1.id1!=CAST('None' as UNSIGNED) "

        # Schwellwerte
        strMinFreq = "0"
        if iMinFreq > 0:
            strMinFreq = str(iMinFreq)
        strMinStat = "-9999999"
        if iMinStat > -100000000:
            strMinStat = str(iMinStat)

        iMweStelligkeit = len(setInfoId)

        # Konstruieren der Where-Bedingung
        strWhereRec = ""
        strCheckRec = ""
        vCheckRec = []
        strConditionalRec = ""
        iCount = 1
        for i in sorted(setInfoId):
            if strWhereRec != "":
                strWhereRec += " and "
            strWhereRec += "idToConditional_" + str(iMweStelligkeit) + ".id" + str(iCount) + "=" + str(i) + " "
            vCheckRec.append(i)
            strCheckRec += "," + str(i)
            iCount += 1

        # Konstruieren der MWE-Bedingungen
        strRelIds = ""
        if len(listRelationId) > 0:
            strRelIds = " and idToConditional_" + str(iMweStelligkeit) + ".function IN" + self.CWpMySQL.list_2_in(
                listRelationId)
        iCount = 1
        for i in range(0, len(setInfoId) + 1):
            if i == 0:
                strCheckRec = ',' + str(vCheckRec[i])
            elif i == len(setInfoId):
                strCheckRec = ',' + str(vCheckRec[i - 1])
            else:
                strCheckRec = ',' + str(vCheckRec[i - 1]) + ',' + str(vCheckRec[i])
            if strConditionalRec != "":
                strConditionalRec += " , "
            if i == 0:
                strConditionalRec += "func_order_initial" + "(x.mate" + strCheckRec + ")"
                pass
            elif i == len(setInfoId):
                strConditionalRec += "func_order_final" + "(x.mate" + strCheckRec + ")"
                pass
            else:
                strConditionalRec += "func_order_middle" + "(x.mate" + strCheckRec + ")"
                pass
            iCount += 1

        # Bedingungen für den MWE-Check
        strConditionalRecJoin = ""
        iCount = 1
        for i in range(0, len(setInfoId) + 1):
            if strConditionalRecJoin != "":
                strConditionalRecJoin += " and "
            strConditionalRecJoin += "ConditionalCheck_" + str(iMweStelligkeit + 1) + ".id" + str(
                iCount) + "=myMateCut.id" + str(iCount)
            iCount += 1

        # Anhand der Mate-ConcordId die Passenden Kookkurenz-IDS finden
        strCreate1 = "CREATE TEMPORARY TABLE myMate LIKE tmpMate; "
        strIn1 = "INSERT INTO myMate "
        strSelect1 = " SELECT idToConditional_" + str(iMweStelligkeit) + ".mate,-idToConditional_" + str(
            iMweStelligkeit) + ".frequency,-idToConditional_" + str(
            iMweStelligkeit) + ".freqBelege,-idToConditional_" + str(
            iMweStelligkeit) + ".logDice,idToConditional_" + str(iMweStelligkeit) + ".function,idToConditional_" + str(
            iMweStelligkeit) + ".lemma,idToConditional_" + str(iMweStelligkeit) + ".POS "
        strFrom1 = "FROM idToConditional_" + str(iMweStelligkeit) + " "
        strWhere1 = " WHERE " + strWhereRec + " " + strRelIds + " "
        strOrder1 = " ORDER BY function,lemma,pos," + strOrder + ";"

        # Abschneiden der Kookkurenz-IDs
        strVar2 = "set @num := 0, @function := '', @lemma := '', @POS := '' ;"
        strCreate2 = "CREATE TEMPORARY TABLE myMateCut LIKE tmpMateCut_" + str(iMweStelligkeit + 1) + "; "
        strIn2 = "INSERT INTO myMateCut "
        strSelect2 = """SELECT x.mate, x.frequency, x.freqBelege,x.logDice, x.function, x.lemma, x.POS,""" + strConditionalRec + """, x.row_number FROM (SELECT mate,frequency,freqBelege,logDice,function,lemma,POS, @num := if(@function=function and @lemma=lemma and @POS=POS, @num + 1, 1) as row_number , @function := function as current_function, @lemma := lemma as current_lemma, @POS := POS as current_POS
                      """
        strFrom2 = "FROM myMate) as x "
        strWhere2 = " WHERE x.logDice>=" + strMinStat + " and frequency>=" + strMinFreq + " and x.row_number>" + str(
            iStart) + " and x.row_number <= " + str(iNumber + iStart) + ";"

        # Ermitteln der Kookkurrrenzen
        if self.CWpMySQL.iMweDepth > iMweStelligkeit:

            # Schwellwerte für den MWE-Check
            strMinFreqCheck = ""
            if iMinFreq > 0:
                strMinFreqCheck = " and (-ConditionalCheck_" + str(iMweStelligkeit + 1) + ".frequency)>=" + str(
                    iMinFreq) + " "
            strMinStatCheck = ""
            if iMinStat > -100000000:
                strMinStatCheck = " and (-ConditionalCheck_" + str(iMweStelligkeit + 1) + ".logDice)>=" + str(
                    iMinStat) + " "

            strSelect3 = """ SELECT relations.function,prep,lemma1,lemma2,surfacePrep,surface1,surface2,POS2,myMateCut.frequency,myMateCut.freqBelege,0,myMateCut.logDice,0,info,POS1,
    if(ConditionalCheck_""" + str(
                iMweStelligkeit + 1) + """.id1!=CAST('None' as UNSIGNED) """ + strMinFreqCheck + strMinStatCheck + """,1,0) """
            strFrom3 = """FROM myMateCut
                        STRAIGHT_JOIN relations FORCE INDEX(I_info) ON
                        (
                          relations.info=myMateCut.mate and
                          relations.function=myMateCut.function
                        )
                        LEFT JOIN ConditionalCheck_""" + str(iMweStelligkeit + 1) + """ FORCE INDEX(I_id) ON
                        (
                           """ + strConditionalRecJoin + """
                        )
                        """
        else:
            strSelect3 = " SELECT relations.function,prep,lemma1,lemma2,surfacePrep,surface1,surface2,POS2,myMateCut.frequency,myMateCut.freqBelege,0,myMateCut.logDice,0,info,POS1,'0' "
            strFrom3 = """FROM myMateCut STRAIGHT_JOIN relations FORCE INDEX(I_info) ON
                        (
                          relations.info=myMateCut.mate and
                          relations.function=myMateCut.function
                        )
                        """

        # wenn auch das zweite Lemma bei der Abfrage angegeben ist
        strWhere3 = ""
        if iLemma2ID != -1 and iPos2ID != -1:
            strWhere3 = " WHERE lemma2=\"" + str(iLemma2ID) + "\"  and POS2=\"" + str(iPos2ID) + "\" "

        # MySQL Abfrage
        self.CWpMySQL.connect()
        self.CWpMySQL.execute("SET NAMES 'utf8';")
        self.CWpMySQL.execute(strCreate1)
        self.CWpMySQL.execute(strIn1 + strSelect1 + strFrom1 + strWhere1 + strOrder1)
        self.CWpMySQL.execute(strVar2)
        self.CWpMySQL.execute(strCreate2)
        self.CWpMySQL.execute(strIn2 + strSelect2 + strFrom2 + strWhere2)
        self.CWpMySQL.execute(strSelect3 + strFrom3 + strWhere3)
        listResult = self.CWpMySQL.fetchall()

        self.CWpMySQL.disconnect()

        return listResult

    @deprecated
    def get_relation_tuples_diff(self, mapParam, listRelationId):
        """
        Ermitteln der Kookkurrenzen zu einer Liste von syntaktischen Relationen für die 'diff'-Abfrage
        """
        mapParam1 = {}
        mapParam2 = {}

        strOrderBy = "logDice"
        iMinFreq = -100000000
        iMinStat = -100000000
        strSubcorpus = ""
        strRelIds = ""

        # Parameter
        iLemmaId1 = mapParam["LemmaId1"]
        iLemmaId2 = mapParam["LemmaId2"]
        iPosID = mapParam["PosId"]
        if "OrderBy" in mapParam:
            strOrderBy = mapParam["OrderBy"]
        if "MinFreq" in mapParam:
            iMinFreq = mapParam["MinFreq"]
        if "MinStat" in mapParam:
            iMinStat = mapParam["MinStat"]
        if "Subcorpus" in mapParam:
            strSubcorpus = mapParam["Subcorpus"]
        if isinstance(strSubcorpus, type("")):
            strSubcorpus.encode("utf8")

        # Schwellwerte
        strMinFreq = ""
        if iMinFreq > 0:
            strMinFreq = " and (-frequency)>=" + str(iMinFreq) + " "
        strMinStat = ""
        if iMinStat > -100000000:
            strMinStat = " and (-" + strOrderBy + ")>=" + str(iMinStat) + " "

        # MySQL-In-Liste aus den Relation-Ids bauen
        strRelIds = self.CWpMySQL.list_2_in(listRelationId)

        # rel,prep,lemma1,lemma2,surfacePrep,surface1,surface2,POS2,frequency,freqBelege,score,info
        strSelect = "SELECT function, prep, lemma1, lemma2, surfacePrep, surface1, surface2, POS2, -frequency, -freqBelege, -" + strOrderBy + ", info  FROM " + strSubcorpus + "relations  USE INDEX(I_" + strOrderBy + ") WHERE lemma1 IN (\"" + str(
            iLemmaId1) + "\",\"" + str(iLemmaId2) + "\") and POS1=\"" + str(
            iPosID) + "\" and function IN " + strRelIds + " " + strMinFreq + " " + strMinStat + ";"
        # strOrder = "ORDER BY "+strOrderBy+";"

        # MySQL-Abfrage
        self.CWpMySQL.connect()
        self.CWpMySQL.execute("SET NAMES 'utf8';")
        self.CWpMySQL.execute(strSelect)  # + strOrder
        listResult = self.CWpMySQL.fetchall()
        self.CWpMySQL.disconnect()

        return listResult

    @deprecated
    def __calculate_diff(self, iRel, listData, listRelData, mapParam):
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
        iNumber = 10
        if "Number" in mapParam:
            iNumber = mapParam["Number"]

        strOperation = "adiff"
        if "Operation" in mapParam:
            strOperation = mapParam["Operation"]

        # Ob die Schnittbildung berechnet werden soll (bei rmax)
        bIntersect = False
        if "Intersection" in mapParam:
            bIntersect = bool(mapParam["Intersection"])
        else:
            if strOperation == "rmax":
                bIntersect = True
            else:
                bIntersect = False

        # Frühzeitiges abschneiden der Kandidaten für die Berechnung
        iNBest = None
        if "NBest" in mapParam:
            iNBest = mapParam["NBest"]

        iLem1 = mapParam["LemmaId1"]
        iLem2 = mapParam["LemmaId2"]

        # (0)rel,(1)prep,(2)lemma1,(3)lemma2,(4)surfacePrep,(5)surface1,(6)surface2,(7)POS2,(8)frequency,(9)freqBelege,(10)score,(11)info
        xRel = 0
        xPrep = 1
        xLemma1 = 2
        xLemma2 = 3
        xSurfacePrep = 4
        xSurface1 = 5
        xSurface2 = 6
        xPOS = 7
        xFrequency = 8
        xFreqBelege = 9
        xScore = 10
        xInfo = 11

        yRef1 = 0
        yRef2 = 1
        yRank1 = 2
        yRank2 = 3
        yScore = 4

        mapData = {}

        mapCenter = {}
        mapRank = {}

        # Prüfen, ob die Kookkurrenzpartner für beide Lemmata vorhanden sind
        iCountRank2 = 1
        for k in listRelData:
            i = listData[k]
            if i[xLemma1] == iLem2:
                if iCountRank2 <= iNBest or iNBest == None:
                    mapData[(i[xPrep], i[xLemma2])] = (k, i)
                    mapRank[k] = iCountRank2
                iCountRank2 += 1

        iCountRank1 = 1
        for k in listRelData:
            i = listData[k]
            if i[xLemma1] == iLem1:
                if iCountRank1 <= iNBest or iNBest == None:
                    if (i[xPrep], i[xLemma2]) in mapData:
                        (iPos, myTuple) = mapData[(i[xPrep], i[xLemma2])]
                        iRef1 = k
                        iRef2 = iPos
                        mapCenter[iRef1] = iRef2
                        mapCenter[iRef2] = -1
                    mapRank[k] = iCountRank1
                iCountRank1 += 1

        if bIntersect:
            # wenn der Schnitt berechnet werden soll
            listRes = []
            for i in mapCenter:
                iRef = mapCenter[i]
                if iRef != -1:
                    iRef1 = i
                    iRef2 = iRef
                    iRank1 = mapRank[iRef1]
                    iRank2 = mapRank[iRef2]

                    iScore = self.__diff_operation(strOperation, listData[iRef1][xScore], listData[iRef2][xScore],
                                                   iRank1, iRank2)
                    listRes.append((iRef1, iRef2, iRank1, iRank2, iScore))
        else:
            listRes = []
            for k in listRelData:
                i = listData[k]
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

                        iScore = self.__diff_operation(strOperation, i[xScore], listData[iRef2][xScore], iRank1, iRank2)

                        listRes.append((iRef1, iRef2, iRank1, iRank2, iScore))

                elif k in mapRank:
                    # für nur Lemma1
                    if i[xLemma1] == iLem1:
                        iRef1 = k
                        iRef2 = -1
                        iRank1 = mapRank[iRef1]
                        iRank2 = -1

                        iScore = self.__diff_operation(strOperation, i[xScore], 0, iRank1, 0)

                    # für nur Lemma2
                    else:
                        iRef1 = -1
                        iRef2 = k
                        iRank1 = -1
                        iRank2 = mapRank[iRef2]

                        iScore = self.__diff_operation(strOperation, 0, listData[iRef2][xScore], 0, iRank2)

                    listRes.append((iRef1, iRef2, iRank1, iRank2, iScore))

        # Abschließendes Sortieren und Abschneiden
        lcmp = lambda idx: lambda i, j: (i[idx] > j[idx]) and -1 or (i[idx] < j[idx]) and 1 or 0
        abs_lcmp = lambda idx: lambda i, j: (math.fabs(i[idx]) > math.fabs(j[idx])) and -1 or (
                math.fabs(i[idx]) < math.fabs(j[idx])) and 1 or 0
        rcmp = lambda idx: lambda i, j: (i[idx] < j[idx]) and -1 or (i[idx] > j[idx]) and 1 or 0
        abs_rcmp = lambda idx: lambda i, j: (math.fabs(i[idx]) < math.fabs(j[idx])) and -1 or (
                math.fabs(i[idx]) > math.fabs(j[idx])) and 1 or 0

        if strOperation == "rmax":
            my_cmp = rcmp
        else:
            my_cmp = lcmp
        if strOperation == "adiff":
            listRes.sort(cmp=abs_lcmp(yScore))
            listRes = listRes[0:iNumber]
            listRes.sort(cmp=lcmp(yScore))
        elif strOperation == "ardiff":
            listRes.sort(cmp=abs_lcmp(yScore))
            listRes = listRes[0:iNumber]
            listRes.sort(cmp=lcmp(yScore))
        else:
            listRes.sort(cmp=my_cmp(yScore))
            listRes = listRes[0:iNumber]

        return listRes

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
    def __diff_relation_tuples_2_strings(self, listData, listRes, mapParam):
        """
        Methode, um IDs in den Diff-Kookkurenzlisten auf Strings abzubilden
        """
        bExtendedSurfaceForm = False
        if "ExtendedSurfaceForm" in mapParam:
            bExtendedSurfaceForm = bool(mapParam["ExtendedSurfaceForm"])

        # (0)rel,(1)prep,(2)lemma1,(3)lemma2,(4)surfacePrep,(5)surface1,(6)surface2,(7)POS2,(8)frequency,(9)freqBelege,(10)score,(11)info
        xRel = 0
        xPrep = 1
        xLemma1 = 2
        xLemma2 = 3
        xSurfacePrep = 4
        xSurface1 = 5
        xSurface2 = 6
        xPOS = 7
        xFrequency = 8
        xFreqBelege = 9
        xScore = 10
        xInfo = 11

        yRef1 = 0
        yRef2 = 1
        yRank1 = 2
        yRank2 = 3
        yScore = 4

        listMapRes = []

        for i in listRes:
            localMap = {}
            mapScore = {}
            mapScore['AScomp'] = i[yScore]
            mapScore['Rank1'] = i[yRank1]
            mapScore['Rank2'] = i[yRank2]
            if i[yRef1] != -1:
                # Es gibt Kookkurenzen zum ersten Wort

                mapScore['Frequency1'] = listData[i[yRef1]][xFrequency]
                mapScore['Assoziation1'] = listData[i[yRef1]][xScore]
                localMap['ConcordId1'] = listData[i[yRef1]][xInfo]

                iConcordNo1 = listData[i[yRef1]][xFrequency]
                iFreqBelege1 = listData[i[yRef1]][xFreqBelege]
                if self.CWpMySQL.mapRelIdToType[listData[i[yRef1]][xRel]] == 2 and listData[i[yRef1]][xLemma1] == \
                        listData[i[yRef1]][xLemma2]:
                    iConcordNo1 = iConcordNo1 / 2
                    iFreqBelege1 = iFreqBelege1 / 2
                localMap['ConcordNo1'] = iConcordNo1
                localMap['ConcordNoAccessible1'] = iFreqBelege1

                localMap['Relation'] = self.CWpMySQL.mapIdToRel[listData[i[yRef1]][xRel]]

                # Ids auf Strings mappen
                strLemma = self.CWpMySQL.mmapIdToLem.get(listData[i[yRef1]][xLemma2])
                strSurface = self.CWpMySQL.mmapIdToSurf.get(listData[i[yRef1]][xSurface2])
                strPrep = self.CWpMySQL.mmapIdToLem.get(listData[i[yRef1]][xPrep])
                strPrepSurface = strPrep

                # Oberflächenform formatieren (z.B. bei erweiterten Oberflächenformen mit Kontext)
                strSurface = surface_mapping(strSurface, self.CWpMySQL.mapRelIdToType[listData[i[yRef1]][xRel]],
                                             strPrepSurface, bExtendedSurfaceForm)

                # evt. Lemma Reparieren
                strLemmaRepair = self.CWpSpec.mapLemmaRepair.get((localMap['POS'], strLemma), None)
                if strLemmaRepair != None:
                    strLemma = strLemmaRepair.encode('utf8')

                # Lemma+Präposition formatieren
                if self.CWpMySQL.mapRelIdToType[listData[i[yRef1]][xRel]] == 1 and strPrep != "-":
                    strLemma = strLemma + ' ' + strPrep
                elif self.CWpMySQL.mapRelIdToType[listData[i[yRef1]][xRel]] != 1 and strPrep != "-":
                    strLemma = strPrep + ' ' + strLemma

                localMap['Lemma'] = strLemma
                localMap['Form'] = strSurface
                localMap['POS'] = self.CWpMySQL.mapIdToPOS[listData[i[yRef1]][xPOS]]

                if i[yRef2] == -1:
                    localMap['Position'] = 'left'
                else:
                    localMap['Position'] = 'center'
            else:
                mapScore['Frequency1'] = 0
                mapScore['Assoziation1'] = 0.0
                localMap['ConcordId1'] = 0
                localMap['ConcordNo1'] = 0
                localMap['ConcordNoAccessible1'] = 0

            if i[yRef2] != -1:
                # Es gibt Kookkurenzen zum zweiten Wort

                mapScore['Frequency2'] = listData[i[yRef2]][xFrequency]
                mapScore['Assoziation2'] = listData[i[yRef2]][xScore]
                localMap['ConcordId2'] = listData[i[yRef2]][xInfo]

                iConcordNo2 = listData[i[yRef2]][xFrequency]
                iFreqBelege2 = listData[i[yRef2]][xFreqBelege]
                if self.CWpMySQL.mapRelIdToType[listData[i[yRef2]][xRel]] == 2 and listData[i[yRef2]][xLemma1] == \
                        listData[i[yRef2]][xLemma2]:
                    iConcordNo2 = iConcordNo2 / 2
                    iFreqBelege2 = iFreqBelege2 / 2
                localMap['ConcordNo2'] = iConcordNo2
                localMap['ConcordNoAccessible2'] = iFreqBelege2

                if i[yRef1] == -1:

                    localMap['Relation'] = self.CWpMySQL.mapIdToRel[listData[i[yRef2]][xRel]]

                    # Ids auf Strings mappen
                    strLemma = self.CWpMySQL.mmapIdToLem.get(listData[i[yRef2]][xLemma2])
                    strSurface = self.CWpMySQL.mmapIdToSurf.get(listData[i[yRef2]][xSurface2])
                    strPrep = self.CWpMySQL.mmapIdToLem.get(listData[i[yRef2]][xPrep])
                    strPrepSurface = strPrep

                    # Oberflächenform formatieren (z.B. bei erweiterten Oberflächenformen mit Kontext)
                    strSurface = surface_mapping(strSurface, self.CWpMySQL.mapRelIdToType[listData[i[yRef2]][xRel]],
                                                 strPrepSurface, bExtendedSurfaceForm)

                    # Lemma+Präposition formatieren
                    if self.CWpMySQL.mapRelIdToType[listData[i[yRef2]][xRel]] == 1 and strPrep != "-":
                        strLemma = strLemma + ' ' + strPrep
                    elif self.CWpMySQL.mapRelIdToType[listData[i[yRef2]][xRel]] != 1 and strPrep != "-":
                        strLemma = strPrep + ' ' + strLemma

                    localMap['Lemma'] = strLemma
                    localMap['Form'] = strSurface
                    localMap['POS'] = self.CWpMySQL.mapIdToPOS[listData[i[yRef2]][xPOS]]
                    localMap['Position'] = 'right'
            else:
                mapScore['Frequency2'] = 0
                mapScore['Assoziation2'] = 0.0
                localMap['ConcordId2'] = 0
                localMap['ConcordNo2'] = 0
                localMap['ConcordNoAccessible2'] = 0

            localMap['Score'] = mapScore

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
        info_id = params.get("InfoId")
        coocc_info = self.__extract_coocc_info(info_id)[-1]

        # Ids auf Strings mappen
        lemma1 = self.CWpMySQL.mmapIdToLem.get(coocc_info.iLemma1Id)
        pos1 = self.CWpMySQL.mapIdToPOS.get(coocc_info.iPos1Id)
        lemma2 = self.CWpMySQL.mmapIdToLem.get(coocc_info.iLemma2Id)
        pos2 = self.CWpMySQL.mapIdToPOS.get(coocc_info.iPos2Id)
        relation = self.CWpMySQL.mapIdToRel.get(coocc_info.iRelId)
        prep = self.CWpMySQL.mmapIdToLem.get(coocc_info.iPrepId)

        # Meta-Daten generieren
        if relation in self.CWpSpec.mapRelDescDetail:
            description = self.CWpSpec.mapRelDescDetail[relation]
            description = description.replace('$1', lemma1)
            description = description.replace('$2', lemma2)
            description = description.replace('$3', prep)
        else:
            description = ""

        return {'Description': description, 'Relation': relation, 'Lemma1': lemma1, 'Lemma2': lemma2, 'POS1': pos1,
                'POS2': pos2}

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
        info_id = params.get("InfoId")
        use_context = bool(params.get("UseContext", False))
        subcorpus_id = self.CWpMySQL.mapCorpusToId.get(params["Subcorpus"], -1)
        is_internal_user = bool(params.get("InternalUser", False))
        start_index = params.get("Start", 0)
        result_number = params.get("Number", 20)
        coocc_infos = self.__extract_coocc_info(info_id)

        if len(coocc_infos) > 1:
            raise NotImplementedError('__get_concordances_mwe_base')
            return self.__get_concordances_mwe_base(params)
        else:
            return self.__get_concordances_base(coocc_infos[0].iInfoId, use_context, subcorpus_id, is_internal_user,
                                                start_index, result_number)

    def __get_concordances_base(self, info_id, use_context, subcorpus_id, is_internal_user, start_index, result_number):
        internal_user_cond = " and idToInfo.avail=1 " if not is_internal_user else ""
        subcorpus_cond = " and idToInfo.corpus='{}' ".format(subcorpus_id) if subcorpus_id >= 0 else ""

        if use_context:
            query = """
            SELECT
                s_center.Sentence, idToInfo.tokenPosition1, idToInfo.tokenPosition2, idToInfo.prepPosition, 
                idToInfo.corpus, idToInfo.Date, idToTei.Textclass, idToTei.Orig, idToTei.Scan, idToTei.Avail, 
                s_center.Page, idToTei.file, idToInfo.Score, s_left.Sentence, s_right.Sentence 
            FROM
                idToInfo
            LEFT JOIN concordSentences as s_center ON
                (s_center.corpus = idToInfo.corpus
                and s_center.FileId = idToInfo.File
                and s_center.SentenceId = idToInfo.sentence)
            LEFT JOIN idToTei ON
                (idToInfo.corpus = idToTei.corpus
                and idToInfo.file = idToTei.file)
            LEFT JOIN concordSentences as s_left ON
                (s_left.corpus = idToInfo.corpus
                and s_left.FileId = idToInfo.File
                and s_left.SentenceId =(idToInfo.sentence-1))
            LEFT JOIN concordSentences as s_right ON
                (s_right.corpus = idToInfo.corpus
                and s_right.FileId = idToInfo.File
                and s_right.SentenceId =(idToInfo.sentence + 1))
            WHERE idToInfo.id={} {} {}
            LIMIT {},{}
            """.format(info_id, subcorpus_cond, internal_user_cond, start_index, result_number)
        else:
            query = """
            SELECT
                s_center.Sentence, idToInfo.tokenPosition1, idToInfo.tokenPosition2, idToInfo.prepPosition, 
                idToInfo.corpus, idToInfo.Date, idToTei.Textclass, idToTei.Orig, idToTei.Scan, idToTei.Avail, 
                s_center.Page, idToTei.file, idToInfo.Score
            FROM
                idToInfo
            LEFT JOIN concordSentences as s_center ON
                (s_center.corpus = idToInfo.corpus
                and s_center.FileId = idToInfo.File
                and s_center.SentenceId = idToInfo.sentence)
            LEFT JOIN idToTei ON (idToInfo.corpus=idToTei.corpus and idToInfo.file=idToTei.file)
            WHERE idToInfo.id={} {} {}
            LIMIT {},{}
            """.format(info_id, subcorpus_cond, internal_user_cond, start_index, result_number)

        self.CWpMySQL.connect()
        self.CWpMySQL.execute(query)
        db_results = self.CWpMySQL.fetchall()
        self.CWpMySQL.disconnect()

        results = []
        for item in db_results:
            if use_context:
                (sentence, token_position_1, token_position_2, prep_position, corpus, date, textclass, orig, scan,
                 avail,
                 page, file, score, sentence_left, sentence_right) = item
                sentence_left = format_sentence(sentence_left)
                sentence_right = format_sentence(sentence_right)
            else:
                (sentence, token_position_1, token_position_2, prep_position, corpus, date, textclass, orig, scan,
                 avail, page, file, score) = item
                sentence_left = sentence_right = ""
            if not sentence:
                print("skip line: None in table!")
                continue

            bib_entry = {
                "Corpus": self.CWpMySQL.mapIdToCorpus[corpus],
                "Date": self.CWpMySQL.mapIdToDate[date],
                "TextClass": self.CWpMySQL.mapIdToTextclass[textclass],
                "Orig": orig.replace('#page#', page),
                "Scan": scan.replace('#page#', page),
                "Avail": self.CWpMySQL.mapIdToAvail[avail],
                "Page": page,
                "File": file,
            }
            sentence_main = format_sentence_center(sentence, token_position_1, token_position_2,
                                                   prep_position)
            results.append({
                "Bibl": bib_entry,
                "ConcordLine": sentence_main,
                "ConcordLeft": sentence_left,
                "ConcordRight": sentence_right,
                "Score": score
            })
        return results

    @deprecated
    def __mwe_position_mysql_in(self, iObj, iMax):
        strRes = ""
        strResLocal = ""
        for i in range(1, iMax):
            if i != iObj:
                if strResLocal != "":
                    strResLocal += ","
                strResLocal += "infoDouble" + str(i) + ".tokenPosition1,infoDouble" + str(i) + ".tokenPosition2"

        strRes = "(infoDouble" + str(iObj) + ".tokenPosition1 IN (" + strResLocal + ") or\ninfoDouble" + str(
            iObj) + ".tokenPosition2 IN (" + strResLocal + "))\n"

        return strRes

    @deprecated
    def __get_concordances_mwe_base(self, mapParam):
        iInfoId = 0
        iStart = 0
        iNumber = 20
        strSubcorpus = ""

        bDateDesc = 1
        bUseScore = 0
        bUseContext = 0

        # Parameter
        if ("UseContext" in mapParam):
            bUseContext = mapParam["UseContext"]
        if ("UseScore" in mapParam):
            bUseScore = mapParam["UseScore"]
        if ("DateDesc" in mapParam):
            bDateDesc = mapParam["DateDesc"]
        if ("Start" in mapParam):
            iStart = mapParam["Start"]
        if ("Number" in mapParam):
            iNumber = mapParam["Number"]
        if ("Subcorpus" in mapParam):
            strSubcorpus = mapParam["Subcorpus"]
        strSubcorpus = strSubcorpus
        bInverse = 0
        if 'Inverse' in mapParam:
            bInverse = mapParam['Inverse']

        # Relevante Informationen aus der Treffer-Id extrahieren
        strInfoId = mapParam["InfoId"]
        listInfoId = self.__extract_coocc_info(strInfoId)

        # --SELECT--------------------------------------------------
        strInfoSelect = ""
        for i in range(1, len(listInfoId) + 1):
            strInfoSelect += "infoDouble%i.tokenPosition1,infoDouble%i.tokenPosition2,infoDouble%i.prepPosition,\n" % (
                i, i, i)

        # --WHERE--------------------------------------------------
        strInfoWhere = ""
        for i in range(1, len(listInfoId) + 1):
            if strInfoWhere != "":
                strInfoWhere += " and "
            strInfoWhere += " infoDouble%i.id=\"%s\" " % (i, listInfoId[i - 1].iInfoId)

        # --JOIN--------------------------------------------------
        strInfoJoin = ""
        for i in range(2, len(listInfoId) + 1):
            strInfoJoin += """  INNER JOIN idToInfo as infoDouble""" + str(i) + """ ON (
                             infoDouble1.corpus=infoDouble""" + str(i) + """.corpus and
                             infoDouble1.file=infoDouble""" + str(i) + """.file and
                             infoDouble1.sentence=infoDouble""" + str(i) + """.sentence"""
            # bei letzten Join überprüfung der Positionen im Satz
            if i == len(listInfoId):
                strAdd = ""
                # bei einer dreistelligen MWE-Relation müssen nicht alle Positionen geprüft werden
                if len(listInfoId) == 2:
                    strAdd += self.__mwe_position_mysql_in(1, 3)
                # ansonsten muessen alle Positionen geprüft werden
                else:
                    for j in range(1, len(listInfoId) + 1):
                        if strAdd != "":
                            strAdd += " and "
                        strAdd += self.__mwe_position_mysql_in(j, len(listInfoId) + 1)
                strInfoJoin += " and \n (" + strAdd + ") )\n"
            else:
                strInfoJoin += ")\n"

        # --Position-Select--------------------------------------------------
        strPositionSelect = ""
        for i in range(1, len(listInfoId) + 1):
            strPositionSelect += ", infoDouble.tokenPosition1_%i, infoDouble.tokenPosition2_%i, infoDouble.prepPosition_%i" % (
                i, i, i)

        # Wenn innerhalb eines Subkorpus gesucht werden soll
        if strSubcorpus != "":
            strSubcorpus = " and idToInfo.corpus=\"" + str(self.CWpMySQL.mapCorpusToId[strSubcorpus]) + "\" "

        # Sortierung
        strIndex = ""
        if bDateDesc == 1 and bUseScore == 1:
            strIndex = "I_score_date_desc"
        elif bDateDesc == 1 and bUseScore == 0:
            strIndex = "I_date_desc"
        elif bDateDesc == 0 and bUseScore == 1:
            strIndex = "I_score_date"
        else:
            strIndex = "I_date"

        # Wenn Kontextsätze angezeigt werden sollen
        strJoinContext = ""
        strSelectContext = ""
        if bUseContext == 1:
            strSelectContext = ", s_left.Sentence, s_right.Sentence "
            strJoinContext = """LEFT JOIN concordSentences as s_left ON (s_left.corpus=infoDouble.corpus and s_left.FileId=infoDouble.File and s_left.SentenceId=(infoDouble.sentence-1))
                          LEFT JOIN concordSentences as s_right ON (s_right.corpus=infoDouble.corpus and s_right.FileId=infoDouble.File and s_right.SentenceId=(infoDouble.sentence+1))"""

        # Grundlegendes Ermitteln der Texttreffer
        strCreate = "CREATE TEMPORARY TABLE infoDouble LIKE idToInfoConditionalOhneIndex_%i; " % (len(listInfoId) - 1)
        strIn1 = "INSERT INTO infoDouble "
        strSelect1 = """SELECT infoDouble1.id,
                           """ + strInfoSelect + """
                           infoDouble1.sentence,
                           infoDouble1.file,
                           infoDouble1.corpus,
                           infoDouble1.Date,
                           infoDouble1.DateDesc,
                           infoDouble1.Score
                           """
        strFrom1 = """FROM idToInfo as infoDouble1 FORCE INDEX(""" + strIndex + """)
                                               """ + strInfoJoin + """
                                    where (""" + strInfoWhere + """ ) LIMIT """ + str(iStart) + ',' + str(
            iNumber) + """ ;"""

        # IDs innerhalb der Texttrefferinformation auf Strings abbilden
        strSelect2 = "SELECT s_center.Sentence, infoDouble.corpus, infoDouble.Date, idToTei.Textclass, idToTei.Orig, idToTei.Scan, idToTei.Avail, s_center.Page, idToFile.File, infoDouble.Score " + strSelectContext + " " + strPositionSelect + " "
        strFrom2 = """FROM infoDouble LEFT JOIN idToFile ON (idToFile.id=infoDouble.File)
                        LEFT JOIN concordSentences as s_center ON (s_center.corpus=infoDouble.corpus and s_center.FileId=infoDouble.File and s_center.SentenceId=infoDouble.sentence)
                        """ + strJoinContext + """
                        LEFT JOIN idToTei ON (infoDouble.corpus=idToTei.corpus and infoDouble.File=idToTei.file) """

        # MySQL-Abfrage
        self.CWpMySQL.connect()
        self.CWpMySQL.execute("SET NAMES 'utf8';")
        self.CWpMySQL.execute(strCreate)
        self.CWpMySQL.execute(strIn1 + strSelect1 + strFrom1)
        self.CWpMySQL.execute(strSelect2 + strFrom2)
        listRes = self.CWpMySQL.fetchall()
        self.CWpMySQL.disconnect()

        # Ausgabe formatieren
        listMapRes = []
        for i in listRes:
            if i[0] == None:
                print("): skip line: None in table!")
                continue

            mapBib = {}
            mapBib["Corpus"] = self.CWpMySQL.mapIdToCorpus[i[1]]
            mapBib["Date"] = self.CWpMySQL.mapIdToDate[i[2]]
            mapBib["TextClass"] = self.CWpMySQL.mapIdToTextclass[i[3]]
            mapBib["Orig"] = i[4]
            mapBib["Scan"] = i[5]
            mapBib["Avail"] = self.CWpMySQL.mapIdToAvail[i[6]]
            mapBib["Page"] = i[7]
            mapBib["File"] = i[8]
            strScore = i[9]

            # Bibl-Strings mit Seitenzahlen anreichern
            mapBib["Orig"] = mapBib["Orig"].replace('#page#', mapBib["Page"])
            mapBib["Scan"] = mapBib["Scan"].replace('#page#', mapBib["Page"])

            # Satzkontext Formatieren
            if bUseContext == 1:
                strLeft = format_sentence(i[10])
                strRight = format_sentence(i[11])
            else:
                strLeft = ""
                strRight = ""

            # Tokenpositionen ermitteln
            listPosition = []
            iAbstand = 0
            for j in range(0, len(listInfoId)):
                if strJoinContext == "":
                    listPosition.append(i[10 + iAbstand])
                    listPosition.append(i[11 + iAbstand])
                    listPosition.append(i[12 + iAbstand])
                else:
                    listPosition.append(i[12 + iAbstand])
                    listPosition.append(i[13 + iAbstand])
                    listPosition.append(i[14 + iAbstand])

                iAbstand += 3

            # Satz Formatieren
            strCenter = format_sentence_center_mwe(i[0], listPosition)

            # dem Ergebnis hinzufügen
            listMapRes.append(
                {"Bibl": mapBib, "ConcordLine": strCenter, "ConcordLeft": strLeft, "ConcordRight": strRight,
                 "Score": strScore})

        return listMapRes


class RequestHandler(xmlrpc.server.SimpleXMLRPCRequestHandler):
    # Restrict to a particular path.
    rpc_paths = ('/RPC2',)

    def do_POST(self):
        client_ip, port = self.client_address
        # Log client IP and Port
        logger.info('Client IP: %s - Port: %s' % (client_ip, port))
        try:
            # get arguments
            data = self.rfile.read(int(self.headers["content-length"]))
            # Log client request
            logger.info('Client request: \n%s\n' % data)

            response = self.server._marshaled_dispatch(
                data, getattr(self, '_dispatch', None)
            )
        except:  # This should only happen if the module is buggy
            # internal error, report as HTTP server error
            self.send_response(500)
            self.end_headers()
        else:
            # got a valid XML RPC response
            self.send_response(200)
            self.send_header("Content-type", "text/xml")
            self.send_header("Content-length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

            # shut down the connection
            self.wfile.flush()
            self.connection.shutdown(1)


def main():
    global logger
    parser = ArgumentParser()
    parser.add_argument('-s', dest='spec', type=str, required=True, help="Angabe der Settings-Datei (*.xml)")
    parser.add_argument('-p', dest='port', type=str, required=True, help="Angabe des Ports")
    parser.add_argument('--log', dest='logfile', type=str,
                        default="./log/wp_" + time.strftime("%d_%m_%Y") + ".log",
                        help="Angabe der log-Datei (Default: log/wp_{date}.log)")
    args = parser.parse_args()

    # Schreiben der Logging-Informationen
    logger = logging.getLogger('wortprofilserver')
    hdlr = logging.FileHandler(args.logfile)
    formatter = logging.Formatter("%(asctime)s  %(levelname)s  %(message)s")
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)

    CWpSpec = WpSeSpec()
    CWpSpec.read_specification(args.spec)
    # Create server
    server = xmlrpc.server.SimpleXMLRPCServer(("localhost", int(args.port)),
                                              requestHandler=RequestHandler, logRequests=False, allow_none=True)
    # register function information
    server.register_introspection_functions()
    # register wortprofil
    server.register_instance(WortprofilQuery(CWpSpec))
    # Run the server's main loop
    server.serve_forever()


if __name__ == '__main__':
    main()
