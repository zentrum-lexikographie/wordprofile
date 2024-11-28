# DWDS Wortprofil (wordprofile)

Das *DWDS Wortprofil* Projekt bildet das Backend für die unter www.dwds.de/wp hinterlegte Übersicht von Kollokationen.
Als Grundlage für die Erstellung eines Wortprofils dienen Korpora des ZDL der BBAW.

## Project setup

Dependency management is done via [pipenv](https://pipenv.pypa.io/),
virtual environments and Python version management is done via
[pyenv](https://github.com/pyenv/pyenv#getting-pyenv):

    curl https://pyenv.run | bash
    # add pyenv hooks to ~/.bashrc
    pip install --user pipenv


To install the full project and dev dependencies, run:

    pipenv sync --categories="packages api build prep dev-packages"

If not all parts of the project are necessary, specify the relevant ones using the `categories` option.

The default category (`packages`) and the `api` category contain the packages necessary to run the wordprofile as a service.
The `build` category is necessary for data processing (collocation extraction, statistics, database population).
The `prep` category corresponds to the preprocessing step (data conversion, annotation). A model for dependency annotation has to be installed separately (see below).
`dev-packages` (or `--dev`) contains packages for testing and code maintenance.


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
Sofern die Korpusdaten noch nicht annotiert und im `.conll`-Format vorliegen, müssen sie zunächst konvertiert und mit Dependenzannotationen und morphologischen Annotationen versehen werden (s. `preprocessing`).

### 1. Kollokationsextraktion

In diesem Schritt werden für jedes Teilkorpus die jeweiligen Kollokationen mit Treffern (Matches) extrahiert und die Belegsätze verarbeitet.
Hierzu wird das Skript `wordprofile/cli/extract_collocations.py` verwendet (bei Aufruf als Skript muss der Pythonpath richtig gesetzt sein):

```sh
options:
  -h, --help           show this help message and exit
  --input [INPUT ...]  conll input file(s). As default stdin is used, if this option is not used.
  --dest DEST          temporary storage path
  --njobs NJOBS        number of process jobs
```
Als `--input` werden mehrere `.conll`-Dateien akzeptiert.
Beispielaufruf:
```shell
python -m wordprofile.cli.extract_collocations --input corpora/test_corpus.conll --dest test_wp/colloc/test_corpus --njobs 4
```
Die Datei `test_corpus.conll` wird verarbeitet, die extrahierten Daten werden nach `test_wp/colloc/test_corpus` geschrieben.

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

```sh
usage: load_database.py [-h] [--user USER] [--db DB] source

positional arguments:
  source       temporary storage path

options:
  -h, --help   show this help message and exit
  --user USER  database username
  --db DB      database name
```

Die Daten liegen in Dateiform so vor, dass sie direkt in eine SQL DB geladen werden können. Die Datenbank wird in ein lokales Verzeichnis (`data/db`) geschrieben, das in den Dockercontainer gemountet wird.
Bevor der Dockercontainer gestartet wird, sollte sichergestellt werden, dass dieses Verzeichnis existiert und dem korrekten User gehört, z.B.:
```sh
mkdir -p data/db
```
Der Dockercontainer wird unter dem entsprechenden User gestartet; dazu muss die Umgebungsvariable `USER_GROUP` gesetzt sein:
```sh
export USER_GROUP=$(id -u):$(id -g)
```
Danach kann der Container gestartet werden mit
```sh
docker compose build # falls Container noch nicht existiert
docker compose up
```

Beispielaufruf:
```shell
python wordprofile/cli/load_database.py test_wp/stats --user wpuser --db test_wp
```


## Vorverarbeitung
Für die Umwandlung von `.tabs`-Dateien nach `.conll` können die Python-Skripte `preprocessing/data_update.py` oder `perprocessing/tabs2conllu.py` verwendet werden.

Benutzung siehe [readme](preprocessing/README.md) im `preprocessing`-Verzeichnis.

### Installation
Die Installation der für die Vorverarbeitung nötigen Pakete erfolgt folgendermaßen:
```
pipenv sync --categories prep
```

## Entwicklungssetup

```shell
pipenv sync --dev
```

### Tests
Tests für das gesamt Projekt werden ausgeführt via:

```shell
pytest
```

Um diejenigen Tests auszuführen, die eine Datenbankverbindung benötigen, wird zunächst ein Test-Docker-Container gestartet:
```shell
export USER_GROUP=$(id -u):$(id -g)
docker compose -f docker-compose-test.yml up
```
Für die Integrationstests in `integrations_test.py` und einige Tests aus dem `preprocessing`-Modul wird die Installation des Modells `de_hdt_lg` vorausgesetzt.

## Hintergrund
Das *DWDS Wortprofil* wird im Rahmen des Zentrums für digitale Lexikographie der deutschen Sprache ([ZDL](https://www.zdl.org/)) an der Berlin-Brandenburgischen Akademie der Wissenschaften ([BBAW](https://www.bbaw.de/)) entwickelt. Dieses Projekt ist eine Neuimplementierung des Wortprofils von Jörg Didakowski ([1],[2]) und ersetzt u.a. dessen Syntaxanalyse mittels formaler (handgeschriebener) Grammatiken durch einen auf [UD](https://universaldependencies.org/) trainierten Dependenzparser.

[1] Geyken, A., Didakowski, J., & Siebert, A. (2009). 'Generation of word profiles for large German corpora'. Corpus Analysis and Variation in Linguistics, 141-157. [[PDF](https://www.dwds.de/dwds_static/publications/text/Geyken_Didakowksi_Siebert_WordProfiles_Ms.pdf)]

[2] Didakowski, J. und Geyken, A. (2014). 'From DWDS corpora to a German word proﬁle – methodological problems and solutions'. In: OPAL – Online publizierte Arbeiten zur Linguistik 2/2014, S. 39–47. [[PDF](https://www.dwds.de/dwds_static/publications/pdf/didakowski_geyken_internetlexikografie_2012_final.pdf)]

## Kontakt
Bis Herbst 2023 wurde das DWDS Wortprofil hauptsächlich durch René Knaebel entwickelt. Seitdem wurde Entwicklung und Maintenance von [Luise Köhler](mailto:luise.koehler@bbaw.de) übernommen.

# License
The DWDS Wortprofil (wordprofile) is licensed under the GNU General Public License v3.0.

[Luise Köhler](mailto:luise.koehler@bbaw.de)
