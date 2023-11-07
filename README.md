# DWDS Wortprofil (wordprofile)

Das *DWDS Wortprofil* Projekt bildet das Backend für die unter www.dwds.de/wp hinterlegte Übersicht von Kollokationen.
Als Grundlage für die Erstellung eines Wortprofils dienen Korpora des ZDL der BBAW.
Grundlage für eine Wortprofil-Datenbank und deren Abfrage ist eine Wortprofil-Spezifikation.
Diverse Konfigurationen und zusätzliche Daten liegen unter `spec`.
Im Ordner `log` werden Server-Logfiles hinterlegt.

## Erstellen eines Wortprofils
Ausgeführte Aufgaben:
1. Extraktion der Relationen
2. Berechnung der Statistiken
3. Finden von MWE aus extrahierten Matches
4. Initialisieren der Datenbank
5. Befüllen der DB Tabellen mit extrahierten Matches

Wortprofile werden in zwei Schritten erstellt:
Bevor ein vollständiges Wortprofil erstellt wird, werden die einzelnen Korpora separat verarbeitet, Matches extrahiert und darauf Kollokationen gezählt. Dies reduziert die Arbeit im zweiten Schritt wenn die gesamten Daten verarbeitet werden sollen.
Im nachfolgenden werden die drei Skripte kurz erklärt, die für die Erstellung genutzt werden und im Skript `make_wp.sh` kombiniert sind.
Erstellt werden soll ein Test-Wortprofil aus zwei Korpora: `dradio` und `pnn`, welche bereits im CoNLL Format vorliegen und entsprechende Annotationen (POS, NER, DEPREL) besitzen.

### Kollokationsextraktion
In diesem ersten Schritt werden für jeden Korpus (dradio und pnn) die jeweiligen Matches extrahiert, die Satzbelege aufgearbeitet und die Korpus-Kollokationsstatistik berechnet.
Die Daten liegen in nicht-komprimierter Form vor.
Dies erleichtert den Schritt der Vereinigung aller Teilkorpora erheblich.
```shell
python3.7 -m wordprofile.cli.extract_collocations --input corpora/dradio.conll --dest test_wp/stage/dradio --njobs 4
python3.7 -m wordprofile.cli.extract_collocations --input corpora/pnn.conll --dest test_wp/stage/pnn --njobs 4
```

### Berechnung Wortprofil
Als nächstes werden die extrahierten Informationen beider Korpora aus `test_wp/stage` vereint und unter `test_wp/final` gespeichert.
Weiterhin werden die Daten für die Datenbank vorbereitet und komprimiert bzw. normalisiert.
Statistiken werden in der jeweiligen Kollokationsdatei ergänzt, bevor diese ausgeschrieben wird.

```shell
python3.7 wordprofile/cli/compute_statistics.py test_wp/stage/* --dest test_wp/final --min-rel-freq 3 --mwe
```
In diesem Aufruf werden bei der Berechnung des Wortprofils alle Kollokationen entfernt, die nicht mindestens eine Frequenz von 3 aufweisen.
Im Anschluss werden aus den Kollokationen MWAs berechnet, die sich aus der Kombination zweiter sich überlappender Kollokationen ergeben.

### DB befüllen
Im letzten Schritt wird das finale, komprimierte und für die Datenbank vorbereitete Wortprofil in die Datenbank transferiert.
Die Daten liegen in Dateiform so vor, dass sie direkt in eine SQL DB geladen werden können.
Anschließend werden noch notwendige Indizes erstellt, welche eine performante Abfrage der Kollokationen und ihrer Informationen ermöglichen.
```shell
python3.7 wordprofile/cli/load_database.py test_wp/final --user wpuser --db test_wp
```

## REST Service

Ein fertig erstelltes Wortprofil kann als REST Service bereitgestellt werden.
Über diesen Service werden alle Funktionen zur Wortprofil Datenbank abgewickelt.
Parameter wie Nutzername und Passwort der Datenbank sollten über `.env` festgelegt werden.

```shell script
python3 -m wordprofile.apps.rest_api --http-port 5050 --db-name test_wp
```
Zusätzlich zur REST API wird über das *fastapi* framework eine Dokumentation generiert, welche unter `/docs` bzw. `/redoc` erreichbar ist.


## Build

```shell
docker-compose build
```

## Vorverarbeitung
Für die Umwandlung von `.tabs`-Dateien nach `.conll` kann das Kommandozeilenprogramm `tabs2conllu` verwendet werden.

### Installation
```
pip install .[pre]
```
Oder für Umwandlung nach FoLia-XML:
```
pip install .[pre-folia]
```
Benutzung siehe [readme](preprocessing/README.md) im `preprocessing`-Verzeichnis.

## Entwicklungssetup

```shell
pip install -r requirements.txt -r requirements-dev.txt
```

### Tests

```shell
pytest
```
