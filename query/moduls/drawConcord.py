#!/usr/bin/python
# -*- coding: utf-8 -*-

# g_iMaxLength=140
g_iContext = 3


def fill(count, strObj):
    strResult = ''
    for i in range(0, int(count)):
        strResult = strResult + strObj
    return strResult


def break_concord(strConcord, iMax, bCompact, strTEIinfo):
    if bCompact:

        g_iContext = 3
        bDots = True
        listConc = strConcord.split(' ')
        strConcordOld = ''
        strConcord = ''

        if (strConcord == '' or len(strConcord) < iMax) and bDots:
            bDots = False
            g_iContext = g_iContext + 1

            strConcordOld = strConcord
            strConcord = ''
            iCounter = 0
            setRemember = []

            for iCounter in range(0, len(listConc)):
                if listConc[iCounter].find("_&") != -1 and listConc[iCounter].find("&&") != -1:

                    bOther = False

                    for n in range(max(0, iCounter - g_iContext - 1), min(iCounter, len(listConc))):
                        if n in setRemember or n == 0:
                            bOther = True

                    if bOther != True:
                        bDots = True
                        strConcord = strConcord + "... "

                    for n in range(max(0, iCounter - g_iContext), min(iCounter, len(listConc))):
                        if n not in setRemember:
                            setRemember.append(n)
                            strConcord = strConcord + listConc[n] + ' '

                    for m in range(iCounter, min(len(listConc), iCounter + g_iContext + 1)):
                        if m not in setRemember:
                            setRemember.append(m)
                            strConcord = strConcord + listConc[m] + ' '

            if len(listConc) - 1 not in setRemember:
                bDots = True
                strConcord = strConcord + '...'

            strConcord = strConcord.rstrip(' ')  # + "|"+ ' '.join(listConc)

        if strConcordOld != '':
            strConcord = strConcordOld

    listResult = []

    if len(strTEIinfo) > 0:
        if len(strTEIinfo) > iMax:
            while len(strTEIinfo) > iMax:
                iDummy = iMax
                strDummy = strTEIinfo
                while (strDummy[iDummy] != ' ' or iDummy == 0):
                    iDummy = iDummy - 1
                iDummy = iDummy + 1

                strDummy2 = strDummy[0:iDummy]
                listResult.append(strDummy2)
                strTEIinfo = strDummy[iDummy:]

            listResult.append(strTEIinfo)
        else:
            listResult.append(strTEIinfo)

    iBegin = len(listResult)

    if len(strConcord) > iMax:
        while len(strConcord) > iMax:
            iDummy = iMax
            strDummy = strConcord
            while (strDummy[iDummy] != ' ' or iDummy == 0):
                iDummy = iDummy - 1
            iDummy = iDummy + 1

            strDummy2 = strDummy[0:iDummy]
            listResult.append(strDummy2)
            strConcord = strDummy[iDummy:]

        listResult.append(strConcord)
    else:
        listResult.append(strConcord)

    for iCounter in range(0, iBegin):
        listResult[iCounter] = listResult[iCounter] + ' '
        listResult[iCounter] = '\033[0;32;40m' + listResult[iCounter] + fill(iMax - len(listResult[iCounter]) + (2),
                                                                             ' ') + '\033[0m'

    for iCounter in range(iBegin, len(listResult)):
        iMarker = 0
        iPos = listResult[iCounter].find('_&')
        while iPos != -1:
            iMarker = iMarker + 1
            iPos = listResult[iCounter].find('_&', iPos + 1)

        iMarker2 = 0
        iPos = listResult[iCounter].find('&&')
        while iPos != -1:
            iMarker2 = iMarker2 + 1
            iPos = listResult[iCounter].find('&&', iPos + 1)

        iMarker = iMarker + (iMarker2 // 2)

        listResult[iCounter] = listResult[iCounter] + fill(iMax - len(listResult[iCounter]) + (iMarker * 4), ' ')
        listResult[iCounter] = listResult[iCounter].replace("_&", '\033[1;31m').replace("&&", '\033[4m\033[1;31m',
                                                                                        1).replace("&_",
                                                                                                   '\033[0m').replace(
            "&&", '\033[0m', 1)
    return (listResult, iBegin)


def calculate_final(iLen):
    strResult = '└─'
    strResult = strResult + fill(iLen, '─')
    strResult = strResult + '─┘'
    return strResult


def calculate_middle(iLen):
    strResult = '├─'

    strResult = strResult + fill(iLen, '─')

    strResult = strResult + '─┤'
    return strResult


def calculate_first(iLen):
    strResult = '┌─'

    strResult = strResult + fill(iLen, '─')

    strResult = strResult + '─┐'
    return strResult


def calculate_line(strConcord, iLen, bCompact, strTEIinfo):
    strResult = ''
    (listParts, iBegin) = break_concord(strConcord, iLen, bCompact, strTEIinfo)
    iCounter = 0
    for i in range(0, iBegin):
        strResult = strResult + '│'

        strResult = strResult + listParts[i]

        iCounter = iCounter + 1

        if iCounter == len(listParts):
            strResult = strResult + '│'
        else:
            # strResult = strResult + u'│\n'
            strResult = strResult + '\n'

    for i in range(iBegin, len(listParts)):
        strResult = strResult + '│ '

        strResult = strResult + listParts[i]

        iCounter = iCounter + 1

        if iCounter == len(listParts):
            strResult = strResult  # + u' │'
        else:
            # strResult = strResult + u' │\n'
            strResult = strResult + ' \n'

    return strResult


def calculateConcord(strConcord, bCompact, iMaxLength, strTEIinfo):
    strResult = ''
    # strResult = strResult + calculate_middle(iMaxLength) + '\n'
    strResult = strResult + calculate_line(strConcord, iMaxLength, bCompact, strTEIinfo)
    return strResult


def calculateConcordFirst(strConcord, bCompact, iMaxLength, strTEIinfo):
    strResult = ''
    strResult = strResult + calculate_first(iMaxLength) + '\n'
    strResult = strResult + calculate_line(strConcord, iMaxLength, bCompact, strTEIinfo)
    return strResult


def draw_concord(setConcord, bCompact, iMaxLength):
    strResult = ''
    bFirst = True
    for i in setConcord:
        if bFirst:
            strResult = strResult + calculateConcordFirst(i[0], bCompact, iMaxLength, i[1]) + '\n'
            bFirst = False
        else:
            strResult = strResult + calculateConcord(i[0], bCompact, iMaxLength, i[1]) + '\n'

    strResult = strResult + calculate_final(iMaxLength)
    print(strResult)
