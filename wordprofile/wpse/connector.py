import logging
from typing import List

import pymysql

from wordprofile.datatypes import CooccInfo, Coocc, Concordance, LemmaInfo

pymysql.install_as_MySQLdb()
import MySQLdb

logger = logging.getLogger('wordprofile.mysql')


class WPConnect:
    """Gives access to word profile database backend, following the repository pattern.
    """

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

    def __fetchall(self, query):
        self.__init_connection()
        self.__cursor.execute(query)
        res = self.__cursor.fetchall()
        self.__close_connection()
        return res

    def get_db_infos(self):
        query = """SELECT TABLE_NAME, TABLE_ROWS, CREATE_TIME, UPDATE_TIME
                   FROM information_schema.tables WHERE table_schema = DATABASE();"""
        db_results = [{
            'name': t[0],
            'rows': t[1],
            'create_time': t[2],
            'last_update': t[3]
        } for t in self.__fetchall(query) if t[1]]
        return db_results

    def get_label_frequencies(self):
        query = """SELECT label, freq FROM corpus_freqs"""
        db_results = {t[0]: t[1] for t in self.__fetchall(query)}
        return db_results

    def get_tag_frequencies(self):
        query = """
        SELECT tag, SUM(freq) 
        FROM token_freqs tf 
        GROUP BY tag"""
        db_results = {t[0]: t[1] for t in self.__fetchall(query)}
        return db_results

    def get_corpus_file_stats(self):
        query = """
        SELECT corpus, COUNT(*), min(`date`) as min_date, MAX(`date`) as max_date
        FROM corpus_files cf
        GROUP BY corpus"""
        db_results = {t[0]: {
            "count": t[1],
            "min_date": t[2],
            "max_date": t[3],
        } for t in self.__fetchall(query)}
        return db_results

    def get_concordances(self, coocc_id: int, use_context: bool, start_index: int, result_number: int) -> List[
        Concordance]:
        """Fetches concordances for collocation id from database backend.

        Args:
            coocc_id: Collocation id for concordances.
            use_context: If true, returns surrounding sentences.
            start_index: Row index to start with.
            result_number: Number of results to return.

        Return:
            List of Concordance.
        """
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
                cf.date, cf.text_class, cf.orig, cf.scan, cf.available, 
                s_center.page, cf.file, 1, s_left.sentence, s_right.sentence 
            FROM
                matches
            INNER JOIN collocations as c ON (matches.collocation_id = c.id)
            INNER JOIN corpus_files as cf ON (matches.corpus_file_id = cf.id)
            INNER JOIN concord_sentences as s_center ON
                (s_center.corpus_file_id = cf.id
                and s_center.sentence_id = matches.sentence_id)
            LEFT JOIN concord_sentences as s_left ON
                (s_left.corpus_file_id = cf.id
                and s_left.sentence_id =(matches.sentence_id-1))
            LEFT JOIN concord_sentences as s_right ON
                (s_right.corpus_file_id = cf.id
                and s_right.sentence_id =(matches.sentence_id + 1))
            WHERE (
                c.label = '{}' and
                c.lemma1 = '{}' and  
                c.lemma1_tag = '{}' and  
                c.lemma2 = '{}' and  
                c.lemma2_tag = '{}'
            )
            ORDER BY cf.date DESC 
            LIMIT {},{};
            """.format(coocc_info.rel, head_lemma, head_tag, dep_lemma, dep_tag,
                       start_index, result_number)
        else:
            query = """
            SELECT
                s_center.sentence, matches.head_position, matches.dep_position, matches.prep_position, cf.corpus, 
                cf.date, cf.text_class, cf.orig, cf.scan, cf.available, 
                s_center.page, cf.file, 1, '', ''
            FROM
                matches
            INNER JOIN collocations as c ON (matches.collocation_id = c.id)
            INNER JOIN corpus_files as cf ON (matches.corpus_file_id = cf.id)
            INNER JOIN concord_sentences as s_center ON
                (s_center.corpus_file_id = cf.id
                and s_center.sentence_id = matches.sentence_id)
            WHERE (
                c.label = '{}' and
                c.lemma1 = '{}' and  
                c.lemma1_tag = '{}' and  
                c.lemma2 = '{}' and  
                c.lemma2_tag = '{}'
            ) 
            ORDER BY cf.date DESC 
            LIMIT {},{};
            """.format(coocc_info.rel, head_lemma, head_tag, dep_lemma, dep_tag,
                       start_index, result_number)
        db_results = self.__fetchall(query)
        db_results: List[Concordance] = list(map(Concordance._make, db_results))
        return db_results

    def get_lemma_and_pos(self, lemma: str, lemma_tag: str = '') -> List[LemmaInfo]:
        """ Fetches lemma information for valid inputs.
        Args:
            lemma: Lemma of form [a-zA-Z-]
            lemma_tag (optional): Pos tag of lemma.

        Return:
            List of LemmaInfo that fits criteria.
        """
        query = """
            SELECT lemma1, lemma1_tag, label, SUM(frequency), inv
            FROM collocations c
            WHERE lemma1 = '{}' {}
            GROUP BY lemma1, lemma1_tag, label, inv
        """.format(
            lemma,
            "and lemma1_tag='{}'".format(lemma_tag) if lemma_tag else "",
        )
        db_results = self.__fetchall(query)
        db_results = list(filter(lambda l: l.lemma.lower() == lemma.lower(), map(LemmaInfo._make, db_results)))
        return db_results

    def get_relation_by_id(self, coocc_id: int) -> CooccInfo:
        """Fetches collocation information for collocation id from database backend.

        Args:
            coocc_id: Collocation id for concordances.

        Return:
            Collocation information.
        """

        query = """
        SELECT
            c.id, c.label, c.lemma1, c.lemma2, c.lemma1_tag, c.lemma2_tag, c.inv, 
            IF(c.id IN (SELECT collocation1_id FROM mwe), 1, 0) as has_mwe
        FROM 
            collocations c
        WHERE c.id = {}
        """.format(coocc_id)
        db_results = self.__fetchall(query)[0]
        return CooccInfo(*db_results)

    def get_relation_tuples(self, lemma1: str, lemma1_tag: str, lemma2: str, lemma2_tag: str, start: int, number: int,
                            order_by: str, min_freq: int, min_stat: float, relation: str) -> List[Coocc]:
        """Fetches collocations with related statistics for a specific relation from database backend.

        Args:
            lemma1: Lemma of interest, first collocate.
            lemma1_tag: Pos tag of first lemma.
            lemma2: Second collocate.
            lemma2_tag: Pos tag of second lemma.
            start: Number of collocations to skip.
            number: Number of collocations to take.
            order_by: Metric for ordering, frequency or log_dice.
            min_freq: Filter collocations with minimal frequency.
            min_stat: Filter collocations with minimal stats score.
            relation: List of relation labels.

        Return:
            List of Coocc.
        """
        if relation.startswith('~'):
            relation = relation[1:]
            inv = 1
        else:
            inv = 0
        min_freq_sql = " and (frequency) >= {} ".format(min_freq) if min_freq > 0 else ""
        min_stat_sql = " and (c.score) >= {} ".format(min_stat) if min_stat > -1000 else ""
        select_from_sql = """
        SELECT
            c.id, c.label, c.lemma1, c.lemma2, c.lemma1_tag, c.lemma2_tag, 
            IFNULL(c.frequency, 0) as frequency, IFNULL(c.score, 0.0) as log_dice, inv,
            IF(ABS(c.id) IN (SELECT collocation1_id FROM mwe WHERE frequency >= 5), 1, 0) as has_mwe
        FROM 
            collocations c
        """
        if not lemma2_tag or not lemma2:
            where_sql = """
                WHERE (lemma1='{}' and lemma1_tag='{}') and label = '{}' and inv = {} {} {} 
                ORDER BY {} DESC LIMIT {},{};""".format(
                lemma1, lemma1_tag, relation, inv, min_freq_sql, min_stat_sql, order_by, start, number
            )
        else:
            where_sql = """
                WHERE 
                    (lemma1='{}' and lemma1_tag='{}' and 
                     lemma2='{}' and lemma2_tag='{}') and 
                     label = '{}' and inv = {} {} {} 
                ORDER BY {} DESC LIMIT {},{};""".format(
                lemma1, lemma1_tag, lemma2, lemma2_tag, relation, inv, min_freq_sql, min_stat_sql, order_by, start,
                number
            )
        db_results = self.__fetchall(select_from_sql + where_sql)
        return list(map(Coocc._make, db_results))

    def get_relation_meta(self, lemma1: str, lemma1_tag: str, lemma2: str, lemma2_tag: str, start: int, number: int,
                          order_by: str, min_freq: int, min_stat: float) -> List[Coocc]:
        """Fetches collocations with related statistics for all relations from database backend.

        Args:
            lemma1: Lemma of interest, first collocate.
            lemma1_tag: Pos tag of first lemma.
            lemma2: Second collocate.
            lemma2_tag: Pos tag of second lemma.
            start: Number of collocations to skip.
            number: Number of collocations to take.
            order_by: Metric for ordering, frequency or log_dice.
            min_freq: Filter collocations with minimal frequency.
            min_stat: Filter collocations with minimal stats score.

        Return:
            List of Coocc.
        """
        min_freq_sql = " and (frequency) >= {} ".format(min_freq) if min_freq > 0 else ""
        min_stat_sql = " and (c.score) >= {} ".format(min_stat) if min_stat > -1000 else ""
        select_from_sql = """
        SELECT
            c.id, c.label, c.lemma1, c.lemma2, c.lemma1_tag, c.lemma2_tag, 
            IFNULL(c.frequency, 0) as frequency, IFNULL(c.score, 0.0) as log_dice, inv,
            IF(ABS(c.id) IN (SELECT collocation1_id FROM mwe WHERE frequency >= 5), 1, 0) as has_mwe
        FROM 
            collocations c
        """
        if not lemma2_tag or not lemma2:
            where_sql = """
                WHERE 
                    (lemma1='{}' and lemma1_tag='{}')
                    and label NOT REGEXP 'VZ|PP|KON|KOM'
                    {} {} 
                ORDER BY {} DESC LIMIT {},{};""".format(
                lemma1, lemma1_tag, min_freq_sql, min_stat_sql, order_by, start, number
            )
        else:
            where_sql = """
                WHERE 
                    (lemma1='{}' and lemma1_tag='{}' and
                     lemma2='{}' and lemma2_tag='{}')
                     and label NOT REGEXP 'VZ|PP|KON|KOM'
                     {} {}
                ORDER BY {} DESC LIMIT {},{};""".format(
                lemma1, lemma1_tag, lemma2, lemma2_tag, min_freq_sql, min_stat_sql, order_by, start, number
            )
        db_results = self.__fetchall(select_from_sql + where_sql)
        return list(map(Coocc._make, db_results))

    def get_relation_tuples_diff(self, lemma1: str, lemma2: str, lemma_tag: str, relation: str, order_by: str,
                                 min_freq: int, min_stat) -> List[Coocc]:
        """Fetches collocations for both lemmas with related statistics for a specific relation from database backend.

        Args:
            lemma1: Lemma of interest, first collocate.
            lemma2: Second collocate.
            lemma_tag: Pos tag of second lemma.
            relation: List of relation labels.
            order_by: Metric for ordering, frequency or log_dice.
            min_freq: Filter collocations with minimal frequency.
            min_stat: Filter collocations with minimal stats score.

        Return:
            List of Coocc.
        """
        if relation.startswith('~'):
            relation = relation[1:]
            inv = 1
        else:
            inv = 0
        min_freq_sql = " and (frequency) >= {} ".format(min_freq) if min_freq > 0 else ""
        min_stat_sql = " and (c.score) >= {} ".format(min_stat) if min_stat > -1000 else ""
        query = """
        SELECT 
            c.id, label, lemma1, lemma2, lemma1_tag, lemma2_tag, 
            IFNULL(c.frequency, 0) as frequency, IFNULL(c.score, 0.0) as log_dice, inv,
            IF(ABS(c.id) IN (SELECT collocation1_id FROM mwe), 1, 0) as has_mwe
        FROM collocations c
        WHERE lemma1 IN ('{}','{}') and lemma1_tag='{}' and label = '{}' and inv = {}
        {} {}
        ORDER BY {} DESC""".format(
            lemma1, lemma2, lemma_tag,
            relation,
            inv,
            min_freq_sql,
            min_stat_sql,
            order_by
        )
        db_results = self.__fetchall(query)
        return list(map(Coocc._make, db_results))

    def get_relation_tuples_diff_meta(self, lemma1: str, lemma2: str, lemma_tag: str, order_by: str,
                                      min_freq: int, min_stat) -> List[Coocc]:
        """Fetches collocations for both lemmas with related statistics for all relations from database backend.

        Args:
            lemma1: Lemma of interest, first collocate.
            lemma2: Second collocate.
            lemma_tag: Pos tag of second lemma.
            order_by: Metric for ordering, frequency or log_dice.
            min_freq: Filter collocations with minimal frequency.
            min_stat: Filter collocations with minimal stats score.

        Return:
            List of Coocc.
        """
        min_freq_sql = " and (frequency) >= {} ".format(min_freq) if min_freq > 0 else ""
        min_stat_sql = " and (c.score) >= {} ".format(min_stat) if min_stat > -1000 else ""
        query = """
        SELECT 
            c.id, label, lemma1, lemma2, lemma1_tag, lemma2_tag, 
            IFNULL(c.frequency, 0) as frequency, IFNULL(c.score, 0.0) as log_dice, inv,
            IF(ABS(c.id) IN (SELECT collocation1_id FROM mwe), 1, 0) as has_mwe
        FROM collocations c
        WHERE lemma1 IN ('{}','{}') and lemma1_tag='{}'
        {} {}
        ORDER BY {} DESC""".format(
            lemma1, lemma2, lemma_tag,
            min_freq_sql,
            min_stat_sql,
            order_by
        )
        db_results = self.__fetchall(query)
        return list(map(Coocc._make, db_results))
