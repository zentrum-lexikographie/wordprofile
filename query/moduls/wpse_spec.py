#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
sys.path.append('./moduls')
sys.path.append('./xmlrpc/moduls')

import codecs

"""
  Hilfsklasse für das einlesen der Spezifikation (TAB-separierte Datei) und das Bereitstellen der Parameter
"""
class WpSeSpec:

  strTablePath=""
  strRelDesc=""
  strRelDescDetail=""
  mapRelDesc={}
  mapRelDescDetail={}
  listRelOrder=[]
  mapRelOrder={}
  listMweRelOrder=[]
  mapMweRelOrder={}
  strUser=""
  strHost=None
  strSocket=""
  strPasswd=""
  strDatabase=""
  iPort=3306
  mapVariation={}
  mapLemmaRepair={}


  def __error ( self, strObj ):
    print "):",strObj

  def __status ( self, strObj ):
    print "|:",strObj

  """
    Einlesen der Spezifikation
  """
  def read_specification ( self, strFilename ):

    ### Load SpecificationFile
    try:
      fileConfig = codecs.open(strFilename,'r','utf8')
    except:
      self.__error("unknown specification file:"+strFilename)
      sys.exit(-1)
    self.strHost=None
    for i in fileConfig.readlines():
      setting = i.rstrip('\n').split('\t')
      ### mögliche Parameter
      if len(setting) > 1:
        if setting[0] == 'TablePath':
          self.strTablePath = setting[1]
        if setting[0] == 'User':
          self.strUser = setting[1]
        elif setting[0] == 'Host':
          self.strHost = setting[1]
        elif setting[0] == 'Socket':
          self.strSocket = setting[1]
        elif setting[0] == 'Passwd':
          self.strPasswd = setting[1]
        elif setting[0] == 'Database':
          self.strDatabase = setting[1]
        elif setting[0] == 'Port':
          self.iPort = int(setting[1])
        elif setting[0] == 'RelDescDefault':
          self.strRelDesc = setting[1].encode('utf8')
          self.strRelDescDetail = setting[2].encode('utf8')
        elif setting[0] == 'RelDesc':
          self.mapRelDesc[setting[1]] = setting[2].encode('utf8')
          self.mapRelDescDetail[setting[1]] = setting[3].encode('utf8')
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
            self.__status("read variation list %s" % (setting[1]))
            myFileVariations=codecs.open(setting[1],'r','utf8')
            for j in myFileVariations.readlines():      
              myLine = j.rstrip('\n').split('\t')
              if len(myLine) == 2:
                if not self.mapVariation.has_key(myLine[0]):
                  self.mapVariation[myLine[0]]=myLine[1]
          except:
            self.__error("unknown variation file:"+i)
        elif setting[0] == 'LemmaRepair':
          try:
            # Load LemmaRepairFile
            self.__status("read lemma repair list %s" % (setting[2]))
            myFileLemmaRepair=codecs.open(setting[2],'r','utf8')
            for j in myFileLemmaRepair.readlines():      
              myLine = j.rstrip('\n').split('\t')
              if len(myLine) == 2:
                if not self.mapLemmaRepair.has_key(myLine[0]):
                  self.mapLemmaRepair[(setting[1],myLine[0])]=myLine[1]
          except:
            self.__error("unknown lemma repair file:"+i)

    if self.strTablePath=="":
      self.__error("missing table-path")


