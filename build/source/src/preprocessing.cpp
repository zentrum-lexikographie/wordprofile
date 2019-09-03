/**
 * Programm, um gleiche Kookkurrenzen der Relationsdateien des Parsers zu zählen.
 * 
 * folgende Tabellen werden generiert: 
 *
 * + {Relationsname}.relations.freq.table -> 
 *   Kookkurrrenzinformationen zu den einzelnen syntaktischen Relationen:
 *     -Frequenz
 *     -Präposition (ID)
 *     -Lemma des ersten Wortes (ID)
 *     -Lemma des zweiten Wortes (ID)
 *     -Oberflächenform der Präposition (ID)
 *     -Oberflächenform des ersten Wortes (ID)
 *     -Oberflächenform des zweiten Wortes (ID)
 *     -Wortkategorie der Präposition (ID)
 *     -Wortkategorie des ersten Wortes (ID)
 *     -Wortkategorie des zweiten Wortes (ID)
 *     -Id für die Korpustrefferinformationen
 *
 **/

#include <iostream>
#include <vector>
#include <string.h>
#include <fstream>
#include <fstream>
#include <math.h>
#include <map>
#include <algorithm>
#include "hashes.h"
#include "read_specification.h"
#include "read_tab_input.h"

/**
 * Fundstelleninformationen zu einer Kookkurrrenz
 *
 * + Oberflächenformen
 * + Fundstellen
 * + Frequenzen (normal, mit Berücksichtigung der Filter, mit Berücksichtigung der Rechte)
 *
 **/
struct Info
{
  Info():
    iFrequency(0),
		iInfoId(0)
  {    
  }
  
  unsigned int iFrequency;
  vector<pair< unsigned short int,float> > mapFrequency;
  vector<unsigned int> vInfo;
  vector<pair<unsigned int, unsigned short int> > vSurface1;
  vector<pair<pair<unsigned int,unsigned int>,unsigned short int> > vSurface2;
	unsigned int iInfoId;
};


//map<string,pair<unsigned int, unsigned int> > mapFreqStatistic;
//map<string,pair<unsigned int, unsigned int> >::iterator itMapFreqStatistic;

string g_strRelationPath = "";
string g_strTablePath = "";
string g_strTmpPath = "";

///Zaehler fuer das Ermitteln von Groessen fuer die Datenbank
unsigned int g_iSizeLemma(0);
unsigned int g_iSizeSurface(0);
unsigned int g_iSizeInfo(0);
unsigned int g_iSizePrep(0);
unsigned int g_iSizeRelation(0);
unsigned int g_iSizePOS(0);
unsigned int g_iLengthLemma(0);
unsigned int g_iLengthSurface(0);
unsigned int g_iLengthPrep(0);
unsigned int g_iLengthPOS(0);

///Zaehler fuer neue id-Belegung (wenn die Tupel zusammengelegt werden (positionsinformation/frequenz) )
unsigned int g_iFrequencyMappingCounter(0);
unsigned int g_iInfoMappingCounter(1);

///modus fuer die berechnung der Oberflaechenform einer Relation
SurfaceMode g_eSurfaceMode = MostFrequentTightLocal;

///hash-maps fuer das Berechnen der Oberflaechenform einer Relation
hash_map<HashPair,vector<unsigned int>,PSHashPair,PSEqualToPair> g_mapSurfaceCountHead;
hash_map<HashPair,vector<unsigned int>,PSHashPair,PSEqualToPair>::iterator g_itMapSurfaceCountHead;
hash_map<HashPair,vector<unsigned int>,PSHashPair,PSEqualToPair> g_mapSurfaceCountDependent;
hash_map<HashPair,vector<unsigned int>,PSHashPair,PSEqualToPair>::iterator g_itMapSurfaceCountDependent;
hash_map<HashPair,unsigned int,PSHashPair,PSEqualToPair> g_mapSurfaceHead;
hash_map<HashPair,unsigned int,PSHashPair,PSEqualToPair>::iterator g_itMapSurfaceHead;
hash_map<HashPair,unsigned int,PSHashPair,PSEqualToPair> g_mapSurfaceDependent;
hash_map<HashPair,unsigned int,PSHashPair,PSEqualToPair>::iterator g_itMapSurfaceDependent;

hash_map<HashPair,set<unsigned int>,PSHashPair,PSEqualToPair> g_MapSurfaceLemma;
hash_map<HashPair,set<unsigned int>,PSHashPair,PSEqualToPair>::iterator g_itMapSurfaceLemma;

hash_map<int,int> mapInfoId;
///hash fuer die Relationen
hash_map<HashSix,Info,PSHashSix,PSEqualToSix> g_mapRelations;
hash_map<HashSix,Info,PSHashSix,PSEqualToSix>::iterator g_itMapRelations;
hash_map<HashSix,Info,PSHashSix,PSEqualToSix>::iterator g_itMapRelations2;
hash_map<HashSix,Info,PSHashSix,PSEqualToSix>::iterator g_itMapRelations3;

///objekt zum einlesen der Specification
ReadSpecification g_CReadSpecification;
vector<Specifications> g_vSpecifications;

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
 * Einlesen der Spezifikation
 *
 **/
void init_spec(const char* pcFile)
{
  g_CReadSpecification.parse_xml(pcFile);
  g_strRelationPath = g_CReadSpecification.relation_path();
  g_strTablePath = g_CReadSpecification.table_path();
  //g_eSurfaceMode = g_CReadSpecification.surface_mode();
  g_vSpecifications = g_CReadSpecification.get_specifications();
  g_strTmpPath = g_CReadSpecification.tmp_path();
}

/**
 *
 * Einsammeln der möglichen Oberflächenformen zu einer Lemmaform
 *
 **/
void calc_lemma_surfaces_mapping(const Specifications& CSpecifications)
{
  string strFile = g_strTablePath + "/" + CSpecifications.CSpecification1.functionname() + ".relations.table";
  ifstream stream(strFile.c_str());

  char str[1000];
  while (stream)
  {
    stream.getline(str, 1000);  // delim defaults to '\n'
    if(stream) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,14))
      {
        unsigned int iPrep = atoi(CReadTabInput.get_field(1));
        unsigned int iLemma1 = atoi(CReadTabInput.get_field(2));
        unsigned int iLemma2 = atoi(CReadTabInput.get_field(3));
        unsigned int iSurfacePrep = atoi(CReadTabInput.get_field(4));
        unsigned int iSurface1 = atoi(CReadTabInput.get_field(5));
        unsigned int iSurface2 = atoi(CReadTabInput.get_field(6));
        unsigned int iPrepPOS = atoi(CReadTabInput.get_field(7));
        unsigned int iPOS1 = atoi(CReadTabInput.get_field(8));
        unsigned int iPOS2 = atoi(CReadTabInput.get_field(9));
        unsigned int iCorpus = atoi(CReadTabInput.get_field(10));
        unsigned int iInfo = atoi(CReadTabInput.get_field(11));        

        string strTrigger = CReadTabInput.get_field(12);        

        unsigned short int iGrundform1 = atoi(CReadTabInput.get_field(13));
        unsigned short int iGrundform2 = atoi(CReadTabInput.get_field(14));

        g_itMapSurfaceLemma = g_MapSurfaceLemma.find(HashPair(iLemma1,iPOS1));
        if (g_itMapSurfaceLemma != g_MapSurfaceLemma.end())
        {
          g_itMapSurfaceLemma->second.insert(iSurface1);
        }
        else
        {
          set<unsigned int> setDummy;
          setDummy.insert(iSurface1);
          g_MapSurfaceLemma.insert(make_pair(HashPair(iLemma1,iPOS1),setDummy));
        }

        g_itMapSurfaceLemma = g_MapSurfaceLemma.find(HashPair(iLemma2,iPOS2));
        if (g_itMapSurfaceLemma != g_MapSurfaceLemma.end())
        {
          g_itMapSurfaceLemma->second.insert(iSurface2);
        }
        else
        {
          set<unsigned int> setDummy;
          setDummy.insert(iSurface2);
          g_MapSurfaceLemma.insert(make_pair(HashPair(iLemma2,iPOS2),setDummy));
        }
      }
    }
  }
}

/**
 *
 * Schreiben der Kookkurrrenzen der einzelnen Relationen
 *
 **/
void write_relations(const Specifications& CSpecifications, ofstream& outputRelations, ofstream& outputInfoMapping, ofstream& outputFrequencyMapping)
{
  vector<pair<unsigned int,unsigned short int> >::iterator it;  
  vector<unsigned int>::iterator itInfo;  
  vector<pair<pair<unsigned int,unsigned int>,unsigned short int> >::iterator it2;  

  bool bUseBaseformAsSurface1(CSpecifications.bUseBaseformAsSurface1);
  bool bUseBaseformAsSurface2(CSpecifications.bUseBaseformAsSurface2);

  for (g_itMapRelations = g_mapRelations.begin(); g_itMapRelations != g_mapRelations.end(); ++g_itMapRelations)
  {
    if (g_itMapRelations->second.mapFrequency[1].second >= CSpecifications.min_frequency() && 
      g_itMapRelations->second.mapFrequency[1].second <= CSpecifications.max_frequency())
    {      
      ++g_iSizeRelation;
      
      bool bBaseform1(false);
      bool bBaseform2(false);
      int iMostFrequentSurface1(-1);
      int iMostFrequentSurface2(-1);
      int iMostFrequentPrep(-1);
			///wenn die haeufigste Oberflaechenform streng lokal berechnet werden soll
      if (g_eSurfaceMode == MostFrequentTightLocal)
      {
        map<unsigned int, pair<unsigned int,bool> > mapCountSurface;
        map<pair<unsigned int,unsigned int>, pair<unsigned int,bool> > mapCountSurface2;
        map<unsigned int, pair<unsigned int,bool> >::iterator itMapCountSurface;
        map<pair<unsigned int,unsigned int>, pair<unsigned int,bool> >::iterator itMapCountSurface2;

				///zaehlen der haeufigsten Oberflaechenform bezueglich der Koefpfe
        unsigned int iHighestCountSurface1(0);
        for (it = g_itMapRelations->second.vSurface1.begin(); it != g_itMapRelations->second.vSurface1.end(); ++it)
        {
          itMapCountSurface = mapCountSurface.find(it->first);
          if (itMapCountSurface != mapCountSurface.end())
          {
            ++(itMapCountSurface->second.first);
          }
          else
          {
            mapCountSurface.insert(make_pair(it->first,make_pair(1,it->second)));
          }
        }

        if (bUseBaseformAsSurface1)
        {
          bBaseform1=false;
          iHighestCountSurface1=0;
				  for (itMapCountSurface = mapCountSurface.begin(); itMapCountSurface != mapCountSurface.end(); ++itMapCountSurface)
				  {
            if (itMapCountSurface->second.second == 2)
            {
              continue;
            }    
            if (bBaseform1 and itMapCountSurface->second.second != 1)
            {
              continue;
            }    
            if (not bBaseform1 and itMapCountSurface->second.second == 1)
            {
              bBaseform1=true;
              iHighestCountSurface1=0;
            }
            if (itMapCountSurface->second.first > iHighestCountSurface1)
            {
              iHighestCountSurface1 = itMapCountSurface->second.first;
              iMostFrequentSurface1 = itMapCountSurface->first;
            }
				  }
        }
        else
        {
          iHighestCountSurface1=0;
				  for (itMapCountSurface = mapCountSurface.begin(); itMapCountSurface != mapCountSurface.end(); ++itMapCountSurface)
				  {
            if (itMapCountSurface->second.second == 2)
            {
              continue;
            }    
            if (itMapCountSurface->second.first > iHighestCountSurface1)
            {
              iHighestCountSurface1 = itMapCountSurface->second.first;
              iMostFrequentSurface1 = itMapCountSurface->first;
            }
				  }
        }
        if (iMostFrequentSurface1==-1)
        {
          iHighestCountSurface1=0;
				  for (itMapCountSurface = mapCountSurface.begin(); itMapCountSurface != mapCountSurface.end(); ++itMapCountSurface)
				  {
            if (itMapCountSurface->second.second == 2)
            {
              if (itMapCountSurface->second.first > iHighestCountSurface1)
              {
                iHighestCountSurface1 = itMapCountSurface->second.first;
                iMostFrequentSurface1 = itMapCountSurface->first;
              }
            }
				  }
        }

        g_itMapRelations->second.vSurface1.clear();
        mapCountSurface.clear();
    
				///zaehlen der haeufigsten Oberflaechenform bezueglich der Dependenten
        unsigned int iHighestCountSurface2(0);
        for (it2 = g_itMapRelations->second.vSurface2.begin(); it2 != g_itMapRelations->second.vSurface2.end(); ++it2)
        {
          itMapCountSurface2 = mapCountSurface2.find(it2->first);
          if (itMapCountSurface2 != mapCountSurface2.end())
          {
            ++(itMapCountSurface2->second.first);
          }
          else
          {
            mapCountSurface2.insert(make_pair(it2->first,make_pair(1,it2->second)));
          }
        }
        if (bUseBaseformAsSurface2)
        {
          bBaseform2=false;
          iHighestCountSurface2=0;
				  for (itMapCountSurface2 = mapCountSurface2.begin(); itMapCountSurface2 != mapCountSurface2.end(); ++itMapCountSurface2)
				  {
            if (itMapCountSurface->second.second == 2)
            {
              continue;
            }    
            if (bBaseform2 and not itMapCountSurface2->second.second != 1)
            {
              continue;
            }    
            if (not bBaseform2 and itMapCountSurface2->second.second ==1)
            {
              bBaseform2=true;
              iHighestCountSurface2=0;
            }
            if (itMapCountSurface2->second.first > iHighestCountSurface2)
            {
              iHighestCountSurface2 = itMapCountSurface2->second.first;
              iMostFrequentSurface2 = itMapCountSurface2->first.first;
              iMostFrequentPrep = itMapCountSurface2->first.second;
            }
				  }
        }
        else
        {
          iHighestCountSurface2=0;
				  for (itMapCountSurface2 = mapCountSurface2.begin(); itMapCountSurface2 != mapCountSurface2.end(); ++itMapCountSurface2)
				  {
            if (itMapCountSurface->second.second == 2)
            {
              continue;
            }    
            if (itMapCountSurface2->second.first > iHighestCountSurface2)
            {
              iHighestCountSurface2 = itMapCountSurface2->second.first;
              iMostFrequentSurface2 = itMapCountSurface2->first.first;
              iMostFrequentPrep = itMapCountSurface2->first.second;
            }
				  }
        }
        if (iMostFrequentSurface2==-1)
        {
          iHighestCountSurface2=0;
				  for (itMapCountSurface2 = mapCountSurface2.begin(); itMapCountSurface2 != mapCountSurface2.end(); ++itMapCountSurface2)
				  {
            if (itMapCountSurface->second.second == 2)
            {
              if (itMapCountSurface2->second.first > iHighestCountSurface2)
              {
                iHighestCountSurface2 = itMapCountSurface2->second.first;
                iMostFrequentSurface2 = itMapCountSurface2->first.first;
                iMostFrequentPrep = itMapCountSurface2->first.second;
              }
            }    
          }
        }
        g_itMapRelations->second.vSurface2.clear();
      }

			///schreiben des Mapping der Relation-zu-Positionsinformationen-Information
      unsigned int iInfo(g_itMapRelations->second.iInfoId);      

      if (!g_itMapRelations->second.vInfo.empty())
      {
        for (itInfo = g_itMapRelations->second.vInfo.begin(); itInfo != g_itMapRelations->second.vInfo.end(); ++itInfo)
        {
	        outputInfoMapping<<iInfo<<'\t';
          outputInfoMapping<<*itInfo<<'\n';
        }
      }
      else
      {
        iInfo=0;
      }

			///schreiben der Frequenzinformation zu den verschiedenen Korpora
      vector<pair<unsigned short int, float> >::iterator rt;
      unsigned int iFrequency(g_iFrequencyMappingCounter);      
      if (!g_itMapRelations->second.mapFrequency.empty())
      {
        for (rt = g_itMapRelations->second.mapFrequency.begin(); rt != g_itMapRelations->second.mapFrequency.end(); ++rt)
        {
	        outputFrequencyMapping<<iFrequency<<'\t';
          outputFrequencyMapping<<rt->first<<'\t'; ///Corpus-ID + 1000
          outputFrequencyMapping<<rt->second<<'\n'; ///Frequenz
        }
        ++g_iFrequencyMappingCounter;          
      }
      else
      {
        iFrequency=0;
      }

      unsigned int iPrep(g_itMapRelations->first.first);
      unsigned int iLemma1(g_itMapRelations->first.second);
      unsigned int iLemma2(g_itMapRelations->first.third);
      unsigned int iPrepPOS(g_itMapRelations->first.fourth);      
      unsigned int iPOS1(g_itMapRelations->first.fifth);
      unsigned int iPOS2(g_itMapRelations->first.sixth);
      unsigned int iSurface1(0);
      unsigned int iSurface2(0);
      unsigned int iSurfacePrep(0);

			///wenn die haeufigste Oberflaechenform streng lokal berechnet werden soll
      if (g_eSurfaceMode == MostFrequentTightLocal)
      {
        iSurface1 = iMostFrequentSurface1;
        iSurface2 = iMostFrequentSurface2;
        iSurfacePrep = iMostFrequentPrep;
      }

      /*itMapFreqStatistic = mapFreqStatistic.find(CSpecifications.CSpecification1.functionname());
      if (itMapFreqStatistic == mapFreqStatistic.end())
      {
        mapFreqStatistic.insert(make_pair(CSpecifications.CSpecification1.functionname(),make_pair(0,1)));
      }
      else
      {
        itMapFreqStatistic->second.second+=g_itMapRelations->second.mapFrequency[0].second;
      }*/

			///schreiben der Kookkurrenz
      outputRelations<<iFrequency<<'\t';
      outputRelations<<iPrep<<'\t';
      outputRelations<<iLemma1<<'\t';
      outputRelations<<iLemma2<<'\t';
      outputRelations<<iSurfacePrep<<'\t';
      outputRelations<<iSurface1<<'\t';
      outputRelations<<iSurface2<<'\t';
      outputRelations<<iPrepPOS<<'\t';
      outputRelations<<iPOS1<<'\t';
      outputRelations<<iPOS2<<'\t';
      outputRelations<<iInfo<<'\n';

    }
  }  
}

/**
 *
 * Zusammenlegen der Kookkurrenzen einer syntaktischen Relation
 *
 **/
void merge_relations(const Specifications& CSpecifications, ofstream& outputRelations, ofstream& outputInfoMapping, ofstream& outputFrequencyMapping,int  iSchwellwertVon,int iSchwellwertBis)
{
  mapInfoId.clear();
  mapInfoId.insert(make_pair(0,0));
	g_mapRelations.clear();
  vector<unsigned int>::iterator it;  
  int iLemmaOld=-1;
  int iPrepOld=-1;

  string strFile = g_strTablePath + "/" + CSpecifications.CSpecification1.functionname() + ".relations.table";
  string strFileInv = g_strTablePath + "/" + CSpecifications.CSpecification1.functionname() + ".relations.inv.table";
  string strFileInvSort = g_strTablePath + "/" + CSpecifications.CSpecification1.functionname() + ".relations.inv.sort.table";

  ifstream stream(strFile.c_str());
  ofstream streamInv(strFileInv.c_str());
  char str[1000];
  while (stream)
  {
    stream.getline(str, 1000);  // delim defaults to '\n'
    if(stream) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,15))
      {
        unsigned int iPrep = atoi(CReadTabInput.get_field(1));
        unsigned int iLemma1 = atoi(CReadTabInput.get_field(2));
        unsigned int iLemma2 = atoi(CReadTabInput.get_field(3));
        string strSurfacePrep = CReadTabInput.get_field(4);
        string strSurface1 = CReadTabInput.get_field(5);
        string strSurface2 = CReadTabInput.get_field(6);
        unsigned int iPrepPOS = atoi(CReadTabInput.get_field(7));
        unsigned int iPOS1 = atoi(CReadTabInput.get_field(8));
        unsigned int iPOS2 = atoi(CReadTabInput.get_field(9));
        string strCorpus = CReadTabInput.get_field(10);
        string strInfo = CReadTabInput.get_field(11);  
      
        string strTrigger = CReadTabInput.get_field(12);        

        unsigned short int iGrundform1 = atoi(CReadTabInput.get_field(13));
        unsigned short int iGrundform2 = atoi(CReadTabInput.get_field(14));
        unsigned short int iAvail = atoi(CReadTabInput.get_field(15));

        streamInv<<iPrep<<"\t";
        streamInv<<iLemma1<<"\t";
        streamInv<<iLemma2<<"\t";
        streamInv<<strSurfacePrep<<"\t";
        streamInv<<strSurface1<<"\t";
        streamInv<<strSurface2<<"\t";
        streamInv<<iPrepPOS<<"\t";
        streamInv<<iPOS1<<"\t";
        streamInv<<iPOS2<<"\t";
        streamInv<<strCorpus<<"\t";
        streamInv<<strInfo<<"\t";
        streamInv<<strTrigger<<"\t";
        streamInv<<iGrundform1<<"\t";
        streamInv<<iGrundform2<<"\t";
        streamInv<<iAvail<<"\n";

        if (CSpecifications.invert() == InvertBidirectEQ)
        {
          streamInv<<iPrep<<"\t";
          streamInv<<iLemma2<<"\t";
          streamInv<<iLemma1<<"\t";
          streamInv<<strSurfacePrep<<"\t";
          streamInv<<strSurface2<<"\t";
          streamInv<<strSurface1<<"\t";
          streamInv<<iPrepPOS<<"\t";
          streamInv<<iPOS2<<"\t";
          streamInv<<iPOS1<<"\t";
          streamInv<<strCorpus<<"\t";
          streamInv<<strInfo<<"\t";
          streamInv<<strTrigger<<"\t";
          streamInv<<iGrundform2<<"\t";
          streamInv<<iGrundform1<<"\t";
          streamInv<<iAvail<<"\n";
        }
      }
    }
  }
  stream.close();
  streamInv.close();

  ///Sortieren der Kookkurrenzen
  string strCall;
  int iStatus;
  strCall="sort -T "+g_strTmpPath+" -n -s -k 1,1 -k 2,2 "+strFileInv+" > "+strFileInvSort;
  iStatus = system(strCall.c_str());
  check_error(iStatus,strCall);
  strCall="mv "+strFileInvSort+" "+strFileInv;
  iStatus = system(strCall.c_str());
  check_error(iStatus,strCall);

  stream.open(strFileInv.c_str());
  while (stream)
  {
    stream.getline(str, 1000);  // delim defaults to '\n'
    if(stream) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,15))
      {
        unsigned int iPrep = atoi(CReadTabInput.get_field(1));
        unsigned int iLemma1 = atoi(CReadTabInput.get_field(2));
        unsigned int iLemma2 = atoi(CReadTabInput.get_field(3));
        unsigned int iSurfacePrep = atoi(CReadTabInput.get_field(4));
        unsigned int iSurface1 = atoi(CReadTabInput.get_field(5));
        unsigned int iSurface2 = atoi(CReadTabInput.get_field(6));
        unsigned int iPrepPOS = atoi(CReadTabInput.get_field(7));
        unsigned int iPOS1 = atoi(CReadTabInput.get_field(8));
        unsigned int iPOS2 = atoi(CReadTabInput.get_field(9));
        unsigned int iCorpus = atoi(CReadTabInput.get_field(10));
        unsigned int iInfo = atoi(CReadTabInput.get_field(11));        

        float iTrigger = atof(CReadTabInput.get_field(12));        

        unsigned short int iGrundform1 = atoi(CReadTabInput.get_field(13));
        unsigned short int iGrundform2 = atoi(CReadTabInput.get_field(14));
        unsigned short int iAvail = atoi(CReadTabInput.get_field(15));

        if (iLemmaOld == -1 || iPrepOld == -1)
        {
          iLemmaOld = iLemma1;
          iPrepOld = iPrep;
        }
        else if (iLemmaOld != iLemma1 || iPrepOld != iPrep)
        {
          write_relations(CSpecifications, outputRelations, outputInfoMapping, outputFrequencyMapping);
          g_mapRelations.clear();
          iLemmaOld = iLemma1;
          iPrepOld = iPrep;
        }

        /*itMapFreqStatistic = mapFreqStatistic.find(CSpecifications.CSpecification1.functionname());
        if (itMapFreqStatistic == mapFreqStatistic.end())
        {
          mapFreqStatistic.insert(make_pair(CSpecifications.CSpecification1.functionname(),make_pair(1,0)));
        }
        else
        {
          ++itMapFreqStatistic->second.first;
        }*/

        unsigned int iCurrentInfo(0);
                                
        g_itMapRelations = g_mapRelations.find(HashSix(iPrep,iLemma1,iLemma2,iPrepPOS,iPOS1,iPOS2));

        if (g_itMapRelations == g_mapRelations.end())
        {
          Info CInfo;
          CInfo.mapFrequency.push_back(make_pair(0,1.0));
          CInfo.mapFrequency.push_back(make_pair(1,iTrigger));
          if (iInfo==0 || iAvail==0)
          {
            CInfo.mapFrequency.push_back(make_pair(2,0));
          }
          else
          {
            CInfo.mapFrequency.push_back(make_pair(2,1));
          }
          CInfo.mapFrequency.push_back(make_pair(iCorpus + 1000 ,1.0));

					///wenn die haeufigste Oberflaechenform streng lokal berechnet werden soll
          if (g_eSurfaceMode == MostFrequentTightLocal)
          {
	          CInfo.vSurface1.push_back(make_pair(iSurface1,iGrundform1));          
	          CInfo.vSurface2.push_back(make_pair(make_pair(iSurface2,iPrep),iGrundform2));
          }

          ///Prüfen auf maximal gesetzte Texttrefferzahl
          if (CInfo.vInfo.size() <= CSpecifications.max_concordance_lines() &&
            CInfo.vInfo.size() >= CSpecifications.min_concordance_lines() &&
            iInfo != 0)
          {
            CInfo.vInfo.push_back(iInfo);
          }
    
          if (iInfo==0)
          {
            CInfo.iInfoId=0;
          }
          else if (CSpecifications.invert() == InvertBidirectEQ)
          {
            hash_map<int,int>::iterator gt;
            gt = mapInfoId.find(iInfo);
            if (gt != mapInfoId.end())
            {
              CInfo.iInfoId = gt->second;
            }
            else
            {
              CInfo.iInfoId = g_iInfoMappingCounter;
              mapInfoId.insert(make_pair(iInfo,CInfo.iInfoId));
              ++g_iInfoMappingCounter;
            }
          }
          else
          {
            CInfo.iInfoId = g_iInfoMappingCounter;
            ++g_iInfoMappingCounter;
          }

          iCurrentInfo = CInfo.iInfoId;
          g_mapRelations.insert(make_pair(HashSix(iPrep,iLemma1,iLemma2,iPrepPOS,iPOS1,iPOS2),CInfo));
        }
        else
        {
          vector<pair<unsigned short int, float> >::iterator rt;
          bool bFound(false);
          for (rt=g_itMapRelations->second.mapFrequency.begin(); rt != g_itMapRelations->second.mapFrequency.end(); ++rt)
          {
            if (rt->first == 0)
            {
              ++rt->second;
            }
            else if (rt->first == 1)
            {
              rt->second += iTrigger;
            }
            else if (rt->first == 2)
            {
              if (iInfo!=0 and iAvail==1)
              {
                ++rt->second;
              }
            }
            else if (rt->first == iCorpus +1000)
            {
              ++rt->second;
              bFound=true;
              break;
            }
          }
          if (!bFound)
          {
            g_itMapRelations->second.mapFrequency.push_back(make_pair(iCorpus + 1000,1));
          }

          ///Prüfen auf maximal gesetzte Fundstellenanzahl
          if (g_itMapRelations->second.vInfo.size() <= CSpecifications.max_concordance_lines() &&
            g_itMapRelations->second.vInfo.size() >= CSpecifications.min_concordance_lines() &&
            iInfo !=0)
          {
            it = find(g_itMapRelations->second.vInfo.begin(),g_itMapRelations->second.vInfo.end(),iInfo);
            if (it == g_itMapRelations->second.vInfo.end())
            {
              g_itMapRelations->second.vInfo.push_back(iInfo);          
            }
          }

          if (g_eSurfaceMode == MostFrequentTightLocal)
          {
            g_itMapRelations->second.vSurface1.push_back(make_pair(iSurface1,iGrundform1));          
            g_itMapRelations->second.vSurface2.push_back(make_pair(make_pair(iSurface2,iPrep),iGrundform2));
          }

          if (iInfo!=0)
          {
            if (g_itMapRelations->second.iInfoId==0)
            {
              if (CSpecifications.invert() == InvertBidirectEQ)
              {
                hash_map<int,int>::iterator gt;
                gt = mapInfoId.find(iInfo);
                if (gt != mapInfoId.end())
                {
                  g_itMapRelations->second.iInfoId = gt->second;
                }
                else
                {
                  g_itMapRelations->second.iInfoId = g_iInfoMappingCounter;
                  mapInfoId.insert(make_pair(iInfo,g_itMapRelations->second.iInfoId));
                  ++g_iInfoMappingCounter;
                }
              }
              else
              {
                g_itMapRelations->second.iInfoId = g_iInfoMappingCounter;
                ++g_iInfoMappingCounter;
              }
            }
          }

          iCurrentInfo = g_itMapRelations->second.iInfoId;
        }
      }
    }
  }  
  write_relations(CSpecifications, outputRelations, outputInfoMapping, outputFrequencyMapping);
  g_mapRelations.clear();
  mapInfoId.clear();
  mapInfoId.insert(make_pair(0,0));
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

  cout<<"|: PREPROCESSING"<<endl;

  ///einlesen der Spezifikation
	init_spec(argv[1]);  

  ///einlesen des Lemmamappings
  char str[1000];
  ifstream inputLemmaMapping((g_strTablePath+"/mapping_lemma.table").c_str());
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
      }
    }
  }
  inputLemmaMapping.close();

  ///Erstellen eines Mappings von Lemmaformen auf die möglichen Oberflächenformen
  vector<Specifications>::const_iterator itVSpecifications;
  for (itVSpecifications = g_vSpecifications.begin(); 
    itVSpecifications != g_vSpecifications.end();
    ++itVSpecifications)
  {
    cout<<"(: collect forms: "<<itVSpecifications->CSpecification1.functionname()<<endl;
    calc_lemma_surfaces_mapping(*itVSpecifications);
  }

  ///schreiben des Mapping von Oberflächenformen auf Lemmaformen
  ofstream outputSurfaceLemma((g_strTablePath+"/surface_to_lemma.table").c_str());
  for (g_itMapSurfaceLemma = g_MapSurfaceLemma.begin(); g_itMapSurfaceLemma != g_MapSurfaceLemma.end(); ++g_itMapSurfaceLemma)
  {
    set<unsigned int>::iterator it;
    for (it = g_itMapSurfaceLemma->second.begin(); it != g_itMapSurfaceLemma->second.end(); ++it)
    {
      outputSurfaceLemma<<g_itMapSurfaceLemma->first.first<<"\t"<<g_itMapSurfaceLemma->first.second<<"\t"<<*it<<"\n";
    }
  }
  g_MapSurfaceLemma.clear();
 
	///Zusammenlegen der Kookkurrenzen der einzelnen syntaktischen Relationen
  ofstream outputInfoMapping((g_strTablePath+"/mapping_info.table").c_str());
  ofstream outputFrequencyMapping((g_strTablePath+"/mapping_frequency.table").c_str());
  for (itVSpecifications = g_vSpecifications.begin(); 
    itVSpecifications != g_vSpecifications.end();
    ++itVSpecifications)
  {
    cout<<"(: process relation: "<<itVSpecifications->CSpecification1.functionname()<<endl;
    string strOutputRelations =  g_strTablePath + "/" + itVSpecifications->CSpecification1.functionname() + ".relations.freq.table";
    ofstream outputRelations(strOutputRelations.c_str());

    merge_relations(*itVSpecifications, outputRelations, outputInfoMapping, outputFrequencyMapping,0,0);

    outputRelations.close();    
  }
  outputInfoMapping.close();
  outputFrequencyMapping.close();

  /*ofstream outputFreqStat((g_strTablePath+"/freq_statistic.table").c_str());
  for (itMapFreqStatistic = mapFreqStatistic.begin(); itMapFreqStatistic != mapFreqStatistic.end(); ++itMapFreqStatistic)
  {
    outputFreqStat<<itMapFreqStatistic->first<<"\t"<<itMapFreqStatistic->second.first<<"\t"<<itMapFreqStatistic->second.second<<"\n";
  }
  outputFreqStat.close();*/


  ///Löschen von temporären Tabellen
  int i;
  string strCall;

  strCall="rm "+g_strTablePath+"/*.inv.table";
  i = system(strCall.c_str());
  check_error(i,strCall);
  /*strCall="rm "+g_strTablePath+"/*.relations.table";
  i = system(strCall.c_str());
  check_error(i,strCall);*/

  cout<<"|: done"<<endl;
}

