#!/usr/bin/python3

import logging
from typing import List

import pymysql

from wordprofile.datatypes import CooccInfo, Coocc, Concordance, MweConcordance

pymysql.install_as_MySQLdb()
import MySQLdb

logger = logging.getLogger('wordprofile.mysql')


class WPMweConnect:
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

    def get_concordances(self, mwe_id: int, use_context: bool, start_index: int, result_number: int) -> List[
        Concordance]:
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
                m1.creation_date, cf.text_class, cf.orig, cf.scan, cf.available, 
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
            LIMIT {},{};
            """.format(mwe_id, start_index, result_number)
        else:
            query = """
            SELECT
                s_center.sentence, m1.head_position, m1.dep_position, m1.prep_position,
                m2.head_position, m2.dep_position, m2.prep_position, 
                cf.corpus, m1.creation_date, cf.text_class, cf.orig, cf.scan, cf.available, 
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
            LIMIT {},{};
            """.format(mwe_id, start_index, result_number)
        db_results = self.__fetchall(query)
        db_results: List[MweConcordance] = list(map(MweConcordance._make, db_results))
        return db_results

    def get_relation_by_id(self, mwe_id: int) -> CooccInfo:
        """Fetches collocation information for collocation id from database backend.

        Args:
            mwe_id: Collocation id for concordances.

        Return:
            Collocation information.
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
                         lemma2=db_result[2], pos1="{}-{}".format(db_result[7], db_result[8]), pos2=db_result[3], inv=0)

    def get_relation_tuples(self, coocc_ids: List[int], min_freq: int,
                            min_stat: float) -> List[Coocc]:
        min_freq_sql = " and (frequency) >= {} ".format(min_freq) if min_freq > 0 else ""
        min_stat_sql = " and (ld.value) >= {} ".format(min_stat) if min_stat > -1000 else ""
        sql = """
        SELECT
            mwe.id, mwe.label, mwe.lemma, mwe.lemma_tag, mwe.frequency, c.lemma1, c.lemma2, c.lemma1_tag, c.lemma2_tag
        FROM mwe
        JOIN collocations as c ON (mwe.collocation1_id = c.id)
        WHERE mwe.collocation1_id IN ({}) {} {} 
        """.format(",".join(map(str, coocc_ids)), min_freq_sql, min_stat_sql)
        db_results = self.__fetchall(sql)
        return [Coocc(RelId=i[0], Rel=i[1], Lemma1="{}-{}".format(i[5], i[6]), Lemma2=i[2],
                      Pos1="{}-{}".format(i[7], i[8]), Pos2=i[3], Frequency=i[4], LogDice=0, inverse=0)
                for i in db_results]
