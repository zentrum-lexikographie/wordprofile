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
result = s.get_info()

### Propjektinformationen
print("\033[32;1mproject:\033[m")
print("author:", result['author'])
print("creation date:", result['creation_date'])
print("spec version:", result['spec_file_version'])
print("spec file:", result['spec_file'])

### verwendete Korpora
listKorpora = result['used_corpora']
print("\033[32;1mcorpora:\033[m")
print(",".join(listKorpora))

### Einbettungstiefe der MWE-Relationen
print("\033[32;1mMWE info:\033[m")
print("MweDepth:", result['mwe_depth'])

### Zahlen über Gößen
print("\033[32;1mglobal info:\033[m")
print("NoOfLemmas:", result['lemma_size'])
print("NoOfCooccurrences:", result['relation_size'])
print("NoOfSentences:", result['sentence_size'])
print("NoOfHits:", result['info_size'])

### relationsbezogene Kookkurrenzinformationen
print("\033[32;1mcooccurrence info:\033[m")
for i in list(result['cooccurrence_info'].items()):
    print(i[0] + ":", i[1])

### Schwellwerte
print("\033[32;1mglobal threshold info:\033[m")
print("LemmaCut:", result['lemma_cut'])
print("\033[32;1mrelation threshold info:\033[m")
for i in list(result['threshold'].items()):
    print(i[0] + ":", i[1])
