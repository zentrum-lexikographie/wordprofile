#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

  Das Client-Programm fragt einen Wortprofil-XMLRPC-Server ab und prüft, ob mit diesem alles in Ordnung ist.
  Wenn der Server abfragbar ist und alles in Ordnung ist, wird "OK" zurückgegeben, ansonsten eine Fehlermeldung.
  
  Beispielaufruf:
    python wp_status.py -x http://localhost:8080

"""

import xmlrpc.client
from optparse import OptionParser

### Komandozeilenoptionen einlesen
parser = OptionParser()
parser.add_option("-x", dest="host", default=None, help="Hostrechner (z.B. http://services.dwds.de:8049)")
(options, args) = parser.parse_args()

### Komandozeilenoptionen prüfen
if len(args) > 0:
    parser.error("incorrect number of arguments")
if options.host == None:
    parser.error("missing host")

### XMLRPC-Client erstellen
s = xmlrpc.client.ServerProxy(options.host)
# Print list of available methods
# print "methods:", s.system.listMethods()

### Prüfabfrage senden
strResponse = s.status()

print("|: status: ", strResponse)
