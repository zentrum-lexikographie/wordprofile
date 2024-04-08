import logging
from typing import List

import pymysql

import wordprofile.config
from wordprofile.datatypes import Concordance, Coocc, LemmaInfo
from wordprofile.errors import InternalError
from wordprofile.utils import split_relation_inversion

pymysql.install_as_MySQLdb()
import MySQLdb

logger = logging.getLogger("wordprofile.mysql")


class WPConnect:
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
        except (MySQLdb.Error, MySQLdb.Warning) as e:
            logger.exception(e)
            return []
        finally:
            self.__close_connection()
        return res

    def get_db_infos(self):
        query = """SELECT TABLE_NAME, TABLE_ROWS, CREATE_TIME, UPDATE_TIME
                   FROM information_schema.tables WHERE table_schema = DATABASE();"""
        return [
            {"name": t[0], "rows": t[1], "create_time": t[2], "last_update": t[3]}
            for t in self.__fetchall(query)
            if t[1]
        ]

    def get_label_frequencies(self):
        query = """SELECT label, freq FROM corpus_freqs;"""
        return {t[0]: t[1] for t in self.__fetchall(query)}

    def get_tag_frequencies(self):
        query = """
        SELECT tag, SUM(freq)
        FROM token_freqs tf
        GROUP BY tag;"""
        return {t[0]: t[1] for t in self.__fetchall(query)}

    def get_corpus_file_stats(self):
        query = """
        SELECT corpus, COUNT(*), min(`date`) as min_date, MAX(`date`) as max_date
        FROM corpus_files cf
        GROUP BY corpus;"""
        return {
            t[0]: {
                "count": t[1],
                "min_date": t[2],
                "max_date": t[3],
            }
            for t in self.__fetchall(query)
        }

    def get_concordances(
        self, coocc_id: int, use_context: bool, start_index: int, result_number: int
    ) -> List[Concordance]:
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
        if coocc_info.inverse:
            head_lemma, head_tag = coocc_info.lemma2, coocc_info.tag2
            dep_lemma, dep_tag = coocc_info.lemma1, coocc_info.tag1
        else:
            head_lemma, head_tag = coocc_info.lemma1, coocc_info.tag1
            dep_lemma, dep_tag = coocc_info.lemma2, coocc_info.tag2

        if use_context:
            query = """
            SELECT * FROM
            (SELECT
                s_center.sentence, matches.head_position, matches.dep_position, matches.prep_position, cf.corpus,
                cf.date, cf.text_class, cf.orig, cf.scan, cf.available,
                s_center.page, cf.file, 1, s_left.sentence AS 'left' , s_right.sentence AS 'right'
            FROM
                matches
            INNER JOIN collocations as c ON (matches.collocation_id = c.id)
            INNER JOIN corpus_files as cf ON (matches.corpus_file_id = cf.id)
            INNER JOIN concord_sentences as s_center ON
                (s_center.corpus_file_id = cf.id
                AND s_center.sentence_id = matches.sentence_id)
            LEFT JOIN concord_sentences as s_left ON
                (s_left.corpus_file_id = cf.id
                AND s_left.sentence_id = (matches.sentence_id-1))
            LEFT JOIN concord_sentences as s_right ON
                (s_right.corpus_file_id = cf.id
                AND s_right.sentence_id = (matches.sentence_id + 1))
            WHERE (
                c.label = %s AND
                c.lemma1 = %s AND
                c.lemma1_tag = %s AND
                c.lemma2 = %s AND
                c.lemma2_tag = %s
            )
            ORDER BY s_center.random_val
            LIMIT %s,%s)
            AS sample
            ORDER BY date DESC;
            """
        else:
            query = """
            SELECT *, '', '' FROM
            (SELECT
                s_center.sentence, matches.head_position, matches.dep_position, matches.prep_position, cf.corpus,
                cf.date, cf.text_class, cf.orig, cf.scan, cf.available,
                s_center.page, cf.file, 1
            FROM
                matches
            INNER JOIN collocations as c ON (matches.collocation_id = c.id)
            INNER JOIN corpus_files as cf ON (matches.corpus_file_id = cf.id)
            INNER JOIN concord_sentences as s_center ON
                (s_center.corpus_file_id = cf.id
                AND s_center.sentence_id = matches.sentence_id)
            WHERE (
                c.label = %s AND
                c.lemma1 = %s AND
                c.lemma1_tag = %s AND
                c.lemma2 = %s AND
                c.lemma2_tag = %s
            )
            ORDER BY s_center.random_val
            LIMIT %s,%s)
            as sample
            ORDER BY date DESC;
            """
        params = (
            coocc_info.rel,
            head_lemma,
            head_tag,
            dep_lemma,
            dep_tag,
            start_index,
            result_number,
        )
        return list(map(lambda i: Concordance(*i), self.__fetchall(query, params)))

    def get_lemma_and_pos(self, lemma: str, lemma_tag: str = "") -> List[LemmaInfo]:
        """Fetches lemma information for valid inputs.
        Args:
            lemma: Lemma of form [a-zA-Z-]
            lemma_tag (optional): Pos tag of lemma.

        Return:
            List of LemmaInfo that fits criteria.
        """
        if lemma_tag:
            query = """
            SELECT c.lemma1, tf.surface, c.lemma1_tag, c.label, SUM(c.frequency), c.inv
            FROM collocations c
            JOIN token_freqs tf on (c.lemma1 = tf.lemma && c.lemma1_tag = tf.tag)
            WHERE c.lemma1 = %s AND c.lemma1_tag = %s
            GROUP BY lemma1, lemma1_tag, label, inv;"""
            params = (lemma, lemma_tag)
        else:
            query = """
                SELECT c.lemma1, tf.surface, c.lemma1_tag, c.label, SUM(c.frequency), c.inv
                FROM collocations c
                JOIN token_freqs tf on (c.lemma1 = tf.lemma && c.lemma1_tag = tf.tag)
                WHERE c.lemma1 = %s
                GROUP BY lemma1, lemma1_tag, label, inv;"""
            params = (lemma,)
        return list(
            filter(
                lambda l: l.lemma.lower() == lemma.lower(),
                map(lambda i: LemmaInfo(*i), self.__fetchall(query, params)),
            )
        )

    def get_relation_by_id(self, coocc_id: int, min_freq: int = 1) -> Coocc:
        """Fetches collocation information for collocation id from database backend.

        Args:
            coocc_id: Collocation id for concordances.
            min_freq: Minimal number of occurrences for multi word expression

        Return:
            Collocation information.
        """
        query = """
        SELECT
            c.id, c.label, c.lemma1, c.lemma2, tf1.surface, tf2.surface, c.lemma1_tag, c.lemma2_tag,
            IFNULL(c.frequency, 0) as frequency, IFNULL(c.score, 0.0) as log_dice, inv,
            IF(ABS(c.id) IN (SELECT collocation1_id FROM mwe WHERE frequency >= %s), 1, 0) as has_mwe,
            (SELECT COUNT(*) FROM matches m WHERE m.collocation_id = ABS(c.id)) as num_concords
        FROM collocations c
        JOIN token_freqs tf1 ON (c.lemma1 = tf1.lemma && c.lemma1_tag = tf1.tag)
        JOIN token_freqs tf2 ON (c.lemma2 = tf2.lemma && c.lemma2_tag = tf2.tag)
        WHERE c.id = %s;
        """
        res = self.__fetchall(query, (min_freq, coocc_id))
        if len(res) == 0:
            raise ValueError("Invalid Id")
        elif len(res) > 1:
            raise InternalError(f"Too many results for coocc id {coocc_id}.")
        else:
            return Coocc(*res[0])

    def get_relation_tuples(
        self,
        lemma1: str,
        lemma1_tag: str,
        start: int,
        number: int,
        order_by: str,
        min_freq: int,
        min_stat: float,
        relation: str,
    ) -> List[Coocc]:
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
            relation: relation label.

        Return:
            List of Coocc.
        """
        relation, inv = split_relation_inversion(relation)
        query = f"""
        SELECT
            c.id, c.label, c.lemma1, c.lemma2, tf1.surface, tf2.surface, c.lemma1_tag, c.lemma2_tag,
            IFNULL(c.frequency, 0) as frequency, IFNULL(c.score, 0.0) as log_dice, inv,
            IF(ABS(c.id) IN (SELECT collocation1_id FROM mwe WHERE frequency >= %s), 1, 0) as has_mwe,
            (SELECT COUNT(*) FROM matches m WHERE m.collocation_id = ABS(c.id)) as num_concords
        FROM collocations c
        JOIN token_freqs tf1 ON (c.lemma1 = tf1.lemma && c.lemma1_tag = tf1.tag)
        JOIN token_freqs tf2 ON (c.lemma2 = tf2.lemma && c.lemma2_tag = tf2.tag)
        WHERE
            lemma1 = %s AND lemma1_tag = %s
            AND label = %s AND inv = %s
            AND frequency >= %s AND c.score >= %s
        ORDER BY {order_by} DESC LIMIT %s,%s;
        """
        params = (
            min_freq,
            lemma1,
            lemma1_tag,
            relation,
            inv,
            min_freq,
            min_stat,
            start,
            number,
        )
        return list(map(lambda i: Coocc(*i), self.__fetchall(query, params)))

    def get_relation_meta(
        self,
        lemma1: str,
        lemma1_tag: str,
        start: int,
        number: int,
        order_by: str,
        min_freq: int,
        min_stat: float,
        relations: List[str],
    ) -> List[Coocc]:
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
        query = f"""
        SELECT
            c.id, c.label, c.lemma1, c.lemma2, tf1.surface, tf2.surface, c.lemma1_tag, c.lemma2_tag,
            IFNULL(c.frequency, 0) as frequency, IFNULL(c.score, 0.0) as log_dice, inv, 0,
            (SELECT COUNT(*) FROM matches m WHERE m.collocation_id = ABS(c.id)) as num_concords
        FROM collocations c
        JOIN token_freqs tf1 ON (c.lemma1 = tf1.lemma && c.lemma1_tag = tf1.tag)
        JOIN token_freqs tf2 ON (c.lemma2 = tf2.lemma && c.lemma2_tag = tf2.tag)
        WHERE
            lemma1 = %s AND lemma1_tag = %s
            AND label NOT IN ('VZ', 'PP')
            AND frequency >= %s AND c.score >= %s
        ORDER BY {order_by} DESC LIMIT %s,%s;
        """
        params = (lemma1, lemma1_tag, min_freq, min_stat, start, number)
        relation_filter = {split_relation_inversion(relation) for relation in relations}
        return list(
            filter(
                lambda c: (c.rel, c.inverse) in relation_filter,
                map(lambda i: Coocc(*i), self.__fetchall(query, params)),
            )
        )

    def get_relation_tuples_diff(
        self,
        lemma1: str,
        lemma2: str,
        lemma_tag: str,
        relation: str,
        order_by: str,
        min_freq: int,
        min_stat,
    ) -> List[Coocc]:
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
        relation, inv = split_relation_inversion(relation)
        query = f"""
        SELECT
            c.id, c.label, c.lemma1, c.lemma2, tf1.surface, tf2.surface, c.lemma1_tag, c.lemma2_tag,
            IFNULL(c.frequency, 0) as frequency, IFNULL(c.score, 0.0) as log_dice, c.inv,
            IF(ABS(c.id) IN (SELECT collocation1_id FROM mwe WHERE frequency >= %s), 1, 0) as has_mwe,
            (SELECT COUNT(*) FROM matches m WHERE m.collocation_id = ABS(c.id)) as num_concords
        FROM collocations c
        JOIN token_freqs tf1 ON (c.lemma1 = tf1.lemma && c.lemma1_tag = tf1.tag)
        JOIN token_freqs tf2 ON (c.lemma2 = tf2.lemma && c.lemma2_tag = tf2.tag)
        WHERE
            c.lemma1 IN (%s, %s) AND c.lemma1_tag = %s
            AND c.label = %s AND c.inv = %s
            AND c.frequency >= %s AND c.score >= %s
        ORDER BY {order_by} DESC;"""
        params = (
            min_freq,
            lemma1,
            lemma2,
            lemma_tag,
            relation,
            inv,
            min_freq,
            min_stat,
        )
        return list(map(lambda i: Coocc(*i), self.__fetchall(query, params)))

    def get_relation_tuples_diff_meta(
        self,
        lemma1: str,
        lemma2: str,
        lemma_tag: str,
        order_by: str,
        min_freq: int,
        min_stat,
        relations: List[str],
    ) -> List[Coocc]:
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
        query = f"""
        SELECT
            c.id, c.label, c.lemma1, c.lemma2, tf1.surface, tf2.surface, c.lemma1_tag, c.lemma2_tag,
            IFNULL(c.frequency, 0) as frequency, IFNULL(c.score, 0.0) as log_dice, c.inv, 0,
            (SELECT COUNT(*) FROM matches m WHERE m.collocation_id = ABS(c.id)) as num_concords
        FROM collocations c
        JOIN token_freqs tf1 ON (c.lemma1 = tf1.lemma && c.lemma1_tag = tf1.tag)
        JOIN token_freqs tf2 ON (c.lemma2 = tf2.lemma && c.lemma2_tag = tf2.tag)
        WHERE
            c.lemma1 IN (%s, %s) AND c.lemma1_tag = %s
            AND c.frequency >= %s AND c.score >= %s
            AND label NOT IN ('VZ', 'PP')
        ORDER BY {order_by} DESC;"""
        params = (lemma1, lemma2, lemma_tag, min_freq, min_stat)
        relation_filter = {split_relation_inversion(relation) for relation in relations}
        return list(
            filter(
                lambda c: (c.rel, c.inverse) in relation_filter,
                map(lambda i: Coocc(*i), self.__fetchall(query, params)),
            )
        )
