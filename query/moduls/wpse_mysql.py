#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys

import MySQLdb

from .MMap import MMap

"""
  Hilfsklasse für die Kommunikation mit MySQL und für die Bereitstellung bestimmter Mappings, die sich aus der Wortprofil-Datenbank ergeben
"""


class WpSeMySql:
    conn = 0
    cursor = 0
    strHost = ''
    strUser = ''
    strPasswd = ''
    strDatabase = ''
    iPort = 3306

    iMweDepth = 0
    mapIdToCorpus = {}
    mapCorpusToId = {}
    mapIdToAvail = {}
    mapAvailToId = {}
    mapIdToTextclass = {}
    mapTextclassToId = {}
    mapRelIdToType = {}
    mapRelToId = {}
    mapIdToRel = {}
    mapIdToPOS = {}
    mapPosToId = {}
    mapIdToDate = {}
    mapTypeToValue = {}
    mapProjectInfo = {}
    mapRelInfo = {}
    mapThresholdInfo = {}

    vCorpusName = []

    bReloadMmap = False
    strTablePath = ""

    bHasHit = False

    mmapIdToLem = None
    mmapIdToSurf = None

    def __error(self, strObj):
        print("):", strObj)

    def __status(self, strObj):
        print("|:", strObj)

    """
      Initialisieren und Laden bestimmter Mappings aus der Wortprofil-Datenbank
    """

    def __init__(self, CWpSpec, bReloadMmap):
        self.strHost = CWpSpec.strHost
        self.strSocket = CWpSpec.strSocket
        self.strUser = CWpSpec.strUser
        self.strPasswd = CWpSpec.strPasswd
        self.strDatabase = CWpSpec.strDatabase
        self.iPort = CWpSpec.iPort
        self.strTablePath = CWpSpec.strTablePath

        self.bReloadMmap = bReloadMmap

    """
      Prüfen, ob eine Verbindung zu MySQL besteht
    """

    def check_connection(self):
        self.connect()
        bSucc = self.execute("show tables;")
        self.disconnect()
        return bSucc

    def init_data(self):

        ### informationen über die Tablellen
        self.__calc_table_info()

        ### Kookkurrenzbezogene Mappings
        self.__calc_corpus_mapping()
        self.__calc_rel_mapping()
        self.__calc_pos_mapping()
        self.__calc_types_mapping()

        ### Projektinformationen
        self.__calc_project_info()
        self.__calc_rel_info()
        self.__calc_threshold_info()
        self.__calc_corpus_name()

        ### Mappings, die in mmap geladen werden
        self.__calc_lemma_mapping()
        self.__calc_surface_mapping()

        ### Texttrefferbezogene Mappings
        if self.bHasHit:
            self.__calc_avail_mapping()
            self.__calc_textclass_mapping()
            self.__calc_date_mapping()
            self.__calc_tei_types_mapping()

        ### Definieren von MySQL-Funktionen
        # if self.iMweDepth>0:
        self.__define_functions()

        ### Tabellen für den temporären Gebrauch erstellen
        self.__create_tmp_tables()

    """
     für ein Integer den unsigned-MySQL-Typ ermitteln
    """

    def __get_type(self, iSize):
        if iSize <= 255:
            return "TINYINT unsigned NOT NULL"
        elif iSize <= 65535:
            return "SMALLINT unsigned NOT NULL"
        elif iSize <= 16777215:
            return "MEDIUMINT unsigned NOT NULL"
        elif iSize <= 4294967295:
            return "INT unsigned NOT NULL"
        else:
            return "BIGINT unsigned NOT NULL"

    """
     für ein Integer den signed-MySQL-Typ ermitteln
    """

    def __get_type_signed(self, iSize):
        if iSize <= 127:
            return "TINYINT signed NOT NULL"
        elif iSize <= 32767:
            return "SMALLINT signed NOT NULL"
        elif iSize <= 8388607:
            return "MEDIUMINT signed NOT NULL"
        elif iSize <= 2147483647:
            return "INT signed NOT NULL"
        else:
            return "BIGINT signed NOT NULL"

    """
     für einen String (anhand der Länge) den MySQL-Typ ermitteln
    """

    def __get_type_char(self, iLength):
        if iLength > 4294967295:
            print("text zu groß")
            sys.exit(-1)
        elif iLength > 16777215:
            return "LONGTEXT BINARY NOT NULL"
        elif iLength > 65535:
            return "MEDIUMTEXT BINARY NOT NULL"
        elif iLength > 255:
            return "TEXT BINARY NOT NULL"
        else:
            return "CHAR(" + str(iLength) + ") BINARY NOT NULL"

    """
     MySQL-Abfrage ausführen
    """

    def execute(self, strQuery):
        try:
            self.cursor.execute(strQuery)
        except:
            if self.connect():
                self.__status("connect to MYSQL")
                self.cursor.execute(strQuery)
            else:
                self.__error("MySQL ist nicht erreichbar")
                return False
        return True

    """
     MySQL-Ergebnis abfragen
    """

    def fetchall(self):
        return self.cursor.fetchall()

    """
     mit MySQL verbinden
    """

    def connect(self):
        try:
            if self.strHost == None:
                self.conn = MySQLdb.connect(
                    unix_socket=self.strSocket,
                    user=self.strUser,
                    passwd=self.strPasswd,
                    port=self.iPort,
                    db=self.strDatabase)
            else:
                self.conn = MySQLdb.connect(
                    host=self.strHost,
                    user=self.strUser,
                    passwd=self.strPasswd,
                    port=self.iPort,
                    db=self.strDatabase)
            self.cursor = self.conn.cursor()
            return True
        except:
            return False

    """
     MySQL-Verbindung trennen
    """

    def disconnect(self):
        try:
            self.cursor.close()
            self.conn.close()
            return True
        except:
            return False

    """
     Liste von Relation-Ids in das Arbument eines In-Statements umwandeln
    """

    def list_2_in(self, listRel):
        strRelId = ""
        for i in listRel:
            if strRelId != "":
                strRelId += ","
            strRelId += str(i)
        strRelId = "( " + strRelId + " )"
        return strRelId

    """
      Prüfen, welche Tiefe die MWE-Relationen haben und ob Texttrefferinformationen vorliegen
    """

    def __calc_table_info(self):
        try:
            self.connect()
            self.execute("SET NAMES 'utf8';")
            self.execute("show tables;")
            resDummy = self.cursor.fetchall()
            setTable = set()
            for i in resDummy:
                setTable.add(i[0])

            self.iMweDepth = 0
            while True:
                if "ConditionalCheck_" + str(self.iMweDepth + 1) in setTable:
                    self.iMweDepth += 1
                else:
                    break

            if "idToInfo" in setTable:
                self.bHasHit = True
            else:
                self.bHasHit = False

            self.disconnect()
        except:
            self.__error("MySQL: MWE depth failed")

    """
      Abfragen und ablegen des Korpus-Mapping
    """

    def __calc_corpus_mapping(self):
        try:
            self.connect()
            self.execute("SET NAMES 'utf8';")
            self.execute("Select * From idToCorpus")
            resDummy = self.cursor.fetchall()
            self.disconnect()
            self.mapIdToCorpus[None] = None
            for i in resDummy:
                self.mapCorpusToId[i[1]] = i[0]
                self.mapIdToCorpus[i[0]] = i[1]
        except:
            self.__error("MySQL: corpus mapping failed")

    """
      Abfragen und ablegen des Avail-Mapping
    """

    def __calc_avail_mapping(self):
        try:
            self.connect()
            self.execute("SET NAMES 'utf8';")
            self.execute("Select * From idToAvail")
            resDummy = self.cursor.fetchall()
            self.disconnect()
            for i in resDummy:
                self.mapAvailToId[i[1]] = i[0]
                self.mapIdToAvail[i[0]] = i[1]
        except:
            self.__error("MySQL: avail mapping failed")
            pass

    """
      Abfragen und ablegen des Textklassen-Mapping
    """

    def __calc_textclass_mapping(self):
        try:
            self.connect()
            self.execute("SET NAMES 'utf8';")
            self.execute("Select * From idToTextclass")
            resDummy = self.cursor.fetchall()
            self.disconnect()
            for i in resDummy:
                self.mapTextclassToId[i[1]] = i[0]
                self.mapIdToTextclass[i[0]] = i[1]
        except:
            self.__error("MySQL: textclass mapping failed")
            pass

    """
      Abfragen und ablegen des Relationen-Mapping
    """

    def __calc_rel_mapping(self):
        try:
            self.connect()
            self.execute("SET NAMES 'utf8';")
            self.execute("Select * From idToFunction")
            resDummy = self.cursor.fetchall()
            self.disconnect()
            self.mapIdToRel[None] = None
            for i in resDummy:
                self.mapRelToId[i[1]] = i[0]
                self.mapIdToRel[i[0]] = i[1]
                self.mapRelIdToType[i[0]] = i[2]
        except:
            self.__error("MySQL: relation mapping failed")
            pass

    """
      Abfragen und ablegen des Wortarten-Mapping
    """

    def __calc_pos_mapping(self):
        try:
            self.connect()
            self.execute("SET NAMES 'utf8';")
            self.execute("Select * From idToPOS")
            resDummy = self.cursor.fetchall()
            self.disconnect()
            for i in resDummy:
                self.mapIdToPOS[i[0]] = i[1]
                self.mapPosToId[i[1]] = i[0]
        except:
            self.__error("MySQL: pos mapping failed")
            pass

    """
      Abfragen und ablegen des Datum-Mapping
    """

    def __calc_date_mapping(self):
        try:
            self.connect()
            self.execute("SET NAMES 'utf8';")
            self.execute("Select * From idToDate")
            resDummy = self.cursor.fetchall()
            self.disconnect()
            for i in resDummy:
                self.mapIdToDate[i[0]] = i[1]
        except:
            self.__error("MySQL: date mapping failed")
            pass

    """
      Abfragen und ablegen der Typ-Informationen
    """

    def __calc_types_mapping(self):
        try:
            self.connect()
            self.execute("SET NAMES 'utf8';")
            self.execute("Select * From types")
            resDummy = self.cursor.fetchall()
            self.disconnect()
            for i in resDummy:
                self.mapTypeToValue[i[0]] = i[1]
        except:
            self.__error("MySQL: type mapping failed")
            pass

    """
      Abfragen und ablegen der TEI-Typ-Informationen
    """

    def __calc_tei_types_mapping(self):
        try:
            self.connect()
            self.execute("SET NAMES 'utf8';")
            self.execute("Select * From teiTypes")
            resDummy = self.cursor.fetchall()
            self.disconnect()
            for i in resDummy:
                self.mapTypeToValue[i[0]] = i[1]
        except:
            self.__error("MySQL: teiType mapping failed")
            pass

    """
      Abfragen und ablegen der Projekt-Informationen
    """

    def __calc_project_info(self):
        try:
            self.connect()
            self.execute("SET NAMES 'utf8';")
            self.execute("Select * From Info")
            resDummy = self.cursor.fetchall()
            self.disconnect()
            for i in resDummy:
                self.mapProjectInfo[i[0]] = i[1]
        except:
            self.__error("MySQL: project info failed")
            pass

    """
      Abfragen und ablegen der Relation-Informationen (Frequenzen und co.)
    """

    def __calc_rel_info(self):
        try:
            self.connect()
            self.execute("SET NAMES 'utf8';")
            self.execute("Select * From relInfo")
            resDummy = self.cursor.fetchall()
            self.disconnect()
            for i in resDummy:
                strRel = self.mapIdToRel[i[0]]
                mapDummy = {}
                mapDummy['Count'] = int(i[1])
                mapDummy['Frequency'] = int(i[2])
                mapDummy['ConcordNo'] = int(i[3])
                mapDummy['Name'] = strRel
                self.mapRelInfo[strRel] = mapDummy
        except:
            self.__error("MySQL: rel info failed")
            pass

    """
      Abfragen und ablegen der Schwellwert-Informationen
    """

    def __calc_threshold_info(self):
        try:
            self.connect()
            self.execute("SET NAMES 'utf8';")
            self.execute("Select * From threshold")
            resDummy = self.cursor.fetchall()
            self.disconnect()
            for i in resDummy:
                strRel = self.mapIdToRel[i[0]]
                if strRel in self.mapThresholdInfo:
                    self.mapThresholdInfo[strRel][i[1]] = float(i[2])
                else:
                    mapDummy = {}
                    mapDummy[i[1]] = i[2]
                    self.mapThresholdInfo[strRel] = mapDummy
        except:
            self.__error("MySQL: threshold info failed")
            pass

    """
      Abfragen und ablegen verwendeten Korpusnamen
    """

    def __calc_corpus_name(self):
        try:
            self.connect()
            self.execute("SET NAMES 'utf8';")
            self.execute("Select * From CorpusName")
            resDummy = self.cursor.fetchall()
            self.disconnect()
            for i in resDummy:
                self.vCorpusName.append(i[1])
            self.vCorpusName.sort()
        except:
            self.__error("MySQL: corpus name failed")

    """
      Abfragen und ablegen (MMap) des Lemma-Mappings
    """

    def __calc_lemma_mapping(self):
        # try:
        self.mmapIdToLem = MMap(self.strTablePath, "mapping_lemma")
        if not os.path.isfile(self.strTablePath + "/mapping_lemma.dat") or self.bReloadMmap:
            self.__status("generate mmap")
            self.connect()
            self.execute("SET NAMES 'utf8';")
            self.execute("Select * From lemmaToRelation")
            listDummy = self.cursor.fetchall()
            self.disconnect()
            self.mmapIdToLem.generate_index_from_list(listDummy)
        self.mmapIdToLem.load()

    # except:
    #   self.__error("MySQL: lemma mapping failed")

    """
      Abfragen und ablegen (MMap) des Oberflächenform-Mappings
    """

    def __calc_surface_mapping(self):
        # try:
        self.mmapIdToSurf = MMap(self.strTablePath, "mapping_surface")
        if not os.path.isfile(self.strTablePath + "/mapping_surface.dat") or self.bReloadMmap:
            self.connect()
            self.execute("SET NAMES 'utf8';")
            self.execute("Select * From idToSurface")
            listDummy = self.cursor.fetchall()
            self.disconnect()
            self.mmapIdToSurf.generate_index_from_list(listDummy)
        self.mmapIdToSurf.load()

    # except:
    #     self.__error("surface mapping failed")

    """
      Einfache MySQL-Funktionen anlegen. Diese werden für die MWE-Abfragen benötigt, um die Treffer-Ids zu sortieren
    """

    def __define_functions(self):

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

    """
      Temporäre Tabellen für einige komplexere Wortprofil-Abfragen erstellen
    """

    def __create_tmp_tables(self):

        self.connect()
        self.cursor.execute("SELECT type, value FROM types where type=\"highestFrequency\"")
        typeFrequency = self.__get_type_signed(self.cursor.fetchone()[1]);
        self.cursor.execute("SELECT type, value FROM types where type=\"logDiceLength\"")
        typelogDiceStr = str(self.cursor.fetchone()[1] + 2)
        self.cursor.execute("SELECT type, value FROM types where type=\"posSize\"")
        typePOSId = self.__get_type(self.cursor.fetchone()[1]);
        self.cursor.execute("SELECT type, value FROM types where type=\"lemmaSize\"")
        typeLemmaId = self.__get_type(self.cursor.fetchone()[1])
        self.cursor.execute("SELECT type, value FROM types where type=\"highestFunction\"")
        typeFunctionId = self.__get_type(self.cursor.fetchone()[1]);
        self.cursor.execute("SELECT type, value FROM types where type=\"InfoSize\"")
        typeInfoId = self.__get_type(self.cursor.fetchone()[1]);
        self.cursor.execute("SELECT type, value FROM types where type=\"highestTokenPositionW1\"")
        iTokenPositionW1 = self.cursor.fetchone()[1]
        typeTokenPositionW1 = self.__get_type(iTokenPositionW1);
        self.cursor.execute("SELECT type, value FROM types where type=\"highestTokenPositionW2\"")
        iTokenPositionW2 = self.cursor.fetchone()[1]
        typeTokenPositionW2 = self.__get_type(iTokenPositionW2);
        self.cursor.execute("SELECT type, value FROM types where type=\"highestPrepPosition\"")
        typePrepPosition = self.__get_type(self.cursor.fetchone()[1]);
        self.cursor.execute("SELECT type, value FROM types where type=\"highestSentence\"")
        typeSentence = self.__get_type(self.cursor.fetchone()[1]);
        self.cursor.execute("SELECT type, value FROM types where type=\"highestText\"")
        typeText = self.__get_type(self.cursor.fetchone()[1]);
        self.cursor.execute("SELECT type, value FROM types where type=\"corpusSize\"")
        typeCorpusId = self.__get_type(self.cursor.fetchone()[1]);
        typeDateId = "INT signed NOT NULL"
        typeDateDescId = "INT signed NOT NULL"
        self.disconnect()

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
            self.connect()
            self.execute("SET NAMES 'utf8';")
            self.execute("DROP TABLE IF EXISTS tmpMweList" + str(k))
            self.execute(strExecute)
            self.disconnect()

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
            self.connect()
            self.execute("SET NAMES 'utf8';")
            self.execute("DROP TABLE IF EXISTS tmpMweListCut_" + str(k))
            self.execute(strExecute)
            self.disconnect()

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
            self.connect()
            self.execute("SET NAMES 'utf8';")
            self.execute("DROP TABLE IF EXISTS tmpMateCut_" + str(k))
            self.execute(strExecute)
            self.disconnect()

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
            self.connect()
            self.execute("SET NAMES 'utf8';")
            self.execute("DROP TABLE IF EXISTS tmpMateCutSingle_" + str(k))
            self.execute(strExecute)
            self.disconnect()

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
            self.connect()
            self.execute("SET NAMES 'utf8';")
            self.execute("DROP TABLE IF EXISTS idToInfoConditionalOhneIndex_" + str(k))
            self.execute(strExecute)
            self.disconnect()

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
        self.connect()
        self.execute("SET NAMES 'utf8';")
        self.execute("DROP TABLE IF EXISTS tmpMate")
        self.execute(strExecute)
        self.disconnect()

    """
      Eine Präposition auf seine Id abbilden
    """

    def get_prep_id(self, strPrep):

        if strPrep == "*" or strPrep == "" or strPrep == "-":
            return -1

        self.connect()
        self.execute("SET NAMES 'utf8';")

        strSelect = "SELECT id "
        strFrom = "FROM lemmaToRelation "
        strWhere = "WHERE lemma=\"%s\"" % (strPrep)

        # print strSelect + strFrom + strWhere
        self.execute(strSelect + strFrom + strWhere)

        listResult = self.fetchall()
        # print listResult

        self.disconnect()

        if listResult != []:
            return listResult[0][0]
        else:
            return -1
