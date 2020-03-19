#!/usr/bin/python

import logging

from wordprofile.wp import Wordprofile

logger = logging.getLogger('wordprofile')


class WordprofileXMLRPC:
    def __init__(self, db_host, db_user, db_passwd, db_name, db_port, wp_spec_file):
        self.wp = Wordprofile(db_host, db_user, db_passwd, db_name, db_port, wp_spec_file)

    def status(self):
        """
        Status-Function für "icinga". Es wird geprüft, ob der Server einwandfrei funktioniert.
        Hierzu werden Testweise Kookkurrenzen zu einem Wort abgefragt.
        """
        raise self.wp.status()

    def get_info(self):
        raise self.wp.get_info()

    def get_lemma_and_pos(self, params):
        """
        Die Methode ermöglicht es, zu einem gegebenen Wort die Wortprofil-Lemma/POS-IDs zu ermitteln (evtl. mehrere Part-Of-Speech Lesarten ).
        """
        use_external_variations = bool(params.get('UseVariations', True))
        word = params.get("Word")
        pos = params.get("POS", "")
        return self.wp.get_lemma_and_pos(word, pos, use_external_variations)

    def get_lemma_and_pos_diff(self, params):
        """
        Die Methode ermöglicht es, zu einem gegebenen Wort die Wortprofil-Lemma/POS-IDs zu ermitteln (evtl. mehrere Part-Of-Speech Lesarten ).
        mapParam = {'Word1':<string>, 'Word2':<string>, 'Subcorpus':<string>, 'CaseSensitive':<bool=False>}
        hiervon sind obligatorisch: 'Word1' und 'Word2'
        *Eingabe ist die Lemma/Oberflächen-Form des ersten Wortes in UTF-8 ('Word1') und des zweiten Vergleichswortes in UTF-8 ('Word2') (z.B. Laufen, Baum, Haus, schön, ...) zusammen mit der optionalen Angabe eines Subkorpus ( 'Subcorpus') (z.B. zeit, kern, 21jhd, ...). Zudem ist parametrisiert, ob caseinsensitiv abgefragt werden soll ( 'CaseSensitive'). Diese Parameter werden über einen Dictionary übergeben
        *Rückgabe ist eine Liste aus: erster Lemmaform ('Lemma1'), zweiter Lemmaform ('Lemma2'), erster Lemma-ID ('LemmaId1'), zweiter Lemma-ID ('LemmaId2'), part-of-speech ('POS'), POS-ID ('PosId'), Anzahl der Relationen mit Doppelten für das erste Wort ('Frequency1') und für das zweite Wort ('Frequency2'), Anzahl Relationen ohne Doppelte für das erte Wort ('Count1') und für das zweite Wort ('Count2') und Liste aller möglichen Relationen für beide Wörter ('Relations'), die nach Relevanz geordnet sind. Die Listeneinträge sind als dictionary abgelegt:
        [ {'Lemma1':<string>,'Lemma2':<string>,'POS':<string>,'LemmaId1':<int>,'LemmaId2':<int>,'PosId':<int>,'Frequency1':<int>,'Frequency2':<int>,'Count1':<int>,'Count2':<int>,'Relations:<Liste aus Strings>} , ... ]
        """
        use_external_variations = bool(params.get('UseVariations', True))
        word_1 = params.get("Word1")
        word_2 = params.get("Word2")
        return self.wp.get_lemma_and_pos_diff(word_1, word_2, use_external_variations)

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
        return self.wp.get_relations(lemma, lemma2, pos, pos2, relations, start, number, order_by, min_freq, min_stat)

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
        return self.wp.get_cooccurrences(hit_id, start, number, order_by, min_freq, min_stat)

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
        return self.wp.get_diff(lemma1, lemma2, pos, cooccs, number, order_by, min_freq, min_stat, operation,
                                use_intersection, nbest)

    def get_intersection(self, mapParam):
        """
        Indirekter aufruf von get_diff mit der Operation 'rmax'
        """
        mapParam['Operation'] = 'rmax'
        mapParam['Intersection'] = True
        return self.get_diff(mapParam)

    def get_relation_by_info_id(self, params):
        """
        Die Funktion ermöglicht es, anhand einer Concordanz-ID ('InfoId') eine Relation abzufragen.
        mapParam = {'InfoId':<int>}
        hiervon sind obligatorisch: 'InfoId'
        *Rückgabe ist ein Dictionary aus: syntaktischer Relation ('Relation'), Lemmaform von W1 ('Lemma1'), Lemmaform von W2 ('Lemma2'), POS-Tag von W1 ('POS1'), POS-Tag von W2 ('POS2'), Oberflächenform von W1 ('Form1'), Oberflächenform von W2 ('Form2'):
        {'Relation':<string>,'Lemma1':<string>,'Lemma2':<string>,'POS1':<string>,'POS2':<string>,'Form1':<string>,'Form2':<string>}
        """
        coocc_id = int(params.get("InfoId"))
        return self.wp.get_relation_by_info_id(coocc_id)

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
        return self.wp.get_concordances(coocc_id, use_context, start_index, result_number)
