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

## Service

Ein fertig erstelltes Wortprofil kann als Service (XMLRPC oder REST) bereitgestellt werden.
Über diesen Service werden alle Funktionen zur Wortprofil Datenbank abgewickelt.

### XMLRPC
Starten des XMLRPC Service:
`python3 wordprofile/apps/xmlrpc_api.py --user wpuser --database wp_test --hostname riker --spec spec/config.json`

Über die XMLRPC Schnittstelle werden folgende Funktionen (mit den jeweils obligatorischen Argumenten) bereitgestellt:
- get_lemma_and_pos({Word: str, POS: str, UseVariations: bool})
- get_lemma_and_pos_diff({ Word1: str, Word2: str, UseVariations: bool})
- get_relations({Lemma: str, POS: str})
- get_diff({LemmaId1: str, LemmaId2: str, PosId: str})
- get_intersection({LemmaId1: str, LemmaId2: str, PosId: str})
- get_relation_by_info_id({coocc_id: int})
- get_concordances_and_relation({coocc_id: int})

### REST API
`python3 wordprofile/apps/rest_api.py --user wpuser --database wp_test --hostname riker --spec spec/config.json`

Über die REST Schnittstellen sollen die gleichen Funktionen über eine URL zur verfügung stehen und so leichter zuganglich gemacht werden.
- `/info/lemma/`: get_lemma_and_pos
- `/info/lemmas/`: get_lemma_and_pos_diff
- `/rel/`: get_relations
- `/cmp/difference/`: get_diff
- `/cmp/intersection/`: get_intersection
- `/lemma/id/{coocc_id}`: get_relation_by_info_id
- `/hits/{coocc_id}`: get_concordances_and_relation

Zusätzlich zur REST API wird über das *fastapi* framework eine Dokumentation generiert, welche unter `/docs` bzw. `/redoc` erreichbar ist.

### CLI

Abfrage einfacher Kookkurrenzen zu verschiedenen syntaktischen Relationen:
```
python3 cli/wp.py --user DBUSER --database DBNAME --hostname localhost --port 8086 --spec spec/config.json rel -l Mann
```

Abfrage von Texttreffern zu einer Kookkurrenz. Für die Abfrage wird die Treffer-ID (hit id) genutzt:
```
python3 cli/wp.py --user DBUSER --database DBNAME --hostname localhost --port 8086 --spec spec/config.json hit -i 1948509
```

Vergleich der Wortprofile zweier Lemmata:
```
python3 cli/wp.py --user DBUSER --database DBNAME --hostname localhost --port 8086 --spec spec/config.json cmp --lemma1 Mann --lemma2 Frau --nbest 5
```

Vergleich von zwei parallel laufenden WP Instanzen (host1, host2):
```
python3 cli/cmp_wp.py --host2 riker:8086 --host1 services3.dwds.de:7780 -r META -n 10
```