#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

  Das Client-Programm fragt eine Wortprofil-MySQL-Datenbank über einen XMLRPC-Server ab und liefert Informationen
  über die verwendeten Korpora, Anzahl an Lemmaformen, Kookkurrenzen, Texttreffern und Sätzen.
  Des Weiteren liefert es Informationen über die Schwellwerte, die beider Wortprofilberechnung
  verwendet wurden.

  Beispielaufruf:
  python wp_info_client.py -x http://localhost:8080

"""

import xmlrpc.client

from optparse import OptionParser

### Komandozeilenoptionen einlesen
parser = OptionParser()
parser.add_option("-x", dest="host", default=None, help="Hostrechner (z.B. http://services.dwds.de:9999)")
(options, args) = parser.parse_args()

### Komandozeilenoptionen prüfen
if options.host == None:
    parser.error("missing host")

### XMLRPC-Client erstellen
s = xmlrpc.client.ServerProxy(options.host)

listResult = []

### Propjektinformationen
print("\033[32;1mproject:\033[m")
print("author:", s.get_author())
print("creation date:", s.get_creation_date())
print("spec version:", s.get_spec_version())
print("spec file:", s.get_spec_filename())

### verwendete Korpora
listKorpora = s.get_used_corpora()
print("\033[32;1mcorpora:\033[m")
strKorpora = ""
for i in listKorpora:
    if strKorpora != "":
        strKorpora += ","
    strKorpora += i
print(strKorpora)

### Einbettungstiefe der MWE-Relationen
iMweDepth = s.get_mwe_depth()
print("\033[32;1mMWE info:\033[m")
print("MweDepth:", str(iMweDepth))

### Zahlen über Gößen
iNoOfLemma = s.get_no_of_lemmas()
iNoOfCooccurrences = s.get_no_of_cooccurrences()
iNoOfSentences = s.get_no_of_sentences()
iNoOfHits = s.get_no_of_hits()
print("\033[32;1mglobal info:\033[m")
print("NoOfLemmas:", iNoOfLemma)
print("NoOfCooccurrences:", iNoOfCooccurrences)
print("NoOfSentences:", iNoOfSentences)
print("NoOfHits:", iNoOfHits)

### relationsbezogene Kookkurrenzinformationen
mapCooccurrenceInfo = s.get_cooccurrence_info()
print("\033[32;1mcooccurrence info:\033[m")
for i in list(mapCooccurrenceInfo.items()):
    print(i[0] + ":", i[1])

### Schwellwerte
mapThresholdInfo = s.get_threshold_info()
print("\033[32;1mglobal threshold info:\033[m")
print("LemmaCut:", s.get_lemma_cut_threshold())
print("\033[32;1mrelation threshold info:\033[m")
for i in list(mapThresholdInfo.items()):
    print(i[0] + ":", i[1])
