import json
import logging

import wordprofile.config

logger = logging.getLogger('wordprofile.spec')


class WpSeSpec:
    """
    Hilfsklasse für das einlesen der Spezifikation
    """

    def __init__(self, fname=None):
        self.strRelDesc = ""
        self.strRelDescDetail = ""
        self.mapRelDesc = {}
        self.mapRelDescDetail = {}
        self.listRelOrder = []
        self.mapRelOrder = {}

        config = json.load(open(fname or wordprofile.config.SPEC, 'r'))

        self.strRelDesc = config['RelDescDefault'][0]
        self.strRelDescDetail = config['RelDescDefault'][1]
        for rel, (desc, detail) in config['RelDesc'].items():
            self.mapRelDesc[rel] = desc
            self.mapRelDescDetail[rel] = detail

        self.listRelOrder = config['RelOrderDefault']
        for rel, ordering in config['RelOrder'].items():
            self.mapRelOrder[rel] = ordering
