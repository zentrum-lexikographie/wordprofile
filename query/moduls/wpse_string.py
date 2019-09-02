#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
  String-Hilfsfunktionen für den Wortprofil-XMLRPC-Server, die in einer Klasse gebündelt sind
"""


class WpSeString:

    def error(self, strObj):
        print("):", strObj)
        # sys.exit(-1)

    def status(self, strObj):
        print("|:", strObj)

    def status_complete(self, strObj):
        print("(:", strObj)

    """
      Integer auf Subscript abbilden
    """

    def get_subscript(self, iObj):
        if iObj == 1:
            return "₁"
        elif iObj == 2:
            return "₂"
        elif iObj == 3:
            return "₃"
        elif iObj == 4:
            return "₄"
        elif iObj == 5:
            return "₅"
        elif iObj == 6:
            return "₆"
        elif iObj == 7:
            return "₇"
        elif iObj == 8:
            return "₈"
        elif iObj == 9:
            return "₉"
        else:
            return ""

    """
      Formatieren eines Hit
    """

    def format_sentence(self, strSent):
        if strSent == None:
            return ""

        bBracket = True
        strRes = ""
        listLine = []
        iTokenCounter = 1
        strSent = strSent.replace('\x02', '\x01')
        listObj = strSent.split('\x01')
        for a in listObj:
            if bBracket:
                strBlank = ''
                bBracket = False
            else:
                strBlank = ' '

            if a == '.' or a == ',' or a == ';' or a == ':' or a == '?' or a == '!' or a == ')' or a == ']' or a == '}' or a == '“':
                listLine.append(a)
            elif a == '(' or a == '[' or a == '{' or a == '„':
                listLine.append(strBlank + a)
                bBracket = True
            else:
                listLine.append(strBlank + a)
            iTokenCounter = iTokenCounter + 1
        strRes = ''.join(listLine)
        return strRes

    """
      Formatieren eines Hit mit Highlighting der Keywords
    """

    def format_sentence_center(self, strSent, iPos1, iPos2, iPos3):
        strWord = ""
        listWords = []
        listDelimiter = []
        iTokCount = 1
        for i in strSent:
            if i == '\x01' or i == '\x02':

                if iTokCount == iPos1:
                    listWords.append('&&')
                    listWords.append(strWord)
                    listWords.append('&&')
                elif iTokCount == iPos2 or iTokCount == iPos3:
                    listWords.append('_&')
                    listWords.append(strWord)
                    listWords.append('&_')
                else:
                    listWords.append(strWord)

                if i == '\x01':
                    listWords.append('')
                if i == '\x02':
                    listWords.append(' ')

                iTokCount += 1
                strWord = ""
            else:
                strWord += i

        listWords.append(strWord)

        strSent = ''.join(listWords)
        return ''.join(listWords)

    """
      Formatieren eines Hit mit Highlighting der Keywords bei einer MWE-Kookkurrernz
    """

    def format_sentence_center_mwe(self, strSent, listPosition):
        strWord = ""
        listWords = []
        listDelimiter = []
        iTokCount = 1
        for i in strSent:
            if i == '\x01' or i == '\x02':

                iCount = 0
                bSuccess = False
                for j in listPosition:
                    if iTokCount == j:
                        if iCount == 0:
                            listWords.append('&&')
                            listWords.append(strWord)
                            listWords.append('&&')
                            bSuccess = True
                            break
                        else:
                            listWords.append('_&')
                            listWords.append(strWord)
                            listWords.append('&_')
                            bSuccess = True
                            break
                    iCount += 1

                if not bSuccess:
                    listWords.append(strWord)

                if i == '\x01':
                    listWords.append('')
                if i == '\x02':
                    listWords.append(' ')

                iTokCount += 1
                strWord = ""
            else:
                strWord += i

        listWords.append(strWord)

        strSent = ''.join(listWords)
        return ''.join(listWords)

    """
      Mapping eines (kryptischen) Oberflächenstring auf einen lesbaren Oberflächenstring
    """

    def surface_mapping(self, strSurf, strRel, iRelType, strPrep, bExtendedSurfaceForm):

        if bExtendedSurfaceForm:

            if iRelType == 1 and strPrep != "-" and strPrep != "":
                iPos = strSurf.find('<')
                if iPos != -1:
                    strSurf = strSurf[0:iPos] + ' ' + strPrep + ' ' + strSurf[iPos + 1:]
                    strSurf = strSurf.replace('<', ' ').replace('>', ' ').lstrip()
                else:
                    strSurf = strSurf.replace('<', ' ').replace('>', ' ').lstrip()
                    strSurf = strSurf + ' ' + strPrep
            elif iRelType != 1 and strPrep != "-":
                strSurf = strSurf.replace('<', ' ').replace('>', ' ').lstrip()
                strSurf = strPrep + ' ' + strSurf
            else:
                strSurf = strSurf.replace('<', ' ').replace('>', ' ').lstrip()

            return strSurf.replace('  ', ' ')
        else:
            strExtrSurf = ""

            iPos = strSurf.rfind('>')
            if iPos != -1:
                iPos2 = strSurf[iPos + 1:].rfind('<')
                if iPos2 != -1:
                    strExtrSurf = strSurf[iPos + 1:iPos2 + 1]
                else:
                    strExtrSurf = strSurf[iPos + 1:]
            else:
                iPos2 = strSurf[iPos + 1:].rfind('<')
                if iPos2 != -1:
                    strExtrSurf = strSurf[0:iPos2 + 1]
                else:
                    strExtrSurf = strSurf

            if iRelType == 1 and strPrep != "-" and strPrep != "":
                return strExtrSurf + ' ' + strPrep
            elif iRelType != 1 and strPrep != "-" and strPrep != "":
                return strPrep + ' ' + strExtrSurf
            else:
                return strExtrSurf

    """
      Kombinieren der Bibl-Strings Orig und Scan mit der Seitenzahl
    """

    def gen_bibl_with_page(self, strOrig, strScan, strPage):

        strOrig = strOrig.replace('#page#', strPage)
        strScan = strScan.replace('#page#', strPage)
        return (strOrig, strScan)
