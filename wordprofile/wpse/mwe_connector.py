import logging
from typing import List, Optional

import pymysql

import wordprofile.config
from wordprofile.datatypes import Coocc, MweConcordance

pymysql.install_as_MySQLdb()
import MySQLdb

logger = logging.getLogger("wordprofile.mysql")


class WPMweConnect:
    """Gives access to word profile database backend, following the repository pattern."""

    def __init__(self, host=None, user=None, passwd=None, dbname=None):
        self.__host = host or wordprofile.config.DB_HOST
        self.__user = user or wordprofile.config.DB_USER
        self.__passwd = passwd or str(wordprofile.config.DB_PASSWORD)
        self.__dbname = dbname or wordprofile.config.DB_NAME
        self.__conn = None
        self.__cursor = None

    def __init_connection(self):
        self.__conn = MySQLdb.connect(
            host=self.__host, user=self.__user, passwd=self.__passwd, db=self.__dbname
        )
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

    def get_concordances(
        self, mwe_id: int, start_index: int, result_number: int
    ) -> List[MweConcordance]:
        """Fetches concordances for collocation id from database backend.

        Args:
            mwe_id: Collocation id for concordances.
            start_index: Row index to start with.
            result_number: Number of results to return.

        Return:
            List of Concordance.
        """

        query = """
            SELECT *
            FROM
            (SELECT
                s_center.sentence, m1.head_position AS m1_head_pos,
                m1.dep_position AS m1_dep_pos, m1.prep_position AS m1_prep_pos,
                m2.head_position AS m2_head_pos, m2.dep_position AS m2_dep_pos,
                m2.prep_position AS m2_prep_pos,
                cf.corpus, cf.date, cf.orig, cf.available, cf.file
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
            ORDER BY s_center.random_val
            LIMIT %s,%s)
            as sample
            ORDER BY date DESC ;
            """
        params = (mwe_id, start_index, result_number)
        return list(map(lambda i: MweConcordance(*i), self.__fetchall(query, params)))

    def get_relation_by_id(self, mwe_id: int) -> Optional[Coocc]:
        """Fetches MWE information for mwe id from database backend.

        Args:
            mwe_id: Collocation id for concordances.

        Return:
            MWE information.
        """
        query = """
        SELECT
            mwe.id, mwe.label, mwe.lemma, mwe.lemma_tag, mwe.frequency, c.lemma1,
            c.lemma2, c.lemma1_tag, c.lemma2_tag, IFNULL(mwe.score, 0.0) as log_dice,
            tf_mwe.surface, tf1.surface, tf2.surface, mwe.inv, (SELECT COUNT(*)
            FROM mwe_match m WHERE m.mwe_id = ABS(mwe.id)) as num_concords,
            c2.preposition
        FROM mwe
        JOIN collocations as c ON (mwe.collocation1_id = c.id)
        JOIN collocations as c2 ON (mwe.collocation2_id = c2.id)
        JOIN token_freqs tf1 ON (c.lemma1 = tf1.lemma && c.lemma1_tag = tf1.tag)
        JOIN token_freqs tf2 ON (c.lemma2 = tf2.lemma && c.lemma2_tag = tf2.tag)
        JOIN token_freqs tf_mwe ON (mwe.lemma = tf_mwe.lemma && mwe.lemma_tag = tf_mwe.tag)
        WHERE mwe.id = %s;
        """
        params = (mwe_id,)
        res = self.__fetchall(query, params)
        if len(res) == 0:
            logger.info("Invalid Id: %d" % mwe_id)
            return None
        c = res[0]
        return Coocc(
            id=c[0],
            rel=c[1],
            lemma1="{}-{}".format(c[5], c[6]),
            lemma2=c[2],
            form1="{}-{}".format(c[11], c[12]),
            form2=c[10],
            tag1="{}-{}".format(c[7], c[8]),
            tag2=c[3],
            freq=c[4],
            score=c[9],
            inverse=c[13],
            has_mwe=0,
            num_concords=c[14],
            prep=c[15],
        )

    def get_relation_tuples(
        self, coocc_ids: List[int], order_by: str, min_freq: int, min_stat: float
    ) -> List[Coocc]:
        """Fetches MWE with related statistics for collocation ids from database.

        Args:
            coocc_ids: List of Collocation ids, one per relation.
            min_freq: Filter collocations with minimal frequency.
            min_stat: Filter collocations with minimal stats score.

        Return:
            List of Coocc.
        """
        sql = """
        SELECT
            mwe.id, mwe.label, mwe.lemma, mwe.lemma_tag, mwe.frequency, c.lemma1,
            c.lemma2, c.lemma1_tag, c.lemma2_tag, IFNULL(mwe.score, 0.0) as log_dice,
            tf_mwe.surface, tf1.surface, tf2.surface, mwe.inv,
            (SELECT COUNT(*) FROM mwe_match m WHERE m.mwe_id = ABS(mwe.id)) as num_concords,
            c2.preposition
        FROM mwe
        JOIN collocations as c ON (mwe.collocation1_id = c.id)
        JOIN collocations as c2 ON (mwe.collocation2_id = c2.id)
        JOIN token_freqs tf1 ON (c.lemma1 = tf1.lemma && c.lemma1_tag = tf1.tag)
        JOIN token_freqs tf2 ON (c.lemma2 = tf2.lemma && c.lemma2_tag = tf2.tag)
        JOIN token_freqs tf_mwe ON (mwe.lemma = tf_mwe.lemma && mwe.lemma_tag = tf_mwe.tag)
        WHERE
            mwe.collocation1_id IN ({})
            AND mwe.frequency >= %s
            AND mwe.score >= %s
        ORDER BY {} DESC;
        """.format(
            ",".join("%s" for _ in coocc_ids), order_by
        )
        params = coocc_ids + [min_freq, min_stat]
        return [
            Coocc(
                id=i[0],
                rel=i[1],
                lemma1="{}-{}".format(i[5], i[6]),
                lemma2=i[2],
                form1="{}-{}".format(i[11], i[12]),
                form2=i[10],
                tag1="{}-{}".format(i[7], i[8]),
                tag2=i[3],
                freq=i[4],
                score=i[9],
                inverse=i[13],
                has_mwe=0,
                num_concords=i[14],
                prep=i[15],
            )
            for i in self.__fetchall(sql, params)
        ]

    def get_collocations(self, lemma1: str, lemma2: str) -> List[tuple[int]]:
        """
        Fetches collocation ids for a pair of lemmas if they are MWE.

        Args:
            lemma1: First collocate.
            lemma2: Second collocate.

        Return:
            List of collocation ids.
        """
        query = """
            SELECT
                c.id
            FROM
                collocations c
            WHERE
                (lemma1 = %(lemma1)s AND lemma2 = %(lemma2)s)
                OR (lemma1 = %(lemma2)s AND lemma2 = %(lemma1)s)
                AND ABS(c.id) in (SELECT collocation1_id FROM mwe);"""
        params = {"lemma1": lemma1, "lemma2": lemma2}
        return list(self.__fetchall(query, params))
