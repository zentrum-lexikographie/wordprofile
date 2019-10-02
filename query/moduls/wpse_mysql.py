#!/usr/bin/python
import logging
import sys

import MySQLdb

from moduls import deprecated
from moduls.wpse_spec import WpSeSpec

logger = logging.getLogger('wordprofile.mysql')


def get_type_unsigned(i):
    if i <= 255:
        return "TINYINT unsigned NOT NULL"
    elif i <= 65535:
        return "SMALLINT unsigned NOT NULL"
    elif i <= 16777215:
        return "MEDIUMINT unsigned NOT NULL"
    elif i <= 4294967295:
        return "INT unsigned NOT NULL"
    else:
        return "BIGINT unsigned NOT NULL"


def get_type_signed(i):
    if i <= 127:
        return "TINYINT signed NOT NULL"
    elif i <= 32767:
        return "SMALLINT signed NOT NULL"
    elif i <= 8388607:
        return "MEDIUMINT signed NOT NULL"
    elif i <= 2147483647:
        return "INT signed NOT NULL"
    else:
        return "BIGINT signed NOT NULL"


def get_type_char(c):
    if c > 4294967295:
        print("text zu groß")
        sys.exit(-1)
    elif c > 16777215:
        return "LONGTEXT BINARY NOT NULL"
    elif c > 65535:
        return "MEDIUMTEXT BINARY NOT NULL"
    elif c > 255:
        return "TEXT BINARY NOT NULL"
    else:
        return "CHAR(" + str(c) + ") BINARY NOT NULL"


class WpSeMySql:
    """
    Hilfsklasse für die Kommunikation mit MySQL und für die Bereitstellung bestimmter Mappings, die sich aus der Wortprofil-Datenbank ergeben
    """

    def __init__(self, wp_spec: WpSeSpec):
        self.host = wp_spec.host
        self.socket = wp_spec.socket
        self.user = wp_spec.user
        self.passwd = wp_spec.passwd
        self.dbname = wp_spec.dbname
        self.port = wp_spec.port
        self.table_path = wp_spec.table_path
        self.__cursor = None

        self.mwe_depth = 0
        self.mapIdToCorpus = {}
        self.mapCorpusToId = {}
        self.mapIdToAvail = {}
        self.mapAvailToId = {}
        self.mapIdToTextclass = {}
        self.mapTextclassToId = {}
        self.mapRelIdToType = {}
        self.mapRelToId = {}
        self.mapIdToRel = {}
        self.mapIdToPOS = {}
        self.mapPosToId = {}
        self.mapIdToDate = {}
        self.mapTypeToValue = {}
        self.mapProjectInfo = {}
        self.mapRelInfo = {}
        self.mapThresholdInfo = {}

        self.corpus_names = []
        self.table_path = ""
        self.has_hit = False

        self.mmapIdToLem = None
        self.mmapIdToSurf = None

        if self.host is None:
            self.__conn = MySQLdb.connect(
                unix_socket=self.socket,
                user=self.user,
                passwd=self.passwd,
                port=self.port,
                db=self.dbname)
        else:
            self.__conn = MySQLdb.connect(
                host=self.host,
                user=self.user,
                passwd=self.passwd,
                port=self.port,
                db=self.dbname)
        self.__cursor = self.__conn.cursor()
        self.execute("SET NAMES 'latin1';")

    def init_data(self):
        # informationen über die Tablellen
        self.__calc_table_info()
        # Kookkurrenzbezogene Mappings
        self.__calc_corpus_mapping()
        self.__calc_rel_mapping()
        self.__calc_pos_mapping()
        self.__calc_types_mapping()
        # Projektinformationen
        self.__calc_project_info()
        self.__calc_rel_info()
        self.__calc_threshold_info()
        self.__calc_corpus_name()
        # Mappings, die in mmap geladen werden
        self.__calc_lemma_mapping()
        self.__calc_surface_mapping()
        # Texttrefferbezogene Mappings
        if self.has_hit:
            self.__calc_avail_mapping()
            self.__calc_textclass_mapping()
            self.__calc_date_mapping()
            self.__calc_tei_types_mapping()
        # Definieren von MySQL-Funktionen
        if self.mwe_depth > 0:
            self.__define_functions()
        # Tabellen für den temporären Gebrauch erstellen
        self.__create_tmp_tables()

    def execute(self, query):
        self.__cursor.execute(query)

    def fetchall(self, query):
        self.__cursor.execute(query)
        return self.__cursor.fetchall()

    def connect(self):
        try:
            if self.host is None:
                self.__conn = MySQLdb.connect(
                    unix_socket=self.socket,
                    user=self.user,
                    passwd=self.passwd,
                    port=self.port,
                    db=self.dbname)
            else:
                self.__conn = MySQLdb.connect(
                    host=self.host,
                    user=self.user,
                    passwd=self.passwd,
                    port=self.port,
                    db=self.dbname)
            self.__cursor = self.__conn.cursor()
            self.execute("SET NAMES 'latin1';")
            return True
        except:
            return False

    @deprecated
    def list_2_in(self, listRel):
        """
         Liste von Relation-Ids in das Arbument eines In-Statements umwandeln
        """
        strRelId = ""
        for i in listRel:
            if strRelId != "":
                strRelId += ","
            strRelId += str(i)
        strRelId = "( " + strRelId + " )"
        return strRelId

    def __calc_table_info(self):
        """
          Prüfen, welche Tiefe die MWE-Relationen haben und ob Texttrefferinformationen vorliegen
        """
        table_names = {entry[0] for entry in self.fetchall("show tables;")}
        self.mwe_depth = 0
        while True:
            if "ConditionalCheck_" + str(self.mwe_depth + 1) in table_names:
                self.mwe_depth += 1
            else:
                break
        self.has_hit = "idToInfo" in table_names

    def __calc_corpus_mapping(self):
        """
          Abfragen und ablegen des Korpus-Mapping
        """
        try:
            self.mapIdToCorpus[None] = None
            for i in self.fetchall("Select * From idToCorpus"):
                self.mapCorpusToId[i[1]] = i[0]
                self.mapIdToCorpus[i[0]] = i[1]
        except:
            logger.error("MySQL: corpus mapping failed")

    def __calc_avail_mapping(self):
        """
        Abfragen und ablegen des Avail-Mapping
        """
        try:
            for i in self.fetchall("Select * From idToAvail"):
                self.mapAvailToId[i[1]] = i[0]
                self.mapIdToAvail[i[0]] = i[1]
        except:
            logger.error("MySQL: avail mapping failed")
            pass

    def __calc_textclass_mapping(self):
        """
        Abfragen und ablegen des Textklassen-Mapping
        """
        try:
            for i in self.fetchall("Select * From idToTextclass"):
                self.mapTextclassToId[i[1]] = i[0]
                self.mapIdToTextclass[i[0]] = i[1]
        except:
            logger.error("MySQL: textclass mapping failed")
            pass

    def __calc_rel_mapping(self):
        """
        Abfragen und ablegen des Relationen-Mapping
        """
        try:
            self.mapIdToRel[None] = None
            for i in self.fetchall("Select * From idToFunction"):
                self.mapRelToId[i[1]] = i[0]
                self.mapIdToRel[i[0]] = i[1]
                self.mapRelIdToType[i[0]] = i[2]
        except:
            logger.error("MySQL: relation mapping failed")
            pass

    def __calc_pos_mapping(self):
        """
        Abfragen und ablegen des Wortarten-Mapping
        """
        try:
            for i in self.fetchall("Select * From idToPOS"):
                self.mapIdToPOS[i[0]] = i[1]
                self.mapPosToId[i[1]] = i[0]
        except:
            logger.error("MySQL: pos mapping failed")
            pass

    def __calc_date_mapping(self):
        """
        Abfragen und ablegen des Datum-Mapping
        """
        try:
            for i in self.fetchall("Select * From idToDate"):
                self.mapIdToDate[i[0]] = i[1]
        except:
            logger.error("MySQL: date mapping failed")
            pass

    def __calc_types_mapping(self):
        """
          Abfragen und ablegen der Typ-Informationen
        """
        try:
            for i in self.fetchall("Select * From types"):
                self.mapTypeToValue[i[0]] = i[1]
        except:
            logger.error("MySQL: type mapping failed")
            pass

    def __calc_tei_types_mapping(self):
        """
        Abfragen und ablegen der TEI-Typ-Informationen
        """
        try:
            for i in self.fetchall("Select * From teiTypes"):
                self.mapTypeToValue[i[0]] = i[1]
        except:
            logger.error("MySQL: teiType mapping failed")
            pass

    def __calc_project_info(self):
        """
          Abfragen und ablegen der Projekt-Informationen
        """
        try:
            for i in self.fetchall("Select * From Info"):
                self.mapProjectInfo[i[0]] = i[1]
        except:
            logger.error("MySQL: project info failed")
            pass

    def __calc_rel_info(self):
        """
          Abfragen und ablegen der Projekt-Informationen
        """
        try:
            for i in self.fetchall("Select * From relInfo"):
                strRel = self.mapIdToRel[i[0]]
                mapDummy = {}
                mapDummy['Count'] = int(i[1])
                mapDummy['Frequency'] = int(i[2])
                mapDummy['ConcordNo'] = int(i[3])
                mapDummy['Name'] = strRel
                self.mapRelInfo[strRel] = mapDummy
        except:
            logger.error("MySQL: rel info failed")
            pass

    def __calc_threshold_info(self):
        """
          Abfragen und ablegen der Schwellwert-Informationen
        """
        try:
            for i in self.fetchall("Select * From threshold"):
                strRel = self.mapIdToRel[i[0]]
                if strRel in self.mapThresholdInfo:
                    self.mapThresholdInfo[strRel][i[1]] = float(i[2])
                else:
                    mapDummy = {}
                    mapDummy[i[1]] = i[2]
                    self.mapThresholdInfo[strRel] = mapDummy
        except:
            logger.error("MySQL: threshold info failed")
            pass

    def __calc_corpus_name(self):
        """
          Abfragen und ablegen verwendeten Korpusnamen
        """
        try:
            for i in self.fetchall("Select * From CorpusName"):
                self.corpus_names.append(i[1])
            self.corpus_names.sort()
        except:
            logger.error("MySQL: corpus name failed")

    def __calc_lemma_mapping(self):
        """
          Abfragen und ablegen (MMap) des Lemma-Mappings
        """
        if not self.mmapIdToLem:
            logger.info("generate mmap")
            self.mmapIdToLem = dict(self.fetchall("Select * From lemmaToRelation"))

    def __calc_surface_mapping(self):
        """
          Abfragen und ablegen (MMap) des Oberflächenform-Mappings
        """
        if not self.mmapIdToSurf:
            self.mmapIdToSurf = dict(self.fetchall("Select * From idToSurface"))

    def __define_functions(self):
        """
          Einfache MySQL-Funktionen anlegen. Diese werden für die MWE-Abfragen benötigt, um die Treffer-Ids zu sortieren
        """
        # func_order_initial(2230519,1871983) , func_order_middle(2230519,1871983,2704698) , func_order_final(2230519,2704698)
        self.execute("DROP FUNCTION IF EXISTS func_order_initial")
        self.execute("""
    CREATE FUNCTION func_order_initial(mate INT,id INT)
      RETURNS INT
      BEGIN

        IF mate < id THEN
          return mate;
        ELSE
          return id;
        END IF;

      END;""")

        self.execute("DROP FUNCTION IF EXISTS func_order_final")
        self.execute("""
    CREATE FUNCTION func_order_final(mate INT,id INT)
      RETURNS INT
      BEGIN

        IF mate < id THEN
          return id;
        ELSE
          return mate;
        END IF;

      END;""")

        self.execute("DROP FUNCTION IF EXISTS func_order_middle")
        self.execute("""
    CREATE FUNCTION func_order_middle(mate INT,id1 INT,id2 INT)
      RETURNS INT
      BEGIN

        IF mate < id1 THEN
          return id1;
        ELSE
          IF mate < id2 THEN
            return mate;
          ELSE
            return id2;
          END IF;
        END IF;

      END;""")

    def __create_tmp_tables(self):
        """
          Temporäre Tabellen für einige komplexere Wortprofil-Abfragen erstellen
        """
        self.execute("SELECT type, value FROM types where type=\"highestFrequency\"")
        typeFrequency = get_type_signed(self.__cursor.fetchone()[1])
        self.execute("SELECT type, value FROM types where type=\"logDiceLength\"")
        typelogDiceStr = str(self.__cursor.fetchone()[1] + 2)
        self.execute("SELECT type, value FROM types where type=\"posSize\"")
        typePOSId = get_type_unsigned(self.__cursor.fetchone()[1])
        self.execute("SELECT type, value FROM types where type=\"lemmaSize\"")
        typeLemmaId = get_type_unsigned(self.__cursor.fetchone()[1])
        self.execute("SELECT type, value FROM types where type=\"highestFunction\"")
        typeFunctionId = get_type_unsigned(self.__cursor.fetchone()[1])
        self.execute("SELECT type, value FROM types where type=\"InfoSize\"")
        typeInfoId = get_type_unsigned(self.__cursor.fetchone()[1])
        self.execute("SELECT type, value FROM types where type=\"highestTokenPositionW1\"")
        iTokenPositionW1 = self.__cursor.fetchone()[1]
        typeTokenPositionW1 = get_type_unsigned(iTokenPositionW1)
        self.execute("SELECT type, value FROM types where type=\"highestTokenPositionW2\"")
        iTokenPositionW2 = self.__cursor.fetchone()[1]
        typeTokenPositionW2 = get_type_unsigned(iTokenPositionW2)
        self.execute("SELECT type, value FROM types where type=\"highestPrepPosition\"")
        typePrepPosition = get_type_unsigned(self.__cursor.fetchone()[1])
        self.execute("SELECT type, value FROM types where type=\"highestSentence\"")
        typeSentence = get_type_unsigned(self.__cursor.fetchone()[1])
        self.execute("SELECT type, value FROM types where type=\"highestText\"")
        typeText = get_type_unsigned(self.__cursor.fetchone()[1])
        self.execute("SELECT type, value FROM types where type=\"corpusSize\"")
        typeCorpusId = get_type_unsigned(self.__cursor.fetchone()[1])
        typeDateId = "INT signed NOT NULL"
        typeDateDescId = "INT signed NOT NULL"

        strId = ""
        for k in range(1, self.iMweDepth + 1):
            strId += "id%s %s,\n" % (k, typeInfoId)
            strExecute = """
      CREATE TABLE tmpMweList""" + str(k) + """
      (
         """ + strId + """
         info TEXT
      )
      """
            self.execute("DROP TABLE IF EXISTS tmpMweList" + str(k))
            self.execute(strExecute)

        strId = ""
        for k in range(1, self.iMweDepth + 1):
            strId += "id%s %s,\n" % (k, typeInfoId)
            strExecute = """
      CREATE TABLE tmpMweListCut_""" + str(k) + """
      (
         mate """ + typeInfoId + """,
         frequency """ + typeFrequency + """,
         freqBelege """ + typeFrequency + """,
         logDice float(""" + typelogDiceStr + """,2),
         function """ + typeFunctionId + """,
         lemma """ + typeLemmaId + """,
         POS """ + typePOSId + """,
         """ + strId + """
         info TEXT
      )
      """
            self.execute("DROP TABLE IF EXISTS tmpMweListCut_" + str(k))
            self.execute(strExecute)

        strId = ""
        for k in range(1, self.iMweDepth + 1):
            strId += "id%s %s,\n" % (k, typeInfoId)
            strExecute = """
      CREATE TABLE tmpMateCut_""" + str(k) + """
      (
         mate """ + typeInfoId + """,
         frequency """ + typeFrequency + """,
         freqBelege """ + typeFrequency + """,
         logDice float(""" + typelogDiceStr + """,2),
         function """ + typeFunctionId + """,
         lemma """ + typeLemmaId + """,
         POS """ + typePOSId + """,
         """ + strId + """
         row_number INT unsigned NOT NULL
      )
      """
            self.execute("DROP TABLE IF EXISTS tmpMateCut_" + str(k))
            self.execute(strExecute)

        strId = ""
        for k in range(1, self.iMweDepth + 1):
            strId += "id%s %s,\n" % (k, typeInfoId)
            strExecute = """
      CREATE TABLE tmpMateCutSingle_""" + str(k) + """
      (
         mate """ + typeInfoId + """,
         frequency """ + typeFrequency + """,
         freqBelege """ + typeFrequency + """,
         logDice float(""" + typelogDiceStr + """,2),
         function """ + typeFunctionId + """,
         lemma """ + typeLemmaId + """,
         POS """ + typePOSId + """,
         """ + strId.rstrip(',\n') + """
      )
      """
            self.execute("DROP TABLE IF EXISTS tmpMateCutSingle_" + str(k))
            self.execute(strExecute)

        iOhneIndex = self.iMweDepth + 1
        for k in range(1, iOhneIndex):
            strPosition = ""
            for j in range(1, k + 2):
                strPosition += "tokenPosition1_" + str(j) + " " + typeTokenPositionW1 + ",\n"
                strPosition += "tokenPosition2_" + str(j) + " " + typeTokenPositionW2 + ",\n"
                strPosition += "prepPosition_" + str(j) + " " + typePrepPosition + ",\n"
            strExecute = """
      CREATE TABLE idToInfoConditionalOhneIndex_""" + str(k) + """
      (
       id """ + typeInfoId + """,
       """ + strPosition + """
       sentence """ + typeSentence + """,
       file """ + typeText + """,
       corpus """ + typeCorpusId + """,
       Date """ + typeDateId + """,
       DateDesc """ + typeDateDescId + """,
       Score INT NOT NULL
      )
      """
            self.execute("DROP TABLE IF EXISTS idToInfoConditionalOhneIndex_" + str(k))
            self.execute(strExecute)

        strExecute = """
    CREATE TABLE tmpMate
    (
       mate """ + typeInfoId + """,
       frequency """ + typeFrequency + """,
       freqBelege """ + typeFrequency + """,
       logDice float(""" + typelogDiceStr + """,2),
       function """ + typeFunctionId + """,
       lemma """ + typeLemmaId + """,
       POS """ + typePOSId + """
    )
    """
        self.execute("DROP TABLE IF EXISTS tmpMate")
        self.execute(strExecute)

    def get_prep_id(self, prep):
        """
          Eine Präposition auf seine Id abbilden
        """
        if prep == "*" or prep == "" or prep == "-":
            return -1
        query = """SELECT id 
                   FROM lemmaToRelation 
                   WHERE lemma='%s'""".format(prep)
        results = self.fetchall(query)
        if results:
            return results[0][0]
        else:
            return -1
