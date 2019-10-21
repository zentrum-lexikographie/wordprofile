#!/usr/bin/python
import logging
from collections import defaultdict, namedtuple

import MySQLdb

from wordprofile.wpse.wpse_string import format_sentence, format_sentence_center

logger = logging.getLogger('wordprofile.mysql')


class WpSeMySql:
    def __init__(self, host, user, passwd, dbname, port):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.dbname = dbname
        self.port = port

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

    def get_match_id(self, coocc_info):
        query = """
        SELECT  
            match_id
        FROM 
            relations
        WHERE head_lemma='{}' and head_pos='{}' and 
              dep_lemma='{}' and dep_pos='{}' and 
              relation = '{}'
        """.format(coocc_info.lemma1, coocc_info.pos1, coocc_info.lemma2, coocc_info.pos2, coocc_info.rel)
        db_results = self.fetchall(query)
        return db_results[0][0]

    def get_concordances(self, coocc_info, use_context, subcorpus, is_internal_user, start_index, result_number):
        match_id = self.get_match_id(coocc_info)
        internal_user_cond = " and matches.rights=1 " if not is_internal_user else ""
        subcorpus_cond = " and matches.corpus='{}' ".format(subcorpus) if subcorpus else ""

        if use_context:
            query = """
            SELECT
                s_center.sentence, matches.head_position, matches.dep_position, matches.prep_position, matches.corpus, 
                matches.date, corpus_files.text_class, corpus_files.orig, corpus_files.scan, corpus_files.available, 
                s_center.page, corpus_files.file, matches.gdex_score, s_left.sentence, s_right.sentence 
            FROM
                matches
            LEFT JOIN concord_sentences as s_center ON
                (s_center.corpus = matches.corpus
                and s_center.file = matches.file
                and s_center.sentence_id = matches.sentence_id)
            LEFT JOIN corpus_files ON
                (matches.corpus = corpus_files.corpus
                and matches.file = corpus_files.file)
            LEFT JOIN concord_sentences as s_left ON
                (s_left.corpus = matches.corpus
                and s_left.file = matches.file
                and s_left.sentence_id =(matches.sentence_id-1))
            LEFT JOIN concord_sentences as s_right ON
                (s_right.corpus = matches.corpus
                and s_right.file = matches.file
                and s_right.sentence_id =(matches.sentence_id + 1))
            WHERE matches.match_id = {} {} {}
            LIMIT {},{};
            """.format(match_id, subcorpus_cond, internal_user_cond, start_index, result_number)
        else:
            query = """
            SELECT
                s_center.sentence, matches.head_position, matches.dep_position, matches.prep_position, matches.corpus, 
                matches.date, corpus_files.text_class, corpus_files.orig, corpus_files.scan, corpus_files.available, 
                s_center.page, corpus_files.file, matches.gdex_score
            FROM
                matches
            LEFT JOIN concord_sentences as s_center ON
                (s_center.corpus = matches.corpus
                and s_center.file = matches.file
                and s_center.sentence_id = matches.sentence_id)
            LEFT JOIN corpus_files ON 
                (matches.corpus = corpus_files.corpus 
                and matches.file = corpus_files.file)
            WHERE matches.match_id = {} {} {}
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
            SELECT head_lemma lemma, head_pos pos, 
                   CAST(SUM(-frequency) AS SIGNED) frequency, relation
            FROM relations
            WHERE LOWER(head_lemma) LIKE '{}' {}
            GROUP BY lemma, pos, relation;
        """.format(
            word.lower(),
            # TODO determine for default POS value
            "and pos='{}'".format(pos) if pos not in ["*", ""] else "")
        db_results = self.fetchall(query)

        return self.__get_valid_sorted_lemmas(db_results, word, is_case_sensitive)

    @staticmethod
    def __get_valid_sorted_lemmas(db_results, word, is_case_sensitive):
        """
        Bei einer gegebenen Liste von Lemmainformationen werden Einträge gelöscht und die Einträge werden Sortiert.
        Hierbei wird Bezug auf die Großschreibung und auf die Wortarten Bezug genommen. So sind Großgeschriebene Worte
        eher Substantiv als Verb.
        """
        lemma_pos_mapping = defaultdict(list)
        for lemma, pos, frequency, relation in db_results:
            lemma_pos_mapping[(lemma, pos)].append((relation, frequency))

        # Erstellen einer map, die zu einer Wortart, die frequenteste Lemmainformation besitzt
        most_frequent_lemma = {}
        for (lemma, pos), relations in lemma_pos_mapping.items():
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
            results.append((score, {'Lemma': lemma, 'POS': pos,
                                    'Frequency': frequency, 'Relations': relations}))
        results = [r[1] for r in sorted(results, key=lambda x: x[0])]
        return results

    def get_relation_tuples_check(self, lemma1, lemma2, pos1, pos2, start, number, order_by, min_freq,
                                  min_stat, relation):
        """
        Methode zum Abfragen der Kookkurrenztupeln zu einer liste von gegebenen Relation-IDs über die
        Wortprofil-MySQL-Datenbank
        """
        min_freq_sql = " and (-relations.frequency) >= {} ".format(min_freq) if min_freq > 0 else ""
        min_stat_sql = " and (-relations.{}) >= {} ".format(order_by, min_stat) if min_stat > -100000000 else ""

        select_from_sql = """
        SELECT  
            relation, prep_lemma, head_lemma, dep_lemma, prep_surface, head_surface, dep_surface, head_pos, dep_pos, 
            -relations.frequency, -counts_with_rights, -mi_log_freq, -relations.log_dice, -mi3, match_id
        FROM 
            relations
        """

        if pos2 == -1 or lemma2 == -1:
            where_sql = "WHERE head_lemma='{}' and head_pos='{}' and relation = '{}' {} {} LIMIT {}, {};".format(
                lemma1, pos1, relation, min_freq_sql, min_stat_sql, start, number
            )
        else:
            where_sql = """WHERE head_lemma='{}' and head_pos='{}' and 
                                dep_lemma='{}' and dep_pos='{}' and 
                                relation = '{}' {} {} ORDER BY frequency;""".format(
                lemma1, pos1, lemma2, pos2, relation, min_freq_sql, min_stat_sql
            )

        db_results = self.fetchall(select_from_sql + where_sql)
        Coocc = namedtuple("Coocc",
                           ["Rel", "Prep", "Lemma1", "Lemma2", "SurfacePrep", "Surface1", "Surface2", "Pos1", "Pos2",
                                     "Frequency", "FreqBelege", "Score_MiLogFreq", "Score_logDice", "Score_MI3",
                                     "Info"])
        return map(Coocc._make, db_results)

    def get_relation_tuples_diff(self, lemma1, lemma2, pos, relations,
                                 order_by, min_freq, min_stat):
        """
        Ermitteln der Kookkurrenzen zu einer Liste von syntaktischen Relationen für die 'diff'-Abfrage
        """
        query = """
        SELECT relation, prep_lemma, head_lemma, dep_lemma, prep_surface, head_surface, dep_surface, dep_pos, 
               -frequency, -counts_with_rights, -{}, match_id
        FROM relations
        WHERE head_lemma IN ("{}","{}") and head_pos="{}" and relation IN ({}) {} {};
        """.format(
            order_by,
            lemma1, lemma2, pos,
            ",".join(['"{}"'.format(r) for r in relations]),
            " and (-frequency) >= {}".format(min_freq) if min_freq > 0 else "",
            " and (-{}) >= {}".format(order_by, min_stat) if min_stat > -100000000 else ""
        )
        db_results = self.fetchall(query)
        Coocc = namedtuple("CooccDiff",
                           ["Rel", "Prep", "Lemma1", "Lemma2", "SurfacePrep", "Surface1", "Surface2", "Pos2",
                            "Frequency", "FreqBelege", "Score", "Info"])
        return list(map(Coocc._make, db_results))
