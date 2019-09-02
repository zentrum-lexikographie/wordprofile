/**
 * Über das Programm werden Tabellen neu und lückenlos durchnummeriert. 
 * Es werden eventuell werte negiert, um eine bestimmte Sortierung in MySQL zu erhalten.
 * Für MySQL werden Typinformationen aus den Tabellen generiert und geschrieben
 * 
 * folgende Tabellen werden generiert: 
 *
 * + types.table -> Typinformationen für MySQL (Name - Wert)
 *      Anzahl von Einträgen in den Tablellen:
 *       -POSSize (Wortarten)
 *       -corpusSize (Korpora)
 *       -lemmaSize (Lemmaformen)
 *       -surfaceSize (Oberflächenformen)
 *       -infoSize (Fundstellen)
 *       -relationSize (Kookkurrrenzen)
 *
 *      maximale Zeichenkettenlängen innerhalb der Tabellen:
 *       -POSLength (Wortartennamen)
 *       -corpusLength (Korpusnamen)
 *       -lemmaLength (Lemmaform)
 *       -surfaceLength (interne frequenteste Oberflächenform)
 *       -surfaceToLemmaLength (Oberflächenform die auf ein Lemma abgebildet wird)
 *       -MI3Length (Länge des Float in Zeichen)
 *       -MiLogFreqLength (Länge des Float in Zeichen)
 *       -TScoreLength (Länge des Float in Zeichen)
 *       -LogDiceLength (Länge des Float in Zeichen)
 *       -LogLikeLength (Länge des Float in Zeichen)
 *       -FilenameLength (Länge des Dateinamens)
 *       -functionLength (Länge des Relationsnamens)
 *       -snippetLength (Länge der Relationskurzbeschreibung)
 *       -descriptionLength (Länge der Relationsbeschreibung)
 *       -exampleLength (Länge des Beispiels für die Relation)
 *
 *      Maximalwerte innerhalb der Tabellen:
 *       -highestFrequency (Frequenz)
 *       -highestDepFrequency (Frequenz der Dependenten der Relationen)
 *       -highestHeadFrequency (Frequenz der Köpfe der Relationen)
 *       -highestDepCount (Anzahl der verschiedenen Dependenten der Relationen)
 *       -highestHeadCount (Anzahl der verschiedenen Köpfe der Relationen)
 * 
 * + info.table -> Projekt-Informationen (Name - Wert)
 *       -Author
 *       -Erstellungsdatum
 *       -Spezifikationsdateiname
 *       -Versionsnummer der Spezifikationsdatei
 *
 * + rel_info.table -> Informationen, die sich auf die einzelnen syntaktischen Relationen beziehen
 *       -Relation-ID
 *       -Anzahl an Kookkurrenzen (ohne doppelte)
 *       -Anzahl an Kookkurrenzen (mit doppelten)
 *       -Anzahl an Rechtefreien Fundstellen
 *
 *  + threshold_rel.table -> schwellwerte innerhalb der Spezifikation (Relationsname, Typ, Wert)
 *     mit folgenden Typen:
 *      -min_word_length (minimale Länge für die Oberflächen- und Lemmaformen)
 *      -max_word_length (maximale Länge für die Oberflächen- und Lemmaformen)
 *      -min_precut_frequency (minimale Frequenz der Kookkurrenzen vor der Statistikberechnung)
 *      -max_precut_frequency (maximale Frequenz der Kookkurrenzen vor der Statistikberechnung)
 *      -min_frequency (minimale Frequenz der Kookkurrenzen nach der Statistikberechnung)
 *      -max_frequency (maximale Frequenz der Kookkurrenzen nach der Statistikberechnung)
 *      -min_MiLogFreq (minimaler MiLogFreq-Wert der Kookkurrenzen)
 *      -max_MiLogFreq (maximaler MiLogFreq-Wert der Kookkurrenzen)
 *      -min_TScore (minimaler TScore-Wert der Kookkurrenzen)
 *      -max_TScore (maximaler TScore-Wert der Kookkurrenzen)
 *      -min_MI3 (minimaler MI3-Wert der Kookkurrenzen)
 *      -max_MI3 (maximaler MI3-Wert der Kookkurrenzen)
 *      -min_LogDice (minimaler LogDice-Wert der Kookkurrenzen)
 *      -max_LogLike (maximaler LogLike-Wert der Kookkurrenzen)
 *
 * + relations.table -> optimierte und negierte Variante der Kookkurrenztabelle
 *    -Relation-ID
 *    -ID der Lemmaform der Präposition
 *    -ID der Lemmaform des ersten Wortes
 *    -ID der Lemmaform des zweiten Wortes
 *    -ID der Oberflächenform der Präposition
 *    -ID der Oberflächenform des ersten Wortes
 *    -ID der Oberflächenform des zweiten Wortes
 *    -ID der Wortkategorie der Präposition
 *    -ID der Wortkategorie des ersten Wortes
 *    -ID der Wortkategorie des zweiten Wortes
 *    -ID für die Trefferinforationen
 *    -Anzahl an Texttreffern mit Rechten
 *    -Frequenz
 *    -Statistikwert: MI3
 *    -Statistikwert: MiLogFreq
 *    -Statistikwert: TScore
 *    -Statistikwert: LogDice
 *    -Statistikwert: LogLike
 *
 * + head_pos_rel_freq.table -> Frequenzen von (w1,POS1,R) mit w1=erstes Wort,POS1=Wortkategorie,R=syntaktische Relation 
 *    -ID der Lemmaform
 *    -ID der Wortkategorie
 *    -ID der syntaktischen Relation
 *    -Frequenz
 *    -Anzahl (verschiedener)
 *
 * + head_pos_freq.table -> Frequenzen von (w1,POS1) mit w1=erstes Wort,POS1=Wortkategorie
 *    -ID der Lemmaform
 *    -ID der Wortkategorie
 *    -Frequenz
 *    -Anzahl (verschiedener)
 *
 * + mapping_lemma.table -> optimierte Variante des Lemmaformenmappings:
 *    -ID
 *    -Lemmaform
 *
 * + mapping_lemma_lower.table -> Lemmaformenmapping mit Ignorieren der Großschreibung:
 *    -ID
 *    -Lemmaform
 *
 * + mapping_surface.table -> optimierte Variante des Oberflächenformenmappings:
 *    -ID
 *    -Oberflächenform
 *
 * + mapping_position_info.table 
 *    -Texttreffer-ID
 *    -Position des ersten Wortes im Satz
 *    -Position des zweiten Wortes im Satz
 *    -Position der Präposition im Satz
 *    -Position des Satzes im Text (die Sätze sind durchnummeriert)
 *    -Dateinamen-ID
 *    -Korpus-ID
 *    -Rechteinformation (Rechtefrei=1)
 *
 *
 **/


#include <iostream>
#include <vector>
#include <string.h>
#include <fstream>
#include <fstream>
#include <map>
#include <algorithm>

#include <tuple>

#include "hashes.h"
#include "read_specification.h"
#include "Normalization.h"
#include "read_tab_input.h"

///verwendete Pfade
string g_strRelationPath = "";
string g_strTablePath = "";
string g_strTmpPath = "";

///Counter
unsigned int g_iInfoMappingCounter(1);
unsigned int g_iLemmaMappingCounter(0);
unsigned int g_iSurfaceMappingCounter(0);
unsigned int g_iPOSMappingCounter(0);
unsigned int g_iFilenameMappingCounter(0);

///Mappings
hash_map<unsigned int, unsigned int> g_mapNewLemmaId;
hash_map<unsigned int, unsigned int> g_mapNewSurfaceId;
hash_map<unsigned int, unsigned int> g_mapNewInfoId;
hash_map<unsigned int, unsigned int> g_mapNewFilenameId;

///Groessen
unsigned int g_iSizeLemma(0);
unsigned int g_iSizeSurface(0);
unsigned int g_iSizeInfo(0);
unsigned int g_iSizeCorpus(0);
unsigned int g_iSizeRelation(0);
unsigned int g_iSizePOS(0);
///Limits
unsigned int g_iHighestFrequency(0);
unsigned int g_iHighestDepFrequency(0);
unsigned int g_iHighestDepCount(0);
unsigned int g_iHighestHeadFrequency(0);
unsigned int g_iHighestHeadCount(0);
unsigned int g_iHighestGlobalDepFrequency(0);
unsigned int g_iHighestGlobalDepCount(0);
unsigned int g_iHighestGlobalHeadFrequency(0);
unsigned int g_iHighestGlobalHeadCount(0);
unsigned int g_iHighestHeadPosFrequency(0);
unsigned int g_iHighestTokenPositionW1(0);
unsigned int g_iHighestTokenPositionW2(0);
unsigned int g_iHighestPrepPosition(0);
unsigned int g_iHighestSentence(0);
unsigned int g_iHighestFilename(0);
unsigned int g_iHighestFunction(0);
unsigned int g_iHighestRelation(0);
///Laengen
unsigned int g_iLengthLemma(0);
unsigned int g_iLengthSurface(0);
unsigned int g_iLengthPOS(0);
unsigned int g_iLengthCorpus(0);
unsigned int g_iLengthFunction(0);
unsigned int g_iLengthSnippet(0);
unsigned int g_iLengthExample(0);
unsigned int g_iLengthDescription(0);
unsigned int g_iLengthFilename(0);
///Float-Laengen
unsigned int g_iLengthMiLogFreq(0);
unsigned int g_iLengthMI3(0);
unsigned int g_iLengthLogDice(0);
unsigned int g_iLengthTScore(0);
unsigned int g_iLengthLogLike(0);

///vektor mit den Relationsspezifikationen
vector<Specifications> g_vSpecifications;
///map von Spezifikationen bezueglich der Relationen
map<unsigned int,Specifications> g_mapSpecifications;
//hash-mapfür das zählen der Kookkurrenzen für die einzelnen Relationen
hash_map<unsigned int,tuple<unsigned int,unsigned int,unsigned int> > g_mapRel2NoOfKook;
hash_map<unsigned int,tuple<unsigned int,unsigned int,unsigned int> >::iterator g_itMapRel2NoOfKook;
///hash-map fuer die relationen
hash_map<string,unsigned int> g_mapFunction;
hash_map<string,unsigned int>::iterator g_itMapFunction;
///hash-map fuer das ermitteln des corpusnamen
hash_map<unsigned int,string> g_mapIdToCorpus;
///objekt zum einlesen der Specification
ReadSpecification g_CReadSpecification;
///ob Subkorpora berechnet werden sollen
bool g_bUseSubcorpora;
///Autorname
string g_strAuthor;
///Spezifikationsversion
string g_strVersion;
///globaler Lemmafrequenzschwellwert
int g_iLemmaCut;

/**
 *
 * Einlesen der Spezifikationsdatei
 *
 */
void init_spec(const char* pcFile)
{
  g_CReadSpecification.parse_xml(pcFile);
  g_strRelationPath = g_CReadSpecification.relation_path();
  g_strTablePath = g_CReadSpecification.table_path();
  g_strTmpPath = g_CReadSpecification.tmp_path();
  g_bUseSubcorpora = g_CReadSpecification.use_subcorpora();
  g_vSpecifications = g_CReadSpecification.get_specifications();
  g_strAuthor = g_CReadSpecification.author();
  g_strVersion = g_CReadSpecification.version();
  g_iLemmaCut = g_CReadSpecification.lemma_cut();
}

/**
 *
 * eventuell einen Fehler werfen
 *
 **/
void check_error(int iCode)
{
  if (iCode != 0)
  {
		exit(-1);
  }
}

/**
 *
 * Schreiben der Typinformationen fuer die MySQL-Datenbank, der Schwellwertinformationen und allgemeiner Zahlen zu den Relationen
 *
 **/
void write_types()
{
  ofstream outputSize((g_strTablePath+"/types.table").c_str());
  outputSize<<"POSSize"<<'\t'<<g_iSizePOS<<'\n';
  outputSize<<"corpusSize"<<'\t'<<g_iSizeCorpus<<'\n';
  outputSize<<"lemmaSize"<<'\t'<<g_iLemmaMappingCounter<<'\n';
  outputSize<<"surfaceSize"<<'\t'<<g_iSurfaceMappingCounter<<'\n';
  outputSize<<"infoSize"<<'\t'<<g_iInfoMappingCounter<<'\n';
  outputSize<<"relationSize"<<'\t'<<g_iHighestRelation<<'\n';
  outputSize<<"POSLength"<<'\t'<<g_iLengthPOS<<'\n';
  outputSize<<"corpusLength"<<'\t'<<g_iLengthCorpus<<'\n';
  outputSize<<"lemmaLength"<<'\t'<<g_iLengthLemma<<'\n';
  outputSize<<"surfaceLength"<<'\t'<<g_iLengthSurface<<'\n';

  outputSize<<"MI3Length"<<'\t'<<g_iLengthMI3<<'\n';
  outputSize<<"MiLogFreqLength"<<'\t'<<g_iLengthMiLogFreq<<'\n';
  outputSize<<"TScoreLength"<<'\t'<<g_iLengthTScore<<'\n';
  outputSize<<"LogDiceLength"<<'\t'<<g_iLengthLogDice<<'\n';
  outputSize<<"LogLikeLength"<<'\t'<<g_iLengthLogLike<<'\n';

  outputSize<<"FilenameLength"<<'\t'<<g_iLengthFilename<<'\n';
  outputSize<<"functionLength"<<'\t'<<g_iLengthFunction<<'\n';
  outputSize<<"snippetLength"<<'\t'<<g_iLengthSnippet<<'\n';
  outputSize<<"descriptionLength"<<'\t'<<g_iLengthDescription<<'\n';
  outputSize<<"exampleLength"<<'\t'<<g_iLengthExample<<'\n';

  outputSize<<"highestFrequency"<<'\t'<<g_iHighestFrequency<<'\n';
  outputSize<<"highestDepFrequency"<<'\t'<<g_iHighestDepFrequency<<'\n';
  outputSize<<"highestHeadFrequency"<<'\t'<<g_iHighestHeadFrequency<<'\n';
  outputSize<<"highestDepCount"<<'\t'<<g_iHighestDepCount<<'\n';
  outputSize<<"highestHeadCount"<<'\t'<<g_iHighestHeadCount<<'\n';

  outputSize<<"highestGlobalDepFrequency"<<'\t'<<g_iHighestGlobalDepFrequency<<'\n';
  outputSize<<"highestGlobalHeadFrequency"<<'\t'<<g_iHighestGlobalHeadFrequency<<'\n';
  outputSize<<"highestGlobalDepCount"<<'\t'<<g_iHighestGlobalDepCount<<'\n';
  outputSize<<"highestGlobalHeadCount"<<'\t'<<g_iHighestGlobalHeadCount<<'\n';

  outputSize<<"highestHeadPosFrequency"<<'\t'<<g_iHighestHeadPosFrequency<<'\n';
  
  outputSize<<"highestTokenPositionW1"<<'\t'<<g_iHighestTokenPositionW1<<'\n';
  outputSize<<"highestTokenPositionW2"<<'\t'<<g_iHighestTokenPositionW2<<'\n';
  outputSize<<"highestPrepPosition"<<'\t'<<g_iHighestPrepPosition<<'\n';
  outputSize<<"highestSentence"<<'\t'<<g_iHighestSentence<<'\n';
  outputSize<<"highestText"<<'\t'<<g_iHighestFilename<<'\n';
  outputSize<<"highestFunction"<<'\t'<<g_iHighestFunction<<'\n';
  
  outputSize.close();

  ///Schreiben der Schwellwerte  
  ofstream outputThresholdRel((g_strTablePath+"/threshold_rel.table").c_str());
  for (Specifications el : g_vSpecifications)
  {
    unsigned int iFunctionname1 = g_mapFunction[el.CSpecification1.functionname()];
    unsigned int iFunctionname2 = g_mapFunction[el.CSpecification2.functionname()];

    unsigned int iMinStringLength = el.min_string_length();
    outputThresholdRel<<iFunctionname1<<"\tmin_word_length\t"<<iMinStringLength<<"\n";
    outputThresholdRel<<iFunctionname2<<"\tmin_word_length\t"<<iMinStringLength<<"\n";

    unsigned int iMaxStringLength = el.max_string_length();
    outputThresholdRel<<iFunctionname1<<"\tmax_word_length\t"<<iMaxStringLength<<"\n";
    outputThresholdRel<<iFunctionname2<<"\tmax_word_length\t"<<iMaxStringLength<<"\n";

    unsigned int iMinFreqPrecut = el.min_frequency();
    outputThresholdRel<<iFunctionname1<<"\tmin_precut_frequency\t"<<iMinFreqPrecut<<"\n";
    outputThresholdRel<<iFunctionname2<<"\tmin_precut_frequency\t"<<iMinFreqPrecut<<"\n";

    unsigned int iMaxFreqPrecut = el.max_frequency();
    outputThresholdRel<<iFunctionname1<<"\tmax_precut_frequency\t"<<iMaxFreqPrecut<<"\n";
    outputThresholdRel<<iFunctionname2<<"\tmax_precut_frequency\t"<<iMaxFreqPrecut<<"\n";


    unsigned int iMinFrequency1 = el.CSpecification1.min_frequency();
    outputThresholdRel<<iFunctionname1<<"\tmin_frequency\t"<<iMinFrequency1<<"\n";
    unsigned int iMinFrequency2 = el.CSpecification2.min_frequency();
    outputThresholdRel<<iFunctionname2<<"\tmin_frequency\t"<<iMinFrequency2<<"\n";

    unsigned int iMaxFrequency1 = el.CSpecification1.max_frequency();
    outputThresholdRel<<iFunctionname1<<"\tmax_frequency\t"<<iMaxFrequency1<<"\n";
    unsigned int iMaxFrequency2 = el.CSpecification2.max_frequency();
    outputThresholdRel<<iFunctionname2<<"\tmax_frequency\t"<<iMaxFrequency2<<"\n";


    float iMinSalience1 = max(el.CSpecification1.min_MiLogFreq(),el.CSpecification1.min_MiLogFreq_con());
    outputThresholdRel<<iFunctionname1<<"\tmin_MiLogFreq\t"<<iMinSalience1<<"\n";
    float iMinSalience2 = max(el.CSpecification2.min_MiLogFreq(),el.CSpecification2.min_MiLogFreq_con());
    outputThresholdRel<<iFunctionname2<<"\tmin_MiLogFreq\t"<<iMinSalience2<<"\n";

    float iMaxSalience1 = min(el.CSpecification1.max_MiLogFreq(),el.CSpecification1.max_MiLogFreq_con());
    outputThresholdRel<<iFunctionname1<<"\tmax_MiLogFreq\t"<<iMaxSalience1<<"\n";
    float iMaxSalience2 = min(el.CSpecification2.max_MiLogFreq(),el.CSpecification2.max_MiLogFreq_con());
    outputThresholdRel<<iFunctionname2<<"\tmax_MiLogFreq\t"<<iMaxSalience2<<"\n";

    float iMinMI3_1 = max(el.CSpecification1.min_MI3(),el.CSpecification1.min_MI3_con());
    outputThresholdRel<<iFunctionname1<<"\tmin_MI3\t"<<iMinMI3_1<<"\n";
    float iMinMI3_2 = max(el.CSpecification2.min_MI3(),el.CSpecification2.min_MI3_con());
    outputThresholdRel<<iFunctionname2<<"\tmin_MI3\t"<<iMinMI3_2<<"\n";

    float iMaxMI3_1 = min(el.CSpecification1.max_MI3(),el.CSpecification1.max_MI3_con());
    outputThresholdRel<<iFunctionname1<<"\tmax_MI3\t"<<iMaxMI3_1<<"\n";
    float iMaxMI3_2 = min(el.CSpecification2.max_MI3(),el.CSpecification2.max_MI3_con());
    outputThresholdRel<<iFunctionname2<<"\tmax_MI3\t"<<iMaxMI3_2<<"\n";

    float iMinTScore1 = max(el.CSpecification1.min_TScore(),el.CSpecification1.min_TScore_con());
    outputThresholdRel<<iFunctionname1<<"\tmin_TScore\t"<<iMinTScore1<<"\n";
    float iMinTScore2 = max(el.CSpecification2.min_TScore(),el.CSpecification2.min_TScore_con());
    outputThresholdRel<<iFunctionname2<<"\tmin_TScore\t"<<iMinTScore2<<"\n";

    float iMaxTScore1 = min(el.CSpecification1.max_TScore(),el.CSpecification1.max_TScore_con());
    outputThresholdRel<<iFunctionname1<<"\tmax_TScore\t"<<iMaxTScore1<<"\n";
    float iMaxTScore2 = min(el.CSpecification2.max_TScore(),el.CSpecification2.max_TScore_con());
    outputThresholdRel<<iFunctionname2<<"\tmax_TScore\t"<<iMaxTScore2<<"\n";

    float iMinLogDice1 = max(el.CSpecification1.min_logDice(),el.CSpecification1.min_logDice_con());
    outputThresholdRel<<iFunctionname1<<"\tmin_LogDice\t"<<iMinLogDice1<<"\n";
    float iMinLogDice2 = max(el.CSpecification2.min_logDice(),el.CSpecification2.min_logDice_con());
    outputThresholdRel<<iFunctionname2<<"\tmin_LogDice\t"<<iMinLogDice2<<"\n";

    float iMaxLogDice1 = min(el.CSpecification1.max_logDice(),el.CSpecification1.max_logDice_con());
    outputThresholdRel<<iFunctionname1<<"\tmax_LogDice\t"<<iMaxLogDice1<<"\n";
    float iMaxLogDice2 = min(el.CSpecification2.max_logDice(),el.CSpecification2.max_logDice_con());
    outputThresholdRel<<iFunctionname2<<"\tmax_LogDice\t"<<iMaxLogDice2<<"\n";

    float iMinLogLike1 = max(el.CSpecification1.min_logLike(),el.CSpecification1.min_logLike_con());
    outputThresholdRel<<iFunctionname1<<"\tmin_LogLike\t"<<iMinLogLike1<<"\n";
    float iMinLogLike2 = max(el.CSpecification2.min_logLike(),el.CSpecification2.min_logLike_con());
    outputThresholdRel<<iFunctionname2<<"\tmin_LogLike\t"<<iMinLogLike2<<"\n";

    float iMaxLogLike1 = min(el.CSpecification1.max_logLike(),el.CSpecification1.max_logLike_con());
    outputThresholdRel<<iFunctionname1<<"\tmax_LogLike\t"<<iMaxLogLike1<<"\n";
    float iMaxLogLike2 = min(el.CSpecification2.max_logLike(),el.CSpecification2.max_logLike_con());
    outputThresholdRel<<iFunctionname2<<"\tmax_LogLike\t"<<iMaxLogLike2<<"\n";
  }
  outputThresholdRel.close();

  ///schreiben von Relationsspezifischen Informationen
  ofstream outputRelKook((g_strTablePath+"/rel_info.table").c_str());
  for (pair<unsigned int,tuple<unsigned int,unsigned int,unsigned int> > el : g_mapRel2NoOfKook)
  {
    ///Relations-Id
    outputRelKook<<el.first<<"\t";
    ///Anzahl (ohne doppelte)
    outputRelKook<<get<0>(el.second)<<"\t";
    ///Frequenz
    outputRelKook<<get<1>(el.second)<<"\t";
    ///Anzahl an Rechtefreien Fundstellen
    outputRelKook<<get<2>(el.second)<<endl;
  }
  outputRelKook.close();
}

/**
 *
 * Laden der ID-Mappings für die Korpora und Relationsnamen
 *
 **/
void load_relation_corpus_mappings()
{
  char str[10000];
  hash_map<unsigned int,unsigned int>::iterator itMapNewPOSId;
  ifstream inputFunctionMapping((g_strTablePath+"/mapping_function.table").c_str());  
  while(inputFunctionMapping) 
  {
    inputFunctionMapping.getline(str, 1000);
    if(inputFunctionMapping) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,6))
      {
        unsigned int iFunction = atoi(CReadTabInput.get_field(1));
        string strFunction = CReadTabInput.get_field(2);
        const char* szType = CReadTabInput.get_field(3);
        string strSnippet = CReadTabInput.get_field(4);
        string strDescription = CReadTabInput.get_field(5);
        string strExample = CReadTabInput.get_field(6);
        g_mapFunction.insert(make_pair(strFunction,iFunction));

        if (strFunction.length()>g_iLengthFunction)
        {
          g_iLengthFunction = strFunction.length();
        }
        if (strSnippet.length()>g_iLengthSnippet)
        {
          g_iLengthSnippet = strSnippet.length();
        }
        if (strDescription.length()>g_iLengthDescription)
        {
          g_iLengthDescription = strDescription.length();
        }
        if (strExample.length()>g_iLengthExample)
        {
          g_iLengthExample = strExample.length();
        }
        if (iFunction>g_iHighestFunction)
        {
          g_iHighestFunction = iFunction;
        }
      }
    }
  }

  string strInputCorpusMapping = g_strTablePath+"/mapping_corpus.table";
  ifstream inputCorpusMapping(strInputCorpusMapping.c_str());  
  while (inputCorpusMapping)
  {
    inputCorpusMapping.getline(str, 10000);
    if(inputCorpusMapping) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,2))
      {
        unsigned int iId = atoi(CReadTabInput.get_field(1));
        string strName = CReadTabInput.get_field(2);
        g_mapIdToCorpus.insert(make_pair(iId,strName));
      }
    }
  }
}

/**
 *
 * Negieren der Statistiken bezüglich der Subkorpora (wegen der Sortierung in MySQL)
 *
 **/
void negate_statistics_subcorpora()
{
  //if (g_mapIdToCorpus.size()>1)
  {
		char str[10000];
		hash_map<unsigned int,string>::iterator it;
		cout<<"(: negate subcorpora"<<endl;
		for (it = g_mapIdToCorpus.begin(); it != g_mapIdToCorpus.end(); ++it)
		{
		  cout<<"(: negate subcorpus:"<<it->second<<endl;

			hash_map<HashTriple,pair<unsigned int,unsigned int>,PSHashTriple,PSEqualToTriple> mapHeadPOSFrequency;
			hash_map<HashTriple,pair<unsigned int,unsigned int>,PSHashTriple,PSEqualToTriple>::iterator itMapHeadPOSFrequency;

			string strOutFile = g_strTablePath+"/relations."+it->second+".optimized.negate.table";
			string strInFile = g_strTablePath+"/relations."+it->second+".optimized.table";
			ifstream streamIn(strInFile.c_str());
			ofstream streamOut(strOutFile.c_str());
			char str[1000];
			while (streamIn)
			{
				streamIn.getline(str, 10000);
				if(streamIn) 
				{
					ReadTabInput CReadTabInput;
					if (CReadTabInput.read_line(str,18))
					{
				    const char* strFunctionname = CReadTabInput.get_field(1);
				    const char* strPrep = CReadTabInput.get_field(2);
				    const char* strLemma1 = CReadTabInput.get_field(3);
				    const char* strLemma2 = CReadTabInput.get_field(4);
				    const char* strSurfacePrep = CReadTabInput.get_field(5);
				    const char* strSurface1 = CReadTabInput.get_field(6);
				    const char* strSurface2 = CReadTabInput.get_field(7);
				    const char* strPrepPOS = CReadTabInput.get_field(8);
				    const char* strPOS1 = CReadTabInput.get_field(9);
				    const char* strPOS2 = CReadTabInput.get_field(10);
				    const char* strInfo = CReadTabInput.get_field(11);        
            int iFreqBelege = atoi(CReadTabInput.get_field(12));
				    int iFreqRelation = atoi(CReadTabInput.get_field(13));

				    float iMI3 = atof(CReadTabInput.get_field(14));        
				    float iSalience = atof(CReadTabInput.get_field(15));        
				    float iTScore = atof(CReadTabInput.get_field(16));        
				    float iLogDice = atof(CReadTabInput.get_field(17));    
				    float iLogLike = atof(CReadTabInput.get_field(18));    
						streamOut<<strFunctionname<<'\t';
            streamOut<<strPrep<<'\t';
            streamOut<<strLemma1<<'\t';
            streamOut<<strLemma2<<'\t';
            streamOut<<strSurfacePrep<<'\t';
            streamOut<<strSurface1<<'\t';
            streamOut<<strSurface2<<'\t';
            streamOut<<strPrepPOS<<'\t';
            streamOut<<strPOS1<<'\t';
            streamOut<<strPOS2<<'\t';	
						streamOut<<strInfo<<'\t';
            streamOut<<-iFreqBelege<<'\t';
            streamOut<<-iFreqRelation<<'\t';
            streamOut<<-iMI3<<'\t';
            streamOut<<-iSalience<<'\t';
            streamOut<<-iTScore<<'\t';
            streamOut<<-iLogDice<<'\t';
            streamOut<<-iLogLike<<'\n';
					}
				}
			}
			streamIn.close();
			streamOut.close();
			int i = system(("mv "+g_strTablePath+"/relations."+it->second+".optimized.negate.table "+g_strTablePath+"/relations."+it->second+".optimized.table").c_str());
      check_error(i);
		}
	}
}

/**
 *
 * Negieren der Statistiken (wegen der Sortierung in MySQL)
 *
 **/
void negate_statistics()
{
  cout<<"(: negate statistics"<<endl;

  string strInFile = g_strTablePath+"/relations.optimized.table";
  string strOutFile = g_strTablePath+"/relations.optimized.negate.table";

  ifstream streamIn(strInFile.c_str());
  ofstream streamOut(strOutFile.c_str());
  char str[1000];
  while (streamIn)
  {
    streamIn.getline(str, 1000);
    if(streamIn) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,18))
      {
        const char* strFunctionname = CReadTabInput.get_field(1);
        const char* strPrep = CReadTabInput.get_field(2);
        const char* strLemma1 = CReadTabInput.get_field(3);
        const char* strLemma2 = CReadTabInput.get_field(4);
        const char* strSurfacePrep = CReadTabInput.get_field(5);
        const char* strSurface1 = CReadTabInput.get_field(6);
        const char* strSurface2 = CReadTabInput.get_field(7);
        const char* strPrepPOS = CReadTabInput.get_field(8);
        const char* strPOS1 = CReadTabInput.get_field(9);
        const char* strPOS2 = CReadTabInput.get_field(10);
        const char* strInfo = CReadTabInput.get_field(11);        
        int iFreqBelege = atoi(CReadTabInput.get_field(12));
        int iFreqRelation = atoi(CReadTabInput.get_field(13));

        float iMI3 = atof(CReadTabInput.get_field(14));        
        float iSalience = atof(CReadTabInput.get_field(15));        
        float iTScore = atof(CReadTabInput.get_field(16));        
        float iLogDice = atof(CReadTabInput.get_field(17));    
        float iLogLike = atof(CReadTabInput.get_field(18));    

				streamOut<<strFunctionname<<'\t';
        streamOut<<strPrep<<'\t';
        streamOut<<strLemma1<<'\t';
        streamOut<<strLemma2<<'\t';
        streamOut<<strSurfacePrep<<'\t';
        streamOut<<strSurface1<<'\t';
        streamOut<<strSurface2<<'\t';
        streamOut<<strPrepPOS<<'\t';
        streamOut<<strPOS1<<'\t';
        streamOut<<strPOS2<<'\t';
        streamOut<<strInfo<<'\t';
        streamOut<<-iFreqBelege<<'\t';
        streamOut<<-iFreqRelation<<'\t';
        streamOut<<-iMI3<<'\t';
        streamOut<<-iSalience<<'\t';
        streamOut<<-iTScore<<'\t';
        streamOut<<-iLogDice<<'\t';
        streamOut<<-iLogLike<<'\n';
      }
    }
  }
  streamIn.close();
  streamOut.close();
	int i = system(("mv "+g_strTablePath+"/relations.optimized.negate.table "+g_strTablePath+"/relations.optimized.table").c_str());
	check_error(i);
}

/**
 *
 * Berechnen der Frequenz von (w1_lemma,w1_POS,R)
 *
 **/
void head_pos_relation_frequency()
{
  cout<<"(: calculate head-POS-relation frequencies"<<endl;

  hash_map<HashTriple,pair<unsigned int,unsigned int>,PSHashTriple,PSEqualToTriple> mapHeadPOSFrequency;
  hash_map<HashTriple,pair<unsigned int,unsigned int>,PSHashTriple,PSEqualToTriple>::iterator itMapHeadPOSFrequency;
  
  string strInFile = g_strTablePath+"/relations.optimized.table";
  ifstream streamIn(strInFile.c_str());
  char str[1000];
  while (streamIn)
  {
    streamIn.getline(str, 1000);
    if(streamIn) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,18))
      {
        unsigned int iFunctionname = atoi(CReadTabInput.get_field(1));
        unsigned int iPrep = atoi(CReadTabInput.get_field(2));
        unsigned int iLemma1 = atoi(CReadTabInput.get_field(3));
        unsigned int iLemma2 = atoi(CReadTabInput.get_field(4));
        unsigned int iSurfacePrep = atoi(CReadTabInput.get_field(5));
        unsigned int iSurface1 = atoi(CReadTabInput.get_field(6));
        unsigned int iSurface2 = atoi(CReadTabInput.get_field(7));
        unsigned int iPrepPOS = atoi(CReadTabInput.get_field(8));
        unsigned int iPOS1 = atoi(CReadTabInput.get_field(9));
        unsigned int iPOS2 = atoi(CReadTabInput.get_field(10));
        unsigned int iInfo = atoi(CReadTabInput.get_field(11));        
        int iFreqBelege = atoi(CReadTabInput.get_field(12));
        unsigned int iFreqRelation = atoi(CReadTabInput.get_field(13));

				string cMI3 = CReadTabInput.get_field(14);
				string cSalience = CReadTabInput.get_field(15);
				string cTScore = CReadTabInput.get_field(16);
				string cLogDice = CReadTabInput.get_field(17);
				string cLogLike = CReadTabInput.get_field(18);

				///berechnen der Laengen vor dem '.'
				int iLengthMI3 = cMI3.find(".");
				int iLengthMiLogFreq = cSalience.find(".");
				int iLengthTScore = cTScore.find(".");
				int iLengthLogDice = cLogDice.find(".");
				int iLengthLogLike = cLogLike.find(".");

				///anpassen der globalen Laengeninformationen
				if (iLengthMI3==string::npos)
					iLengthMI3 = cMI3.length();
				if (iLengthMiLogFreq==string::npos)
					iLengthMiLogFreq = cSalience.length();
				if (iLengthTScore==string::npos)
					iLengthTScore = cTScore.length();
				if (iLengthLogDice==string::npos)
					iLengthLogDice = cLogDice.length();
				if (iLengthLogLike==string::npos)
					iLengthLogLike = cLogLike.length();

				if (iLengthMI3>=g_iLengthMI3)
					g_iLengthMI3=iLengthMI3;
				if (iLengthMiLogFreq>=g_iLengthMiLogFreq)
					g_iLengthMiLogFreq=iLengthMiLogFreq;
				if (iLengthTScore>=g_iLengthTScore)
					g_iLengthTScore=iLengthTScore;
				if (iLengthLogDice>=g_iLengthLogDice)
					g_iLengthLogDice=iLengthLogDice;
				if (iLengthLogLike>=g_iLengthLogLike)
					g_iLengthLogLike=iLengthLogLike;
        
				///sammeln und zaehlen der (w1(lemma),w1(POS),Rel) tupel
        itMapHeadPOSFrequency = mapHeadPOSFrequency.find(HashTriple(iLemma1,iPOS1,iFunctionname));
        if (itMapHeadPOSFrequency != mapHeadPOSFrequency.end())
        {
          itMapHeadPOSFrequency->second.first+=iFreqRelation;
          ++itMapHeadPOSFrequency->second.second;
        }
        else
        {
          mapHeadPOSFrequency.insert(make_pair(HashTriple(iLemma1,iPOS1,iFunctionname),make_pair(iFreqRelation,1)));
        }
      }
    }
  }
  streamIn.close();

	///schreiben der (w1(lemma),w1(POS),Rel) tupel
  ofstream streamOut((g_strTablePath+"/head_pos_rel_freq.table").c_str());  
  for (itMapHeadPOSFrequency = mapHeadPOSFrequency.begin(); itMapHeadPOSFrequency != mapHeadPOSFrequency.end(); ++itMapHeadPOSFrequency)
  {
    if (g_iHighestHeadPosFrequency<itMapHeadPOSFrequency->second.first)
    {
      g_iHighestHeadPosFrequency = itMapHeadPOSFrequency->second.first;
    }    
    streamOut<<itMapHeadPOSFrequency->first.first<<'\t';
    streamOut<<itMapHeadPOSFrequency->first.second<<'\t';
    streamOut<<itMapHeadPOSFrequency->first.third<<'\t';
    streamOut<<itMapHeadPOSFrequency->second.first<<'\t';
    streamOut<<itMapHeadPOSFrequency->second.second<<'\n';
  }
  streamOut.close();

}

/**
 *
 * Berechnen der Frequenz von (w1(lemma),w1(POS))
 *
 **/
void head_pos_frequency()
{
  cout<<"(: calculate head-POS frequencies"<<endl;

  hash_map<HashPair,pair<unsigned int,unsigned int>,PSHashPair,PSEqualToPair> mapHeadPOSFrequency;
  hash_map<HashPair,pair<unsigned int,unsigned int>,PSHashPair,PSEqualToPair>::iterator itMapHeadPOSFrequency;
  
  string strInFile = g_strTablePath+"/relations.optimized.table";
  ifstream streamIn(strInFile.c_str());
  char str[1000];
  while (streamIn)
  {
    streamIn.getline(str, 1000);
    if(streamIn) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,18))
      {
        unsigned int iFunctionname = atoi(CReadTabInput.get_field(1));
        unsigned int iPrep = atoi(CReadTabInput.get_field(2));
        unsigned int iLemma1 = atoi(CReadTabInput.get_field(3));
        unsigned int iLemma2 = atoi(CReadTabInput.get_field(4));
        unsigned int iSurfacePrep = atoi(CReadTabInput.get_field(5));
        unsigned int iSurface1 = atoi(CReadTabInput.get_field(6));
        unsigned int iSurface2 = atoi(CReadTabInput.get_field(7));
        unsigned int iPrepPOS = atoi(CReadTabInput.get_field(8));
        unsigned int iPOS1 = atoi(CReadTabInput.get_field(9));
        unsigned int iPOS2 = atoi(CReadTabInput.get_field(10));
        unsigned int iInfo = atoi(CReadTabInput.get_field(11));        
        int iFreqBelege = atoi(CReadTabInput.get_field(12));
        unsigned int iFreqRelation = atoi(CReadTabInput.get_field(13));

        float iMI = atof(CReadTabInput.get_field(14));        
        float iSalience = atof(CReadTabInput.get_field(15));        
        float iTScore = atof(CReadTabInput.get_field(16));        
        float iLogDice = atof(CReadTabInput.get_field(17));
        float iMaxLike = atof(CReadTabInput.get_field(18));

				///aufsammeln und zaehlen der (w1(lemma),w1(POS)) tupel
        itMapHeadPOSFrequency = mapHeadPOSFrequency.find(HashPair(iLemma1,iPOS1));
        if (itMapHeadPOSFrequency != mapHeadPOSFrequency.end())
        {
          itMapHeadPOSFrequency->second.first+=iFreqRelation;
          ++itMapHeadPOSFrequency->second.second;
        }
        else
        {
          mapHeadPOSFrequency.insert(make_pair(HashPair(iLemma1,iPOS1),make_pair(iFreqRelation,1)));
        }
      }
    }

  }
  streamIn.close();

	///schreiben der (w1(lemma),w1(POS)) tupel
  ofstream streamOut((g_strTablePath+"/head_pos_freq.table").c_str());  
  for (itMapHeadPOSFrequency = mapHeadPOSFrequency.begin(); itMapHeadPOSFrequency != mapHeadPOSFrequency.end(); ++itMapHeadPOSFrequency)
  {
    if (g_iHighestHeadPosFrequency<itMapHeadPOSFrequency->second.first)
    {
      g_iHighestHeadPosFrequency = itMapHeadPOSFrequency->second.first;
    }
    streamOut<<itMapHeadPOSFrequency->first.first<<'\t';
    streamOut<<itMapHeadPOSFrequency->first.second<<'\t';
    streamOut<<itMapHeadPOSFrequency->second.first<<'\t';
    streamOut<<itMapHeadPOSFrequency->second.second<<'\n';
  }
  streamOut.close();

}

/**
 *
 * Berechnen der Frequenz von (w1(lemma),w1(POS),R) für die Subkorpora
 *
 **/
void head_pos_relation_frequency_subcorpora()
{
  //if (g_mapIdToCorpus.size()>1)
  {
		char str[10000];
		hash_map<unsigned int,string>::iterator it;
		//cout<<"(: head-pos-relation subcorpora"<<endl;
		for (it = g_mapIdToCorpus.begin(); it != g_mapIdToCorpus.end(); ++it)
		{
		  cout<<"(: head-POS-relation, subcorpus: "<<it->second<<endl;

			hash_map<HashTriple,pair<unsigned int,unsigned int>,PSHashTriple,PSEqualToTriple> mapHeadPOSFrequency;
			hash_map<HashTriple,pair<unsigned int,unsigned int>,PSHashTriple,PSEqualToTriple>::iterator itMapHeadPOSFrequency;

			string strInFile = g_strTablePath+"/relations."+it->second+".optimized.table";
			ifstream streamIn(strInFile.c_str());
			char str[1000];
			while (streamIn)
			{
				streamIn.getline(str, 10000);
				if(streamIn) 
				{
					ReadTabInput CReadTabInput;
					if (CReadTabInput.read_line(str,18))
					{
						unsigned int iFunctionname = atoi(CReadTabInput.get_field(1));
						unsigned int iPrep = atoi(CReadTabInput.get_field(2));
						unsigned int iLemma1 = atoi(CReadTabInput.get_field(3));
						unsigned int iLemma2 = atoi(CReadTabInput.get_field(4));
						unsigned int iSurfacePrep = atoi(CReadTabInput.get_field(5));
						unsigned int iSurface1 = atoi(CReadTabInput.get_field(6));
						unsigned int iSurface2 = atoi(CReadTabInput.get_field(7));
						unsigned int iPrepPOS = atoi(CReadTabInput.get_field(8));
						unsigned int iPOS1 = atoi(CReadTabInput.get_field(9));
						unsigned int iPOS2 = atoi(CReadTabInput.get_field(10));
						unsigned int iInfo = atoi(CReadTabInput.get_field(11));        
            int iFreqBelege = atoi(CReadTabInput.get_field(12));
						unsigned int iFreqRelation = atoi(CReadTabInput.get_field(13));

						float iMI = atof(CReadTabInput.get_field(14));        
						float iSalience = atof(CReadTabInput.get_field(15));        
						float iTScore = atof(CReadTabInput.get_field(16));        
						float iLogDice = atof(CReadTabInput.get_field(17));
						float iMaxLike = atof(CReadTabInput.get_field(18));
						
						///aufsammeln und zaehlen der (w1(lemma),w1(POS),R) tupel
						itMapHeadPOSFrequency = mapHeadPOSFrequency.find(HashTriple(iLemma1,iPOS1,iFunctionname));
						if (itMapHeadPOSFrequency != mapHeadPOSFrequency.end())
						{
						  itMapHeadPOSFrequency->second.first+=iFreqRelation;
						  ++itMapHeadPOSFrequency->second.second;
						}
						else
						{
						  mapHeadPOSFrequency.insert(make_pair(HashTriple(iLemma1,iPOS1,iFunctionname),make_pair(iFreqRelation,1)));
						}
					}
				}
			}
			streamIn.close();

			///schreiben der (w1(lemma),w1(POS),R) tupel
			ofstream streamOut((g_strTablePath+"/head_pos_rel_freq."+it->second+".table").c_str());  
			for (itMapHeadPOSFrequency = mapHeadPOSFrequency.begin(); itMapHeadPOSFrequency != mapHeadPOSFrequency.end(); ++itMapHeadPOSFrequency)
			{
				if (g_iHighestHeadPosFrequency<itMapHeadPOSFrequency->second.first)
				{
					g_iHighestHeadPosFrequency = itMapHeadPOSFrequency->second.first;
				}		
				streamOut<<itMapHeadPOSFrequency->first.first<<'\t'<<itMapHeadPOSFrequency->first.second<<'\t'<<itMapHeadPOSFrequency->first.third<<'\t'<<itMapHeadPOSFrequency->second.first<<'\t'<<itMapHeadPOSFrequency->second.second<<'\n';
			}
			streamOut.close();
		}
	}
}

/**
 *
 * Berechnen der Frequenz von (w1(lemma),w1(POS)) für die Subkorpora
 *
 **/
void head_pos_frequency_subcorpora()
{
  //if (g_mapIdToCorpus.size()>1)
  {
		char str[10000];
		hash_map<unsigned int,string>::iterator it;
		//cout<<"(: head-pos subcorpora"<<endl;
		for (it = g_mapIdToCorpus.begin(); it != g_mapIdToCorpus.end(); ++it)
		{
		  cout<<"(: head-POS, subcorpus: "<<it->second<<endl;

			hash_map<HashPair,pair<unsigned int,unsigned int>,PSHashPair,PSEqualToPair> mapHeadPOSFrequency;
			hash_map<HashPair,pair<unsigned int,unsigned int>,PSHashPair,PSEqualToPair>::iterator itMapHeadPOSFrequency;

			string strInFile = g_strTablePath+"/relations."+it->second+".optimized.table";
			ifstream streamIn(strInFile.c_str());
			char str[1000];
			while (streamIn)
			{
				streamIn.getline(str, 1000);  // delim defaults to '\n'
				if(streamIn) 
				{
					ReadTabInput CReadTabInput;
					if (CReadTabInput.read_line(str,18))
					{
						unsigned int iFunctionname = atoi(CReadTabInput.get_field(1));
						unsigned int iPrep = atoi(CReadTabInput.get_field(2));
						unsigned int iLemma1 = atoi(CReadTabInput.get_field(3));
						unsigned int iLemma2 = atoi(CReadTabInput.get_field(4));
						unsigned int iSurfacePrep = atoi(CReadTabInput.get_field(5));
						unsigned int iSurface1 = atoi(CReadTabInput.get_field(6));
						unsigned int iSurface2 = atoi(CReadTabInput.get_field(7));
						unsigned int iPrepPOS = atoi(CReadTabInput.get_field(8));
						unsigned int iPOS1 = atoi(CReadTabInput.get_field(9));
						unsigned int iPOS2 = atoi(CReadTabInput.get_field(10));
						unsigned int iInfo = atoi(CReadTabInput.get_field(11));        
            int iFreqBelege = atoi(CReadTabInput.get_field(12));
						unsigned int iFreqRelation = atoi(CReadTabInput.get_field(13));

						float iMI = atof(CReadTabInput.get_field(14));        
						float iSalience = atof(CReadTabInput.get_field(15));        
						float iTScore = atof(CReadTabInput.get_field(16));        
						float iLogDice = atof(CReadTabInput.get_field(17));
						float iMaxLike = atof(CReadTabInput.get_field(18));
				
						///aufsammeln und zaehlen der (w1(lemma),w1(POS)) tupel
						itMapHeadPOSFrequency = mapHeadPOSFrequency.find(HashPair(iLemma1,iPOS1));
						if (itMapHeadPOSFrequency != mapHeadPOSFrequency.end())
						{
							itMapHeadPOSFrequency->second.first+=iFreqRelation;
							++itMapHeadPOSFrequency->second.second;
						}
						else
						{
							mapHeadPOSFrequency.insert(make_pair(HashPair(iLemma1,iPOS1),make_pair(iFreqRelation,1)));
						}
					}
				}

			}
			streamIn.close();

			///schreiben der (w1(lemma),w1(POS)) tupel
			ofstream streamOut((g_strTablePath+"/head_pos_freq."+it->second+".table").c_str());  
			for (itMapHeadPOSFrequency = mapHeadPOSFrequency.begin(); itMapHeadPOSFrequency != mapHeadPOSFrequency.end(); ++itMapHeadPOSFrequency)
			{
				streamOut<<itMapHeadPOSFrequency->first.first<<'\t'<<itMapHeadPOSFrequency->first.second<<'\t'<<itMapHeadPOSFrequency->second.first<<'\t'<<itMapHeadPOSFrequency->second.second<<'\n';
			}
			streamOut.close();

		}
	}
}

/**
 *
 * Berechnen neuer zusammenhängender IDs für Relationen Mappings
 *
 **/
void renumber()
{
  char a[1000];
  char str[1000];
  string strInFile = g_strTablePath+"/relations.table";
  ifstream streamIn(strInFile.c_str());
  string strOutFile = g_strTablePath+"/relations.optimized.table";
  ofstream streamOut(strOutFile.c_str());

  sprintf(a,"(: calculate renumbering");
  cout<<a<<endl;

  while (streamIn)
  {
    streamIn.getline(str, 1000);  // delim defaults to '\n'
    if(streamIn) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,18))
      {
        unsigned int iFunctionname = atoi(CReadTabInput.get_field(1));
        unsigned int iPrep = atoi(CReadTabInput.get_field(2));
        unsigned int iLemma1 = atoi(CReadTabInput.get_field(3));
        unsigned int iLemma2 = atoi(CReadTabInput.get_field(4));
        unsigned int iSurfacePrep = atoi(CReadTabInput.get_field(5));
        unsigned int iSurface1 = atoi(CReadTabInput.get_field(6));
        unsigned int iSurface2 = atoi(CReadTabInput.get_field(7));
        unsigned int iPrepPOS = atoi(CReadTabInput.get_field(8));
        unsigned int iPOS1 = atoi(CReadTabInput.get_field(9));
        unsigned int iPOS2 = atoi(CReadTabInput.get_field(10));
        unsigned int iInfo = atoi(CReadTabInput.get_field(11));        
        int iFreqBelege = atoi(CReadTabInput.get_field(12));
        unsigned int iFreqRelation = atoi(CReadTabInput.get_field(13));        

        float iMI = atof(CReadTabInput.get_field(14));        
        float iSalience = atof(CReadTabInput.get_field(15));        
        float iTScore = atof(CReadTabInput.get_field(16));        
        float iLogDice = atof(CReadTabInput.get_field(17));
        float iMaxLike = atof(CReadTabInput.get_field(18));
                       
				///zaehlen der Relationen
        if (g_iHighestFrequency < iFreqRelation)
        {
          g_iHighestFrequency = iFreqRelation;
        }

				///neue ID's fuer die Positionsinformationen
        unsigned int iInfoMapping(iInfo);        
        //if (iFreqBelege != 0)
        {
          //g_iInfoMappingCounter = max(g_iInfoMappingCounter,iInfoMapping);
          hash_map<unsigned int, unsigned int>::iterator itMapNewInfoId;
          itMapNewInfoId = g_mapNewInfoId.find(iInfo);
          if (itMapNewInfoId != g_mapNewInfoId.end())
          {
            iInfoMapping = itMapNewInfoId->second;
          }
          else
          {
            g_mapNewInfoId.insert(make_pair(iInfo,g_iInfoMappingCounter));
            //g_mapNewInfoId.insert(make_pair(iInfo,iInfo));
            iInfoMapping = g_iInfoMappingCounter;
            ++g_iInfoMappingCounter;
          }
        }

				///neue ID's fuer die Praepositionen
        unsigned int iPrepMapping(0);        
        hash_map<unsigned int, unsigned int>::iterator itg_mapNewLemmaId;
        itg_mapNewLemmaId = g_mapNewLemmaId.find(iPrep);
        if (itg_mapNewLemmaId != g_mapNewLemmaId.end())
        {
          iPrepMapping = itg_mapNewLemmaId->second;
        }
        else
        {
          g_mapNewLemmaId.insert(make_pair(iPrep,g_iLemmaMappingCounter));
          iPrepMapping = g_iLemmaMappingCounter;
          ++g_iLemmaMappingCounter;
        }

				///neue ID's fuer die Lemmata
        unsigned int iLemma1Mapping(0);  
        itg_mapNewLemmaId = g_mapNewLemmaId.find(iLemma1);
        if (itg_mapNewLemmaId != g_mapNewLemmaId.end())
        {
          iLemma1Mapping = itg_mapNewLemmaId->second;
        }
        else
        {
          g_mapNewLemmaId.insert(make_pair(iLemma1,g_iLemmaMappingCounter));
          iLemma1Mapping = g_iLemmaMappingCounter;
          ++g_iLemmaMappingCounter;
        }
        unsigned int iLemma2Mapping(0);  
        itg_mapNewLemmaId = g_mapNewLemmaId.find(iLemma2);
        if (itg_mapNewLemmaId != g_mapNewLemmaId.end())
        {
          iLemma2Mapping = itg_mapNewLemmaId->second;
        }
        else
        {
          g_mapNewLemmaId.insert(make_pair(iLemma2,g_iLemmaMappingCounter));
          iLemma2Mapping = g_iLemmaMappingCounter;
          ++g_iLemmaMappingCounter;
        }
				///neue ID's fuer die Oberflaechenformen
        unsigned int iSurface1Mapping(0);
        hash_map<unsigned int, unsigned int>::iterator itg_mapNewSurfaceId;
        itg_mapNewSurfaceId = g_mapNewSurfaceId.find(iSurface1);
        if (itg_mapNewSurfaceId != g_mapNewSurfaceId.end())
        {
          iSurface1Mapping = itg_mapNewSurfaceId->second;
        }
        else
        {
          g_mapNewSurfaceId.insert(make_pair(iSurface1,g_iSurfaceMappingCounter));
          iSurface1Mapping = g_iSurfaceMappingCounter;
          ++g_iSurfaceMappingCounter;
        }
        unsigned int iSurface2Mapping(0);  
        itg_mapNewSurfaceId = g_mapNewSurfaceId.find(iSurface2);
        if (itg_mapNewSurfaceId != g_mapNewSurfaceId.end())
        {
          iSurface2Mapping = itg_mapNewSurfaceId->second;
        }
        else
        {
          g_mapNewSurfaceId.insert(make_pair(iSurface2,g_iSurfaceMappingCounter));
          iSurface2Mapping = g_iSurfaceMappingCounter;
          ++g_iSurfaceMappingCounter;
        }
        unsigned int iSurfacePrepMapping(0);  
        itg_mapNewSurfaceId = g_mapNewSurfaceId.find(iSurfacePrep);
        if (itg_mapNewSurfaceId != g_mapNewSurfaceId.end())
        {
          iSurfacePrepMapping = itg_mapNewSurfaceId->second;
        }
        else
        {
          g_mapNewSurfaceId.insert(make_pair(iSurfacePrep,g_iSurfaceMappingCounter));
          iSurfacePrepMapping = g_iSurfaceMappingCounter;
          ++g_iSurfaceMappingCounter;
        }
        
				///schreiben der Relationen mit neuen ID's
        streamOut<<iFunctionname<<'\t';
        streamOut<<iPrepMapping<<'\t';
        streamOut<<iLemma1Mapping<<'\t';
        streamOut<<iLemma2Mapping<<'\t';
        streamOut<<iSurfacePrepMapping<<'\t';
        streamOut<<iSurface1Mapping<<'\t';
        streamOut<<iSurface2Mapping<<'\t';
        streamOut<<iPrepPOS<<'\t';
        streamOut<<iPOS1<<'\t';
        streamOut<<iPOS2<<'\t';
        streamOut<<iInfoMapping<<'\t';
        streamOut<<iFreqBelege<<'\t';
        streamOut<<iFreqRelation<<'\t';
        streamOut<<iMI<<'\t';
        streamOut<<iSalience<<'\t';
        streamOut<<iTScore<<'\t';
        streamOut<<iLogDice<<'\t';
        streamOut<<iMaxLike<<'\n';

        ++g_iHighestRelation;

        g_itMapRel2NoOfKook = g_mapRel2NoOfKook.find(iFunctionname);
        if (g_itMapRel2NoOfKook != g_mapRel2NoOfKook.end())
        {
          get<0>(g_itMapRel2NoOfKook->second)+=1;
          get<1>(g_itMapRel2NoOfKook->second)+=iFreqRelation;
          get<2>(g_itMapRel2NoOfKook->second)+=iFreqBelege;
        }
        else
        {
          g_mapRel2NoOfKook[iFunctionname]=make_tuple(1,iFreqRelation,iFreqBelege);
        }

      }
    }
  }
};

/**
 *
 * Berechnen neuer zusammenhängender IDs für die Relationen der Subkorpora
 *
 **/
void renumber_subcorpora()
{
  //if (g_mapIdToCorpus.size()>1)
  {
		char str[10000];
		hash_map<unsigned int,string>::iterator it;
		for (it = g_mapIdToCorpus.begin(); it != g_mapIdToCorpus.end(); ++it)
		{
		  cout<<"(: renumber subcorpus:"<<it->second<<endl;
		  ifstream streamIn((g_strTablePath+"/relations."+it->second+".table").c_str());
		  ofstream streamOut((g_strTablePath+"/relations."+it->second+".optimized.table").c_str());
		  while (streamIn)
		  {
		    streamIn.getline(str, 1000);
		    if(streamIn) 
		    {
		      ReadTabInput CReadTabInput;
		      if (CReadTabInput.read_line(str,18)) 
		      {
		        unsigned int iFunctionname = atoi(CReadTabInput.get_field(1));
		        unsigned int iPrep = atoi(CReadTabInput.get_field(2));
		        unsigned int iLemma1 = atoi(CReadTabInput.get_field(3));
		        unsigned int iLemma2 = atoi(CReadTabInput.get_field(4));
		        unsigned int iSurfacePrep = atoi(CReadTabInput.get_field(5));
		        unsigned int iSurface1 = atoi(CReadTabInput.get_field(6));
		        unsigned int iSurface2 = atoi(CReadTabInput.get_field(7));
		        unsigned int iPrepPOS = atoi(CReadTabInput.get_field(8));
		        unsigned int iPOS1 = atoi(CReadTabInput.get_field(9));
		        unsigned int iPOS2 = atoi(CReadTabInput.get_field(10));
		        unsigned int iInfo = atoi(CReadTabInput.get_field(11));        
            int iFreqBelege = atoi(CReadTabInput.get_field(12));
		        unsigned int iFreqRelation = atoi(CReadTabInput.get_field(13));        

		        float iMI3 = atof(CReadTabInput.get_field(14));        
		        float iMiLogFreq = atof(CReadTabInput.get_field(15));        
		        float iTScore = atof(CReadTabInput.get_field(16));        
		        float iLogDice = atof(CReadTabInput.get_field(17));    
		        float iMaxLike = atof(CReadTabInput.get_field(18));    


						///neue ID's fuer die Positionsinformationen
				    unsigned int iInfoMapping(iInfo);				    
            if (iFreqBelege != 0)
            {
				      hash_map<unsigned int, unsigned int>::iterator itMapNewInfoId;
				      itMapNewInfoId = g_mapNewInfoId.find(iInfo);
				      if (itMapNewInfoId != g_mapNewInfoId.end())
				      {
				        iInfoMapping = itMapNewInfoId->second;
				      }
				      else
				      {
				        g_mapNewInfoId.insert(make_pair(iInfo,g_iInfoMappingCounter));
				        iInfoMapping = g_iInfoMappingCounter;
				        ++g_iInfoMappingCounter;
				      }
            }
						///neue ID's fuer die Praepositionen
				    unsigned int iPrepMapping(0);				    
				    hash_map<unsigned int, unsigned int>::iterator itg_mapNewLemmaId;
				    itg_mapNewLemmaId = g_mapNewLemmaId.find(iPrep);
				    if (itg_mapNewLemmaId != g_mapNewLemmaId.end())
				    {
				      iPrepMapping = itg_mapNewLemmaId->second;
				    }
				    else
				    {
				      g_mapNewLemmaId.insert(make_pair(iPrep,g_iLemmaMappingCounter));
				      iPrepMapping = g_iLemmaMappingCounter;
				      ++g_iLemmaMappingCounter;
				    }
						///neue ID's fuer die Lemmata
				    unsigned int iLemma1Mapping(0);
				    itg_mapNewLemmaId = g_mapNewLemmaId.find(iLemma1);
				    if (itg_mapNewLemmaId != g_mapNewLemmaId.end())
				    {
				      iLemma1Mapping = itg_mapNewLemmaId->second;
				    }
				    else
				    {
				      g_mapNewLemmaId.insert(make_pair(iLemma1,g_iLemmaMappingCounter));
				      iLemma1Mapping = g_iLemmaMappingCounter;
				      ++g_iLemmaMappingCounter;
				    }
				    unsigned int iLemma2Mapping(0);		
				    itg_mapNewLemmaId = g_mapNewLemmaId.find(iLemma2);
				    if (itg_mapNewLemmaId != g_mapNewLemmaId.end())
				    {
				      iLemma2Mapping = itg_mapNewLemmaId->second;
				    }
				    else
				    {
				      g_mapNewLemmaId.insert(make_pair(iLemma2,g_iLemmaMappingCounter));
				      iLemma2Mapping = g_iLemmaMappingCounter;
				      ++g_iLemmaMappingCounter;
				    }
						///neue ID's fuer die Oberflaechenformen
				    unsigned int iSurface1Mapping(0);		
				    hash_map<unsigned int, unsigned int>::iterator itg_mapNewSurfaceId;
				    itg_mapNewSurfaceId = g_mapNewSurfaceId.find(iSurface1);
				    if (itg_mapNewSurfaceId != g_mapNewSurfaceId.end())
				    {
				      iSurface1Mapping = itg_mapNewSurfaceId->second;
				    }
				    else
				    {
				      g_mapNewSurfaceId.insert(make_pair(iSurface1,g_iSurfaceMappingCounter));
				      iSurface1Mapping = g_iSurfaceMappingCounter;
				      ++g_iSurfaceMappingCounter;
				    }
				    unsigned int iSurface2Mapping(0);		
				    itg_mapNewSurfaceId = g_mapNewSurfaceId.find(iSurface2);
				    if (itg_mapNewSurfaceId != g_mapNewSurfaceId.end())
				    {
				      iSurface2Mapping = itg_mapNewSurfaceId->second;
				    }
				    else
				    {
				      g_mapNewSurfaceId.insert(make_pair(iSurface2,g_iSurfaceMappingCounter));
				      iSurface2Mapping = g_iSurfaceMappingCounter;
				      ++g_iSurfaceMappingCounter;
				    }

				    unsigned int iSurfacePrepMapping(0);		
				    itg_mapNewSurfaceId = g_mapNewSurfaceId.find(iSurfacePrep);
				    if (itg_mapNewSurfaceId != g_mapNewSurfaceId.end())
				    {
				      iSurfacePrepMapping = itg_mapNewSurfaceId->second;
				    }
				    else
				    {
				      g_mapNewSurfaceId.insert(make_pair(iSurfacePrep,g_iSurfaceMappingCounter));
				      iSurfacePrepMapping = g_iSurfaceMappingCounter;
				      ++g_iSurfaceMappingCounter;
				    }

						///schreiben der Relationen mit neuen ID's
		        streamOut<<iFunctionname<<'\t';
				    streamOut<<iPrepMapping<<'\t';
				    streamOut<<iLemma1Mapping<<'\t';
				    streamOut<<iLemma2Mapping<<'\t';
				    streamOut<<iSurfacePrepMapping<<'\t';
				    streamOut<<iSurface1Mapping<<'\t';
				    streamOut<<iSurface2Mapping<<'\t';
		        streamOut<<iPrepPOS<<'\t';
		        streamOut<<iPOS1<<'\t';
		        streamOut<<iPOS2<<'\t';
				    streamOut<<iInfoMapping<<'\t';
		        streamOut<<iFreqBelege<<'\t';
		        streamOut<<iFreqRelation<<'\t';
		        streamOut<<iMI3<<'\t';
		        streamOut<<iMiLogFreq<<'\t';
		        streamOut<<iTScore<<'\t';
		        streamOut<<iLogDice<<'\t';
		        streamOut<<iMaxLike<<'\n';
		      }
		    }
		  }
		}
  }
}

/**
 *
 * Berechnen neuer IDs für die Mappings und Schreiben dieser Mappings
 *
 **/
void renumber_mappings()
{
  cout<<"(: renumber tables"<<endl;

  char a[1000];  
  char str[1000];
  
  {
	  ///berechnen von groessen und laengen bezueglich der praepositionen
    hash_map<unsigned int,unsigned int>::iterator itMapNewPOSId;
    ifstream inputPOSMapping((g_strTablePath+"/mapping_POS.table").c_str());  
    while(inputPOSMapping) 
    {
      inputPOSMapping.getline(str, 1000);  // delim defaults to '\n'
      if(inputPOSMapping) 
      {
        ReadTabInput CReadTabInput;
        if (CReadTabInput.read_line(str,2))
        {
          unsigned int iPOS = atoi(CReadTabInput.get_field(1));
          const char* szPOS = CReadTabInput.get_field(2);

          unsigned int iLength(strlen(szPOS));
          if (iLength > g_iLengthPOS)
            g_iLengthPOS = iLength;
          if (iPOS > g_iSizePOS)
            g_iSizePOS = iPOS;
        }
      }
    }
  }
  
  {
	  ///berechnen von groessen und laengen bezueglich der corpora
    hash_map<unsigned int,unsigned int>::iterator itMapNewCorpusId;
    ifstream inputCorpusMapping((g_strTablePath+"/mapping_corpus.table").c_str());  
    while(inputCorpusMapping) 
    {
      inputCorpusMapping.getline(str, 1000);  // delim defaults to '\n'
      if(inputCorpusMapping) 
      {
        ReadTabInput CReadTabInput;
        if (CReadTabInput.read_line(str,2))
        {
          unsigned int iCorpus = atoi(CReadTabInput.get_field(1));
          const char* szCorpus = CReadTabInput.get_field(2);

          unsigned int iLength(strlen(szCorpus));
          if (iLength > g_iLengthCorpus)
            g_iLengthCorpus = iLength;
          if (iCorpus > g_iSizeCorpus)
            g_iSizeCorpus = iCorpus;
        }
      }
    }
  }

  {
    cout<<"(: renumber lemma forms"<<endl;
	  hash_map<unsigned int,string> mapLemmaId;
	  ///Aktualisierung der Lemma-IDs und berechnen von groessen und laengen
    hash_map<unsigned int,unsigned int>::iterator itg_mapNewLemmaId;
    ifstream inputLemmaMapping((g_strTablePath+"/mapping_lemma.table").c_str());
    ofstream outputLemmaMapping((g_strTablePath+"/mapping_lemma.optimized.table").c_str());
    ofstream outputLemmaMappingLower((g_strTablePath+"/mapping_lemma_lower.table").c_str());
    while(inputLemmaMapping) 
    {
      inputLemmaMapping.getline(str, 1000);  // delim defaults to '\n'
      if(inputLemmaMapping) 
      {
        ReadTabInput CReadTabInput;
        if (CReadTabInput.read_line(str,2))
        {
          unsigned int iLemma = atoi(CReadTabInput.get_field(1));
          const char* szLemma = CReadTabInput.get_field(2);

          itg_mapNewLemmaId = g_mapNewLemmaId.find(iLemma);
          if (itg_mapNewLemmaId != g_mapNewLemmaId.end())
          {
					  mapLemmaId.insert(make_pair(itg_mapNewLemmaId->second,szLemma));

            unsigned int iLength(strlen(szLemma));
            if (iLength > g_iLengthLemma)
              g_iLengthLemma = iLength;
               
            ++g_iSizeLemma;
            outputLemmaMapping<<itg_mapNewLemmaId->second<<'\t';
            outputLemmaMapping<<szLemma<<'\n';

            outputLemmaMappingLower<<itg_mapNewLemmaId->second<<'\t';
            outputLemmaMappingLower<<normalize_to_lower(szLemma)<<'\n';
          }
        }
      }
    }
    inputLemmaMapping.close();

    hash_map<unsigned int, set<pair<unsigned int,unsigned int> > > mapSurfaceLemma;
    hash_map<unsigned int, set<pair<unsigned int,unsigned int> > >::iterator itMapSurfaceLemma;

	  mapLemmaId.clear();
    
    cout<<"(: renumber surface forms"<<endl;
	  ///Aktualisierung der Oberflaechenform-IDs und berechnen von groessen und laengen
    hash_map<unsigned int,unsigned int>::iterator itg_mapNewSurfaceId;
    ifstream inputSurfaceMapping((g_strTablePath+"/mapping_surface.table").c_str());
    ofstream outputSurfaceMapping((g_strTablePath+"/mapping_surface.optimized.table").c_str());
    while(inputSurfaceMapping) 
    {
      inputSurfaceMapping.getline(str, 1000);  // delim defaults to '\n'
      if(inputSurfaceMapping) 
      {
        ReadTabInput CReadTabInput;
        if (CReadTabInput.read_line(str,2))
        {
          unsigned int iSurface = atoi(CReadTabInput.get_field(1));
          const char* szSurface = CReadTabInput.get_field(2);

          itg_mapNewSurfaceId = g_mapNewSurfaceId.find(iSurface);
          if (itg_mapNewSurfaceId != g_mapNewSurfaceId.end())
          {
            unsigned int iLength(strlen(szSurface));
            if (iLength > g_iLengthSurface)
              g_iLengthSurface = iLength;

            ++g_iSizeSurface;
            outputSurfaceMapping<<itg_mapNewSurfaceId->second<<'\t';
            outputSurfaceMapping<<szSurface<<'\n';
          }
        }
      }
    }
    //outputSurfaceLemma.close();
    mapSurfaceLemma.clear();
  }
  
  cout<<"(: renumber hits"<<endl;
	///Aktualisierung der Positionsinformation-IDs und berechnen von groessen und laengen
  unsigned int max(-1);
  vector<unsigned int> vTest(g_iInfoMappingCounter+1,max);
  map<unsigned int,unsigned int> mapTest;
  ifstream inputInfo2Mapping((g_strTablePath+"/mapping_info.table").c_str());
  while(inputInfo2Mapping) 
  {
    inputInfo2Mapping.getline(str, 1000); 
    if(inputInfo2Mapping) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,2))
      {
        unsigned int iDummy (atoi(CReadTabInput.get_field(2)));
        unsigned int iDummy2 (atoi(CReadTabInput.get_field(1)));
        
        hash_map<unsigned int, unsigned int>::iterator it;
        it = g_mapNewInfoId.find(iDummy2);
        if (it != g_mapNewInfoId.end())
        {                 
          if (vTest.size()<=iDummy)
          {
            vTest.resize(iDummy+1,max);
          }
          vTest[iDummy] = it->second;
        }
      }      
    }
  }
	///Belege auf das minimum reduzieren (nur das, was gebraucht wird) und berechnen von groessen und laengen
  char str2[100000];
  ifstream inputInfoMapping((g_strTablePath+"/mapping_position.table").c_str());
  ofstream outputInfoMapping2((g_strTablePath+"/mapping_position_info.table").c_str());
  while(inputInfoMapping) 
  {
    inputInfoMapping.getline(str2, 100000);  // delim defaults to '\n'
    if(inputInfoMapping) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str2,8))
      {
        //if (mapTest.find(atoi(CReadTabInput.get_field(1))) != mapTest.end())
        if (atoi(CReadTabInput.get_field(1))<vTest.size())
        {
          unsigned int iDummy = vTest[atoi(CReadTabInput.get_field(1))];

          int iTokenPositionW1 = atoi(CReadTabInput.get_field(2));
          int iTokenPositionW2 = atoi(CReadTabInput.get_field(3));
          int iTokenPositionPrep = atoi(CReadTabInput.get_field(4));
          unsigned int iSentence = atoi(CReadTabInput.get_field(5));
          unsigned int iFilename = atoi(CReadTabInput.get_field(6));
          unsigned int iCorpus = atoi(CReadTabInput.get_field(7));
          unsigned int iAvail = atoi(CReadTabInput.get_field(8));

          if (iTokenPositionW1 == -1)
            iTokenPositionW1 = 0;
          if (iTokenPositionW2 == -1)
            iTokenPositionW2 = 0;
          if (iTokenPositionPrep == -1)
            iTokenPositionPrep = 0;
          
					///wenn der Beleg wirklich gebraucht wird
          if (iDummy!=max)
          {
            unsigned int iFilenameMapping(0);
            
            hash_map<unsigned int, unsigned int>::iterator itMapNewFilenameId;
            itMapNewFilenameId = g_mapNewFilenameId.find(iFilename);
            if (itMapNewFilenameId != g_mapNewFilenameId.end())
            {
              iFilenameMapping = itMapNewFilenameId->second;
            }
            else
            {
              g_mapNewFilenameId.insert(make_pair(iFilename,g_iFilenameMappingCounter));
              iFilenameMapping = g_iFilenameMappingCounter;
              ++g_iFilenameMappingCounter;
            }

						///aktualisieren globaler groessen und laengen
            if (iTokenPositionW1 > g_iHighestTokenPositionW1)
            {
              g_iHighestTokenPositionW1 = iTokenPositionW1; 
            }
            if (iTokenPositionW2 > g_iHighestTokenPositionW2)
            {
              g_iHighestTokenPositionW2 = iTokenPositionW2; 
            }
            if (iTokenPositionPrep > g_iHighestPrepPosition)
            {
              g_iHighestPrepPosition = iTokenPositionPrep; 
            }
            if (iSentence > g_iHighestSentence)
            {
              g_iHighestSentence = iSentence; 
            }
            if (iFilenameMapping > g_iHighestFilename)
            {
              g_iHighestFilename = iFilenameMapping; 
            }            

						///schreiben der reduzierten Belege            
            outputInfoMapping2<<iDummy<<'\t';
            outputInfoMapping2<<iTokenPositionW1<<'\t';
            outputInfoMapping2<<iTokenPositionW2<<'\t';
            outputInfoMapping2<<iTokenPositionPrep<<'\t';
            outputInfoMapping2<<iSentence<<'\t';
            outputInfoMapping2<<iFilenameMapping<<'\t';
            outputInfoMapping2<<iCorpus<<'\t';
            outputInfoMapping2<<iAvail<<'\n';

            ++g_iSizeInfo;
          } 
        }
      }
    }
  }
  inputInfoMapping.close();
  outputInfoMapping2.close();

  ////////////////////////////////////////////////////////////////////
  /// wegen der KOORD-Relationen oder META-Relationen können Doppelungen auftreten (über vTest auf das selbe abgebildet)
  ///////////////////////////////////////////////////////////////////
  cout<<"(: remove unique hits"<<endl;

  int i;
  i = system(("sort -T "+g_strTmpPath+" -o "+g_strTablePath+"/mapping_position_info.table_sort "+g_strTablePath+"/mapping_position_info.table").c_str());  
	check_error(i);

  i = system(("uniq "+g_strTablePath+"/mapping_position_info.table_sort "+g_strTablePath+"/mapping_position_info.table").c_str());  
	check_error(i);

  i = system(("rm "+g_strTablePath+"/mapping_position_info.table_sort ").c_str());  
	check_error(i);

  {
	  ///Aktualisierung der File-IDs und berechnen von groessen und laengen
    hash_map<unsigned int,unsigned int>::iterator itMapNewFilenameId;
    ifstream inputFilenameMapping((g_strTablePath+"/mapping_file.table").c_str());
    ofstream outputFilenameMapping((g_strTablePath+"/mapping_file.optimized.table").c_str());
    while(inputFilenameMapping) 
    {
      inputFilenameMapping.getline(str, 1000);  // delim defaults to '\n'
      if(inputFilenameMapping) 
      {
        ReadTabInput CReadTabInput;
        if (CReadTabInput.read_line(str,2))
        {
          unsigned int iFilename = atoi(CReadTabInput.get_field(1));
          const char* szFilename = CReadTabInput.get_field(2);

          itMapNewFilenameId = g_mapNewFilenameId.find(iFilename);
          if (itMapNewFilenameId != g_mapNewFilenameId.end())
          {
            unsigned int iLength(strlen(szFilename));
            if (iLength > g_iLengthFilename)
              g_iLengthFilename = iLength;

            outputFilenameMapping<<itMapNewFilenameId->second<<'\t';
            outputFilenameMapping<<szFilename<<'\n';
          }
        }
      }
    }
  }
};

/**
 *
 * Schreiben von Projektinformationen:
 *   -Autor
 *   -Erstellungsdfatum
 *   -Spezifikationsdateiname
 *   -Spezifikationsversionsnummer
 *
 **/
void write_project_info(string strSpecificationfilename)
{
  time_t Zeitstempel;
  tm *nun;
  Zeitstempel = time(0);
  nun = localtime(&Zeitstempel);
  char buffer [50];
  sprintf (buffer, "%i.%i.%i", nun->tm_mday, nun->tm_mon+1, nun->tm_year+1900);
  string strTime = buffer;

  ofstream outputInfo((g_strTablePath+"/info.table").c_str());

  outputInfo<<"Author\t"<<g_strAuthor<<endl;
  outputInfo<<"CreationDate\t"<<strTime<<endl;
  outputInfo<<"SpecFile\t"<<strSpecificationfilename<<endl;
  outputInfo<<"SpecFileVersion\t"<<g_strVersion<<endl;
  outputInfo<<"LemmaCut\t"<<g_iLemmaCut<<endl;
  
  outputInfo.close();
}

/**
 *
 * Hauptfunktion
 *
 **/
int main(int argc, char* argv[])
{
  if (argc != 2)
  {
    cerr<<"): falscher Parameteraufruf -> die XML-Specification angeben"<<endl; 
    exit(-1);
  }  

  cout<<"|: POSTPROCESSING"<<endl;

  //bei fehlender coord information -> 0
  g_mapNewInfoId.insert(make_pair(0,0));

  ///Spezifikation einlesen
	init_spec(argv[1]);

	///einige wichtige informationen laden (relationen und corpora)
  load_relation_corpus_mappings();

 	///Relationsdateien mit neuen IDs (durchgehend nummeriert) versehen
  renumber();  
  if (g_bUseSubcorpora)
  {
    renumber_subcorpora();
  }

	///die mapping-Dateien bezueglich der neuen IDs aktualisieren
  renumber_mappings(); 
 
	///Berechnen der (w1(Lemma),w1(POS)) tupel
  head_pos_frequency();
  if (g_bUseSubcorpora)
  {
    head_pos_frequency_subcorpora();
  }

	///Berechnen der (w1(Lemma),w1(POS),R) tupel
  head_pos_relation_frequency();
  if (g_bUseSubcorpora)
  {
    head_pos_relation_frequency_subcorpora();  
  }

  ///negieren der Statistikwerte
	negate_statistics();
  if (g_bUseSubcorpora)
  {
	  negate_statistics_subcorpora();
  }

	///Schreiben der Typeninformationen fuer die Datenbank
	write_types();

  int i;
  ///Umbenennen von Tabellen
  /*i = system(("mv "+g_strTablePath+"/mapping_lemma.optimized.table "+g_strTablePath+"/mapping_lemma.table ").c_str());
  check_error(i);
  i = system(("mv "+g_strTablePath+"/relations.optimized.table "+g_strTablePath+"/relations.table ").c_str());
  check_error(i);
  i = system(("mv "+g_strTablePath+"/mapping_surface.optimized.table "+g_strTablePath+"/mapping_surface.table ").c_str());
  check_error(i);
  i = system(("mv "+g_strTablePath+"/mapping_file.optimized.table "+g_strTablePath+"/mapping_file.table ").c_str());
  check_error(i);*/

  ///schreiben von Projektinformationen
  write_project_info(argv[1]);

  cout<<"|: done"<<endl;
};
  
