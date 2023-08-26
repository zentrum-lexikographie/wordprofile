import logging
from typing import List

import pymysql

import wordprofile.config
from wordprofile.datatypes import Coocc, MweConcordance
from wordprofile.errors import InternalError

pymysql.install_as_MySQLdb()
import MySQLdb

logger = logging.getLogger('wordprofile.mysql')


class WPMweConnect:
    """Gives access to word profile database backend, following the repository pattern.
    """

    def __init__(self, host=None, user=None, passwd=None, dbname=None):
        self.__host = host or wordprofile.config.DB_HOST
        self.__user = user or wordprofile.config.DB_USER
        self.__passwd = passwd or str(wordprofile.config.DB_PASSWORD)
        self.__dbname = dbname or wordprofile.config.DB_NAME
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
        self.__cursor.close()
        self.__conn.close()

    def __fetchall(self, query, params=None):
        self.__init_connection()
        try:
            self.__cursor.execute(query, params)
            res = self.__cursor.fetchall()
        finally:
            self.__close_connection()
        return res

    def get_concordances(self, mwe_id: int, use_context: bool, start_index: int, result_number: int) -> List[
        MweConcordance]:
        """Fetches concordances for collocation id from database backend.

        Args:
            mwe_id: Collocation id for concordances.
            use_context: If true, returns surrounding sentences.
            start_index: Row index to start with.
            result_number: Number of results to return.

        Return:
            List of Concordance.
        """
        if use_context:
            query = """
            SELECT
                s_center.sentence, m1.head_position, m1.dep_position, m1.prep_position,
                m2.head_position, m2.dep_position, m2.prep_position, cf.corpus, 
                cf.date, cf.text_class, cf.orig, cf.scan, cf.available, 
                s_center.page, cf.file, 1, s_left.sentence, s_right.sentence 
            FROM
                mwe_match
            INNER JOIN matches as m1 ON (mwe_match.match1_id = m1.id)
            INNER JOIN matches as m2 ON (mwe_match.match2_id = m2.id)
            INNER JOIN corpus_files as cf ON (m1.corpus_file_id = cf.id)
            INNER JOIN concord_sentences as s_center ON
                (s_center.corpus_file_id = cf.id
                and s_center.sentence_id = m1.sentence_id)
            LEFT JOIN concord_sentences as s_left ON
                (s_left.corpus_file_id = cf.id
                and s_left.sentence_id =(m1.sentence_id-1))
            LEFT JOIN concord_sentences as s_right ON
                (s_right.corpus_file_id = cf.id
                and s_right.sentence_id =(m1.sentence_id + 1))
            WHERE 
                mwe_match.mwe_id = %s  
            ORDER BY cf.date DESC 
            LIMIT %s,%s;
            """
            params = (mwe_id, start_index, result_number)
        else:
            query = """
            SELECT
                s_center.sentence, m1.head_position, m1.dep_position, m1.prep_position,
                m2.head_position, m2.dep_position, m2.prep_position, 
                cf.corpus, cf.date, cf.text_class, cf.orig, cf.scan, cf.available, 
                s_center.page, cf.file, 1, '', ''
            FROM
                mwe_match
            INNER JOIN matches as m1 ON (mwe_match.match1_id = m1.id)
            INNER JOIN matches as m2 ON (mwe_match.match2_id = m2.id)
            INNER JOIN corpus_files as cf ON (m1.corpus_file_id = cf.id)
            INNER JOIN concord_sentences as s_center ON
                (s_center.corpus_file_id = cf.id
                and s_center.sentence_id = m1.sentence_id)
            WHERE 
                mwe_match.mwe_id = %s  
            ORDER BY cf.date DESC 
            LIMIT %s,%s;
            """
            params = (mwe_id, start_index, result_number)
        return list(map(lambda i: MweConcordance(*i), self.__fetchall(query, params)))

    def get_relation_by_id(self, mwe_id: int) -> Coocc:
        """Fetches MWE information for mwe id from database backend.

        Args:
            mwe_id: Collocation id for concordances.

        Return:
            MWE information.
        """
        query = """
        SELECT
            mwe.id, mwe.label, mwe.lemma, mwe.lemma_tag, mwe.frequency, c.lemma1, c.lemma2, c.lemma1_tag, c.lemma2_tag, 
            IFNULL(mwe.score, 0.0) as log_dice, tf_mwe.surface, tf1.surface, tf2.surface,
            (SELECT COUNT(*) FROM mwe_match m WHERE m.mwe_id = ABS(mwe.id)) as num_concords
        FROM mwe
        JOIN collocations as c ON (mwe.collocation1_id = c.id)
        JOIN token_freqs tf1 ON (c.lemma1 = tf1.lemma && c.lemma1_tag = tf1.tag) 
        JOIN token_freqs tf2 ON (c.lemma2 = tf2.lemma && c.lemma2_tag = tf2.tag) 
        JOIN token_freqs tf_mwe ON (mwe.lemma = tf_mwe.lemma && mwe.lemma_tag = tf_mwe.tag) 
        WHERE mwe.id = %s;
        """
        params = (mwe_id,)
        res = self.__fetchall(query, params)
        if len(res) == 0:
            raise ValueError("Invalid Id")
        elif len(res) > 1:
            raise InternalError('Too many results.')
        else:
            c = res[0]
            return Coocc(id=c[0], rel=c[1], lemma1="{}-{}".format(c[5], c[6]), lemma2=c[2],
                         form1="{}-{}".format(c[11], c[12]), form2=c[10],
                         tag1="{}-{}".format(c[7], c[8]), tag2=c[3], freq=c[4], score=c[9], inverse=0, has_mwe=0,
                         num_concords=c[13])

    def get_relation_tuples(self, coocc_ids: List[int], order_by: str, min_freq: int, min_stat: float) -> List[Coocc]:
        """Fetches MWE with related statistics for a specific relation from database backend.

        Args:
            coocc_ids: List of Collocation ids, one per relation.
            min_freq: Filter collocations with minimal frequency.
            min_stat: Filter collocations with minimal stats score.

        Return:
            List of Coocc.
        """
        sql = """
        SELECT
            mwe.id, mwe.label, mwe.lemma, mwe.lemma_tag, mwe.frequency, c.lemma1, c.lemma2, c.lemma1_tag, c.lemma2_tag, 
            IFNULL(mwe.score, 0.0) as log_dice, tf_mwe.surface, tf1.surface, tf2.surface,
            (SELECT COUNT(*) FROM mwe_match m WHERE m.mwe_id = ABS(mwe.id)) as num_concords
        FROM mwe
        JOIN collocations as c ON (mwe.collocation1_id = c.id)
        JOIN token_freqs tf1 ON (c.lemma1 = tf1.lemma && c.lemma1_tag = tf1.tag) 
        JOIN token_freqs tf2 ON (c.lemma2 = tf2.lemma && c.lemma2_tag = tf2.tag) 
        JOIN token_freqs tf_mwe ON (mwe.lemma = tf_mwe.lemma && mwe.lemma_tag = tf_mwe.tag) 
        WHERE 
            mwe.collocation1_id IN ({})
            AND mwe.frequency >= %s 
            AND mwe.score >= %s
        ORDER BY {} DESC;
        """.format(",".join('%s' for _ in coocc_ids), order_by)
        params = coocc_ids + [min_freq, min_stat]
        return [Coocc(id=i[0], rel=i[1], lemma1="{}-{}".format(i[5], i[6]), lemma2=i[2],
                      form1="{}-{}".format(i[11], i[12]), form2=i[10],
                      tag1="{}-{}".format(i[7], i[8]), tag2=i[3], freq=i[4], score=i[9], inverse=0, has_mwe=0,
                      num_concords=i[13])
                for i in self.__fetchall(sql, params)]

    def get_collocations(self, lemma1: str, lemma2: str) -> List[Coocc]:
        """Fetches collocations with related statistics for a specific relation from database backend.

        Args:
            lemma1: Lemma of interest, first collocate.
            lemma2: Second collocate.

        Return:
            List of Coocc.
        """
        query = """
            SELECT
                c.id, c.label, c.lemma1, c.lemma2, tf1.surface, tf2.surface, c.lemma1_tag, c.lemma2_tag, 
                IFNULL(c.frequency, 0) as frequency, IFNULL(c.score, 0.0) as log_dice, inv,
                IF(ABS(c.id) IN (SELECT collocation1_id FROM mwe), 1, 0) as has_mwe,
                (SELECT COUNT(*) FROM mwe_match m WHERE m.mwe_id = ABS(mwe.id)) as num_concords
            FROM 
                collocations c
            JOIN token_freqs tf1 ON (c.lemma1 = tf1.lemma && c.lemma1_tag = tf1.tag) 
            JOIN token_freqs tf2 ON (c.lemma2 = tf2.lemma && c.lemma2_tag = tf2.tag) 
            WHERE 
                lemma1 = %s AND lemma2 = %s;"""
        params = (lemma1, lemma2)
        return list(filter(lambda c: c.has_mwe == 1, map(lambda i: Coocc(*i), self.__fetchall(query, params))))
