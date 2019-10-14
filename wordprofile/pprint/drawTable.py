#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

g_exprFarbe = re.compile(r"(?P<farbe>( \033\[[0-9;]*m ))", re.U | re.X)

def fill(count, strObj):
    strResult = ''
    for i in range(0, count):
        strResult = strResult + strObj
    return strResult


def calculate_line(listLength, line, bSwitch):
    if bSwitch:
        strResult = '│\033[0;40m '
    else:
        strResult = '│ '

    iCounter = 0
    for i in line:
        iLenI = len(re.sub(g_exprFarbe, "", i))

        strToken = i + fill(listLength[iCounter] - iLenI, ' ')
        strResult = strResult + strToken
        iCounter = iCounter + 1
        if iCounter == len(listLength):
            if bSwitch:
                strResult = strResult + ' \033[0m│'
            else:
                strResult = strResult + ' \033[0m│'
            break
        else:
            strResult = strResult + ' \033[37;1m│ '
    return strResult
    pass


def calculate_header(listLength, line):
    strResult = '│ '
    iCounter = 0
    for i in line:
        strToken = '\033[1m' + i + '\033[0m' + fill(listLength[iCounter] - len(i), ' ')
        strResult = strResult + strToken
        iCounter = iCounter + 1
        if iCounter == len(listLength):
            strResult = strResult + ' │'
            break
        else:
            strResult = strResult + ' │ '
    return strResult
    pass


def calculate_final(listLength):
    strResult = '└─'
    iCounter = 0
    for i in listLength:
        strToken = fill(listLength[iCounter], '─')

        if iCounter == len(listLength) - 1:
            strResult = strResult + strToken + '─┘'
        else:
            strResult = strResult + strToken + '─┴─'
        iCounter = iCounter + 1
    return strResult
    pass


def calculate_first(listLength):
    strResult = '┌─'
    iCounter = 0
    for i in listLength:
        strToken = fill(listLength[iCounter], '─')

        if iCounter == len(listLength) - 1:
            strResult = strResult + strToken + '─┐'
        else:
            strResult = strResult + strToken + '─┬─'
        iCounter = iCounter + 1
    return strResult
    pass


def calculate_border(listLength):
    strResult = '╞═'
    iCounter = 0
    for i in listLength:
        strToken = fill(listLength[iCounter], '═')

        if iCounter == len(listLength) - 1:
            strResult = strResult + strToken + '═╡'
        else:
            strResult = strResult + strToken + '═╪═'
        iCounter = iCounter + 1
    return strResult
    pass


def calculate_table(header, table):
    listLength = []
    for i in header:
        listLength.append(len(i))

    listCopy = []

    for i in table:
        listDummy = []
        iCounter = 0
        for j in i:

            if isinstance(j, type(99)) or isinstance(j, type(9.9)):

                if len(str(j)) > listLength[iCounter]:
                    listLength[iCounter] = len(str(j))
                listDummy.append(str(j))
                iCounter = iCounter + 1
            else:

                iLenJ = len(re.sub(g_exprFarbe, "", j))

                if iLenJ > listLength[iCounter]:
                    listLength[iCounter] = iLenJ
                listDummy.append(j)
                iCounter = iCounter + 1
            if iCounter == len(listLength):
                break
        listCopy.append(listDummy)

    strResult = ''
    bSwitch = False
    for i in listCopy:
        strResult = strResult + calculate_line(listLength, i, bSwitch) + '\n'
        bSwitch = not bSwitch

    return calculate_first(listLength) + '\n' + calculate_header(listLength, header) + '\n' + calculate_border(
        listLength) + '\n' + strResult + calculate_final(listLength)
    pass
