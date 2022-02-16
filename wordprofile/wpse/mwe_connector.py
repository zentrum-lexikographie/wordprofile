import logging
from typing import List

import pymysql

import wordprofile.config
from wordprofile.datatypes import CooccInfo, Coocc, MweConcordance

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
        self.__conn.commit()
        self.__cursor.close()
        self.__conn.close()

    def __fetchall(self, query):
        self.__init_connection()
        self.__cursor.execute(query)
        res = self.__cursor.fetchall()
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
                mwe_match.mwe_id = {}  
            ORDER BY cf.date DESC 
            LIMIT {},{};
            """.format(mwe_id, start_index, result_number)
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
                mwe_match.mwe_id = {}  
            ORDER BY cf.date DESC 
            LIMIT {},{};
            """.format(mwe_id, start_index, result_number)
        db_results = self.__fetchall(query)
        db_results: List[MweConcordance] = list(map(MweConcordance._make, db_results))
        return db_results

    def get_relation_by_id(self, mwe_id: int) -> CooccInfo:
        """Fetches MWE information for mwe id from database backend.

        Args:
            mwe_id: Collocation id for concordances.

        Return:
            MWE information.
        """
        sql = """
        SELECT
            mwe.id, mwe.label, mwe.lemma, mwe.lemma_tag, mwe.frequency, c.lemma1, c.lemma2, c.lemma1_tag, c.lemma2_tag
        FROM mwe
        JOIN collocations as c ON (mwe.collocation1_id = c.id)
        WHERE mwe.id = {}
        """.format(mwe_id)
        db_result = self.__fetchall(sql)[0]
        return CooccInfo(id=db_result[0], rel=db_result[1], lemma1="{}-{}".format(db_result[5], db_result[6]),
                         lemma2=db_result[2], pos1="{}-{}".format(db_result[7], db_result[8]), pos2=db_result[3], inv=0,
                         has_mwe=0)

    def get_relation_tuples(self, coocc_ids: List[int], min_freq: int, min_stat: float) -> List[Coocc]:
        """Fetches MWE with related statistics for a specific relation from database backend.

        Args:
            coocc_ids: List of Collocation ids, one per relation.
            min_freq: Filter collocations with minimal frequency.
            min_stat: Filter collocations with minimal stats score.

        Return:
            List of Coocc.
        """
        min_freq_sql = " and (mwe.frequency) >= {} ".format(min_freq) if min_freq > 0 else ""
        min_stat_sql = " and (mwe.score) >= {} ".format(min_stat) if min_stat > -1000 else ""
        sql = """
        SELECT
            mwe.id, mwe.label, mwe.lemma, mwe.lemma_tag, mwe.frequency, c.lemma1, c.lemma2, c.lemma1_tag, c.lemma2_tag, 
            IFNULL(mwe.score, 0.0) as log_dice
        FROM mwe
        JOIN collocations as c ON (mwe.collocation1_id = c.id)
        WHERE mwe.collocation1_id IN ({}) {} {} 
        ORDER BY log_dice DESC
        """.format(",".join(map(str, coocc_ids)), min_freq_sql, min_stat_sql)
        db_results = self.__fetchall(sql)
        return [Coocc(RelId=i[0], Rel=i[1], Lemma1="{}-{}".format(i[5], i[6]), Lemma2=i[2],
                      Pos1="{}-{}".format(i[7], i[8]), Pos2=i[3], Frequency=i[4], LogDice=i[9], inverse=0, has_mwe=0)
                for i in db_results]

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
                c.id, c.label, c.lemma1, c.lemma2, c.lemma1_tag, c.lemma2_tag, 
                IFNULL(c.frequency, 0) as frequency, IFNULL(c.score, 0.0) as log_dice, inv,
                IF(ABS(c.id) IN (SELECT collocation1_id FROM mwe), 1, 0) as has_mwe
            FROM 
                collocations c
            WHERE lemma1='{}' and lemma2='{}';""".format(
            lemma1, lemma2
        )
        db_results = self.__fetchall(query)
        return list(filter(lambda c: c.has_mwe == 1, map(Coocc._make, db_results)))
