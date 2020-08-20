# DWDS Wortprofil (wordprofile)

Das *DWDS Wortprofil* Projekt bildet das Backend für die unter www.dwds.de/wp hinterlegte Übersicht von Kollokationen.
Als Grundlage für die Erstellung eines Wortprofils dienen Korpora des ZDL der BBAW.
Grundlage für eine Wortprofil-Datenbank und deren Abfrage ist eine Wortprofil-Spezifikation. 
Diverse Konfigurationen und zusätzliche Daten liegen unter `spec`.
Im Ordner `log` werden Server-Logfiles hinterlegt.

## Erstellen eines Wortprofils
Ausgeführte Aufgaben:
- Initialisieren der Datenbank
- Extraktion der Relationen
- Befüllen der DB Tabellen mit extrahierten Matches
- Berechnung der Statistiken
- Finden von MWE aus extrahierten Matches

```
usage: make_wp.py [-h] [--user USER] [--maria-db MARIA_DB] [--input INPUT]
                  [--create-wp] [--passwd] [--tmp TMP]
                  [--chunk-size CHUNK_SIZE] [--njobs NJOBS]

optional arguments:
  -h, --help            show this help message and exit
  --user USER           database username
  --maria-db MARIA_DB   database name
  --input INPUT         conll input file
  --create-wp           create wordprofile from tmp data
  --passwd              ask for database password
  --tmp TMP             temporary storage path
  --chunk-size CHUNK_SIZE
                        size of document chunks per process per corpus
  --njobs NJOBS         size of document chunks per process per corpus
```
Beispielaufruf:

Read from stdin, create wordprofile tables, and store them under tmp dir:
```shell script
$ cat some.conll | python3 cli/make_wp.py --tmp /mnt/SSD/data/wp_dev
```

Create wordprofile from some file and load everything from temp dir into database:
```shell script
$ python3 cli/make_wp.py --input test.conll --tmp /mnt/SSD/data/wp_dev --njobs 4 --chunk-size 100 --create-wp --user wpuser --maria-db wp_dev 
```

Disable input and create wordprofile from temp files:
```shell script
$ python3 cli/make_wp.py --input '' --tmp /mnt/SSD/data/wp_dev_ud --create-wp --user wpuser --maria-db wp_dev
```

## Service

Ein fertig erstelltes Wortprofil kann als Service (XMLRPC oder REST) bereitgestellt werden.
Über diesen Service werden alle Funktionen zur Wortprofil Datenbank abgewickelt.

### XMLRPC
```
usage: xmlrpc_api.py [-h] --user USER --database DATABASE
                     [--hostname HOSTNAME] [--db-hostname DB_HOSTNAME]
                     [--passwd] [--port PORT] --spec SPEC [--log LOGFILE]

optional arguments:
  -h, --help            show this help message and exit
  --user USER           database username
  --database DATABASE   database name
  --hostname HOSTNAME   XML-RPC hostname
  --db-hostname DB_HOSTNAME
                        XML-RPC hostname
  --passwd              ask for database password
  --port PORT           XML-RPC port
  --spec SPEC           Angabe der Settings-Datei (*.xml)
  --log LOGFILE         Angabe der log-Datei (Default: log/wp_{date}.log)
```
Starten des XMLRPC Service:
```shell script
python3 apps/xmlrpc_api.py --user wpuser --database wp_test --hostname riker --spec spec/config.json
```

Über die XMLRPC Schnittstelle werden folgende Funktionen (mit den jeweils obligatorischen Argumenten) bereitgestellt:
- get_lemma_and_pos({Word: str, POS: str, UseVariations: bool})
- get_lemma_and_pos_diff({ Word1: str, Word2: str, UseVariations: bool})
- get_relations({Lemma: str, POS: str})
- get_diff({LemmaId1: str, LemmaId2: str, PosId: str})
- get_intersection({LemmaId1: str, LemmaId2: str, PosId: str})
- get_relation_by_info_id({coocc_id: int})
- get_concordances_and_relation({coocc_id: int})

### REST API

```shell script
python3 apps/rest_api.py --user wpuser --database wp_test --hostname riker --spec spec/config.json
```

Über die REST Schnittstellen sollen die gleichen Funktionen über eine URL zur verfügung stehen und so leichter zuganglich gemacht werden.
- `/info/lemma/`: get_lemma_and_pos
- `/info/lemmas/`: get_lemma_and_pos_diff
- `/rel/`: get_relations
- `/cmp/difference/`: get_diff
- `/cmp/intersection/`: get_intersection
- `/lemma/id/{coocc_id}`: get_relation_by_info_id
- `/hits/{coocc_id}`: get_concordances_and_relation

Zusätzlich zur REST API wird über das *fastapi* framework eine Dokumentation generiert, welche unter `/docs` bzw. `/redoc` erreichbar ist.

## CLI
Zusätzlich für Tests oder ähliches bietet `cli/wp.py` die Möglichkeit, ohne laufenden WP Service die Funktionalität zu testen.
Hierfür wird ein temporäres WP erstellt.

### Einfache Abfrage
Abfrage einfacher Kookkurrenzen zu verschiedenen syntaktischen Relationen:
```shell script
python3 cli/wp.py --user DBUSER --database DBNAME --hostname localhost --port 8086 --spec spec/config.json rel -l Mann
```

Abfrage von Texttreffern zu einer Kookkurrenz. Für die Abfrage wird die Treffer-ID (hit id) genutzt:
```shell script
python3 cli/wp.py --user DBUSER --database DBNAME --hostname localhost --port 8086 --spec spec/config.json hit -i 1948509
```

Vergleich der Wortprofile zweier Lemmata:
```shell script
python3 cli/wp.py --user DBUSER --database DBNAME --hostname localhost --port 8086 --spec spec/config.json cmp --lemma1 Mann --lemma2 Frau --nbest 5
```

### MWE Abfrage

```shell script
python3 cli/wp.py --user DBUSER --database DBNAME --hostname localhost --port 8086 --spec spec/config.json mwe-rel -l laufen,schnell
```

Abfrage von Texttreffern zu einer Kookkurrenz. Für die Abfrage wird die Treffer-ID (hit id) genutzt:
```shell script
python3 cli/wp.py --user DBUSER --database DBNAME --hostname localhost --port 8086 --spec spec/config.json mwe-hit -i 1948509
```

### WP Vergleich

Vergleich von zwei parallel laufenden WP Instanzen (host1, host2):
```shell script
python3 cli/cmp_wp.py --host2 riker:8086 --host1 services3.dwds.de:7780 -r META -n 10
```