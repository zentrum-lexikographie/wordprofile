#!/usr/bin/python
import logging

logger = logging.getLogger('wordprofile.spec')


class WpSeSpec:
    """
    Hilfsklasse für das einlesen der Spezifikation (TAB-separierte Datei) und das Bereitstellen der Parameter
    """

    def __init__(self, fname):
        self.table_path = ""
        self.strRelDesc = ""
        self.strRelDescDetail = ""
        self.mapRelDesc = {}
        self.mapRelDescDetail = {}
        self.listRelOrder = []
        self.mapRelOrder = {}
        self.listMweRelOrder = []
        self.mapMweRelOrder = {}
        self.user = ""
        self.host = None
        self.socket = ""
        self.passwd = ""
        self.dbname = ""
        self.port = 3306
        self.mapVariation = {}
        self.mapLemmaRepair = {}

        with open(fname, 'r', encoding='utf-8') as config:
            for config_line in config:
                setting = config_line.rstrip('\n').split('\t')
                if len(setting) > 1:
                    if setting[0] == 'TablePath':
                        self.table_path = setting[1]
                    if setting[0] == 'User':
                        self.user = setting[1]
                    elif setting[0] == 'Host':
                        self.host = setting[1]
                    elif setting[0] == 'Socket':
                        self.socket = setting[1]
                    elif setting[0] == 'Passwd':
                        self.passwd = setting[1]
                    elif setting[0] == 'Database':
                        self.dbname = setting[1]
                    elif setting[0] == 'Port':
                        self.port = int(setting[1])
                    elif setting[0] == 'RelDescDefault':
                        self.strRelDesc = setting[1]
                        self.strRelDescDetail = setting[2]
                    elif setting[0] == 'RelDesc':
                        self.mapRelDesc[setting[1]] = setting[2]
                        self.mapRelDescDetail[setting[1]] = setting[3]
                    elif setting[0] == 'RelOrderDefault':
                        self.listRelOrder = setting[1].split(',')
                    elif setting[0] == 'RelOrder':
                        self.mapRelOrder[setting[1]] = setting[2].split(',')
                    elif setting[0] == 'MweRelOrderDefault':
                        self.listMweRelOrder = setting[1].split(',')
                    elif setting[0] == 'MweRelOrder':
                        self.mapMweRelOrder[setting[1]] = setting[2].split(',')
                    elif setting[0] == 'Variations':
                        try:
                            # Load VariationFile
                            logger.info("read variation list %s" % (setting[1]))
                            with open(setting[1], 'r', encoding='utf-8') as variations_file:
                                for line in variations_file:
                                    line = line.strip().split('\t')
                                    if len(line) == 2:
                                        if line[0] not in self.mapVariation:
                                            self.mapVariation[line[0]] = line[1]
                        except FileNotFoundError:
                            logger.error("unknown variation file:" + line)
                    elif setting[0] == 'LemmaRepair':
                        try:
                            # Load LemmaRepairFile
                            logger.info("read lemma repair list %s" % (setting[2]))
                            for line in open(setting[2], 'r', encoding='utf-8'):
                                line = line.strip().split('\t')
                                if len(line) == 2:
                                    if line[0] not in self.mapLemmaRepair:
                                        self.mapLemmaRepair[(setting[1], line[0])] = line[1]
                        except FileNotFoundError:
                            logger.error("unknown lemma repair file:" + line)

        if self.table_path == "":
            logger.error("missing table-path")
