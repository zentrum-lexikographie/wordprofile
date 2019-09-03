/**
 * Programm zum Anreichen der Kookkurrenzinformationen mit statistischen Werten.
 * 
 * folgende Tabellen werden generiert: 
 *
 * + relations.table -> 
 *    -Relationsname
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
 **/

#include <iostream>
#include <vector>
#include <string.h>
#include <fstream>
#include <fstream>
#include <map>
#include <algorithm>
#include <math.h>

#include "hashes.h"
#include "read_specification.h"
#include "read_tab_input.h"

///Pfade
string g_strRelationPath = "";
string g_strTablePath = "";

///Modus fuer die Statistikberechnung (wie dreistellige Relationen behandelt werden)
TernaryRelationMode g_eTernaryRelationMode = AttachToRelation;
///hash-map fuer die Relationen

hash_map<HashPair,unsigned int,PSHashPair,PSEqualToPair>::iterator g_itMapMate;
hash_map<unsigned int,unsigned int>::iterator g_itMapMate_global;
hash_map<unsigned int,unsigned int>::iterator g_itMapMate_global2;
///informationen fuer die transrelationalen Bedingungen
vector<Connection> g_vCConnection;
map<string,vector<Connection> > g_mapCConnection;
map<string,vector<Connection> >::iterator g_itMapCConnection;
///hash-maps fuer relationstyp corpus und frequenz
hash_map<string,unsigned int> g_mapFunction;
hash_map<string,unsigned int>::iterator g_itMapFunction;
hash_map<unsigned int,unsigned int> g_mapFrequency;
hash_map<unsigned int,unsigned int> g_mapFrequencyTrigger;
hash_map<unsigned int,unsigned int> g_mapFrequencyBelege;
hash_map<unsigned int,string> g_mapIdToCorpus;
///Set mit verwendeten Corpora
set<unsigned int> g_setUsedCorpora;
///Anzahl aller Relationen
unsigned int g_iAllTriple;
///map von Spezifikationen bezueglich der Relationen
map<unsigned int,Specification> g_mapSpecification;
hash_set<unsigned int> g_setFrequencyIdCut;
///object zum einlesen der Specification
ReadSpecification g_CReadSpecification;
vector<Specifications> g_vSpecifications;

///lemma-Zählung: (w,*,*)
hash_map<unsigned int,unsigned int> g_mapLemmaCut;
hash_map<unsigned int,unsigned int>::iterator g_itMapLemmaCut;

hash_map<unsigned int,unsigned int> g_mapLemmaCut2;
hash_map<unsigned int,unsigned int>::iterator g_itMapLemmaCut2;

///globaler Lemmafrequenzschwellwert
int g_iLemmaCut;
///ob Subkorpora berechnet werden sollen
bool g_bUseSubcorpora;

/**
 *
 * eventuell einen Fehler werfen
 *
 **/
void check_error(int iCode,string strCall)
{
  if (iCode != 0)
  {
    cerr<<"): Systemaufrufsfehler: "<<strCall<<endl;
		exit(-1);
  }
}

/**
 *
 * Relevante Informationen für die Berechnung der Statistik
 *
 **/
struct StatInfo
{
  ///Frequenz einer Kookkurrenz innerhalb einer Relation
  unsigned int iFreqRelation;
  ///Anzahl der unterschiedlichen Kookkurrenzen in einer Relation
  unsigned int iCountRelation;
  ///Frequenz des Kopfes des Kookkurrenzpaares innerhalb einer Relation
  unsigned int iFreqHeadWord;
  ///Frequenz des Dependenten des Kookkurrenzpaares innerhalb einer Relation
  unsigned int iFreqDepWord;
};

/**
 *
 * Speicher für die relevanten Kookkurrenzinformationen
 *
 **/
struct CooccInfo
{
  CooccInfo():
    iFrequency(0),
    iSurfacePrep(0),
    iSurface1(0),
    iSurface2(0),
    iInfo(0)
  {
  } 
  ///Frequenz-ID
  unsigned int iFrequency;
  ///ID der Oberflächenform der Präposition
  unsigned int iSurfacePrep;
  ///ID der Oberflächenform des ersten Wortes
  unsigned int iSurface1;
  ///ID der Oberflächenform des zweiten Wortes
  unsigned int iSurface2;
  ///ID der Fundstelleninformation
  unsigned int iInfo;
};

/**
 *
 * Ergebniszahlen der Statistischen Berechnung
 *
 **/
struct StatRes
{
  StatRes():
    iMI3(0),
    iMiLogFreq(0),
    iLogDice(0),
    TScore(0),
		iLogLike(0)
  {
  }
  long double iMI3;
  long double iMiLogFreq;
  long double iLogDice;
  long double TScore;
  long double iLogLike;
};

///Funktionen
void init_spec(const char* pcFile);
void read_mappings();
void read_subcorpus_frequency_mapping(unsigned int _iCorpus);
StatRes calculate_statistics(const StatInfo& SI);
StatRes adjust_statistics(StatRes CStatRes, unsigned int iFunctionname);
void calculate_transrelational_connections(Connection& CConnection);
void calc_lemma_cut();
void lemma_cut_beta(int iFunctionname, unsigned short int iCountMode, ifstream& stream, hash_map<unsigned int,unsigned int>& l_mapLemmaCut);
void lemma_cut(const Specifications& CSpecifications,hash_map<unsigned int,unsigned int>& l_mapLemmaCut);
void salience(const Specifications& CSpecifications, ofstream& outputStatistics, const string& strCorpus);
void salience_beta(int iFunctionname, bool bInvert, ifstream& stream, ofstream& outputStatistics,bool bSubcorpus, string strCorpus="");

/**
 *
 * Einlesen der Spezifikation
 *
 **/
void init_spec(const char* pcFile)
{
  g_CReadSpecification.parse_xml(pcFile);
  g_strRelationPath = g_CReadSpecification.relation_path();
  g_strTablePath = g_CReadSpecification.table_path();
  g_eTernaryRelationMode = g_CReadSpecification.ternary_relation_mode();
  g_vSpecifications = g_CReadSpecification.get_specifications();
  g_vCConnection = g_CReadSpecification.get_connections();
  g_bUseSubcorpora = g_CReadSpecification.use_subcorpora();
  g_iLemmaCut = g_CReadSpecification.lemma_cut();
}

/**
 *
 * Einlesen der Mapping-Informationen
 * +Relationsnamen
 * +Korpusnamen
 * +Frequenzinformationen
 *
 **/
void read_mappings()
{
  char str[10000];
  hash_map<unsigned int,unsigned int>::iterator itMapNewPOSId;
  ifstream inputFunctionMapping((g_strTablePath+"/mapping_function.table").c_str());  
  while(inputFunctionMapping) 
  {
    inputFunctionMapping.getline(str, 10000);
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

  ifstream inputFrequencyMapping((g_strTablePath+"/mapping_frequency.table").c_str());  
  while(inputFrequencyMapping) 
  {
    inputFrequencyMapping.getline(str, 10000);
    if(inputFrequencyMapping) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,3))
      {
        unsigned int iId = atoi(CReadTabInput.get_field(1));
        unsigned int iCorpus = atoi(CReadTabInput.get_field(2));
        unsigned int iFrequency = atoi(CReadTabInput.get_field(3));

        if (iCorpus==0)
        {
          g_mapFrequency.insert(make_pair(iId,iFrequency));
        }
        else if (iCorpus==1)
        {
          g_mapFrequencyTrigger.insert(make_pair(iId,iFrequency));
        }
        else if (iCorpus==2)
        {
          g_mapFrequencyBelege.insert(make_pair(iId,iFrequency));
        }
        else
        {
          g_setUsedCorpora.insert(iCorpus - 1000);
        }
      }
    }
  }
}

/**
 *
 * Einlesen der Frequenzinformationen bezüglich eines Subkorpus
 *
 **/
void read_subcorpus_frequency_mapping(unsigned int _iCorpus)
{
  char str[10000];
  ifstream inputFrequencyMapping((g_strTablePath+"/mapping_frequency.table").c_str());  
  while(inputFrequencyMapping) 
  {
    inputFrequencyMapping.getline(str, 10000);
    if(inputFrequencyMapping) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,3))
      {
        unsigned int iId = atoi(CReadTabInput.get_field(1));
        unsigned int iCorpus = atoi(CReadTabInput.get_field(2));
        unsigned int iFrequency = atoi(CReadTabInput.get_field(3));

        if (iCorpus==_iCorpus +1000)
        {
          ///wenn Globale Schwellwerte gegriffen haben (global für alle Korpora)
					if (g_setFrequencyIdCut.find(iId) != g_setFrequencyIdCut.end())
					{
		        g_mapFrequency.insert(make_pair(iId,0));
		        g_setUsedCorpora.insert(iCorpus - 1000);
					}
					else
					{
		        g_mapFrequency.insert(make_pair(iId,iFrequency));
		        g_setUsedCorpora.insert(iCorpus - 1000);
					}
        }
      }
    }
  }
}

/**
 *
 * Berechnen der Statistikwerte zu einer Kookkurrrenz
 * +nach "Corpora and Collocations" von Stefan Evert
 *
 **/
StatRes calculate_statistics(const StatInfo& SI)
{
	StatRes CStatRes;

  long double iCountRelation(SI.iCountRelation);
  long double iFreqRelation(SI.iFreqRelation);
  long double iFreqHeadWord(SI.iFreqHeadWord);
  long double iFreqDepWord(SI.iFreqDepWord);
  long double iAllTriple(g_iAllTriple);

  long double iO11 = iFreqRelation;
  long double iO12 = iFreqHeadWord - iFreqRelation;
  long double iO21 = iFreqDepWord - iFreqRelation;
  long double iO22 = iCountRelation - iFreqDepWord - iFreqHeadWord + iFreqRelation;

  long double iR1 = iFreqHeadWord;
  long double iR2 = iCountRelation - iFreqHeadWord;
  long double iC1 = iFreqDepWord;
  long double iC2 = iCountRelation - iFreqDepWord;
  long double iN = iCountRelation;

  long double iE11 = (iR1 * iC1) / iN;
  long double iE12 = (iR1 * iC2) / iN;
  long double iE21 = (iR2 * iC1) / iN;
  long double iE22 = (iR2 * iC2) / iN;

  ///local MI
  long double iStat_localMI = iO11 * log2(iO11 / iE11);
  ///MiLogFreq
  long double iStat_MiLogFreq = log(iO11+1.0) * log2(iO11 / iE11);
	///Association Score
  long double iStat_ChiSquare = log((iFreqRelation*iAllTriple)/(iFreqHeadWord*iFreqDepWord))*log(iFreqRelation+1.0);
  ///MI
  long double iStat_MI = log2(iO11 / iE11);
  ///MI2
  long double iStat_MI2 = log2(pow(iO11,2) / iE11);
  ///MI3
  long double iStat_MI3 = log2(pow(iO11,3) / iE11);

	///LogDice
  long double iStat_logDice = 14 + log2((2.0 * iO11) / (iR1 + iC1));

  ///Log-Likelihood (Formel von Evert)
  long double iStat_logLike = 2 * ( 
                          (iO11 * log(iO11 / iE11)) +
                          (iO12 * log(iO12 / iE12)) +
                          (iO21 * log(iO21 / iE21)) +
                          (iO22 * log(iO22 / iE22))
                         );
	if (isnan(iStat_logLike))
	{
		iStat_logLike = 0.0;
	}
	else if (iStat_logLike>100000.0 || iStat_logLike<-100000.0)
	{
		iStat_logLike = 99999.0;
	}

  //Chi-Squared
  long double iStat_chiSquared = (pow(iO11 - iE11,2) / iE11) +
                                  (pow(iO12 - iE12,2) / iE12) +
                                  (pow(iO21 - iE21,2) / iE21) +
                                  (pow(iO22 - iE22,2) / iE22);

  //T-Score
  long double iStat_tScore = (iO11 - iE11) / sqrt(iO11);

  //Minimum Sensitivity
  long double iStat_MinSensitivity = min((iFreqRelation / iFreqHeadWord),(iFreqRelation / iFreqDepWord));

  ///Zuweisung der relevanten Werte
  CStatRes.iLogLike = iStat_logLike;
  CStatRes.TScore = iStat_tScore;
  CStatRes.iMI3 = iStat_MI3;
  CStatRes.iLogDice = iStat_logDice;
  CStatRes.iMiLogFreq = iStat_MiLogFreq;

	return CStatRes;
}

/**
 *
 * Verschiebung der Statistikwerte (auf der X-Achse)
 *
 **/
StatRes adjust_statistics(StatRes CStatRes, unsigned int iFunctionname)
{
  map<unsigned int,Specification>::iterator itMapSpecification;
  itMapSpecification = g_mapSpecification.find(iFunctionname);
  if (itMapSpecification!=g_mapSpecification.end())
  {
		CStatRes.iMI3 += itMapSpecification->second.adjust_MI3();
		CStatRes.iMiLogFreq += itMapSpecification->second.adjust_MiLogFreq();
		CStatRes.TScore += itMapSpecification->second.adjust_TScore();
		CStatRes.iLogDice += itMapSpecification->second.adjust_logDice();
		CStatRes.iLogLike += itMapSpecification->second.adjust_logLike();
	}
	return CStatRes;
}

/**
 *
 * Berechnung transrelationaler Bedingungen
 * +Es werden zwei Relationen in Beziehung gesetzt und es werden Kookkurrrenzen anhand eines Anteilvergleiches ausgeschlossen
 *
 **/
void calculate_transrelational_connections(Connection& CConnection)
{
  ///hash-maps fuer die Berechnung transrelationaler Bedingungen
  hash_map<HashPair,unsigned int,PSHashPair,PSEqualToPair> g_mapMate;
  hash_map<unsigned int,unsigned int> g_mapMate_global;
  hash_map<unsigned int,unsigned int> g_mapMate_global2;
  hash_map<unsigned int,unsigned int> g_mapMate_global_inv;
  hash_map<unsigned int,unsigned int> g_mapMate_global_inv2;

  string strFileRel1 = g_strTablePath + "/" + CConnection.strRel1 + ".relations.freq.table";
  string strFileRel2 = g_strTablePath + "/" + CConnection.strRel2 + ".relations.freq.table";

  cout<<"(: calculate trans-relational connections"<<endl;

  string strInFile1 = strFileRel1;
  string strInFile2 = strFileRel2;

  ///Einsammeln der Information zur zweiten Relation
  ifstream streamIn(strInFile2.c_str());  
  char str[1000];
  while (streamIn)
  {
    streamIn.getline(str, 1000);
    if(streamIn) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,11))
      {
        unsigned int iFrequency = atoi(CReadTabInput.get_field(1));
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

        g_mapMate.insert(make_pair(HashPair(iLemma1,iLemma2),g_mapFrequencyTrigger[iFrequency]));

				g_itMapMate_global = g_mapMate_global.find(iLemma1);
				if (g_itMapMate_global!=g_mapMate_global.end())
				{
					g_itMapMate_global->second += g_mapFrequencyTrigger[iFrequency];
				}
				else
				{
          g_mapMate_global.insert(make_pair(iLemma1,g_mapFrequencyTrigger[iFrequency]));
        }

				g_itMapMate_global = g_mapMate_global_inv.find(iLemma2);
				if (g_itMapMate_global!=g_mapMate_global_inv.end())
				{
					g_itMapMate_global->second += g_mapFrequencyTrigger[iFrequency];
				}
				else
				{
          g_mapMate_global_inv.insert(make_pair(iLemma2,g_mapFrequencyTrigger[iFrequency]));
        }
      }
    }
  }
  streamIn.close();

  ///Einsammeln der Information zur ersten Relation
  streamIn.open(strInFile1.c_str());
  while (streamIn)
  {
    streamIn.getline(str, 1000);
    if(streamIn) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,11))
      {
        unsigned int iFrequency = atoi(CReadTabInput.get_field(1));
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

				g_itMapMate_global2 = g_mapMate_global2.find(iLemma1);
				if (g_itMapMate_global2!=g_mapMate_global2.end())
				{
					g_itMapMate_global2->second += g_mapFrequencyTrigger[iFrequency];
				}
				else
				{
          g_mapMate_global2.insert(make_pair(iLemma1,g_mapFrequencyTrigger[iFrequency]));
        }

				g_itMapMate_global2 = g_mapMate_global_inv2.find(iLemma2);
				if (g_itMapMate_global2!=g_mapMate_global_inv2.end())
				{
					g_itMapMate_global2->second += g_mapFrequencyTrigger[iFrequency];
				}
				else
				{
          g_mapMate_global_inv2.insert(make_pair(iLemma2,g_mapFrequencyTrigger[iFrequency]));
        }
			}
		}
	}
	streamIn.close();

  cout<<"(: calculate transrelational cut: "<<CConnection.strRel1<<"/"<<CConnection.strRel2<<endl;

  ///Ausschliessen von Kookkurrrenzen
  streamIn.open(strInFile1.c_str());
  while (streamIn)
  {
    streamIn.getline(str, 1000);
    if(streamIn) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,11))
      {
        unsigned int iFrequency = atoi(CReadTabInput.get_field(1));
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

				///pruefen auf lokale Bedingung (zB.: SUBJ --> sehen <-- OBJA)
        g_itMapMate = g_mapMate.find(HashPair(iLemma1,iLemma2)); 
        if (g_itMapMate != g_mapMate.end())
        {
          unsigned int iOtherFreq = g_itMapMate->second; 
          ///Anteil der ersten Relation an beiden Relationen (in Bezug zur Frequenz der entsprechenden Kookkurrenz)
          float iW = ((float(g_mapFrequencyTrigger[iFrequency])/(float(iOtherFreq) + float(g_mapFrequencyTrigger[iFrequency])))*100);

          ///prüfen der Schwellwerte
          if (iW < CConnection.iMin || iW > CConnection.iMax)
          {   
						///bedingung ist nicht erfuellt, markieren mit der Frequenz 0
						g_mapFrequency[iFrequency]=0;
		        continue;
					}
        }

				///pruefen auf globale Bedingung (nur bezüglich des ersten Wortes) (zB.: SUBJ --> <-- OBJA)
        g_itMapMate_global = g_mapMate_global.find(iLemma1); 
        g_itMapMate_global2 = g_mapMate_global2.find(iLemma1); 
        if (g_itMapMate_global != g_mapMate_global.end() && g_itMapMate_global2 != g_mapMate_global2.end())
        {
		      unsigned int iOtherFreq_global = g_itMapMate_global->second; 
          ///Anteil der ersten Relation an beiden Relationen (in Bezug zur Frequenz der entsprechenden Kookkurrenz)
		      float iW_global = ((float(g_itMapMate_global2->second)/(float(iOtherFreq_global) + float(g_itMapMate_global2->second)))*100);
          ///prüfen der Schwellwerte
		      if (iW_global < CConnection.iMin_global || iW_global > CConnection.iMax_global)
		      {   
						///bedingung ist nicht erfuellt, markieren mit der Frequenz 0
						g_mapFrequency[iFrequency]=0;
		        continue;
					}
				}

				///pruefen auf globale Bedingung (nur bezüglich des zweiten Wortes) (zB.: SUBJ --> <-- OBJA)
        g_itMapMate_global = g_mapMate_global_inv.find(iLemma2); 
        g_itMapMate_global2 = g_mapMate_global_inv2.find(iLemma2); 
        if (g_itMapMate_global != g_mapMate_global_inv.end() && g_itMapMate_global2 != g_mapMate_global_inv2.end())
        {
		      unsigned int iOtherFreq_global = g_itMapMate_global->second; 
          ///Anteil der ersten Relation an beiden Relationen (in Bezug zur Frequenz der entsprechenden Kookkurrenz)
		      float iW_global = ((float(g_itMapMate_global2->second)/(float(iOtherFreq_global) + float(g_itMapMate_global2->second)))*100);
          ///prüfen der Schwellwerte
		      if (iW_global < CConnection.iMin_global_inv || iW_global > CConnection.iMax_global_inv)
		      {   
						///bedingung ist nicht erfuellt, markieren mit der Frequenz 0
						g_mapFrequency[iFrequency]=0;
		        continue;
					}
				}
      }
    }
  }

  g_mapMate.clear();
  g_mapMate_global.clear();
  g_mapMate_global2.clear();
  g_mapMate_global_inv.clear();
  g_mapMate_global_inv2.clear();
};

/**
 *
 * Berechnung von Frequenzen für den Schwellwert auf die globale Lemmafrequenzen
 * +ablegen der Frequenzinformationen in l_mapLemmaCut
 *
 **/
void lemma_cut(const Specifications& CSpecifications,hash_map<unsigned int,unsigned int>& l_mapLemmaCut)
{
  ///Einlesen des Relationsnamenmappings
  hash_map<string,unsigned int> g_mapFunctionMapping;  
  ifstream inputFunctionMapping((g_strTablePath+"/mapping_function.table").c_str());
  char str[1000];
  while(inputFunctionMapping) 
  {
    inputFunctionMapping.getline(str, 1000);
    if(inputFunctionMapping) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,3))
      {
        unsigned int iFunction = atoi(CReadTabInput.get_field(1));
        const char* szFunction = CReadTabInput.get_field(2);
        const char* szType = CReadTabInput.get_field(3);
        g_mapFunctionMapping.insert(make_pair(szFunction,iFunction));
      }
    }
  }

  string strFile = g_strTablePath + "/" + CSpecifications.CSpecification1.functionname() + ".relations.freq.table";
  ifstream stream(strFile.c_str());

  unsigned int iFunctionname(0);
  iFunctionname = g_mapFunctionMapping[CSpecifications.CSpecification1.functionname()];

  if (CSpecifications.invert() == InvertNo)
  {
    if (CSpecifications.CSpecification1.use_lemma_cut())
    {
      lemma_cut_beta(iFunctionname, 0, stream,l_mapLemmaCut);
    }
  }
  else if (CSpecifications.invert() == InvertBidirect)
  {
    if (CSpecifications.CSpecification1.use_lemma_cut() && CSpecifications.CSpecification2.use_lemma_cut())
    {
      lemma_cut_beta(iFunctionname, 0, stream,l_mapLemmaCut);
    }
    else if (CSpecifications.CSpecification1.use_lemma_cut())
    {
      lemma_cut_beta(iFunctionname, 1, stream,l_mapLemmaCut);
    }
    else if (CSpecifications.CSpecification2.use_lemma_cut())
    {
      lemma_cut_beta(iFunctionname, 2, stream,l_mapLemmaCut);
    }
  }
  else if (CSpecifications.invert() == InvertBidirectEQ)
  {
    if (CSpecifications.CSpecification1.use_lemma_cut())
    {
      lemma_cut_beta(iFunctionname, 1, stream,l_mapLemmaCut);
    }
  }
  
  stream.close();

}

/**
 *
 * Zählen der Lemmaformen innerhalb einer Relation
 * +ablegen der Frequenzinformationen in l_mapLemmaCut
 *
 **/
void lemma_cut_beta(int iFunctionname, unsigned short int iCountMode, ifstream& stream, hash_map<unsigned int,unsigned int>& l_mapLemmaCut)
{  
  hash_map<unsigned int,unsigned int>::iterator l_itMapLemmaCut;

	///lokales Zaehlen  
  char str[1000];
  while (stream)
  {
    stream.getline(str, 1000);
    if(stream) 
    {
      ReadTabInput CReadTabInput;

      if (CReadTabInput.read_line(str,11))
      {        
        unsigned int iLemma1(0);
        unsigned int iLemma2(0);

        iLemma1 = atoi(CReadTabInput.get_field(3));
        iLemma2 = atoi(CReadTabInput.get_field(4));

        l_mapLemmaCut.insert(make_pair(iLemma1,1));
        l_mapLemmaCut.insert(make_pair(iLemma2,1));

        if (iCountMode==0 || iCountMode==1)
        {
          l_itMapLemmaCut=l_mapLemmaCut.find(iLemma1);
          if (l_itMapLemmaCut != l_mapLemmaCut.end())
          {
            l_itMapLemmaCut->second+=1;
          }
          else
          {
            l_mapLemmaCut.insert(make_pair(iLemma1,1));
          }
        }
        if (iCountMode==0 || iCountMode==2)
        {
          l_itMapLemmaCut=l_mapLemmaCut.find(iLemma2);
          if (l_itMapLemmaCut != l_mapLemmaCut.end())
          {
            l_itMapLemmaCut->second+=1;
          }
          else
          {
            l_mapLemmaCut.insert(make_pair(iLemma2,1));
          }
        }
      }
    }
  }
}

/**
 *
 * Statistikberechnung über alle Korpora oder über einen Subkorpus für die einzelnen Relationen
 *
 **/
void salience(const Specifications& CSpecifications, ofstream& outputStatistics, const string& strCorpus)
{
  ///Prüfen ob ein Subkorpus vorliegt
	bool bSubcorpus(false);
	if (!strCorpus.empty())
	{
    bSubcorpus=true;
	}
	
  ///Einlesen des Relationsnamenmappings
  hash_map<string,unsigned int> g_mapFunctionMapping;  
  ifstream inputFunctionMapping((g_strTablePath+"/mapping_function.table").c_str());
  char str[1000];
  while(inputFunctionMapping) 
  {
    inputFunctionMapping.getline(str, 1000);
    if(inputFunctionMapping) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,3))
      {
        unsigned int iFunction = atoi(CReadTabInput.get_field(1));
        const char* szFunction = CReadTabInput.get_field(2);
        const char* szType = CReadTabInput.get_field(3);
        g_mapFunctionMapping.insert(make_pair(szFunction,iFunction));
      }
    }
  }

  string strFile = g_strTablePath + "/" + CSpecifications.CSpecification1.functionname() + ".relations.freq.table";
  ifstream stream(strFile.c_str());

  unsigned int iFunctionname(0);
  ///bei normalen Relationen
  if (CSpecifications.invert() == InvertNo)
  {
    iFunctionname = g_mapFunctionMapping[CSpecifications.CSpecification1.functionname()]; 
    salience_beta(iFunctionname, false, stream, outputStatistics,bSubcorpus);
  }
  ///bei umgedrehten Relationen
  else if (CSpecifications.invert() == InvertYes)
  {
    cerr<<"): interner Fehler"<<endl;
		exit(-1);
  }
  ///bei zugleich normaler und umgedrehter Relationen
  else if (CSpecifications.invert() == InvertBidirect)
  {
    iFunctionname = g_mapFunctionMapping[CSpecifications.CSpecification1.functionname()];
    salience_beta(iFunctionname, false, stream, outputStatistics,bSubcorpus);
    stream.close();
    stream.open(strFile.c_str());
    iFunctionname = g_mapFunctionMapping[CSpecifications.CSpecification2.functionname()];
    salience_beta(iFunctionname, true, stream, outputStatistics,bSubcorpus);
  }
  ///bei symetrischen Relationen
  else if (CSpecifications.invert() == InvertBidirectEQ)
  {
    iFunctionname = g_mapFunctionMapping[CSpecifications.CSpecification1.functionname()];
    salience_beta(iFunctionname, false, stream, outputStatistics,bSubcorpus);
  }
  
  stream.close();
}

/**
 *
 * Statistikberechnung für eine konkrete Relation
 *
 **/
void salience_beta(int iFunctionname, bool bInvert, ifstream& stream, ofstream& outputStatistics,bool bSubcorpus, string strCorpus)
{
  ///hash-maps fuer relationsspezifisches Zaehlen
	///(w1,R,*)
  hash_map<HashPair,pair<unsigned int,unsigned int>,PSHashPair,PSEqualToPair> mapHeadWord;
  hash_map<HashPair,pair<unsigned int,unsigned int>,PSHashPair,PSEqualToPair>::iterator itMapHeadWord;
	///(*,R,w2)
  hash_map<HashQuad,pair<unsigned int,unsigned int>,PSHashQuad,PSEqualToQuad> mapDepWord;
  hash_map<HashQuad,pair<unsigned int,unsigned int>,PSHashQuad,PSEqualToQuad>::iterator itMapDepWord;
	///(w1,R,w2)
  hash_map<HashSix,CooccInfo,PSHashSix,PSEqualToSix> mapRelation;
  hash_map<HashSix,CooccInfo,PSHashSix,PSEqualToSix>::iterator itMapRelation;
  hash_map<HashSix,CooccInfo,PSHashSix,PSEqualToSix>::iterator itMapRelationRev;
  
	///lokales Zaehlen  
  char str[1000];
  while (stream)
  {
    stream.getline(str, 1000);
    if(stream) 
    {
      ReadTabInput CReadTabInput;

      if (CReadTabInput.read_line(str,11))
      {        
        unsigned int iFrequencyId(0);
        unsigned int iPrep(0);
        unsigned int iLemma1(0);
        unsigned int iLemma2(0);
        unsigned int iSurfacePrep(0);
        unsigned int iSurface1(0);
        unsigned int iSurface2(0);
        unsigned int iPrepPOS(0);
        unsigned int iPOS1(0);
        unsigned int iPOS2(0);
        unsigned int iInfo(0);

				if (!bInvert)
        {
          iFrequencyId = atoi(CReadTabInput.get_field(1));
          iPrep = atoi(CReadTabInput.get_field(2));
          iLemma1 = atoi(CReadTabInput.get_field(3));
          iLemma2 = atoi(CReadTabInput.get_field(4));
          iSurfacePrep = atoi(CReadTabInput.get_field(5));
          iSurface1 = atoi(CReadTabInput.get_field(6));
          iSurface2 = atoi(CReadTabInput.get_field(7));
          iPrepPOS = atoi(CReadTabInput.get_field(8));
          iPOS1 = atoi(CReadTabInput.get_field(9));
          iPOS2 = atoi(CReadTabInput.get_field(10));
          iInfo = atoi(CReadTabInput.get_field(11));

        }
        else if (bInvert)
        {
          iFrequencyId = atoi(CReadTabInput.get_field(1));
          iPrep = atoi(CReadTabInput.get_field(2));
          iLemma2 = atoi(CReadTabInput.get_field(3));
          iLemma1 = atoi(CReadTabInput.get_field(4));
          iSurfacePrep = atoi(CReadTabInput.get_field(5));
          iSurface2 = atoi(CReadTabInput.get_field(6));
          iSurface1 = atoi(CReadTabInput.get_field(7));
          iPrepPOS = atoi(CReadTabInput.get_field(8));
          iPOS2 = atoi(CReadTabInput.get_field(9));
          iPOS1 = atoi(CReadTabInput.get_field(10));
          iInfo = atoi(CReadTabInput.get_field(11));
        }

				unsigned int iFrequency = g_mapFrequency[iFrequencyId];
				///bei keinem Vorkommen der Relation (oder wenn bestimmte Bidingungen nicht erfuellt waren)
        if (iFrequency == 0)
        {
          continue;
        }

				///lokales Zaehlen der Koepfe (w1,R,*)
        itMapHeadWord = mapHeadWord.find(HashPair(iLemma1,iPOS1));
        if (itMapHeadWord!= mapHeadWord.end())
        {
          itMapHeadWord->second.first += iFrequency;
          itMapHeadWord->second.second += 1;
        }
        else
        {
          mapHeadWord.insert(make_pair(HashPair(iLemma1,iPOS1),make_pair(iFrequency,1)));
        }

				///lokales Zaehlen der Dependenten (*,R,w2)
        if (g_eTernaryRelationMode == AttachToWord)
        {
          itMapDepWord = mapDepWord.find(HashQuad(iPrep,iPrepPOS,iLemma2,iPOS2));
        }
        else if (g_eTernaryRelationMode == AttachToRelation)
        {
          itMapDepWord = mapDepWord.find(HashQuad(0,0,iLemma2,iPOS2));
        }
        if (itMapDepWord!= mapDepWord.end())
        {
          itMapDepWord->second.first += iFrequency;
          itMapDepWord->second.second += 1;
        }
        else
        {
          if (g_eTernaryRelationMode == AttachToWord)
          {
            mapDepWord.insert(make_pair(HashQuad(iPrep,iPrepPOS,iLemma2,iPOS2),make_pair(iFrequency,1)));
          }
          else if (g_eTernaryRelationMode == AttachToRelation)
          {
            mapDepWord.insert(make_pair(HashQuad(0,0,iLemma2,iPOS2),make_pair(iFrequency,1)));
          }
        }

				///lokales Zaehlen der Relationen (w1,R,w2)
        itMapRelation = mapRelation.find(HashSix(iPrep,iLemma1,iLemma2,iPrepPOS,iPOS1,iPOS2));
        if (itMapRelation == mapRelation.end())
        {
          CooccInfo CCooccInfo;
          CCooccInfo.iFrequency = iFrequencyId;
          CCooccInfo.iSurfacePrep = iSurfacePrep;
          CCooccInfo.iSurface1 = iSurface1;
          CCooccInfo.iSurface2 = iSurface2;
          CCooccInfo.iInfo = iInfo;
          mapRelation.insert(make_pair(HashSix(iPrep,iLemma1,iLemma2,iPrepPOS,iPOS1,iPOS2),CCooccInfo));
        }
				else
				{
					cerr<<"): interner Fehler"<<endl;
					exit(-1);
				}
      }
    }
  }  
  
  for (itMapRelation = mapRelation.begin(); itMapRelation != mapRelation.end(); ++itMapRelation)
  {      
    unsigned int _iPrep = itMapRelation->first.first;
    unsigned int _iLemma1 = itMapRelation->first.second;
    unsigned int _iLemma2 = itMapRelation->first.third;
    unsigned int _iPrepPOS = itMapRelation->first.fourth;
    unsigned int _iPOS1 = itMapRelation->first.fifth;
    unsigned int _iPOS2 = itMapRelation->first.sixth;   

    bool bLemmaCut=false;
    if (g_iLemmaCut < numeric_limits<int>::max())
    {
      if (g_mapLemmaCut.find(_iLemma1) == g_mapLemmaCut.end())
      {
        bLemmaCut=true;
      }
      else if (g_mapLemmaCut.find(_iLemma2) == g_mapLemmaCut.end())
      {
        bLemmaCut=true;
      }
    }

     
		///Erfragen der Frequenzen
		StatInfo CStatInfo;
    CStatInfo.iFreqRelation = g_mapFrequency[itMapRelation->second.iFrequency];
    CStatInfo.iCountRelation = mapRelation.size();    
    CStatInfo.iFreqHeadWord = mapHeadWord[HashPair(_iLemma1,_iPOS1)].first;

		///die praeposition wird zum dependenten gezogen
    if (g_eTernaryRelationMode == AttachToWord)
    {
      CStatInfo.iFreqDepWord = mapDepWord[HashQuad(_iPrep,_iPrepPOS,_iLemma2,_iPOS2)].first;      
    } 
		///die praeposition wird relationsunterscheident genutzt
    else if (g_eTernaryRelationMode == AttachToRelation)
    {
      CStatInfo.iFreqDepWord = mapDepWord[HashQuad(0,0,_iLemma2,_iPOS2)].first;      
    }

    ///evtl. Statistikwerte anpassen
    StatRes CStatRes = adjust_statistics(calculate_statistics(CStatInfo), iFunctionname);

    if (bSubcorpus)
    {      
		  map<unsigned int,Specification>::iterator itMapSpecification;
		  itMapSpecification = g_mapSpecification.find(iFunctionname);
		  if (itMapSpecification!=g_mapSpecification.end())
		  {
        ///Prüfen der Schwellwerte
		    if (          
					(
          !bLemmaCut 
          &&
          itMapSpecification->second.mapSpec[strCorpus].min_MiLogFreq_corpus() <= (float)CStatRes.iMiLogFreq &&
		      itMapSpecification->second.mapSpec[strCorpus].min_MI3_corpus() <= (float)CStatRes.iMI3 &&
		      itMapSpecification->second.mapSpec[strCorpus].min_TScore_corpus() <= (float)CStatRes.TScore &&
		      itMapSpecification->second.mapSpec[strCorpus].min_logDice_corpus() <= (float)CStatRes.iLogDice &&
		      itMapSpecification->second.mapSpec[strCorpus].min_logLike_corpus() <= (float)CStatRes.iLogLike &&
		      itMapSpecification->second.mapSpec[strCorpus].min_frequency_corpus() <= CStatInfo.iFreqRelation 
					&&
					itMapSpecification->second.mapSpec[strCorpus].max_MiLogFreq_corpus() >= (float)CStatRes.iMiLogFreq &&
		      itMapSpecification->second.mapSpec[strCorpus].max_MI3_corpus() >= (float)CStatRes.iMI3 &&
		      itMapSpecification->second.mapSpec[strCorpus].max_TScore_corpus() >= (float)CStatRes.TScore &&
		      itMapSpecification->second.mapSpec[strCorpus].max_logDice_corpus() >= (float)CStatRes.iLogDice &&
		      itMapSpecification->second.mapSpec[strCorpus].max_logLike_corpus() >= (float)CStatRes.iLogLike &&
		      itMapSpecification->second.mapSpec[strCorpus].max_frequency_corpus() >= CStatInfo.iFreqRelation)	
					&&				
					(itMapSpecification->second.mapSpec[strCorpus].min_MiLogFreq_corpus_con() <= (float)CStatRes.iMiLogFreq ||
		      itMapSpecification->second.mapSpec[strCorpus].min_MI3_corpus_con() <= (float)CStatRes.iMI3 ||
		      itMapSpecification->second.mapSpec[strCorpus].min_TScore_corpus_con() <= (float)CStatRes.TScore ||
		      itMapSpecification->second.mapSpec[strCorpus].min_logDice_corpus_con() <= (float)CStatRes.iLogDice ||
		      itMapSpecification->second.mapSpec[strCorpus].min_logLike_corpus_con() <= (float)CStatRes.iLogLike)
					&&
					(itMapSpecification->second.mapSpec[strCorpus].max_MiLogFreq_corpus_con() >= (float)CStatRes.iMiLogFreq ||
		      itMapSpecification->second.mapSpec[strCorpus].max_MI3_corpus_con() >= (float)CStatRes.iMI3 ||
		      itMapSpecification->second.mapSpec[strCorpus].max_TScore_corpus_con() >= (float)CStatRes.TScore ||
		      itMapSpecification->second.mapSpec[strCorpus].max_logDice_corpus_con() >= (float)CStatRes.iLogDice ||
		      itMapSpecification->second.mapSpec[strCorpus].max_logLike_corpus_con() >= (float)CStatRes.iLogLike))
		    {
          ///Schreiben der Kookkurrenz mit Statistikwert
		      outputStatistics<<(unsigned int)iFunctionname<<'\t';
		      outputStatistics<<_iPrep<<'\t';
		      outputStatistics<<_iLemma1<<'\t';
		      outputStatistics<<_iLemma2<<'\t';
		      outputStatistics<<itMapRelation->second.iSurfacePrep<<'\t';
		      outputStatistics<<itMapRelation->second.iSurface1<<'\t';
		      outputStatistics<<itMapRelation->second.iSurface2<<'\t';
		      outputStatistics<<(unsigned int)_iPrepPOS<<'\t';
		      outputStatistics<<(unsigned int)_iPOS1<<'\t';
		      outputStatistics<<(unsigned int)_iPOS2<<'\t';
		      outputStatistics<<itMapRelation->second.iInfo<<'\t';
		      outputStatistics<<(unsigned int)g_mapFrequencyBelege[itMapRelation->second.iFrequency]<<'\t';
		      outputStatistics<<(unsigned int)CStatInfo.iFreqRelation<<'\t';
          ///Schreiben der Statistikwerte
		      outputStatistics<<(float)CStatRes.iMI3<<'\t';
		      outputStatistics<<(float)CStatRes.iMiLogFreq<<'\t';
		      outputStatistics<<(float)CStatRes.TScore<<'\t';
		      outputStatistics<<(float)CStatRes.iLogDice<<'\t';
		      outputStatistics<<(float)CStatRes.iLogLike<<'\n';
		    }
			}
    }
    else
    {
		  map<unsigned int,Specification>::iterator itMapSpecification;
		  itMapSpecification = g_mapSpecification.find(iFunctionname);
		  if (itMapSpecification!=g_mapSpecification.end())
		  {
        ///Prüfen der Schwellwerte
		    if (
					(
          !bLemmaCut 
          &&
          itMapSpecification->second.min_MiLogFreq() <= (float)CStatRes.iMiLogFreq &&
		      itMapSpecification->second.min_MI3() <= (float)CStatRes.iMI3 &&
		      itMapSpecification->second.min_TScore() <= (float)CStatRes.TScore &&
		      itMapSpecification->second.min_logDice() <= (float)CStatRes.iLogDice &&
		      itMapSpecification->second.min_logLike() <= (float)CStatRes.iLogLike &&
		      itMapSpecification->second.min_frequency() <= CStatInfo.iFreqRelation
					&&
		      itMapSpecification->second.max_MiLogFreq() >= (float)CStatRes.iMiLogFreq &&
		      itMapSpecification->second.max_MI3() >= (float)CStatRes.iMI3 &&
		      itMapSpecification->second.max_TScore() >= (float)CStatRes.TScore &&
		      itMapSpecification->second.max_logDice() >= (float)CStatRes.iLogDice &&
		      itMapSpecification->second.max_logLike() >= (float)CStatRes.iLogLike &&
		      itMapSpecification->second.max_frequency() >= CStatInfo.iFreqRelation)
					&&
					(itMapSpecification->second.min_MiLogFreq_con() <= (float)CStatRes.iMiLogFreq ||
		      itMapSpecification->second.min_MI3_con() <= (float)CStatRes.iMI3 ||
		      itMapSpecification->second.min_TScore_con() <= (float)CStatRes.TScore ||
		      itMapSpecification->second.min_logDice_con() <= (float)CStatRes.iLogDice ||
		      itMapSpecification->second.min_logLike_con() <= (float)CStatRes.iLogLike)
					&&
		      (itMapSpecification->second.max_MiLogFreq() >= (float)CStatRes.iMiLogFreq ||
		      itMapSpecification->second.max_MI3_con() >= (float)CStatRes.iMI3 ||
		      itMapSpecification->second.max_TScore_con() >= (float)CStatRes.TScore ||
		      itMapSpecification->second.max_logDice_con() >= (float)CStatRes.iLogDice ||
		      itMapSpecification->second.max_logLike_con() >= (float)CStatRes.iLogLike))
		    {
          ///Schreiben der Kookkurrenzinformation
		      outputStatistics<<(unsigned int)iFunctionname<<'\t';
		      outputStatistics<<_iPrep<<'\t';
		      outputStatistics<<_iLemma1<<'\t';
		      outputStatistics<<_iLemma2<<'\t';
		      outputStatistics<<itMapRelation->second.iSurfacePrep<<'\t';
		      outputStatistics<<itMapRelation->second.iSurface1<<'\t';
		      outputStatistics<<itMapRelation->second.iSurface2<<'\t';
		      outputStatistics<<(unsigned int)_iPrepPOS<<'\t';
		      outputStatistics<<(unsigned int)_iPOS1<<'\t';
		      outputStatistics<<(unsigned int)_iPOS2<<'\t';
		      outputStatistics<<itMapRelation->second.iInfo<<'\t';
		      outputStatistics<<(unsigned int)g_mapFrequencyBelege[itMapRelation->second.iFrequency]<<'\t';
		      outputStatistics<<(unsigned int)CStatInfo.iFreqRelation<<'\t';
          ///Schreiben der Statistikwerte
		      outputStatistics<<(float)CStatRes.iMI3<<'\t';
		      outputStatistics<<(float)CStatRes.iMiLogFreq<<'\t';
		      outputStatistics<<(float)CStatRes.TScore<<'\t';
		      outputStatistics<<(float)CStatRes.iLogDice<<'\t';
		      outputStatistics<<(float)CStatRes.iLogLike<<'\n';
        }
	  		else
		  	{
			  	g_setFrequencyIdCut.insert(itMapRelation->second.iFrequency);
			  }
      }
    }
  }
};

/**
 *
 * Anwenden des 'lemma-cut'-Schwellwertes
 *
 **/
void calc_lemma_cut()
{
  ///wenn ein Schwellwert gesetzt ist
  if (g_iLemmaCut < numeric_limits<int>::max())
  {
    cout<<"|: use Lemma cut:"<<g_iLemmaCut<<endl;

    vector<Specifications>::const_iterator itVSpecifications;
    hash_map<unsigned int,unsigned int> l_mapLemmaCut;
    hash_map<unsigned int,unsigned int>::iterator l_itMapLemmaCut;
    for (itVSpecifications = g_vSpecifications.begin(); 
      itVSpecifications != g_vSpecifications.end();
      ++itVSpecifications)
    {
      cout<<"(: calculate lemma cut |w1,*,*|: "<<itVSpecifications->CSpecification1.functionname()<<endl;
      lemma_cut(*itVSpecifications,l_mapLemmaCut);
    }

    ///Anwenden des Schwellwertes auf die Lemmamenge
    for (l_itMapLemmaCut=l_mapLemmaCut.begin(); l_itMapLemmaCut!=l_mapLemmaCut.end(); ++l_itMapLemmaCut)
    {  
      if (l_itMapLemmaCut->second >= g_iLemmaCut)
      {
        g_mapLemmaCut.insert(*l_itMapLemmaCut);
      }
    }
  }
}

int main(int argc, char* argv[])
{
  if (argc != 2)
  {
    cerr<<"): falscher Parameteraufruf -> die XML-Specification angeben"<<endl; 
    exit(-1);
  }

  char str[10000];
  g_iAllTriple=0;

	init_spec(argv[1]);

  cout<<"|: CALCULATION of STATISTICS"<<endl;

  read_mappings();

	///Berechnung transrelationaler Abhaengigkeiten
  vector<Connection>::iterator itVCConnection;
  for (itVCConnection = g_vCConnection.begin(); itVCConnection != g_vCConnection.end(); ++itVCConnection)
  {
      calculate_transrelational_connections(*itVCConnection);
  }
	g_mapFrequencyTrigger.clear();

  ///Spezifikationsinformationen Anlegen
  vector<Specifications>::const_iterator itVSpecifications;
  for (itVSpecifications = g_vSpecifications.begin(); 
    itVSpecifications != g_vSpecifications.end();
    ++itVSpecifications)
  {            
    if (itVSpecifications->invert()==InvertNo && !itVSpecifications->CSpecification1.ignore())
    {
      g_mapSpecification.insert(make_pair(g_mapFunction[itVSpecifications->CSpecification1.functionname()],itVSpecifications->CSpecification1));
    }
    else if (itVSpecifications->invert()==InvertBidirectEQ && !itVSpecifications->CSpecification1.ignore())
    {
      g_mapSpecification.insert(make_pair(g_mapFunction[itVSpecifications->CSpecification1.functionname()],itVSpecifications->CSpecification1));
    }
    else if (itVSpecifications->invert()==InvertYes)
    {
			cerr<<"): interner Fehler"<<endl; 
			exit(-1);
    }
    else if (itVSpecifications->invert()==InvertBidirect && !itVSpecifications->CSpecification1.ignore() && !itVSpecifications->CSpecification2.ignore())
    {
      g_mapSpecification.insert(make_pair(g_mapFunction[itVSpecifications->CSpecification1.functionname()],itVSpecifications->CSpecification1));
      g_mapSpecification.insert(make_pair(g_mapFunction[itVSpecifications->CSpecification2.functionname()],itVSpecifications->CSpecification2));
    }
    else
    {
      cout<<"|: ignore: "<<itVSpecifications->CSpecification1.functionname()<<endl;
    }
  }

  ///Lemma-Cut-Schwellwertberechnung
  calc_lemma_cut();  

  ///Statistikberechnung auf allen Korpora
  ofstream outputStatistics((g_strTablePath+"/relations.table").c_str());
  for (itVSpecifications = g_vSpecifications.begin(); 
    itVSpecifications != g_vSpecifications.end();
    ++itVSpecifications)
  {
    ///relationsbezogene Stastistikberechnung
    cout<<"(: calculate |w1,R,*| and |*,R,w2|: "<<itVSpecifications->CSpecification1.functionname()<<endl;
    salience(*itVSpecifications,outputStatistics,"");
  }  
  outputStatistics.close();
  
  ///Statistikberechnung auf individuellen Korpora
  if (g_bUseSubcorpora)
  {
	  ///Statistik fuer die einzelnen corpora unabhaengig berechnen
    //if (g_setUsedCorpora.size()>1)
    {
      cout<<"(: process "<<g_setUsedCorpora.size()<<" subcorpora independently"<<endl;

      set<unsigned int>::iterator zt;
      for (zt = g_setUsedCorpora.begin(); zt != g_setUsedCorpora.end(); ++zt)
      {
			  ///Initialisieren
		    g_iAllTriple=0;
		    g_mapFrequency.clear();  

		    cout<<"(: process "<<g_mapIdToCorpus[*zt]<<endl;
			  read_subcorpus_frequency_mapping(*zt);

		    ofstream outputStatistics((g_strTablePath+"/relations."+g_mapIdToCorpus[*zt]+".table").c_str());
		    for (itVSpecifications = g_vSpecifications.begin(); 
		      itVSpecifications != g_vSpecifications.end();
		      ++itVSpecifications)
		    {
          ///relationsbezogene Stastistikberechnung
		      cout<<"(: calculate |w1,R,*| and |*,R,w2|: "<<itVSpecifications->CSpecification1.functionname()<<endl;
		      salience(*itVSpecifications,outputStatistics,g_mapIdToCorpus[*zt]);
		    }		
		    outputStatistics.close();		  
      }
    }
  }

  cout<<"|: done"<<endl;
}

