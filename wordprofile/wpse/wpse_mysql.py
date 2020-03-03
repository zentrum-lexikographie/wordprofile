#!/usr/bin/python
import logging
from collections import defaultdict, namedtuple, Counter

import pymysql

pymysql.install_as_MySQLdb()
import MySQLdb

from wordprofile.wpse.wpse_string import format_sentence, format_sentence_center

logger = logging.getLogger('wordprofile.mysql')


class WpSeMySql:
    def __init__(self, host, user, passwd, dbname):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.dbname = dbname
        self.__conn = None
        self.__cursor = None

    def init_connection(self):
        self.__conn = MySQLdb.connect(
            host=self.host,
            user=self.user,
            passwd=self.passwd,
            db=self.dbname)
        self.__cursor = self.__conn.cursor()

    def close_connection(self):
        self.__conn.commit()
        self.__cursor.close()
        self.__conn.close()

    def execute(self, query):
        self.__cursor.execute(query)

    def fetchall(self, query):
        self.init_connection()
        self.__cursor.execute(query)
        res = self.__cursor.fetchall()
        self.close_connection()
        return res

    def get_concordances(self, coocc_id, use_context, subcorpus, is_internal_user, start_index, result_number):
        coocc_info = self.get_relation_by_id(coocc_id)
        if use_context:
            query = """
            SELECT
                s_center.sentence, matches.head_position, matches.dep_position, matches.prep_position, cf.corpus, 
                matches.creation_date, cf.text_class, cf.orig, cf.scan, cf.available, 
                s_center.page, cf.file, matches.gdex_score, s_left.sentence, s_right.sentence 
            FROM
                matches
            LEFT JOIN corpus_files as cf ON (matches.corpus_file_id = cf.id)
            LEFT JOIN concord_sentences as s_center ON
                (s_center.corpus_file_id = cf.id
                and s_center.sentence_id = matches.sentence_id)
            LEFT JOIN concord_sentences as s_left ON
                (s_left.corpus_file_id = cf.id
                and s_left.sentence_id =(matches.sentence_id-1))
            LEFT JOIN concord_sentences as s_right ON
                (s_right.corpus_file_id = cf.id
                and s_right.sentence_id =(matches.sentence_id + 1))
            WHERE matches.relation_id = {}
            LIMIT {},{};
            """.format(coocc_info.rel_id, start_index, result_number)
        else:
            query = """
            SELECT
                s_center.sentence, matches.head_position, matches.dep_position, matches.prep_position, cf.corpus, 
                matches.creation_date, cf.text_class, cf.orig, cf.scan, cf.available, 
                s_center.page, cf.file, matches.gdex_score
            FROM
                matches
            LEFT JOIN corpus_files as cf ON (matches.corpus_file_id = cf.id)
            LEFT JOIN concord_sentences as s_center ON
                (s_center.corpus_file_id = cf.id
                and s_center.sentence_id = matches.sentence_id)
            WHERE matches.relation_id = {}
            LIMIT {},{};
            """.format(coocc_info.rel_id, start_index, result_number)
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

    def get_lemma_and_pos(self, word, pos, is_case_sensitive):
        """
        Basismethode zur Abfrage von Lemmainformationen
        """
        if not all(c.isalpha() or c == '-' for c in word):
            return []

        query = """
            SELECT lemma1, lemma1_pos, label, CAST(COUNT(m.id) AS SIGNED) frequency, (c.label LIKE "~%")
            FROM collocations c
            LEFT JOIN matches m on c.relation_id = m.relation_id
            WHERE LOWER(lemma1) = '{}' {}
            GROUP BY lemma1, lemma1_pos, label
            HAVING frequency > 5
        """.format(
            word.lower(),
            # TODO determine for default POS value
            "and lemma1_pos='{}'".format(pos) if pos not in ["*", ""] else "",
        )
        db_results = self.fetchall(query)
        return self.__get_valid_sorted_lemmas(db_results, word, False)

    @staticmethod
    def __get_valid_sorted_lemmas(db_results, word, is_case_sensitive):
        """
        Bei einer gegebenen Liste von Lemmainformationen werden Einträge gelöscht und die Einträge werden Sortiert.
        Hierbei wird Bezug auf die Großschreibung und auf die Wortarten Bezug genommen. So sind Großgeschriebene Worte
        eher Substantiv als Verb.
        """
        lemma_pos_mapping = defaultdict(list)
        for lemma, pos, relation, frequency, inv in db_results:
            lemma_pos_mapping[(lemma, pos)].append((relation, frequency))

        # Erstellen einer map, die zu einer Wortart, die frequenteste Lemmainformation besitzt
        most_frequent_lemma = {}
        for (lemma, pos), relations in lemma_pos_mapping.items():
            relations = list(Counter([r for r, c in relations for _ in range(c)]).items())
            frequency = sum(frequency for _, frequency in relations)
            if pos not in most_frequent_lemma or most_frequent_lemma[pos][1] < frequency:
                most_frequent_lemma[pos] = (lemma, frequency, relations)
        pos_sorted = sorted(most_frequent_lemma.items(), key=lambda x: x[1][1], reverse=True)

        results = []
        for pos, (lemma, frequency, relations) in pos_sorted:
            relations = [relation for (relation, frequency) in relations]

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
            results.append((score, {'Lemma': lemma, 'POS': pos, 'PosId': pos,
                                    'Frequency': frequency, 'Relations': relations}))
        results = [r[1] for r in sorted(results, key=lambda x: x[0])]
        return results

    def get_relation_by_id(self, coocc_id):
        query = """
        SELECT
            c.relation_id, c.label, c.prep_lemma, c.lemma1, c.lemma2, c.lemma1_pos, c.lemma2_pos
        FROM 
            collocations c
        WHERE c.id = {}
        """.format(coocc_id)
        db_results = self.fetchall(query)[0]
        Coocc = namedtuple("CooccInfo", ["rel_id", "rel", "prep", "lemma1", "lemma2", "pos1", "pos2"])
        return Coocc(*db_results)

    def get_relation_tuples_check(self, lemma1, lemma2, pos1, pos2, start, number, order_by, min_freq,
                                  min_stat, relation):
        """
        Methode zum Abfragen der Kookkurrenztupeln zu einer liste von gegebenen Relation-IDs über die
        Wortprofil-MySQL-Datenbank
        """
        min_freq_sql = " and (frequency) >= {} ".format(min_freq) if min_freq > 0 else ""
        min_stat_sql = " and (log_dice) >= {} ".format(min_stat) if min_stat > -100000000 else ""
        select_from_sql = """
        SELECT
            c.id, c.label, c.prep_lemma, c.lemma1, c.lemma2, c.lemma1_pos, c.lemma2_pos, 
            IFNULL(s.frequency, 0), IFNULL(s.log_dice, 0.0), (c.label LIKE "~%")
        FROM 
            collocations c
        LEFT JOIN wp_stats s on c.id = s.collocation_id
        """
        if not pos2 or not lemma2:
            where_sql = """
                WHERE (lemma1='{}' and lemma1_pos='{}') and label = '{}' {} {} 
                ORDER BY {} DESC LIMIT {},{};""".format(
                lemma1, pos1, relation, min_freq_sql, min_stat_sql, order_by, start, number
            )
        else:
            where_sql = """
                WHERE 
                    (lemma1='{}' and lemma1_pos='{}' and 
                     lemma2='{}' and lemma2_pos='{}') and 
                     label = '{}' {} {} 
                ORDER BY {} DESC LIMIT {},{};""".format(
                lemma1, pos1, lemma2, pos2, relation, min_freq_sql, min_stat_sql, order_by, start, number
            )
        db_results = self.fetchall(select_from_sql + where_sql)
        Coocc = namedtuple("Coocc",
                           ["RelId", "Rel", "Prep", "Lemma1", "Lemma2", "Pos1", "Pos2",
                            "Frequency", "LogDice", "inverse"])
        return map(Coocc._make, db_results)

    def get_relation_tuples_diff(self, lemma1, lemma2, pos, relations,
                                 order_by, min_freq, min_stat):
        """
        Ermitteln der Kookkurrenzen zu einer Liste von syntaktischen Relationen für die 'diff'-Abfrage
        """
        query = """
        SELECT c.id, label, prep_lemma, lemma1, lemma2, lemma1_pos, lemma2_pos, 
               COUNT(m.id) frequency, 1 as score
        FROM collocations c
        LEFT JOIN matches m on c.id = m.relation_id
        WHERE lemma1 IN ("{}","{}") and lemma1_pos="{}" and label IN ({})
        GROUP BY c.id, label, prep_lemma, lemma1, lemma2, lemma1_pos, lemma2_pos
        {}
        """.format(
            lemma1, lemma2, pos,
            ",".join(['"{}"'.format(r) for r in relations]),
            "HAVING frequency >= {}".format(min_freq) if min_freq > 0 else ""
        )
        db_results = self.fetchall(query)
        Coocc = namedtuple("CooccDiff",
                           ["RelId", "Rel", "Prep", "Lemma1", "Lemma2", "Pos1", "Pos2", "Frequency", "Score"])
        return list(map(Coocc._make, db_results))
