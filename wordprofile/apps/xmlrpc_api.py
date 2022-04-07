import logging
import socket
from socketserver import ForkingMixIn
from xmlrpc.server import SimpleXMLRPCServer

import wordprofile.config
from wordprofile.utils import configure_logger
from wordprofile.wp import Wordprofile

logger = logging.getLogger('wordprofile')


class ForkingXMLRPCServer(ForkingMixIn, SimpleXMLRPCServer):
    pass


class WordprofileXMLRPC:
    def __init__(self, db_host=None, db_user=None, db_passwd=None, db_name=None, db_port=None, wp_spec_file=None):
        self.wp = Wordprofile(db_host, db_user, db_passwd, db_name, wp_spec_file)

    def status(self):
        """Let icinga know the word profile is online.
        """
        logger.info("status request (icinga)")
        return "OK"

    def get_info(self):
        return self.wp.get_info_stats()

    def get_lemma_and_pos(self, params: dict):
        """Fetches lemma information from word-profile.

        Args:
            params:
                <Word>: Lemma of interest.
                <POS>: Pos tag of first lemma.
                <UseVariations> : Whether to use variations for either lemmas if not found in database.

        Returns:
            List of lemma-pos combinations with stats and possible relations.
        """
        logger.info(str(params))
        use_external_variations = bool(params.get('UseVariations', True))
        word = params.get("Word")
        pos = params.get("POS", "")
        return self.wp.get_lemma_and_pos(word, pos, use_external_variations)

    def get_lemma_and_pos_diff(self, params: dict):
        """Fetches lemma pairs with common pos tags from word-profile.

        Args:
            params:
                <Word1>: Lemma of interest.
                <Word2>: Lemma for comparison.
                <UseVariations>: Whether to use variations for either lemmas if not found in database.

        Returns:
            List of lemma1–lemma2 combinations with additional information such as frequency and relation.
        """
        logger.info(str(params))
        use_external_variations = bool(params.get('UseVariations', True))
        word_1 = params.get("Word1")
        word_2 = params.get("Word2")
        return self.wp.get_lemma_and_pos_diff(word_1, word_2, use_external_variations)

    def get_relations(self, params: dict):
        """Fetches collocations from word-profile.

        Args:
            params:
                <Lemma>: Lemma of interest, first collocate.
                <POS>: Pos tag of first lemma.
                <Lemma2> (optional): Second collocate.
                <Pos2Id> (optional): Pos tag of second lemma.
                <Relations> (optional): List of relation labels.
                <Start> (optional): Number of collocations to skip.
                <Number> (optional): Number of collocations to take.
                <OrderBy> (optional): Metric for ordering, frequency or log_dice.
                <MinFreq> (optional): Filter collocations with minimal frequency.
                <MinStat> (optional): Filter collocations with minimal stats score.

        Return:
            List of selected collocations grouped by relation.
        """
        logger.info(str(params))
        lemma = params["Lemma"]
        lemma2 = params.get("Lemma2", "")
        pos = params["POS"]
        pos2 = params.get("Pos2Id", "")
        relations = params.get("Relations", [])
        start = params.get("Start", 0)
        number = params.get("Number", 20)
        order_by = params.get("OrderBy", "logDice")
        order_by = 'log_dice' if order_by.lower() == 'logdice' else 'frequency'
        min_freq = params.get("MinFreq", 0)
        min_stat = params.get("MinStat", -100000000)
        return self.wp.get_relations(lemma, pos, lemma2, pos2, relations, start, number, order_by, min_freq, min_stat)

    def get_mwe_relations(self, params: dict):
        """Fetches mwe entries for a given hit id.

        Args:
            params:
                <ConcordId>: Hit id.
                <Start> (optional): Number of collocations to skip.
                <Number> (optional): Number of collocations to take.
                <OrderBy> (optional): Metric for ordering, frequency or log_dice.
                <MinFreq> (optional): Filter collocations with minimal frequency.
                <MinStat> (optional): Filter collocations with minimal stats score.

        Return:
            Dictionary of mwe relations for specific collocation parts.
                <parts>: List of Lemma-POS pairs
                <data>: Relations specifically for parts of the input.
        """
        logger.info(str(params))
        coocc_id = abs(int(str(params["ConcordId"]).strip("#")))
        start = params.get("Start", 0)
        number = params.get("Number", 20)
        order_by = params.get("OrderBy", "logDice")
        order_by = 'log_dice' if order_by.lower() == 'logdice' else 'frequency'
        min_freq = params.get("MinFreq", 0)
        min_stat = params.get("MinStat", -100000000)
        return self.wp.get_mwe_relations([coocc_id], start, number, order_by, min_freq, min_stat)

    @staticmethod
    def get_lemma_and_pos_by_list(params: dict):
        """For compatibility to old WP. Just pipes input to output."""
        logger.info(str(params))
        return params["Parts"]

    def get_mwe_relations_by_list(self, params: dict):
        """Fetches mwe entries for a given list of lemmas.

        Args:
            params:
                <Parts> (optional): List of lemmas.
                <Start> (optional): Number of collocations to skip.
                <Number> (optional): Number of collocations to take.
                <OrderBy> (optional): Metric for ordering, frequency or log_dice.
                <MinFreq> (optional): Filter collocations with minimal frequency.
                <MinStat> (optional): Filter collocations with minimal stats score.

        Return:
            Dictionary of mwe relations for specific collocation parts.
                <parts>: List of Lemma-POS pairs
                <data>: Relations specifically for parts of the input.
        """
        logger.info(str(params))
        parts = params["Parts"]
        start = params.get("Start", 0)
        number = params.get("Number", 20)
        order_by = params.get("OrderBy", "logDice")
        order_by = 'log_dice' if order_by.lower() == 'logdice' else 'frequency'
        min_freq = params.get("MinFreq", 0)
        min_stat = params.get("MinStat", -100000000)
        coocc_ids = self.wp.get_collocation_ids(parts[0], parts[1])
        return self.wp.get_mwe_relations(coocc_ids, start, number, order_by, min_freq, min_stat)

    def get_diff(self, params: dict):
        """Fetches collocations of common POS from word-profile and computes distances for comparison.

        Args:
            params:
                <LemmaId1>: Lemma of interest, first collocate.
                <LemmaId2>: Second collocate.
                <PosId>: Pos tag for both lemmas.
                <Relations> (optional): List of relation labels.
                <Number> (optional): Number of collocations to take.
                <OrderBy> (optional): Metric for ordering, frequency or log_dice.
                <MinFreq> (optional): Filter collocations with minimal frequency.
                <MinStat> (optional): Filter collocations with minimal stats score.
                <Operation> (optional): Lemma distance metric.
                <Intersection> (optional): If set, only the intersection of both lemma is computed.
                <NBest> (optional): Checks only the n highest scored lemmas.
        Return:
            List of collocation-diffs grouped by relation.
        """
        logger.info(str(params))
        lemma1 = params["LemmaId1"]
        lemma2 = params["LemmaId2"]
        pos = params["POS"]
        relations = params["Relations"]
        number = params.get("Number", 20)
        order_by = params.get("OrderBy", "logDice")
        order_by = 'log_dice' if order_by.lower() == 'logdice' else 'frequency'
        min_freq = params.get("MinFreq", -100000000)
        min_stat = params.get("MinStat", -100000000)
        operation = params.get("Operation", "adiff")
        use_intersection = params.get("Intersection", False)
        nbest = int(params.get("NBest", 0))
        return self.wp.get_diff(lemma1, lemma2, pos, relations, number, order_by, min_freq, min_stat, operation,
                                use_intersection, nbest)

    def get_intersection(self, params: dict):
        """Redirection for get_diff that sets parameters for intersection computation.

        Args:
            params:
                <LemmaId1>: Lemma of interest, first collocate.
                <LemmaId2>: Second collocate.
                <PosId>: Pos tag for both lemmas.
                <Relations> (optional): List of relation labels.
                <Number> (optional): Number of collocations to take.
                <OrderBy> (optional): Metric for ordering, frequency or log_dice.
                <MinFreq> (optional): Filter collocations with minimal frequency.
                <MinStat> (optional): Filter collocations with minimal stats score.
                <NBest> (optional): Checks only the n highest scored lemmas.
        Return:
            List of collocation-diffs grouped by relation.
        """
        logger.info(str(params))
        params['Operation'] = 'rmax'
        params['Intersection'] = True
        return self.get_diff(params)

    def get_relation_by_info_id(self, params: dict):
        """Fetches collocation information for a specific hit id.

        Args:
            params:
                <coocc_id>: DB index of the collocation.

        Returns:
            Returns a dictionary with collocation information.
        """
        # TODO check info_id inconsistency
        logger.info(str(params))
        coocc_id = int(str(params.get("InfoId")).strip("#"))
        return self.wp.get_relation_by_info_id(coocc_id)

    def get_concordances_and_relation(self, params: dict):
        """Fetches collocation information and concordances for a specified hit id.

        Args:
            params:
                <coocc_id>: Collocation id.
                <use_context> (optional): If true, returns surrounding sentences for matched collocation.
                <start_index> (optional): Collocation id.
                <result_number> (optional): Collocation id.

        Returns:
            Returns a dictionary with collocation information and their concordances.
        """
        logger.info(str(params))
        info_id = str(params.get("InfoId"))
        if info_id.startswith("#mwe"):
            return self.get_mwe_concordances_and_relation(params)
        coocc_id = int(info_id.strip("#"))
        use_context = bool(params.get("UseContext", False))
        start_index = params.get("Start", 0)
        result_number = params.get("Number", 20)
        return self.wp.get_concordances_and_relation(coocc_id, use_context, start_index, result_number)

    def get_mwe_concordances_and_relation(self, params: dict):
        """Fetches collocation information and concordances for a specified hit id.

        Args:
            params:
                <coocc_id>: Collocation id.
                <use_context> (optional): If true, returns surrounding sentences for matched collocation.
                <start_index> (optional): Collocation id.
                <result_number> (optional): Collocation id.

        Returns:
            Returns a dictionary with collocation information and their concordances.
        """
        logger.info(str(params))
        info_id = str(params.get("InfoId"))
        if info_id.startswith("#mwe"):
            info_id = info_id[len("#mwe"):]
        coocc_id = int(info_id.strip("#"))
        use_context = bool(params.get("UseContext", False))
        start_index = params.get("Start", 0)
        result_number = params.get("Number", 20)
        return self.wp.get_concordances_and_relation(coocc_id, use_context, start_index, result_number, is_mwe=True)


def main():
    configure_logger(logger, logging.DEBUG)

    # Create server
    server = ForkingXMLRPCServer(
        ('', wordprofile.config.XML_RPC_PORT),
        logRequests=False,
        allow_none=True
    )
    socket.setdefaulttimeout(30)
    # register function information
    server.register_introspection_functions()
    # register wortprofil
    server.register_instance(WordprofileXMLRPC())
    # Run the server's main loop
    server.serve_forever()


if __name__ == '__main__':
    main()
