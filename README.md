# DWDS Wortprofil (wordprofile)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.15798451.svg)](https://doi.org/10.5281/zenodo.15798451)

Das *DWDS Wortprofil* Projekt bildet das Backend für die unter www.dwds.de/wp hinterlegte Übersicht von Kollokationen.
Als Grundlage für die Erstellung eines Wortprofils dienen Korpora des ZDL der BBAW.

## Project setup

To install the full editable project including dev dependencies, run:

    pip install -U pip pip-tools setuptools
    pip-sync requirements/*.txt

## Erstellen eines Wortprofils
Für das Erstellen eines *Wortprofils* sind folgende Schritte nötig:

0. Datenkonvertierung + Annotation
1. Kollokationsextraktion
2. Aggregation der Teilkorpora
  2.1. Berechnung der Statistiken
  2.2. Finden von MWE aus extrahierten Matches
3. Befüllen der Datenbank

Falls das Korpus für das Wortprofil aus verschiedenen Teilen (Subkorpora) besteht, wird der Schritt der Konvertierung und Annotation sowie die Extraktion der Kollokationen für jedes Subkorpus separat durchgeführt. Im zweiten Schritt werden die Daten aus den Teilkorpora aggregiert.

### 0. Datenkonvertierung + Annotation
Sofern die Korpusdaten noch nicht annotiert und im `.conll`-Format vorliegen, müssen sie zunächst konvertiert und mit Dependenzannotationen und morphologischen Annotationen versehen werden (s. `preprocessing`). Die Skripte zur Annotation und Kollokationsextraktion erwarten mit `gzip` komprimierte Dateien.

### 1. Kollokationsextraktion

In diesem Schritt werden für jedes Teilkorpus die jeweiligen Kollokationen mit Treffern (Matches) extrahiert und die Belegsätze verarbeitet.
Hierzu wird das Skript `wordprofile/cli/extract_collocations.py` verwendet (bei Aufruf als Skript muss der Pythonpath richtig gesetzt sein):

```sh
options:
  -h, --help           show this help message and exit
  --input [INPUT ...]  (gzip compressed) conll input file(s). As default stdin is used, if this option is not used.
  --dest DEST          temporary storage path
  --njobs NJOBS        number of process jobs
```
Als `--input` werden mehrere `.conll`-Dateien akzeptiert.
Beispielaufruf:
```shell
python -m wordprofile.cli.extract_collocations --input corpora/test_corpus.conll.gz --dest test_wp/colloc/test_corpus --njobs 4
```
Die Datei `test_corpus.conll.gz` wird verarbeitet, die extrahierten Daten werden nach `test_wp/colloc/test_corpus` geschrieben.

### 2. Aggregation der Teilkorpora
In diesem Schritt werden die Ergebnisse der Teilkorpora zusammengeführt und die Statistiken über das gesamte Korpus berechnet.
Hierfür ist das Skript `wordprofile/cli/compute_statistics.py` vorgesehen:

```sh
usage: compute_statistics.py [-h] [--dest DEST] [--min-rel-freq MIN_REL_FREQ] [--mwe] src [src ...]

positional arguments:
  src                           Path to input data

options:
  -h, --help                    show this help message and exit
  --dest DEST                   Output path
  --min-rel-freq MIN_REL_FREQ   Minimal frequency filter for aggregated collocations
  --mwe                         Extract MWE collocations
```

#### 2.1. Berechnung der Statistiken
Beispielaufruf:
```shell
python wordprofile/cli/compute_statistics.py test_wp/colloc/* --dest test_wp/stats --min-rel-freq 5
```
In diesem Aufruf werden die Teilkorpora in `test_wp/colloc` zusammengeführt, die Frequenzen der Kollokationen addiert und die logDice-Werte berechnet. Kollokationen, die insgesamt die Mindestfrequenz (`--min-rel-freq`) nicht erreichen, werden aus den Ergebnissen entfernt (Default ist 5). Ebenso werden Kookurrenzen entfernt, deren logDice-Wert kleiner null ist.


#### 2.2. Finden von MWE aus extrahierten Matches
Mit der Option `--mwe` werden nach der Zusammenführung der Teilkorpora Verkettungen von Kollokationen ("Mehrwortausdrücke") gesucht, d.h. Überlappungen zweier Kollokationen.

### 3. Befüllen der Datenbank

In diesem Schritt werden die Ergebnisse in die Datenbank geschrieben und Indizes auf den Datenbanktabellen erstellt, um eine performante Abfrage der Kollokationen zu ermöglichen.

#### 3.1. Starten einer lokalen Datenbankinstanz

Wenn per Umgebungsvariablen keine anderen Einstellungen vorliegen, wird eine lokale Datenbankinstanz befüllt. Um eine solche in einem zur Verfügung zu stellen, wird per Docker ein entsprechender MariaDB-Container gestartet:

```sh
docker compose up db
```

Die Daten der Instanz befinden sich auf einem Docker-Volume, von wo sie zur Verbringung auf andere Systeme kopiert werden können. Unter GNU/Linux befindet sich das Volume z. B. standardmäßig im Dateisystem unter

`/var/lib/docker/volumes/wordprofile_db/_data`

Zum Entfernen des Containers und seiner Daten nach Erstellung eines Profils, dient das Kommando

``` sh
docker compose down db -v
```

#### 3.2. Befüllen der Datenbank

Die Daten liegen in Dateiform so vor, dass sie direkt in eine SQL DB
geladen werden können. Hierzu dient folgendes Skript:

```sh
python wordprofile/cli/load_database.py test_wp/stats
```

Mit dem optionalen Parameter `--clear` kann die Datenbank vor einem (erneuten) Befüllen bereinigt werden.

## Vorverarbeitung
Für die Umwandlung von `.tabs`-Dateien nach `.conll` können die Python-Skripte `data_update.py` oder `tabs2conllu.py` verwendet werden (im Verzeichnis `wordprofile/preprocessing/cli/`).

Benutzung siehe [readme](wordprofile/preprocessing/README.md) im `wordprofile/preprocessing`-Verzeichnis.

### Tests
Tests für das gesamt Projekt werden ausgeführt via:

```shell
pytest
```

## Hintergrund
Das *DWDS Wortprofil* wird im Rahmen des Zentrums für digitale Lexikographie der deutschen Sprache ([ZDL](https://www.zdl.org/)) an der Berlin-Brandenburgischen Akademie der Wissenschaften ([BBAW](https://www.bbaw.de/)) entwickelt. Dieses Projekt ist eine Neuimplementierung des Wortprofils von Jörg Didakowski ([1],[2]) und ersetzt u.a. dessen Syntaxanalyse mittels formaler (handgeschriebener) Grammatiken durch einen auf [UD](https://universaldependencies.org/) trainierten Dependenzparser.

[1] Geyken, A., Didakowski, J., & Siebert, A. (2009). 'Generation of word profiles for large German corpora'. Corpus Analysis and Variation in Linguistics, 141-157. [[PDF](https://www.dwds.de/dwds_static/publications/text/Geyken_Didakowksi_Siebert_WordProfiles_Ms.pdf)]

[2] Didakowski, J. und Geyken, A. (2014). 'From DWDS corpora to a German word proﬁle – methodological problems and solutions'. In: OPAL – Online publizierte Arbeiten zur Linguistik 2/2014, S. 39–47. [[PDF](https://www.dwds.de/dwds_static/publications/pdf/didakowski_geyken_internetlexikografie_2012_final.pdf)]

## Kontakt
Bis Herbst 2023 wurde das DWDS Wortprofil hauptsächlich durch René Knaebel entwickelt. Seitdem wurde Entwicklung und Maintenance von [Luise Köhler](mailto:luise.koehler@bbaw.de) übernommen.

# License
The DWDS Wortprofil (wordprofile) is licensed under the GNU General Public License v3.0.

[Luise Köhler](mailto:luise.koehler@bbaw.de)
