# DWDS Wortprofil (wordprofile)

Das *DWDS Wortprofil* Projekt bildet das Backend für die unter www.dwds.de/wp hinterlegte Übersicht von Kollokationen.
Als Grundlage für die Erstellung eines Wortprofils dienen Korpora des ZDL der BBAW.
Grundlage für eine Wortprofil-Datenbank und deren Abfrage ist eine Wortprofil-Spezifikation. 
Diverse Konfigurationen und zusätzliche Daten liegen unter `spec`.
Im Ordner `log` werden Server-Logfiles hinterlegt.

## Erstellen eines Wortprofils

### Initialisierung der MySQL Tabellen

`python3 init_database.py --user USER --database DB --init`

### Befüllen der DB Tabellen mit extrahierten Matches
Bei der Extraktion der Matches werden pro Dokument Einträge für drei Tabellen generiert, gesammelt und gebündelt in die Datenbank überführt:
(files, concordances, matches)

`python3 insert_doc_mongodb.py --user USER --maria-db DB --mongo-db MONGO_DB --mongo-index MONGO_INDEX [--create-index]`

Oder nur das Erstellen der Indices auf den Tabellen

`python3 insert_doc_mongodb.py --user wpuser --maria-db wp_test --mongo-db zdl_trans_large --create-index`

### Erstellen der WP Statistik
Übertragen der Kollokationen aus den extrahierten Matches

`python3 init_database.py --user wpuser --database wp_test --collocations`

Erstellen der WP Statistik aus den Kollokationen

`python3 init_database.py --user wpuser --database wp_test  --stats`

## OLD STUFF
*Starten eines Wortprofil-Servers

  -wp_server.py
  
    Um Kookkurrenzen und Texttreffer über die Wortprofil-Datenbank abzufragen, dient das Programm
    'wp_server.py'. Dieses stellt eine XMLRPC-Schnittstelle als Server bereit über den über 
    entsprechende Funktionen Informationen aus der Wortprofil-Datenbank abgefragt werden können. 
    Über 'wp_server.py -h' kann die Hilfe zum Aufruf des Programms ausgegeben werden.
    
    XMLRPC-Schnittstelle (im TWiki):
    -für das normale Wortprofil:
	    http://odo.dwds.de/twiki/bin/view/DWDS/WortprofilSchnittstelle2016	
    -für den Wortvergleich:
	    http://odo.dwds.de/twiki/bin/view/DWDS/WortprofilSchnittstelleDiff2014

*Abfragen eines Wortprofil-Servers

  -wp_rel_client.py

    Mit diesem Client-Programm können einfache Kookkurrenzen zu verschiedenen syntaktischen 
    Relationen abgefragt werden. Über 'wp_rel_client.py -h' kann die Hilfe zum Aufruf des 
    Programms ausgegeben werden.

  -wp_mwe_rel_client.py

    Mit diesem Client-Programm können MWE-kookkurrenzen zu verschiedenen syntaktischen Relationen 
    abgefragt werden. Die Abfrage beruht auf einer MWE-ID bzw. Treffer-ID, die einer vorhergehenden 
    Abfrage mit 'wp_rel_client.py' oder 'wp_mwe_rel_client.py' entnommen werden kann. Über 
    'wp_mwe_rel_client.py -h' kann die Hilfe zum Aufruf des Programms ausgegeben werden.

  -wp_mwe_free_client.py
  
    Experimentelles Client-Programm. Mit diesem Programm können MWE-kookkurrenzen abgefragt werden. 
    Eingabe hierzu ist eine Liste von Lemmaformen, die eine bestimmte Reihenfolge besitzen müssen.
    Abfragebeispiele können mit 'wp_mwe_free_client.py -e' ausgegeben werden. Über 
    'wp_mwe_free_client.py -h' kann die allgemeine Hilfe zum Aufruf des Programms ausgegeben werden.

  -wp_hit_client.py
  
    Mit diesem Client-Programm können Texttreffer zu einer Kookkurrenz abgefragt werden. Die 
    Abfrage beruht auf einer Treffer-ID bzw. MWE-ID, die einer vorhergehenden Abfrage mit 
    'wp_rel_client.py' oder 'wp_mwe_rel_client.py' entnommen werden kann. Über 
    'wp_hit_client.py -h' kann die Hilfe zum Aufruf des Programms ausgegeben werden.

  -wp_cmp_client.py

   Mit diesem Client-Programm können zwei Wortprofile (ohne MWE-Kookkurenzen) zu zwei 
   Lemmata gleicher Wortart miteinander verglichen werden. Es ist möglich sowohl
   Gemeinsamkeiten als auch Unterschiede sichtbar zu machen. Über 'wp_cmp_client.py -h' 
   kann die Hilfe zum Aufruf des Programms ausgegeben werden.

  -wp_info_client.py

   Mit diesem Client-Programm können allgemeine Informationen über ein Wortprofil-Projekt 
   abgefragt werden. Sowohl zur Erstellung des Wortprofils als auch zu Frequenzen und Schwellwerten. 
   Über 'wp_info_client.py -h' kann die Hilfe zum Aufruf des Programms ausgegeben werden.

  -wp_status_client.py

   Mit diesem Client-Programm kann geprüft werden, ob der Wortprofil-XMLRPC-Server ordnungsgemäß 
   funktioniert. Über 'wp_status_client.py -h' kann die Hilfe zum Aufruf des Programms ausgegeben werden.

