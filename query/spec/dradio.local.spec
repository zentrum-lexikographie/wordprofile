### File: dradio.spec
### Author: didakowski@bbaw.de
### Description: Spezifikationsdatei für das erstellen und Abfragen einer Wortprofil-MySQL-Datenbank

###### MySQL ######
#
# Für die Verbindung und Kommunikation mit MySQL
#
### MySQL-Benutzername
User	wpuser
### MySQL-Hostname oder Socket
Host	127.0.0.1
#Socket	/var/run/mysqld/mysqld.sock
### MySQL-Port
Port	3306
### MySQL-Passwort
Passwd	wpuser
### MySQL-Wortprofil-Datenbankname
Database	wordprofile

###### Daten ######
#
# Ort der Wortprofil-Tabellen und von Tabellen die Umschreibungen von Lemmaformen auf der Eingabe- und Ausgabeseite betreffen
#
### Pfad für die Wortprofil-Tabellen
TablePath	../wortprofil/table/dradio
### Optionale Angabe von Lemmavariationen (TAB-separierte Datei mit 'LemmaVariation\tLemma')
### Falls mehrere solcher Dateien vorliegen, können diese untereinander über 'Variations' aufgeführt werden
Variations	./spec/lex_variations.csv
### Optionale Angabe von Lemma-Reparaturen für die Lemmausgabe für verschiedene Wortarten 
### (TAB-separierte Dateien mit 'OriginalLemma\tRepariertesLemma' )
LemmaRepair	Substantiv	./spec/lemma_repair_substantiv.csv
LemmaRepair	Verb	./spec/lemma_repair_verb.csv
LemmaRepair	Adjektiv	./spec/lemma_repair_adjektiv.csv

###### Sonstige Parameter ######
### Angabe der maximalen Tiefe der MWE-Relationen
MweDepth	5

###### Ausgabeoptionen ######
#
# Angabe von Relationsbeschreibungen und Angabe, welche Relationen ausgegeben werden sollen und in welcher Reihenfolge
#
### Default-Relationsbeschreibung ($1 steht für Lemma1 und $2 für Lemma3 und $3 für die Präposition)
RelDescDefault	tritt auf mit	$1 tritt auf mit $2
### Beschreibung für die einzelnen Relationen ($1 steht für Lemma1 und $2 für Lemma3 und $3 für die Präposition)
RelDesc	ADV	hat Adverbialbestimmung	$1 hat Adverbialbestimmung $2
RelDesc	~ADV	ist Adverbialbestimmung von	$1 ist Adverbialbestimmung von $2
RelDesc	OBJ	hat Akkusativ/Dativ-Objekt	$1 hat Akkusativ/Dativ-Objekt $2
RelDesc	~OBJ	ist Akkusativ/Dativ-Objekt von	$1 ist Akkusativ/Dativ-Objekt von $2
RelDesc	PP	hat Präpositionalgruppe	$1 hat Präpositionalgruppe "$3 $2"
RelDesc	~PP	ist in Präpositionalgruppe	"$3 $1" ist Präpositionalgruppe von $2
RelDesc	PRED	hat Prädikativ	$1 hat Prädikativ $2
RelDesc	~PRED	ist Prädikativ von	$1 ist Prädikativ von $2
RelDesc	VZ	hat Verbzusatz	$1 hat Verbzusatz $2
RelDesc	~VZ	ist Verbzusatz von	$1 ist Verbzusatz von $2
RelDesc	KOM	hat vergleichende Wortgruppe	$1 hat vergleichende Wortgruppe $2
RelDesc	~KOM	ist in vergleichender Wortgruppe	$1 ist in vergleichender Wortgruppe von $2
RelDesc	ATTR	hat Adjektivattribut	$1 hat Adjektivattribut $2
RelDesc	~ATTR	ist Adjektivattribut von	$1 ist Adjektivattribut von $2
RelDesc	SUBJA	hat Subjekt	$1 hat Subjekt $2
RelDesc	~SUBJA	ist Subjekt von	$1 ist Subjekt von $2
RelDesc	SUBJP	hat Passivsubjekt	$1 hat Passivsubjekt $2
RelDesc	~SUBJP	ist Passivsubjekt von	$1 ist Passivsubjekt von $2
RelDesc	GMOD	hat Genitivattribut	$1 hat Genitivattribut $2
RelDesc	~GMOD	ist Genitivattribut von	$1 ist Genitivattribut von $2
RelDesc	KON	hat in Koordination mit	$1 ist in Koordination mit $2
RelDesc	META	Überblick	$1 tritt auf mit $2
### Default-Ausgabeordnung der Relationen
RelOrderDefault	META,ATTR,~ATTR,OBJ,~OBJ,PP,~PP,GMOD,~GMOD,KON,PRED,~PRED,KOM,~KOM,SUBJA,~SUBJA,SUBJ,~SUBJ,VZ,~VZ,ADV,~ADV,SUBJP,~SUBJP
### Ausgabeordnung der Relationen zu den einzelnen Wortarten
RelOrder	Adjektiv	META,~ATTR,~PRED,ADV,~ADV,KON,KOM
RelOrder	Verb	META,ADV,OBJ,PP,KON,SUBJ,SUBJA,PRED,VZ,KOM,SUBJP
RelOrder	Substantiv	META,ATTR,~OBJ,~PP,GMOD,KON,PRED,KOM,~SUBJ,~SUBJA,PP,~GMOD,~PRED,~KOM
RelOrder	Personalpronomen	META,ATTR,~OBJ,~PP,GMOD,KON,PRED,KOM,~SUBJ,~SUBJA,PP,~GMOD,~PRED,~KOM
### Default-Ausgabeordnung der MWE-Relationen
MweRelOrderDefault	ATTR,~ATTR,OBJ,~OBJ,PP,~PP,GMOD,~GMOD,PRED,~PRED,KOM,~KOM,SUBJA,~SUBJA,SUBJ,~SUBJ,ADV,~ADV,SUBJP,~SUBJP
### Ausgabeordnung der MWE-Relationen zu den einzelnen Wortarten
MweRelOrder	Adjektiv	~ATTR,~PRED,ADV,~ADV,KOM
MweRelOrder	Verb	ADV,OBJ,PP,SUBJ,SUBJA,PRED,KOM,SUBJP
MweRelOrder	Substantiv	ATTR,~OBJ,~PP,GMOD,PRED,KOM,~SUBJ,~SUBJA,PP,~GMOD,~PRED,~KOM
MweRelOrder	Personalpronomen	ATTR,~OBJ,~PP,GMOD,PRED,KOM,~SUBJ,~SUBJA,PP,~GMOD,~PRED,~KOM



