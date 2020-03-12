#!/usr/bin/python
import json
import logging

logger = logging.getLogger('wordprofile.spec')


class WpSeSpec:
    """
    Hilfsklasse für das einlesen der Spezifikation
    """

    def __init__(self, fname):
        self.strRelDesc = ""
        self.strRelDescDetail = ""
        self.mapRelDesc = {}
        self.mapRelDescDetail = {}
        self.listRelOrder = []
        self.mapRelOrder = {}
        self.mapVariation = {}

        config = json.load(open(fname, 'r'))

        self.strRelDesc = config['RelDescDefault'][0]
        self.strRelDescDetail = config['RelDescDefault'][1]
        for rel, (desc, detail) in config['RelDesc'].items():
            self.mapRelDesc[rel] = desc
            self.mapRelDescDetail[rel] = detail

        self.listRelOrder = config['RelOrderDefault']
        for rel, ordering in config['RelOrder'].items():
            self.mapRelOrder[rel] = ordering

        try:
            logger.info("read variation list %s" % (config['Variations']))
            with open(config['Variations'], 'r', encoding='utf-8') as variations_file:
                for line in variations_file:
                    line = line.strip().split('\t')
                    if len(line) == 2:
                        if line[0] not in self.mapVariation:
                            self.mapVariation[line[0]] = line[1]
        except FileNotFoundError:
            logger.error("unknown variation file:" + line)
