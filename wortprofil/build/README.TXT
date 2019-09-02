WORTPROFILBAU


=================================================================================
Zugrundeliegende Daten
  
  Für die Erstellung eines Wortprofils müssen einige Daten Vorhanden sein, aus deren ein Wortprofil erstellt wird.
  Die Daten sind teilweise nochmals in der Wortprofil-Beispiel-Bauspezifikation ./build/spec/dradio.xml' beschrieben.
=================================================================================

*Corpora
  Für die einzelnen Korpora müssen SynCoPe-Parser-Eingabedateien vorliegen (*.wp). Diese werden für die berechnung der Texttreffer
  benötigt. Die Dateien folgen einem TAB-separierten Format.

  In der ersten Zeile der Datei steht stehts der Dateiname des zugrundeliegenden Dokuments
  Die Informationen zu den einzenen Token volgen Zeilenweise. Jede Tokeninformation hat folgende TAB-separite Felder:

    1) Tokentyp (nur für den SynCoPe-Parser relevant)
    2) Oberflächenform
    3) Lemmaform
    4) Wortkategorie (POS-Tag)
    5) Leerzeichenangabe (0=ohne führendes Leerzeichen, 1=mit führendem Leerzeichen)

  Eine Menge von Token wird durch eine Satzinformation eingeleitet. Jede Satzinformation hat folgende TAB-separite Felder:
  
    1) Satztyp (nur für den SynCoPe-Parser relevant)
    2) Seitenzahl

  Ein Beispiel für solch eine Datei ist durch '../doc/examples/corpus_file_example.wp' gegeben
  
*Bibliographische Angaben
  Zu den einzelnen Korpora muss eine Datei mit bibliographische Informationen (Meta-Daten) angegeben werden. 
  Eine entsprechende Datei muss in einem TAB-separierten Format vorliegen und folgt folgender Struktur: 
  Datei\tAttribut\tWert. So werden für Jedes Korpusdokument Attribut-Wert-Paare definiert.

  Ein Beispiel für solch eine Datei ist durch '../doc/examples/bibliography_example.table' gegeben

*Gute Beispiele
  Zu den einzelnen Korpora kann eine Datei angegeben werden, über die die einzelnen Korpus-Sätze gewichtet sind. 
  Eine entsprechende Datei liegt in einem TAB-separierten Format vor und folgt folgender Struktur: Datei\tSatz\tScore. 

  Ein Beispiel für solch eine Datei ist durch '../doc/examples/sentence_scores_example.table' gegeben

*Satz-Dubletten
  Es können können XML-Dateien angegeben werden (z.B. für jedes Korpus aber auch eine Datei für alle Korpora), die 
  Satz-Dubletteninformationen enthalten.

  Die XML-Struktur solch einer Dubletten-Datei folgt folgender Struktur:

  <doubles>
          ...
          <double length="14" number="2">
                  <item corpus="dradio" file="./src/id_217049.ddc.xml" sentence="103"/>
                  <item corpus="dradio" file="./src/id_217050.ddc.xml" sentence="103"/>
          </double>
          ...
  </doubles>

  Hier steht 'length' für die Länge des entsprechenden Satzes und 'number' für die Anzahl von Dubletten+Original. 
  Über 'corpus' wird das Korpuskürzel angegeben, über 'file' der Dateiname und üner 'sentence' die Satzposition. 

  Ein Beispiel für solch eine Datei ist durch '../doc/examples/doubles_example.xml' gegeben

*Kookkurrenzdaten
  Die Kookkurrenzdaten, die vom Syntaxparsers generiert wurden, sollten unter '../relations' unter einem entsprechendem Korpusnamen (z.B. '../relations/dradio') liegen, 
  wobei die Kookkurrenzdaten als TAB-separierte Dateien vorliegen. Die Informationen zu einer Kookkurrenz in einer Kookkurrenz-Datei 
  sind folgend TAB-separiert aufgebaut:

    1) Lemmaform des ersten Wortes
    2) Lemmaform des zweiten Wortes
    3) Lemmaform der Präposition
    4) Oberflächenform des ersten Wortes
    5) Oberflächenform des zweiten Wortes
    6) Oberflächenform der Präposition
    7) Wortart des ersten Wortes
    8) Wortart des zweiten Wortes
    9) Wortart der Präposition
    10) Position des ersten Wortes im Satz
    11) Position des zweiten Wortes im Satz
    12) Position der Präposition im Satz
    13) Position des Satzes im Text (der wievielte Satz)
    14) Dateiname
    15) syntaktischer Trigger (Informationen über den syntaktischen Kontext) 

  Hierbei werden die einzelnen Trigger durch '|' getrennt geschrieben: T_1|T_2|...|T_n
  Ein Trigger spiegelt hierbei einen bistimmten syntaktischen Kontext wider. 
  Von SynCoPe weden folgende Trigger eingestreut:

    -HasComma: ist in Koordination mit Komma
    -IsCJ: ist zweitglied in einer Koordination
    -HasPRF: Bei einem Subjekt existiert auch ein Akkusativobjekt mit 'sich'
    -isAmbig: Verb hat ambige Wortzerlegung
    -HasKON: ist in Koordination mit Konjunktion
    -HasSUBJ: Verb hat Subjekt
    -HasSUBJnn: Verb hat ein einfaches Nomen oder ein Personalpronomen als Subjekt
    -IsPost: Genitivattribut ist nachgestellt
    -IsPre: Genitivattribut ist vorangestellt
    -HasDET: Nominalgruppe hat einen Determiner
    -HasS: befindet sich unter einem Satzknoten (ist in einen vollständig analysierten (Teil-)Satz eingebettet)
    -SentEWP: der Satz endet mit einem Satzzeichen
    -SentBWU: der Satz beginnt mit einem Großbuchstaben
    -SentIC: dem Satz konnte eine zusammenhängende Struktur zugewiesen werden (vollständige Analyse)
    -SentHU: der Satz enthält keine unbekannten Wörter
    -HasATTR: Nominalgruppe hat Adjektivattribut
    -HasPART: Infinitivobjekt mit zu
    -leftNN: Nominalgruppe hat direkt links daneben ein Nomen (NN,XY,NE,FM)
  
  Ein Beispiel für solch eine Datei (Subjekt-Relation) ist durch '../doc/examples/SUBJA__VVFIN_NN_example.rel' gegeben

  Die Relationsdateien sind mit einem Relationsbezeichner präfigiert. Die Bezeichner haben folgende Bedeutung:

    ADV ->  adverbiale Modifikation
    APP -> Nominale Modifikation im Sinne einer Apposition (nomen varians/invarians, enge Apposition, echte Apposition, etc.)
    ATTR -> Adjektivattribut
    AUX -> modifikation durch ein Hilfsverb
    AVZ+ -> Abgetrenntes Verbpräfix (Verb - Präfix)
    AVZ -> Abgetrenntes Verbpräfix (Verb - Verb+Präfix)
    CJ -> Konjunkt
    DET -> Determiner
    GMOD -> Genitivattribut
    KOM -> unterordnung an die Vergleichsworte 'als' und 'wie'
    KOM-CJ -> dreistellige Relation mit dem Zentrum der Vergleichsworte 'als' und 'wie'
    KON -> anbindung einer Konjunktion an das rechtsliegende Konjunkt
    OBJA -> Akkusativobjekt
    OBJA+ -> Akkusativobjekt, wobei auch ein Dativobjekt vorhanden ist
    OBJD -> Dativobjekt
    OBJD+ -> Dativobjekt, wobei auch ein Akkusativobjekt vorhanden ist
    OBJI -> Infinitivobjekt
    PN -> Anbindung an eine Präposition oder Postposition
    PP -> Anbingung über eine Präposition oder Postposition
    PP-PN -> dreistellige Relation mit dem Zentrum der Präposition oder Postposition
    SUBJA-PN -> logische Subjekt als PP in Passivsätzen
    SUBJA -> Subjekt
    SUBJ-PRED -> Subjekt bei Kopulakonstruktuionen
    SUBJP -> Passivsubjekt
    VZ+ -> nicht-abgetrenntes Verbpräfix (Verb - Präfix)
    VZ -> nicht-abgetrenntes Verbpräfix (Verb - Verb+Präfix)

=================================================================================
Wortprofilerstellung
=================================================================================

*Beschreibung der verwendeten Statistiken (im TWiki):
 -für das normale Wortprofil:
    http://odo.dwds.de/twiki/bin/view/DWDS/WortProfilStatistik
 -für den Wortvergleich:
    http://odo.dwds.de/twiki/bin/view/DWDS/WortprofilVergleich

*Bau-Spezifikation
  -Die Spezifikation muss als XML-Datei vorliegen. Der Grundaufbau solch einer Datei ist über
   die Spezifikation './spec/dradio.xml' erläutert. Dort sind die XML-Struktur und 
   die Parameter aufgezählt und beschrieben. Zudem sind die Formate von den Dateien beschrieben,
   die zusätzlich über die Spezifikation eingebunden werden. Eine Spezifikation sollte sich 
   stets unter './spec/' befinden. 

*Lexer-Regeln
  -Für den Bau werden Lemmaformen und Oberflächenformen geprüft und evtl. umgeschrieben. Dies 
   wird über einen re2c-Lexer gemacht. Die Regeln für den Lexer sind in der re2c-Datei 
   './spec/LexerRules.re2c' zu finden. Diese können nach belieben angepasst werden. Entsprechende 
   Regeln und Funktionen sind in der Datei Beschrieben.

*Kompilieren des C++-Projektes:
  -Um das Projekt zu bauen 'make all' aufrufen. 
  -Um die gebauten Dateien zu löschen 'make clean' aufrufen. 
  -die Binaries werden in './bin' abgelegt.
  -der generierte Lexer 'LexerRules.h' wird in './source/include' abgelegt.
  -die C++-Quellen liegen in './source'

*Bau der Wortprofilstatistik:
  -'sh build_statistics.sh -s {Spezifikationsdateiname}' aufrufen
  -Die Informationen für die Berechnung sind in der Bau-Spezifikation anzugeben
  -Beispiel: sh build_statistics.sh -s ./spec/dradio.xml

*Bau der Texttreffer:
  -'sh build_hits.sh -s {Spezifikationsdateiname}' aufrufen
  -Die Informationen für die Berechnung sind in der Bau-Spezifikation anzugeben
  -Beispiel: sh build_hits.sh -s ./spec/dradio.xml

*Bau der Wortprofilstatistik und der Texttreffer:
  -'sh build.sh -s {Spezifikationsdateiname}' aufrufen
  -hierdurch werden 'build_statistics.sh' und 'build_hits.sh' nacheinander aufgerufen.
  -Beispiel: sh build.sh -s ./spec/dradio.xml

=================================================================================
Das wird erstellt
=================================================================================

*Folgende TAB-Separiete Tabellendateien werden beim Bau der Wortprofilstatistik erstellt:
 + relations.table -> Tabelle mit statistisch bewerteten syntaktischen Kookkurrenzen für die verschiedenen syntaktischen Relationen (MySQL: relations)
   -Relationsname
   -ID der Lemmaform der Präposition
   -ID der Lemmaform des ersten Wortes
   -ID der Lemmaform des zweiten Wortes
   -ID der Oberflächenform der Präposition
   -ID der Oberflächenform des ersten Wortes
   -ID der Oberflächenform des zweiten Wortes
   -ID der Wortkategorie der Präposition
   -ID der Wortkategorie des ersten Wortes
   -ID der Wortkategorie des zweiten Wortes
   -ID für die Trefferinforationen
   -Anzahl an Texttreffern mit Rechten
   -Frequenz
   -Statistikwert: MI3
   -Statistikwert: MiLogFreq
   -Statistikwert: TScore
   -Statistikwert: LogDice
   -Statistikwert: LogLike

 + mapping_lemma.table -> Lemmaformen auf IDs abbilden (MySQL: lemmaToRelation)
   -ID
   -Lemmaform
 
 + mapping_lemma_lower.table -> Lemmaformen auf IDs abbilden, mit Ignorieren der Großschreibung (MySQL: lemmaToRelationLower)
   -ID
   -Lemmaform

 + mapping_surface.table -> Oberflächenformen auf IDs abbilden (MySQL: idToSurface)
   -ID
   -Oberflächenform

 + mapping_POS.table -> Wortkategorien auf IDs abbilden (MySQL: idToPOS)
   -ID
   -Wortkategorie
 
 + mapping_function.table -> syntaktische Relationen auf IDs abbilden (MySQL: idToFunction)
   -ID
   -syntaktische Relation
 
 + mapping_file.table -> Dateinamen auf IDs abbilden (MySQL: idToFile)
   -ID
   -Dateiname
 
 + mapping_corpus.table -> Korpuskürzel auf IDs abbilden (MySQL: idToCorpus)
   -ID
   -Korpusname

 + mapping_corpus_name.table -> Korpuskürzel auf Korpusnamen abbilden (MySQL: CorpusName)
   -Korpuskürzel
   -ausführlicher Korpusname

 + head_pos_rel_freq.table -> Frequenzen von (w1,POS1,R) mit w1=erstes Wort, POS1=Wortkategorie und R=syntaktische Relation (MySQL: headPosRelFreq)
   -ID der Lemmaform
   -ID der Wortkategorie
   -ID der syntaktischen Relation
   -Frequenz
   -Anzahl (verschiedener)
 
 + head_pos_freq.table -> Frequenzen von (w1,POS1) mit w1=erstes Wort und POS1=Wortkategorie (MySQL: headPosFreq)
   -ID der Lemmaform
   -ID der Wortkategorie
   -Frequenz
   -Anzahl (verschiedener)

 + rel_info.table -> Meta-Informationen, die sich auf die einzelnen syntaktischen Relationen beziehen (MySQL: relInfo)
   -Relation-ID
   -Anzahl an Kookkurrenzen
   -Anzahl an veerschiedenen Kookkurrenzen
   -Anzahl an Rechtefreien Fundstellen

 + mapping_position_info.table (MySQL: wird nicht eingespielt)
   -Texttreffer-ID
   -Position des ersten Wortes im Satz
   -Position des zweiten Wortes im Satz
   -Position der Präposition im Satz
   -Position des Satzes im Text (die Sätze sind durchnummeriert)
   -Dateinamen-ID
   -Korpus-ID
   -Rechteinformation (Rechtefrei=1)

*Folgende TAB-separierte Attribute-Value-Dateien werden beim Bau der Wortprofilstatistik erstellt:
 + threshold_rel.table -> schwellwerte innerhalb der Spezifikation (Relationsname \t Attribut \t Wert) (MySQL: threshold)
   -min_word_length (minimale Länge für die Oberflächen- und Lemmaformen)
   -max_word_length (maximale Länge für die Oberflächen- und Lemmaformen)
   -min_precut_frequency (minimale Frequenz der Kookkurrenzen vor der Statistikberechnung)
   -max_precut_frequency (maximale Frequenz der Kookkurrenzen vor der Statistikberechnung)
   -min_frequency (minimale Frequenz der Kookkurrenzen nach der Statistikberechnung)
   -max_frequency (maximale Frequenz der Kookkurrenzen nach der Statistikberechnung)
   -min_MiLogFreq (minimaler MiLogFreq-Wert der Kookkurrenzen)
   -max_MiLogFreq (maximaler MiLogFreq-Wert der Kookkurrenzen)
   -min_TScore (minimaler TScore-Wert der Kookkurrenzen)
   -max_TScore (maximaler TScore-Wert der Kookkurrenzen)
   -min_MI3 (minimaler MI3-Wert der Kookkurrenzen)
   -max_MI3 (maximaler MI3-Wert der Kookkurrenzen)
   -min_LogDice (minimaler LogDice-Wert der Kookkurrenzen)
   -max_LogLike (maximaler LogLike-Wert der Kookkurrenzen)

 + types.table -> Typinformationen für MySQL (Attribut \t Wert) (MySQL: types)
   Anzahl von Einträgen in den Tablellen:
     -POSSize (Wortarten)
     -corpusSize (Korpora)
     -lemmaSize (Lemmaformen)
     -surfaceSize (Oberflächenformen)
     -infoSize (Fundstellen)
     -relationSize (Kookkurrrenzen)
   maximale Zeichenkettenlängen innerhalb der Tabellen:
     -POSLength (Wortartennamen)
     -corpusLength (Korpusnamen)
     -lemmaLength (Lemmaform)
     -surfaceLength (interne frequenteste Oberflächenform)
     -surfaceToLemmaLength (Oberflächenform die auf ein Lemma abgebildet wird)
     -MI3Length (Länge des Float in Zeichen)
     -MiLogFreqLength (Länge des Float in Zeichen)
     -TScoreLength (Länge des Float in Zeichen)
     -LogDiceLength (Länge des Float in Zeichen)
     -LogLikeLength (Länge des Float in Zeichen)
     -FilenameLength (Länge des Dateinamens)
     -functionLength (Länge des Relationsnamens)
     -snippetLength (Länge der Relationskurzbeschreibung)
     -descriptionLength (Länge der Relationsbeschreibung)
     -exampleLength (Länge des Beispiels für die Relation)
   Maximalwerte innerhalb der Tabellen:
     -highestFrequency (Frequenz)
     -highestDepFrequency (Frequenz der Dependenten der Relationen)
     -highestHeadFrequency (Frequenz der Köpfe der Relationen)
     -highestDepCount (Anzahl der verschiedenen Dependenten der Relationen)
     -highestHeadCount (Anzahl der verschiedenen Köpfe der Relationen)
  
 + info.table -> Projekt-Informationen (Attribut \t Wert) (MySQL: Info)
     -Author
     -Erstellungsdatum
     -Spezifikationsdateiname
     -Versionsnummer der Spezifikationsdatei

*Folgende TAB-Separiete Tabellendateien werden beim Bau der Texttreffer erstellt:
  + mapping_position_info_tei.table -> Treffer-ID auf Satz-Informationen abbilden (MySQL: idToInfo)
    -Texttreffer-ID
    -Position des ersten Wortes im Satz
    -Position des zweiten Wortes im Satz
    -Position der Präposition im Satz
    -Position des Satzes im Text (die Sätze sind durchnummeriert)
    -Dateinamen-ID
    -Korpus-ID
    -Rechteinformation (Rechtefrei=1)
    -Datum-ID (die IDs sind entsprechend der Datumssortierung angelegt)
    -negierte Datum-ID (für eine umgekehrte Sortierung bei MySQL)
    -Satzbewertung-Score (z.B. aus den "Guten Beispielen")

  + concord_sentences.table -> die einzelnen Sätze (MySQL: concordSentences)
    -Korpus-ID
    -Dateinamen-ID
    -Position des Satzes im Text (die Sätze sind durchnummeriert)
    -der Satz (Token sind durch '\x01' und '\x02' getrennt, wobei '\x01'=ohne Leerzeichen und '\x02'=mit Leerzeichen)
    -Seitenangabe

  + mapping_TEI_textclass.table (MySQL: idToTextclass)
    -ID
    -Texstklasse

  + mapping_TEI_sigle.table (MySQL: noch nicht integriert)
    -ID
    -Sigle

  + mapping_TEI_orig.table (MySQL: idToOrig)
    -ID
    -Bibl-String der Ersterscheinung

  + mapping_TEI_scan.table (MySQL: idToScan)
    -ID
    -Bibl-String der Vorliegenden Version
  
  + mapping_TEI_date.table (MySQL: idToDate)
    -ID
    -Datum (DDC-Format)

  + mapping_TEI_avail.table (MySQL: idToAvail)
    -ID
    -Rechte-String (OR,MR,...)

  + mapping_TEI.table -> Datei eines Korpus auf TEI-Informationen abbilden (MySQL: idToTei)
    -Korpus-ID
    -Datei-ID
    -Orig-String
    -Scan-String
    -Textklasse-ID
    -Rechte-ID

*Folgende TAB-separierte Attribute-Value-Dateien werden beim Bau der Texttreffer erstellt:
  + TEI_types.table (Attribute \t Value) (MySQL: teiTypes)
   Anzahl von Einträgen in den Tablellen:
   -DateSize (Datumsangeben)
   -TextclassSize (Textklassen)
   -OrigSize (Orig-Angabe)
   -ScanSize (Orig-Angabe)
   -SigleSize (Sigle)
   -sentenceSize (Sätze)
   -infoSize (Texttreffer)
   maximale Zeichenkettenlängen innerhalb der Tabellen:
   -lengthDate (Datum-String)
   -lengthTextclass (Textklassenname)
   -lengthOrig (Orig-String)
   -lengthScan (Scan-String)
   -lengthAvail (Rechte-String)
   -lengthSigle (Siglenname)

