#!/usr/bin/python
# -*- coding: utf-8 -*-

import string
import re

g_exprFarbe = re.compile(u""" 
             (?P<farbe>( \033\[[0-9;]*m ))
            """,re.U|re.X)

def repl_farbe(matchobj):
  return ""




def fill(count,strObj):
  strResult=''
  for i in range(0,count):
    strResult = strResult + strObj
  return strResult


def calculate_line (listLength, line, bSwitch):

  strResult=''
  if bSwitch:
     strResult=u'│\033[0;40m '
  else:
     strResult=u'│ '

  iCounter=0
  for i in line:
    iLenI = len(re.sub(g_exprFarbe, repl_farbe, i))

    strToken =  i + fill(listLength[iCounter]-iLenI,u' ')
    strResult = strResult + strToken
    iCounter = iCounter + 1
    if iCounter == len(listLength):
      if bSwitch:
        strResult = strResult + u' \033[0m│'
      else:
        strResult = strResult + u' \033[0m│'
      break
    else:
      strResult = strResult + u' \033[37;1m│ '
  return strResult
  pass

def calculate_header (listLength, line):

  strResult=u'│ '
  iCounter=0
  for i in line:
    strToken =   u'\033[1m' + i + u'\033[0m' + fill(listLength[iCounter]-len(i),u' ')
    strResult = strResult + strToken 
    iCounter = iCounter + 1
    if iCounter == len(listLength):
      strResult = strResult + u' │'
      break
    else:
      strResult = strResult + u' │ '
  return strResult
  pass

def calculate_final (listLength):
  strResult=u'└─'
  iCounter=0
  for i in listLength:
    strToken = fill(listLength[iCounter],u'─')

    if iCounter == len(listLength)-1:
      strResult = strResult + strToken + u'─┘'
    else:  
      strResult = strResult + strToken + u'─┴─'
    iCounter = iCounter + 1
  return strResult
  pass

def calculate_first (listLength):
  strResult=u'┌─'
  iCounter=0
  for i in listLength:
    strToken = fill(listLength[iCounter],u'─')

    if iCounter == len(listLength)-1:
      strResult = strResult + strToken + u'─┐'
    else:  
      strResult = strResult + strToken + u'─┬─'
    iCounter = iCounter + 1
  return strResult
  pass

def calculate_border (listLength):
  strResult=u'╞═'
  iCounter=0
  for i in listLength:
    strToken = fill(listLength[iCounter],u'═')

    if iCounter == len(listLength)-1:
      strResult = strResult + strToken + u'═╡'
    else:  
      strResult = strResult + strToken + u'═╪═'
    iCounter = iCounter + 1
  return strResult
  pass

def calculate_table (header,table):
  listLength = []
  for i in header:
    listLength.append(len(i))

  listCopy = []
  
  for i in table:    
    listDummy = []
    iCounter = 0
    for j in i:

      if type(j) == type(99) or type(j) == type(9.9):
      
        if len(str(j)) > listLength[iCounter]:
          listLength[iCounter]=len(str(j))
        listDummy.append(str(j))
        iCounter=iCounter+1
      else:

        iLenJ = len(re.sub(g_exprFarbe, repl_farbe, j.encode('utf8')))


        if iLenJ > listLength[iCounter]:
          listLength[iCounter]=iLenJ
        listDummy.append(j)
        iCounter=iCounter+1
      if iCounter == len(listLength):
        break
    listCopy.append(listDummy)

  strResult=''
  bSwitch=False
  for i in listCopy:
    strResult = strResult + calculate_line(listLength,i,bSwitch) + '\n'
    bSwitch=not bSwitch

  return calculate_first(listLength) + '\n' + calculate_header(listLength,header) + '\n' + calculate_border(listLength) + '\n' + strResult +  calculate_final(listLength)
  pass


