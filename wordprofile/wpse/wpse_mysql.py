#!/usr/bin/python
import logging
from collections import defaultdict, namedtuple

import MySQLdb

from wordprofile.wpse import deprecated
from wordprofile.wpse.wpse_spec import WpSeSpec
from wordprofile.wpse.wpse_string import format_sentence, format_sentence_center, format_sentence_center_mwe

logger = logging.getLogger('wordprofile.mysql')


class WpSeMySql:
    def __init__(self, wp_spec: WpSeSpec):
        self.host = wp_spec.host
        self.user = wp_spec.user
        self.passwd = wp_spec.passwd
        self.dbname = wp_spec.dbname
        self.port = wp_spec.port

        self.mwe_depth = 0

        self.__conn = MySQLdb.connect(
            host=self.host,
            user=self.user,
            passwd=self.passwd,
            port=self.port,
            db=self.dbname)
        self.__cursor = self.__conn.cursor()
        self.execute("SET NAMES 'latin1';")

    def execute(self, query):
        self.__cursor.execute(query)

    def fetchall(self, query):
        self.__cursor.execute(query)
        return self.__cursor.fetchall()

    @deprecated
    def list_2_in(self, relation_ids):
        """
         Liste von Relation-Ids in das Arbument eines In-Statements umwandeln
        """
        return "( {} )".format(",".join(map(str, relation_ids)))

    def get_concordances(self, match_id, use_context, subcorpus, is_internal_user, start_index, result_number):
        internal_user_cond = " and rk_matches.Rights=1 " if not is_internal_user else ""
        subcorpus_cond = " and rk_matches.Corpus='{}' ".format(subcorpus) if subcorpus else ""

        if use_context:
            query = """
            SELECT
                s_center.Sentence, rk_matches.Word1Position, rk_matches.Word2Position, rk_matches.PrepPosition, 
                rk_matches.Corpus, rk_matches.Date, rk_tei.TextClass, rk_tei.Orig, rk_tei.Scan, rk_tei.Avail, 
                s_center.Page, rk_tei.File, rk_matches.GdexScore, s_left.Sentence, s_right.Sentence 
            FROM
                rk_matches
            LEFT JOIN rk_concord_sentences as s_center ON
                (s_center.Corpus = rk_matches.Corpus
                and s_center.File = rk_matches.File
                and s_center.SentencePosition = rk_matches.SentenceId)
            LEFT JOIN rk_tei ON
                (rk_matches.Corpus = rk_tei.Corpus
                and rk_matches.File = rk_tei.File)
            LEFT JOIN rk_concord_sentences as s_left ON
                (s_left.Corpus = rk_matches.Corpus
                and s_left.File = rk_matches.File
                and s_left.SentencePosition =(rk_matches.SentenceId-1))
            LEFT JOIN rk_concord_sentences as s_right ON
                (s_right.Corpus = rk_matches.Corpus
                and s_right.File = rk_matches.File
                and s_right.SentencePosition =(rk_matches.SentenceId + 1))
            WHERE rk_matches.MatchId={} {} {}
            LIMIT {},{};
            """.format(match_id, subcorpus_cond, internal_user_cond, start_index, result_number)
        else:
            query = """
            SELECT
                s_center.Sentence, rk_matches.Word1Position, rk_matches.Word2Position, rk_matches.PrepPosition, 
                rk_matches.Corpus, rk_matches.Date, rk_tei.TextClass, rk_tei.Orig, rk_tei.Scan, rk_tei.Avail, 
                s_center.Page, rk_tei.File, rk_matches.GdexScore
            FROM
                rk_matches
            LEFT JOIN rk_concord_sentences as s_center ON
                (s_center.Corpus = rk_matches.Corpus
                and s_center.File = rk_matches.File
                and s_center.SentencePosition = rk_matches.SentenceId)
            LEFT JOIN rk_tei ON 
                (rk_matches.Corpus=rk_tei.Corpus 
                and rk_matches.File=rk_tei.File)
            WHERE rk_matches.MatchId={} {} {}
            LIMIT {},{};
            """.format(match_id, subcorpus_cond, internal_user_cond, start_index, result_number)

        db_results = self.fetchall(query)

        results = []
        for item in db_results:
            if use_context:
                (sentence, token_position_1, token_position_2, prep_position, corpus, date, textclass, orig, scan,
                 avail, page, file, score, sentence_left, sentence_right) = item
                sentence_left = format_sentence(sentence_left)
                sentence_right = format_sentence(sentence_right)
            else:
                (sentence, token_position_1, token_position_2, prep_position, corpus, date, textclass, orig, scan,
                 avail, page, file, score) = item
                sentence_left = sentence_right = ""
            if not sentence:
                logger.info("skip line: None in table!")
                continue
            bib_entry = {
                "Corpus": corpus,
                "Date": date.strftime("%d-%m-%Y"),
                "TextClass": textclass,
                "Orig": orig.replace('#page#', page),
                "Scan": scan.replace('#page#', page),
                "Avail": avail,
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

    def get_lemma_and_pos_base(self, word, pos, is_case_sensitive):
        """
        Basismethode zur Abfrage von Lemmainformationen
        """
        if not all(c.isalpha() or c == '-' for c in word):
            return []

        query = """
            SELECT Lemma, Pos, Frequency, Count, Relation
            FROM rk_head_pos_rel_freq
            WHERE LOWER(Lemma) LIKE '{}' {};
        """.format(
            word.lower(),
            " and POS='{}'".format(pos) if pos not in ["*", ""] else "")
        db_results = self.fetchall(query)

        return self.__get_valid_sorted_lemmas(db_results, word, is_case_sensitive)

    def __get_valid_sorted_lemmas(self, db_results, word, is_case_sensitive):
        """
        Bei einer gegebenen Liste von Lemmainformationen werden Einträge gelöscht und die Einträge werden Sortiert.
        Hierbei wird Bezug auf die Großschreibung und auf die Wortarten Bezug genommen. So sind Großgeschriebene Worte
        eher Substantiv als Verb.
        """
        lemma_pos_mapping = defaultdict(list)
        for lemma, pos, frequency, count, relation in db_results:
            lemma_pos_mapping[(lemma, pos)].append((relation, frequency, count))

        # Erstellen einer map, die zu einer Wortart, die frequenteste Lemmainformation besitzt
        most_frequent_lemma = {}
        for (lemma, pos), relations in lemma_pos_mapping.items():
            frequency = sum(frequency for _, frequency, _ in relations)
            count = sum(count for _, _, count in relations)
            if pos not in most_frequent_lemma or most_frequent_lemma[pos][1] < frequency:
                most_frequent_lemma[pos] = (lemma, frequency, count, relations)
        pos_sorted = sorted(most_frequent_lemma.items(), key=lambda x: x[1][1], reverse=True)

        results = []
        for pos, (lemma, frequency, count, relations) in pos_sorted:
            relations = [relation for (relation, frequency, count) in relations]

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
            results.append((score, {'Lemma': lemma, 'POS': pos,
                                    'Frequency': frequency, 'Count': count, 'Relations': relations}))
        results = [r[1] for r in sorted(results, key=lambda x: x[0])]
        return results

    def get_relation_tuples_mwe_check(self, lemma1, lemma2, pos1, pos2, start, number, order_by, min_freq,
                                      min_stat, relation):
        """
        Methode zum Abfragen der Kookkurrenztupeln zu einer liste von gegebenen Relation-IDs über die
        Wortprofil-MySQL-Datenbank
        """
        # Minimalfrequenz behandeln (MWE-Kookkurenzen einbezogen)
        str_min_freq = ""
        str_min_freq_mwe_check = ""
        if min_freq > 0:
            str_min_freq = " and (-rk_relations.Frequency) >= " + str(min_freq) + " "
            str_min_freq_mwe_check = " and (-ConditionalCheck_1.frequency) >= " + str(min_freq) + " "

        # Minimalstatistikwerte behandeln (MWE-Kookkurenzen einbezogen)
        str_min_stat = ""
        str_min_stat_mwe_check = ""
        if min_stat > -100000000:
            str_min_stat = " and (-rk_relations." + order_by + ") >= " + str(min_stat) + " "
            str_min_stat_mwe_check = " and (-ConditionalCheck_1.logDice) >= " + str(min_stat) + " "

        # wenn es allgemein MWE-Relationen gibt
        if self.mwe_depth > 0:
            select_from_sql = """
            SELECT  
                Relation, Prep, Lemma1, Lemma2, PrepSurface, Surface1, Surface2, Pos2, 
                -rk_relations.Frequency, -CountsWithRights, -MiLogFreq, -rk_relations.LogDice, -MI3, MatchId, 
                if(ConditionalCheck_1.id1!=CAST('None' as UNSIGNED) {} {} ,1,0) as MweId 
            FROM 
                rk_relations 
            LEFT JOIN ConditionalCheck_1 ON (relations.info=ConditionalCheck_1.id1) 
            """.format(
                str_min_freq_mwe_check, str_min_stat_mwe_check,
            )
        else:
            select_from_sql = """
            SELECT  
                Relation, Prep, Lemma1, Lemma2, PrepSurface, Surface1, Surface2, Pos2, 
                -rk_relations.Frequency, -CountsWithRights, -MiLogFreq, -rk_relations.LogDice, -MI3, MatchId, '0' 
            FROM 
                rk_relations
            """

        # evtl. auch das zweite Wort in der Kookkurrenz einschränken
        if pos2 == -1 or lemma2 == -1:
            where_sql = "WHERE Lemma1='{}' and Pos1='{}' and Relation = '{}' {} {} LIMIT {}, {};".format(
                lemma1, pos1, relation, str_min_freq, str_min_stat, start, number
            )
        else:
            where_sql = """WHERE Lemma1='{}' and Pos1='{}' and 
                                Lemma2='{}' and Pos2='{}' and 
                                Relation = '{}' {} {} ORDER BY Frequency;""".format(
                lemma1, pos1, lemma2, pos2, relation, str_min_freq, str_min_stat
            )

        db_results = self.fetchall(select_from_sql + where_sql)
        Coocc = namedtuple("Coocc", ["Rel", "Prep", "Lemma1", "Lemma2", "SurfacePrep", "Surface1", "Surface2", "POS",
                                     "Frequency", "FreqBelege", "Score_MiLogFreq", "Score_logDice", "Score_MI3", "Info",
                                     "ConditionalCheck"])
        return map(Coocc._make, db_results)

    @deprecated
    def get_relation_tuples_mwe_single(self, mapParam, setInfoId, mapLemCat):
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
        if self.mwe_depth > iMweStelligkeit:

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

        self.execute(strCreate1)
        # ausfüren der MySQL-Abfrage für die verschiedenen Lemmaformen und Wortarten der Vorhergehenden komplexen MWE-ID (An bestehende Lemma wird angehängt)
        for i in mapLemCat:
            listRelId = mapLemCat[i]
            for j in listRelId:
                strWhereDummy = strWhere1.replace("$LEMMA$", str(i[0])).replace("$POS$", str(i[1])).replace(
                    "$FUNCTION$", str(j))
                self.execute(strIn1 + strSelect1 + strFrom1 + strWhereDummy + strLimit1)

        listResult = self.fetchall(strSelect3 + strFrom3)
        return listResult

    @deprecated
    def get_relation_tuples_mwe(self, mapParam, listRelationId, setInfoId):
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
            strRelIds = " and idToConditional_" + str(iMweStelligkeit) + ".function IN" + self.list_2_in(
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
        if self.mwe_depth > iMweStelligkeit:

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
        self.execute(strCreate1)
        self.execute(strIn1 + strSelect1 + strFrom1 + strWhere1 + strOrder1)
        self.execute(strVar2)
        self.execute(strCreate2)
        self.execute(strIn2 + strSelect2 + strFrom2 + strWhere2)
        listResult = self.fetchall(strSelect3 + strFrom3 + strWhere3)
        return listResult

    def get_relation_tuples_diff(self, lemma1, lemma2, pos, relations,
                                 order_by, min_freq, min_stat):
        """
        Ermitteln der Kookkurrenzen zu einer Liste von syntaktischen Relationen für die 'diff'-Abfrage
        """
        query = """
        SELECT Relation, Prep, Lemma1, Lemma2, PrepSurface, Surface1, Surface2, Pos2, 
               -Frequency, -CountsWithRights, -{}, MatchId
        FROM rk_relations
        WHERE Lemma1 IN ("{}","{}") and Pos1="{}" and Relation IN ({}) {} {};
        """.format(
            order_by,
            lemma1, lemma2, pos,
            ",".join(['"{}"'.format(r) for r in relations]),
            " and (-Frequency) >= {}".format(min_freq) if min_freq > 0 else "",
            " and (-{}) >= {}".format(order_by, min_stat) if min_stat > -100000000 else ""
        )
        db_results = self.fetchall(query)
        Coocc = namedtuple("CooccDiff",
                           ["Rel", "Prep", "Lemma1", "Lemma2", "SurfacePrep", "Surface1", "Surface2", "Pos2",
                            "Frequency", "FreqBelege", "Score", "Info"])
        return list(map(Coocc._make, db_results))

    @deprecated
    def get_concordances_mwe_base(self, mapParam):
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
            strSubcorpus = " and idToInfo.corpus=\"" + str(self.mapCorpusToId[strSubcorpus]) + "\" "

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
        self.execute(strCreate)
        self.execute(strIn1 + strSelect1 + strFrom1)
        listRes = self.fetchall(strSelect2 + strFrom2)

        # Ausgabe formatieren
        listMapRes = []
        for i in listRes:
            if i[0] == None:
                logger.warning("skip line: None in table!")
                continue

            mapBib = {}
            mapBib["Corpus"] = self.mapIdToCorpus[i[1]]
            mapBib["Date"] = self.mapIdToDate[i[2]]
            mapBib["TextClass"] = self.mapIdToTextclass[i[3]]
            mapBib["Orig"] = i[4]
            mapBib["Scan"] = i[5]
            mapBib["Avail"] = self.mapIdToAvail[i[6]]
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

        strRelIds = self.list_2_in(listMweRec[0][2])

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

        self.execute(strCreate1)
        self.execute(strIn1 + strSelect1 + strFrom1 + strWhere1)  #

        # bei komplexeren MWEs, erweitern um die weiteren Komponenten
        iCount = 1
        for i in range(1, len(listMweRec)):
            strRecSelect = self.__get_mwe_rec_select_free(iCount)
            strRecJoinOn = self.__get_mwe_rec_join_on_free(iCount)
            strRelIds = self.list_2_in(listMweRec[i][2])

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

            self.execute(strCreate2)
            self.execute(strIn2 + strSelect2 + strFrom2 + strWhere)  #

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

        self.execute(strCreateCut)

        mapDone = {}
        for i in listMweRec:
            if (i[0]["LemmaId"], i[0]["PosId"]) not in mapDone:
                for j in i[0]["Relations"]:
                    if len(setRelations) == 0 or j in setRelations:
                        strWhereCutDummy = strWhereCut.replace("$LEMMA$", str(i[0]["LemmaId"])).replace("$POS$", str(
                            i[0]["PosId"])).replace("$FUNCTION$", str(self.mapRelToId[j]))
                        self.execute(strInCut + strSelectCut + strFromCut + strWhereCutDummy + strLimitCut)
                mapDone[(i[0]["LemmaId"], i[0]["PosId"])] = True

            if (i[1]["LemmaId"], i[1]["PosId"]) not in mapDone:
                for j in i[1]["Relations"]:
                    if len(setRelations) == 0 or j in setRelations:
                        strWhereCutDummy = strWhereCut.replace("$LEMMA$", str(i[1]["LemmaId"])).replace("$POS$", str(
                            i[1]["PosId"])).replace("$FUNCTION$", str(self.mapRelToId[j]))
                        self.execute(strInCut + strSelectCut + strFromCut + strWhereCutDummy + strLimitCut)
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

        if self.mwe_depth > iCount:

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

        listResult = self.fetchall(strSelect3 + strFrom3)

        return listResult
