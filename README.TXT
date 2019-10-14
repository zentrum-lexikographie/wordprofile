WORTPROFILDATENBANK UND ABFRAGE

Grundlage für eine Wortprofil-Datenbank und deren Abfrage ist eine Wortprofil-Spezifikation. 
Diese solten unter './spec/' liegen.
Eine Beispielspezifikation, die den Grundaufbau solch einer Spezifikation darlegt, 
ist in './Spec/dradio.kira.spec' gegeben. Diese Spezifikation kann als Muster 
verwendet werden.

Einige Python Programme benötigen Module. Diese sind in './moduls/' zu finden.

Einige Python Programme schreiben Log-Dateien. Diese werden standardmäßig in das
Verzeichnis './log/' geschrieben.


*Erstellen einer Wortprofil-MySQL-Datenbank

 -create_database.py:

    Eine Wortprofil-Datenbank kann über 'create_database.py' erstellt werden.
    Hierzu muss eine entsprechende Spezifikation in './Spec' vorhanden sein.
    Über 'python create_database.py -h' kann die Hilfe zum Aufruf des Programms 
    ausgegeben werden. Über 'create_database.py' werden hierbei nur die 
    Kookkurrenzinformationen eingespielt.

 -update_hit_database.py:
  
    Eine bestehende Wortprofil-Datenbank kann über 'update_hit_database.py' um Texttreffer-
    Informationen erweitert werden. Über 'update_hit_database.py -h' kann die 
    Hilfe zum Aufruf des Programms ausgegeben werden. Entsprechende Treffer-Tabellen müssen
    hierbei berechnet und vorhanden sein.

 -update_mwe_database.py:

    Eine bestehende Wortprofil-Datenbank kann über 'update_mwe_database.py' um MWE-
    Informationen erweitert werden. Über 'update_mwe_database.py -h' kann die 
    Hilfe zum Aufruf des Programms ausgegeben werden. Entsprechende MWE-Tabellen müssen
    hierbei berechnet und vorhanden sein.

 -update_moko_database.py

    Eine bestehende Wortprofil-Datenbank kann über 'update_moko_database.py' um 
    MoKo-Projekt-spezifische Informationen erweitert werden. Über 'update_mwe_database.py -h' 
    kann die Hilfe zum Aufruf des Programms ausgegeben werden. Entsprechende MoKo-Tabellen müssen
    hierbei berechnet und vorhanden sein.

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













