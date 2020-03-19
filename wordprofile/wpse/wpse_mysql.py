#!/usr/bin/python
import logging
from typing import List

import pymysql

from wordprofile.datatypes import CooccInfo, Coocc, Concordance

pymysql.install_as_MySQLdb()
import MySQLdb

logger = logging.getLogger('wordprofile.mysql')


class WpSeMySql:
    def __init__(self, host, user, passwd, dbname):
        self.__host = host
        self.__user = user
        self.__passwd = passwd
        self.__dbname = dbname
        self.__conn = None
        self.__cursor = None

    def __init_connection(self):
        self.__conn = MySQLdb.connect(
            host=self.__host,
            user=self.__user,
            passwd=self.__passwd,
            db=self.__dbname)
        self.__cursor = self.__conn.cursor()

    def __close_connection(self):
        self.__conn.commit()
        self.__cursor.close()
        self.__conn.close()

    def fetchall(self, query):
        self.__init_connection()
        self.__cursor.execute(query)
        res = self.__cursor.fetchall()
        self.__close_connection()
        return res

    def get_concordances(self, coocc_id, use_context, start_index, result_number):
        coocc_info = self.get_relation_by_id(coocc_id)
        if coocc_info.inv:
            head_lemma, head_tag = coocc_info.lemma2, coocc_info.pos2
            dep_lemma, dep_tag = coocc_info.lemma1, coocc_info.pos1
        else:
            head_lemma, head_tag = coocc_info.lemma1, coocc_info.pos1
            dep_lemma, dep_tag = coocc_info.lemma2, coocc_info.pos2

        if use_context:
            query = """
            SELECT
                s_center.sentence, matches.head_position, matches.dep_position, matches.prep_position, cf.corpus, 
                matches.creation_date, cf.text_class, cf.orig, cf.scan, cf.available, 
                s_center.page, cf.file, 1, s_left.sentence, s_right.sentence 
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
            WHERE (
                matches.relation_label = '{}' and
                matches.head_lemma = '{}' and  
                matches.head_tag = '{}' and  
                matches.dep_lemma = '{}' and  
                matches.dep_tag = '{}'
            )  
            LIMIT {},{};
            """.format(coocc_info.rel, head_lemma, head_tag, dep_lemma, dep_tag,
                       start_index, result_number)
        else:
            query = """
            SELECT
                s_center.sentence, matches.head_position, matches.dep_position, matches.prep_position, cf.corpus, 
                matches.creation_date, cf.text_class, cf.orig, cf.scan, cf.available, 
                s_center.page, cf.file, 1, "", ""
            FROM
                matches
            LEFT JOIN corpus_files as cf ON (matches.corpus_file_id = cf.id)
            LEFT JOIN concord_sentences as s_center ON
                (s_center.corpus_file_id = cf.id
                and s_center.sentence_id = matches.sentence_id)
            WHERE (
                matches.relation_label = '{}' and
                matches.head_lemma = '{}' and  
                matches.head_tag = '{}' and  
                matches.dep_lemma = '{}' and  
                matches.dep_tag = '{}'
            )  
            LIMIT {},{};
            """.format(coocc_info.rel, head_lemma, head_tag, dep_lemma, dep_tag,
                       start_index, result_number)
        db_results = self.fetchall(query)
        db_results: List[Concordance] = list(map(Concordance._make, db_results))
        return db_results

    def get_lemma_and_pos(self, word, pos=''):
        """
        Basismethode zur Abfrage von Lemmainformationen
        """
        if not all(c.isalpha() or c == '-' for c in word):
            return []

        query = """
            SELECT lemma1, lemma1_tag, label, SUM(frequency), inv
            FROM collocations c
            WHERE lemma1 = '{}' {}
            GROUP BY lemma1, lemma1_tag, label, inv
            HAVING SUM(frequency) > 25
        """.format(
            word,
            # TODO determine for default POS value
            "and lemma1_tag='{}'".format(pos) if pos else "",
        )
        db_results = self.fetchall(query)
        return db_results

    def get_relation_by_id(self, coocc_id):
        query = """
        SELECT
            c.label, c.lemma1, c.lemma2, c.lemma1_tag, c.lemma2_tag, c.inv
        FROM 
            collocations c
        WHERE c.id = {}
        """.format(coocc_id)
        db_results = self.fetchall(query)[0]
        return CooccInfo(*db_results)

    def get_relation_tuples(self, lemma1, lemma2, pos1, pos2, start, number, order_by, min_freq,
                            min_stat, relation):
        """
        Methode zum Abfragen der Kookkurrenztupeln zu einer liste von gegebenen Relation-IDs über die
        Wortprofil-MySQL-Datenbank
        """
        if relation.startswith('~'):
            relation = relation[1:]
            inv = 1
        else:
            inv = 0
        min_freq_sql = " and (frequency) >= {} ".format(min_freq) if min_freq > 0 else ""
        min_stat_sql = " and (log_dice) >= {} ".format(min_stat) if min_stat > -100000000 else ""
        select_from_sql = """
        SELECT
            c.id, c.label, c.lemma1, c.lemma2, c.lemma1_tag, c.lemma2_tag, 
            IFNULL(c.frequency, 0), IFNULL(s.log_dice, 0.0), inv
        FROM 
            collocations c
        LEFT JOIN wp_stats s on c.id = s.collocation_id
        """
        if not pos2 or not lemma2:
            where_sql = """
                WHERE (lemma1='{}' and lemma1_tag='{}') and label = '{}' and inv = {} {} {} 
                ORDER BY {} DESC LIMIT {},{};""".format(
                lemma1, pos1, relation, inv, min_freq_sql, min_stat_sql, order_by, start, number
            )
        else:
            where_sql = """
                WHERE 
                    (lemma1='{}' and lemma1_tag='{}' and 
                     lemma2='{}' and lemma2_tag='{}') and 
                     label = '{}' and inv = {} {} {} 
                ORDER BY {} DESC LIMIT {},{};""".format(
                lemma1, pos1, lemma2, pos2, relation, inv, min_freq_sql, min_stat_sql, order_by, start, number
            )
        db_results = self.fetchall(select_from_sql + where_sql)
        return list(map(Coocc._make, db_results))

    def get_relation_tuples_diff(self, lemma1, lemma2, pos, relation,
                                 order_by, min_freq, min_stat):
        """
        Ermitteln der Kookkurrenzen zu einer Liste von syntaktischen Relationen für die 'diff'-Abfrage
        """
        if relation.startswith('~'):
            relation = relation[1:]
            inv = 1
        else:
            inv = 0

        query = """
        SELECT c.id, label, lemma1, lemma2, lemma1_tag, lemma2_tag, IFNULL(c.frequency, 0), IFNULL(s.log_dice, 0.0), inv
        FROM collocations c
        LEFT JOIN wp_stats s on c.id = s.collocation_id
        WHERE lemma1 IN ('{}','{}') and lemma1_tag='{}' and label = "{}" and inv = {}
        {}
        ORDER BY {} DESC""".format(
            lemma1, lemma2, pos,
            relation,
            inv,
            "and frequency >= {}".format(min_freq) if min_freq > 0 else "",
            order_by
        )
        db_results = self.fetchall(query)
        return list(map(Coocc._make, db_results))
