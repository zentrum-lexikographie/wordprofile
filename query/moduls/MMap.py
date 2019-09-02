#!/usr/bin/python
# -*- coding: utf-8 -*-

import mmap
import struct
import sys


####################################
# Klasse zum Abfragen von Daten über mmap
# 
# Die über MMap abgebildeten Listen müssen für einen Eintrag eine ID und einen Wert besitzen
# Die Listen müssen anhand der IDs sortiert sein und die IDs von 0 ab durchgängig durchgezählt sein
# Die daten können via Datei (tab getrennt) oder via Python-liste (Liste aus Zweiertupeln) eingespielt werden
class MMap:
    g_strTmpDir = ""
    g_strProjectName = ""
    g_mmStrung = None
    g_mmData = None

    g_mySprungBinary = None
    g_myDataBinary = None

    ######
    ### erstellen eines MMap objektes mit angabe des Ortes für den Index
    def __init__(self, strTmpDir, strProjectName):
        self.g_strTmpDir = strTmpDir
        self.g_strProjectName = strProjectName

    ######
    ### generieren des Index aus einer Tabellendatei (*.table -> *.jmp,*.dat)
    def generate_index_from_file(self, strFilename):

        myData = open(strFilename, "r")

        self.g_mySprungBinary = open("%s/%s%s" % (self.g_strTmpDir, self.g_strProjectName, ".jmp"), "wb")
        self.g_myDataBinary = open("%s/%s%s" % (self.g_strTmpDir, self.g_strProjectName, ".dat"), "wb")

        iPosition = 0
        iCount = 0
        for i in myData.readlines():
            mySplit = i.strip('\n').split('\t')
            iId = int(mySplit[0])
            if iId != iCount:
                print("): IDs sind nicht vortlaufend nummeriert")
                sys.exit(-1)
            strData = mySplit[1]
            iLen = len(strData)

            binSprung = struct.pack('@ l h', iPosition, iLen)

            self.g_mySprungBinary.write(binSprung)
            self.g_myDataBinary.write(strData)

            iPosition += len(strData)
            iCount += 1

        myData.close()
        self.g_mySprungBinary.close()
        self.g_myDataBinary.close()

    ######
    ### generieren des Index aus einer Liste (-> *.jmp,*.dat)
    def generate_index_from_list(self, listObj):

        self.g_mySprungBinary = open("%s/%s%s" % (self.g_strTmpDir, self.g_strProjectName, ".jmp"), "wb")
        self.g_myDataBinary = open("%s/%s%s" % (self.g_strTmpDir, self.g_strProjectName, ".dat"), "wb")

        iPosition = 0
        iCount = 0
        for i in listObj:
            iId = int(i[0])
            if iId != iCount:
                print("): IDs sind nicht vortlaufend nummeriert")
                sys.exit(-1)
            strData = i[1]
            iLen = len(strData)

            binSprung = struct.pack('@ l h', iPosition, iLen)

            self.g_mySprungBinary.write(binSprung)
            self.g_myDataBinary.write(strData)

            iPosition += len(strData)
            iCount += 1

        self.g_mySprungBinary.close()
        self.g_myDataBinary.close()

    ######
    ### laden des Index
    def load(self):

        self.g_mySprungBinary = open("%s/%s%s" % (self.g_strTmpDir, self.g_strProjectName, ".jmp"), "rb")
        self.g_myDataBinary = open("%s/%s%s" % (self.g_strTmpDir, self.g_strProjectName, ".dat"), "rb")

        self.g_mmSprung = mmap.mmap(self.g_mySprungBinary.fileno(), 0, prot=mmap.PROT_READ)
        self.g_mmData = mmap.mmap(self.g_myDataBinary.fileno(), 0, prot=mmap.PROT_READ)

    ######
    ### abfragen von Daten
    def get(self, iId):

        strData = self.g_mmSprung[iId * 10:(iId * 10 + 10)]
        pairSprung = struct.unpack('@ l h', strData)

        return self.g_mmData[pairSprung[0]:pairSprung[0] + pairSprung[1]]
