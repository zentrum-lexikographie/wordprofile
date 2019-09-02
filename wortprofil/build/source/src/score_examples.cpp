/**
 * Programm zum gewichten der Sätze nach dem Score der Guten Beispiele
 * 
 * folgende Tabellen werden generiert: 
 *
 * + mapping_position_info_score.table
 *     -InfoId
 *     -Position des ersten Wortes
 *     -Position des zweiten Wortes
 *     -Position der Präposition
 *     -Satzposition
 *     -Datei-ID
 *     -Korpus-ID
 *     -Rechteinformationen
 *     -Score
 *
 **/

#include <iostream>
#include <vector>
#include <string.h>
#include <fstream>
#include <fstream>
#include <map>
#include <set>
#include <algorithm>


#include "hashes.h"
#include "read_specification.h"
#include "read_tab_input.h"

///globale Pfade
string g_strTablePath = "";
string g_strTmpPath = "";

///Mappings
hash_map<int,string> mapFile;
hash_map<string,int> mapFile_rev;
hash_map<int,string> mapCorpus;
hash_map<string,int> mapCorpus_rev;

///Mapping von Dateiname und Satzposition auf einen Score
hash_map<HashPair,pair<unsigned int,unsigned int>,PSHashPair,PSEqualToPair> mapPositionToCost;
///Ort der Gute-Beispiele-Information
map<string,map<string,int> > mapGoodExamples;

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
 * Einlesen der Guten-Beispiele-Scores
 * 
 * folgende Tabellen wird gelesen: 
 *
 *     -Dateiname
 *     -Satzposition
 *     -Score
 *
 **/
void init_good_examples(int iCorpus)
{
  mapPositionToCost.clear();
  hash_map<string,int>::iterator ot; 
  map<string,map<string,int> >::iterator gt;
  map<string,int>::iterator at;
  char str[100000];

  string strCorpus = mapCorpus[iCorpus];
  gt = mapGoodExamples.find(strCorpus);

  cout<<"|: process "+strCorpus<<" ..."<<endl;

  int iCounter=1;

  if (gt != mapGoodExamples.end())
  {
    for (at = gt->second.begin(); at != gt->second.end(); ++at)
    {
      iCounter=1;
      string strNewFile = at->first;
      ifstream fileExamples(strNewFile.c_str());
      while (fileExamples)
      {
        fileExamples.getline(str, 10000);  // delim defaults to '\n'
        if(fileExamples) 
        {
          ReadTabInput CReadTabInput;
          if (CReadTabInput.read_line(str,3))
          {
            string strFile = CReadTabInput.get_field(1);
            int iPos = atoi(CReadTabInput.get_field(2));
            int iScore = atoi(CReadTabInput.get_field(3));
            ot = mapFile_rev.find(strFile);
            if (ot == mapFile_rev.end())
            {
              continue;
            }
            else
            {
              ///mapping auf den Score
              mapPositionToCost.insert(make_pair(HashPair(ot->second,iPos),make_pair(iScore,iCounter)));
            }
          }
        }
        ++iCounter;
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

  cout<<" --- SCORE SENTENCES --- "<<endl;

  ReadSpecification CReadSpecification;
  CReadSpecification.parse_xml(argv[1]);
  g_strTablePath = CReadSpecification.table_path();
  mapGoodExamples =  CReadSpecification.good_examples();
  g_strTmpPath = CReadSpecification.tmp_path();
  char str[100000];

  cout<<"(: sort position information"<<endl;
  int i = system(("sort -T "+g_strTmpPath+" -n -s -k 7,7 "+g_strTablePath+"/mapping_position_info.table > "+g_strTablePath+"/mapping_position_info_sort.table").c_str());
  check_error(i);

  ///Einlesen des Dateinamenmapping
  string strInFile = g_strTablePath+"/mapping_file.table";
  ifstream streamIn(strInFile.c_str());
  while (streamIn)
  {
    streamIn.getline(str, 10000);  // delim defaults to '\n'
    if(streamIn) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,2))
      {
        unsigned int iId = atoi(CReadTabInput.get_field(1));
        const char* strFile = CReadTabInput.get_field(2);
        mapFile_rev.insert(make_pair(strFile,iId));
      }
    }
  }
  streamIn.close();

  ///Einlesen des Korpusnamenmapping
  strInFile = g_strTablePath+"/mapping_corpus.table";
  streamIn.open(strInFile.c_str());
  while (streamIn)
  {
    streamIn.getline(str, 10000);  // delim defaults to '\n'
    if(streamIn) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,2))
      {
        unsigned int iId = atoi(CReadTabInput.get_field(1));
        const char* strCorpus = CReadTabInput.get_field(2);
        mapCorpus_rev.insert(make_pair(strCorpus,iId));
        mapCorpus.insert(make_pair(iId,strCorpus));
      }
    }
  }
  streamIn.close();

  cout<<"(: init and write info"<<endl;
  ///Anreichern der Trefferinformationen mit einem Gute-Beispiele-Score
  int iOldCorpus=-1;
	ifstream inputPositionMapping((g_strTablePath+"/mapping_position_info_sort.table").c_str());
	ofstream outputPositionMapping((g_strTablePath+"/mapping_position_info_score.table").c_str());
	int iScore(-1000);
	while(inputPositionMapping) 
	{
	  inputPositionMapping.getline(str, 10000);  // delim defaults to '\n'
	  if(inputPositionMapping) 
	  {
	    ReadTabInput CReadTabInput;
	    if (CReadTabInput.read_line(str,8))
	    {
	      int iId = atoi(CReadTabInput.get_field(1));
	      int iPos1 = atoi(CReadTabInput.get_field(2));
	      int iPos2 = atoi(CReadTabInput.get_field(3));
	      int iPrepPos = atoi(CReadTabInput.get_field(4));
	      int iSent = atoi(CReadTabInput.get_field(5));
	      int iFile = atoi(CReadTabInput.get_field(6));
	      int iCorpus = atoi(CReadTabInput.get_field(7));
	      int iAvail = atoi(CReadTabInput.get_field(8));

        hash_map<int,string>::iterator ct; 
        ct = mapCorpus.find(iCorpus);
        if (ct == mapCorpus.end())
        {
          continue;
        }

        if (iOldCorpus != iCorpus)
        {
          iOldCorpus = iCorpus;
          ///für jedes Korpus die Gute-Beispiele-Information laden
          init_good_examples(iCorpus);
          ///Default-Score
	        iScore = -1000;
        }

        ///den Score ermitteln
        hash_map<HashPair,pair<unsigned int,unsigned int>,PSHashPair,PSEqualToPair>::iterator it;
        it = mapPositionToCost.find(HashPair(iFile,iSent));
        if (it != mapPositionToCost.end())
        {
          iScore = it->second.first;
        }
      
        ///Schreiben der Trefferinformationen mit Score
	      outputPositionMapping<<iId<<"\t";
	      outputPositionMapping<<iPos1<<"\t";
	      outputPositionMapping<<iPos2<<"\t";
	      outputPositionMapping<<iPrepPos<<"\t";
	      outputPositionMapping<<iSent<<"\t";
	      outputPositionMapping<<iFile<<"\t";
	      outputPositionMapping<<iCorpus<<"\t";
	      outputPositionMapping<<iAvail<<"\t";
	      outputPositionMapping<<iScore<<"\n";
	    }
	  }
	}
	inputPositionMapping.close();
	outputPositionMapping.close();

  ///Entfernen temporärer Dateien
  i = system(("rm "+g_strTablePath+"/mapping_position_info_sort.table").c_str());
  check_error(i);

}
