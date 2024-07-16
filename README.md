# DWDS Wortprofil (wordprofile)

Das *DWDS Wortprofil* Projekt bildet das Backend für die unter www.dwds.de/wp hinterlegte Übersicht von Kollokationen.
Als Grundlage für die Erstellung eines Wortprofils dienen Korpora des ZDL der BBAW.
Grundlage für eine Wortprofil-Datenbank und deren Abfrage ist eine Wortprofil-Spezifikation.
Diverse Konfigurationen und zusätzliche Daten liegen unter `spec`.
Im Ordner `log` werden Server-Logfiles hinterlegt.

## Project setup

Dependency management is done via [pipenv](https://pipenv.pypa.io/),
virtual environments and Python version management is done via
[pyenv](https://github.com/pyenv/pyenv#getting-pyenv):

    curl https://pyenv.run | bash
    # add pyenv hooks to ~/.bashrc
    pip install --user pipenv


To install the full project and dev dependencies, run:

    pipenv install --categories="packages api build prep dev-packages"

If not all parts of the project are necessary, specify the relevant ones using the `categories` option.

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

```
-rw-r--r-- 1 knaebel users  127M Feb 24  2023 sz_regional.conll.bz2
-rw-r--r-- 1 knaebel users  554M Feb 24  2023 tsp_regional.conll.bz2
-rw-r--r-- 1 knaebel users  590M Feb 24  2023 noz.conll.bz2
-rw-r--r-- 1 knaebel users  727M Feb 24  2023 noz_regional.conll.bz2
-rw-r--r-- 1 knaebel users 1000M Feb 24  2023 nzz_regional.conll.bz2
-rw-r--r-- 1 knaebel users  931M Feb 24  2023 tsp_legacy.conll.bz2
-rw-r--r-- 1 knaebel users  3,2G Feb 24  2023 welt.conll.bz2
-rw-r--r-- 1 knaebel users  1,9G Feb 24  2023 tsp.conll.bz2
-rw-r--r-- 1 knaebel users  2,2G Feb 24  2023 fr_regional.conll.bz2
-rw-r--r-- 1 knaebel users  2,9G Feb 24  2023 sz.conll.bz2
-rw-r--r-- 1 knaebel users  3,2G Feb 24  2023 nzz.conll.bz2
-rw-r--r-- 1 knaebel users  3,2G Feb 24  2023 sz_legacy.conll.bz2
-rw-r--r-- 1 knaebel users  3,8G Feb 24  2023 fr.conll.bz2
-rw-r--r-- 1 knaebel users   60M Mär  7  2023 wikivoyage.conll.bz2
-rw-r--r-- 1 knaebel users  5,7G Mär  7  2023 wikipedia.conll.bz2
-rw-r--r-- 1 knaebel users  838M Mär 22  2023 nnzz_regional.conll.bz2
-rw-r--r-- 1 knaebel users  2,7G Mär 22  2023 nnzz.conll.bz2
```

In diesem ersten Schritt werden für jeden Korpus (dradio und pnn) die jeweiligen Matches extrahiert, die Satzbelege aufgearbeitet und die Korpus-Kollokationsstatistik berechnet.
Die Daten liegen in nicht-komprimierter Form vor.
Dies erleichtert den Schritt der Vereinigung aller Teilkorpora erheblich.
```shell
python -m wordprofile.cli.extract_collocations --input corpora/dradio.conll --dest test_wp/stage/dradio --njobs 4
python -m wordprofile.cli.extract_collocations --input corpora/pnn.conll --dest test_wp/stage/pnn --njobs 4
```

### Berechnung Wortprofil
Als nächstes werden die extrahierten Informationen beider Korpora aus `test_wp/stage` vereint und unter `test_wp/final` gespeichert.
Weiterhin werden die Daten für die Datenbank vorbereitet und komprimiert bzw. normalisiert.
Statistiken werden in der jeweiligen Kollokationsdatei ergänzt, bevor diese ausgeschrieben wird.

```shell
python wordprofile/cli/compute_statistics.py test_wp/stage/* --dest test_wp/final --min-rel-freq 5 --mwe
```
In diesem Aufruf werden bei der Berechnung des Wortprofils alle Kollokationen entfernt, die nicht mindestens eine Frequenz von 5 aufweisen.
Im Anschluss werden aus den Kollokationen MWAs berechnet, die sich aus der Kombination zweier sich überlappender Kollokationen ergeben.

### DB befüllen
Im letzten Schritt wird das finale, komprimierte und für die Datenbank vorbereitete Wortprofil in die Datenbank transferiert.
Die Daten liegen in Dateiform so vor, dass sie direkt in eine SQL DB geladen werden können. Diese Dateien werden in ein lokales Verzeichnis (`data/db`) geschrieben, das in den Dockercontainer gemountet wird.
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
docker compose up
```

Anschließend werden noch notwendige Indizes erstellt, welche eine performante Abfrage der Kollokationen und ihrer Informationen ermöglichen.
```shell
python wordprofile/cli/load_database.py test_wp/final --user wpuser --db test_wp
```

## Build

```shell
docker-compose build
```

## Vorverarbeitung
Für die Umwandlung von `.tabs`-Dateien nach `.conll` können die Python-Skripte `preprocessing/data_update.py` oder `perprocessing/tabs2conllu.py` verwendet werden.

Benutzung siehe [readme](preprocessing/README.md) im `preprocessing`-Verzeichnis.

### Installation
Die Installation der für die Vorverarbeitung nötigen Pakete erfolgt folgendermaßen:
```
pipenv install --categories prep
```

## Entwicklungssetup

```shell
pipenv install --dev
```

### Tests

```shell
pytest
```

Um diejenigen Tests auszuführen, die eine Datenbankverbindung benötigen, wird zunächst ein Test-Docker-Container gestartet:
```shell
export USER_GROUP=$(id -u):$(id -g)
docker compose -f docker-compose-test.yml up
```
