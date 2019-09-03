/**
 * Programm, um die Relationsdateien des Parsers auf in entsprechende Tabellen zu überführen.
 * 
 * folgende Tabellen werden generiert: 
 * 
 * + mapping_lemma.table -> Mapping von Lemmaformen of entsprechende IDs:
 *    -ID
 *    -Lemmaform
 *
 * + mapping_surface.table -> Mapping von Oberflächenformen of entsprechende IDs:
 *    -ID
 *    -Oberflächenform
 *
 * + mapping_POS.table -> Mapping von POS-Tags of entsprechende IDs:
 *    -ID
 *    -Wortkategorie
 *
 * + mapping_function.table -> Mapping von syntaktische Relationsnamen of entsprechende IDs:
 *    -ID
 *    -syntaktische Relation
 *
 * + mapping_file.table -> Mapping von Dateinamen of entsprechende IDs:
 *    -ID
 *    -Dateiname
 *
 * + mapping_corpus.table -> Mapping von Korpusnamen of entsprechende IDs:
 *    -ID
 *    -Korpusname
 *
 * + mapping_position.table -> Mapping der Fundstelleninformationen auf IDs:
 *    -Position-ID, 
 *    -erste Wortposition
 *    -zweite Wortposition
 *    -Präpositionsposition
 *    -Satzposition
 *    -Dateiname (ID)
 *    -Korpusname (ID)
 *    -Zugänglichkeit (Rechte)
 *
 * + {Relationsname}.relations.table -> Kookkurrrenzinformationen zu den einzelnen syntaktischen Relationen:
 *   Lemma der Präposition (ID), 
 *    -Lemma des ersten Wortes (ID), 
 *   -Lemma des zweiten Wortes (ID), 
 *   -Oberflächenform der Präposition (ID), 
 *   -Oberflächenform des ersten Wortes (ID)
 *   -Oberflächenform des zweiten Wortes (ID)
 *   -Wortkategorie der Präposition (ID)
 *   -Wortkategorie des ersten Wortes (ID)
 *   -Wortkategorie des zweiten Wortes (ID)
 *   -Korpus (ID)
 *   -Position-ID
 *   -Oberflächenlemmaform der Präposition (ID)
 *   -Oberflächenlemmaform des ersten Wortes (ID)
 *   -Oberflächenlemmaform des zweiten Wortes (ID)
 *   -Triggert (0.0 bis 1.0)
 *   -Was als Grundform für das erste Wort verwendet werden soll (0,1,2)
 *   -Was als Grundform für das zweite Wort verwendet werden soll (0,1,2)
 *   -rechtliche Zugänglichkeit (0,1)
 *
 * Zusätzlich werden folgende Tabellen aus der Wortprofilspezifikation generiert:
 *
 * + mapping_corpus_name.table ->
 *   -Korpuskürzel
 *   -ausführlicher Korpusname
 */

#include <iostream>
#include <vector>
#include <string.h>
#include <fstream>
#include <fstream>
#include <map>
#include <algorithm>
#include <stdio.h>
#include <sys/stat.h>
#include <sys/types.h>

#include "hashes.h"
#include "read_specification.h"
#include "read_tab_input.h"
#include "read_doubles.h"
#include "Lexer.h"


///Mapping von den strings aus der Eingabe auf integer fuer effiziente Berechnungen
int strings_to_numbers(const Specifications& CSpecifications, ifstream& stream, ofstream& outputRelations, ofstream& outputInfoMapping, const string& strCorpusName,const hash_set<string>* pSetPositiveFilter,const hash_set<string>* pSetNegativeFilter);

string g_strTmpPath = "";

hash_map<unsigned int,string> g_mapCorpusToPath;
///used hash-maps for mapping purposes
hash_map<string,unsigned int> g_mapSurfaceToInteger;
hash_map<string,unsigned int> g_mapLemmaToInteger;
hash_map<string,unsigned int> g_mapPOSToInteger;
hash_map<string,unsigned int> g_mapFunctionToInteger;
hash_map<string,unsigned int> g_mapFileToInteger;
hash_map<string,unsigned int> g_mapCorpusToInteger;
map<string, BiblInfo> g_mapBibl;
map<string,map<string,int> > g_mapGoodExamples;
map<pair<string,string>,string > g_mapPOSRewrite;


///used sets for cut-off purposes
hash_set<string> g_setStopDependents;
hash_map<string,TriggerInfo> g_mapStopClass_func;
hash_map<string,string> g_mapSurface1Trigger;
hash_map<string,string> g_mapSurface2Trigger;
hash_map<string,string> g_mapSurface1Stop;
hash_map<string,string> g_mapSurface2Stop;
hash_map<string,map<string,TriggerInfo> > g_mapReqClass_func;
set<string> g_setPositive;
set<string> g_setNegative;
set<string> g_setDoubles;
map<string,BiblField> g_mapCBiblField;
map<pair<unsigned int,unsigned int>, bool > g_mapAvail;

hash_set<HashTriple,PSHashTriple,PSEqualToTriple> g_setLimitSentences;
set<unsigned int> g_setLimitCorpus;

vector<string> g_vCorpusOrder;
map<string,string> g_mapCorpusName;

///used sets for cut-off purposes (schneller zugriff)
hash_set<unsigned int> g_setKeyNegative;
hash_set<unsigned int> g_setKeyPositive;
hash_set<HashTriple,PSHashTriple,PSEqualToTriple> g_setKeyDoubles;
///Zaehler fuer das Mapping auf Integer
unsigned int g_iHighestSurface(0);
unsigned int g_iHighestLemma(0);
unsigned int g_iHighestPOS(0);
unsigned int g_iHighestFunction(0);
unsigned int g_iHighestInfo(1);
unsigned int g_iHighestPrep(0);
unsigned int g_iHighestFile(0);
unsigned int g_iHighestCorpus(2);
///Lexer fuer das filtern und Abbilden von Lemma -und Oberflaechenformen
SynCoP::TXTLexer g_CTXTLexer;
///Objekt zum Einlesen der Spezifikationsdatei
ReadSpecification g_CReadSpecification;

//string g_strLemmaVariations;
//hash_map<string,string> g_mapLemmaVariations;

//string g_strStopLemma;
//hash_set<string> g_setStopLemma;

///Modus fuer die Statistikberechnung (wie dreistellige Relationen behandelt werden)
TernaryRelationMode g_eTernaryRelationMode = AttachToRelation;

///verwendete Pfade
string g_strRelationPath = "";
string g_strTablePath = "";
int g_doubleCounter=0;

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
 * Einlesen der durch die 'Guten Beispiele' bewerteten Sätze
 *
 * Tab-Eingabeformat: 
 *  -Dateiname
 *  -Satzposition
 *  -Score
 *
 */
void read_good_examples()
{
  map<string,map<string,int> >::iterator gt;
  map<string,int>::iterator at;
  char str[100000];
  for (gt = g_mapGoodExamples.begin(); gt != g_mapGoodExamples.end(); ++gt)
  {
    string strCorpus = gt->first;
    unsigned int iCorpus(0);

    hash_map<string,unsigned int>::iterator itMapCorpus;
    itMapCorpus = g_mapCorpusToInteger.find(strCorpus);
    if (itMapCorpus == g_mapCorpusToInteger.end())
    {
      g_mapCorpusToInteger.insert(make_pair(strCorpus,g_iHighestCorpus));
      iCorpus = g_iHighestCorpus;
      ++g_iHighestCorpus;
    }
    else
    {
      iCorpus = itMapCorpus->second;
    }
    
    int iCounter=0;
    for (at = gt->second.begin(); at != gt->second.end(); ++at)
    {
      int iLimit=at->second;

      if (iLimit != numeric_limits<int>::max())
      {
        g_setLimitCorpus.insert(iCorpus);
 
        cout<<"(: read good examples: '"<<at->first<<"'"<<endl;  
        ifstream fileExamples(at->first.c_str());
        while (fileExamples)
        {
          fileExamples.getline(str, 100000);  // delim defaults to '\n'
          if(fileExamples) 
          {
            ReadTabInput CReadTabInput;
            if (CReadTabInput.read_line(str,3))
            {

              if (iCounter == iLimit)
              {
                break;
              }

              string strFile = CReadTabInput.get_field(1);
              int iPos = atoi(CReadTabInput.get_field(2));
              int iScore = atoi(CReadTabInput.get_field(3));

              hash_map<string,unsigned int>::iterator itMapFile;
              itMapFile = g_mapFileToInteger.find(strFile);
              if (itMapFile != g_mapFileToInteger.end())
              {
                g_setLimitSentences.insert(HashTriple(iCorpus,itMapFile->second,iPos));
              }
              else
              {
                /*g_mapFileToInteger.insert(make_pair(strFile,g_iHighestFile));
                g_setLimitSentences.insert(HashTriple(iCorpus,g_iHighestFile,iPos));

                ++g_iHighestFile;*/
              }
          
              ++iCounter;
            }
          }
        }
      }
    }
  } 
}

/**
 *
 * Einlesen der Bibliographieinformation
 *
 **/
void read_bibl()
{
  hash_map<HashPair,map<string,string>,PSHashPair,PSEqualToPair> mapBiblInfo;
  hash_map<HashPair,map<string,string>,PSHashPair,PSEqualToPair>::iterator lt;
  map<string,string>::iterator mt;

  map<string, BiblInfo>::iterator bt;
  for (bt=g_mapBibl.begin() ; bt != g_mapBibl.end(); ++bt)
  {
    string strCorpus = bt->first;
    int iCorpus=0;

    hash_map<string,unsigned int>::iterator itMapCorpus;
    itMapCorpus = g_mapCorpusToInteger.find(strCorpus);
    if (itMapCorpus == g_mapCorpusToInteger.end())
    {
      g_mapCorpusToInteger.insert(make_pair(strCorpus,g_iHighestCorpus));
      iCorpus = g_iHighestCorpus;
      ++g_iHighestCorpus;
    }
    else
    {
      iCorpus = itMapCorpus->second;
    }

    string strFileRemember="";
    int iCurrentFileId=0;
    char str[100000];
    ifstream streamIn;
    cout<<"(: read bibl info: '"<<bt->second.strFile<<"'"<<endl;  
    streamIn.open(bt->second.strFile.c_str());
    while (streamIn)
    {
      streamIn.getline(str, 100000);  // delim defaults to '\n'
      if(streamIn) 
      {
        ReadTabInput CReadTabInput;
        if (CReadTabInput.read_line(str,3))
        {
          string strFile = CReadTabInput.get_field(1);
          string strFeature = CReadTabInput.get_field(2);
          string strValue = CReadTabInput.get_field(3);
          if (strFile != strFileRemember)
          {
            hash_map<string,unsigned int>::iterator itMapFile;
            itMapFile = g_mapFileToInteger.find(strFile);
            if (itMapFile != g_mapFileToInteger.end())
            {
              iCurrentFileId=itMapFile->second;
            }
            else
            {
              g_mapFileToInteger.insert(make_pair(strFile,g_iHighestFile));
              iCurrentFileId=g_iHighestFile;
	            ++g_iHighestFile;
            }
            strFileRemember=strFile;
          }

          bool bAvail=false;
          map<string,BiblField>::iterator rt;
          rt = g_mapCBiblField.find(strCorpus);
          if (rt != g_mapCBiblField.end())
          {
            if (strFeature == rt->second.strAvail)
            {    
              if (rt->second.setAvailValue.find(strValue)!=rt->second.setAvailValue.end() || rt->second.setAvailValue.empty())
              {
                 bAvail=true;
              }
              g_mapAvail.insert(make_pair(make_pair(iCorpus,iCurrentFileId),bAvail));
            }
          }
        }
      }
    }
    streamIn.close();    
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

	g_setStopDependents = g_CReadSpecification.stop_dependents();
	//g_setStopHeads = g_CReadSpecification.stop_heads();
	//g_mapStopClass = g_CReadSpecification.stop_class();
	g_mapStopClass_func = g_CReadSpecification.stop_class_func();
	g_mapSurface1Trigger = g_CReadSpecification.surface1_trigger();
	g_mapSurface2Trigger = g_CReadSpecification.surface2_trigger();
	g_mapSurface1Stop = g_CReadSpecification.surface1_stop();
	g_mapSurface2Stop = g_CReadSpecification.surface2_stop();
	//g_mapReqClass = g_CReadSpecification.req_class();
	g_mapReqClass_func = g_CReadSpecification.req_class_func();
  //g_setStopRelations = g_CReadSpecification.stop_relations();
  g_setDoubles = g_CReadSpecification.doubles();
  g_setPositive = g_CReadSpecification.positive_list();
  g_setNegative = g_CReadSpecification.negative_list();
	//g_strLemmaVariations = g_CReadSpecification.lemma_variations();
	//g_strStopLemma = g_CReadSpecification.stop_lemma();

  g_vCorpusOrder = g_CReadSpecification.corpus_order();
  g_mapCorpusName = g_CReadSpecification.corpus_name();

  g_eTernaryRelationMode = g_CReadSpecification.ternary_relation_mode();

  g_strTmpPath = g_CReadSpecification.tmp_path();

  g_mapBibl = g_CReadSpecification.bibl_info();
  g_mapCBiblField = g_CReadSpecification.bibl_fields();

  g_mapGoodExamples =  g_CReadSpecification.good_examples();

  g_mapPOSRewrite = g_CReadSpecification.get_pos_rewrite();
}

/**
 *
 * Einlesen der cut-off-Dateinamen
 *
 **/
void load_cutoff_files()
{
	///Einlesen der Doppelten-Information
  set<string>::iterator it;
  ReadDoubles CReadDoubles(g_mapCorpusToInteger,g_mapFileToInteger,g_setKeyDoubles);
  for (it = g_setDoubles.begin(); it != g_setDoubles.end(); ++it)
  {
		cout<<"(: read doubles: '"<<*it<<"'"<<endl;
		CReadDoubles.parse_xml(*it);
  }
	//g_iHighestFile = CReadDoubles.get_highest_file();
  
	///Einlesen der Positivliste
  set<string>::iterator st;
  for (st =  g_setPositive.begin(); st != g_setPositive.end(); ++st)
  {
    ifstream streamPositive(st->c_str());
    if(streamPositive) 
    {
		  char str[10000];
			while(streamPositive)
      {
			  streamPositive.getline(str, 10000);  // delim defaults to '\n'
			  if (streamPositive)
        {
          hash_map<string,unsigned int>::iterator ft;
					ft = g_mapFileToInteger.find(str);
					if (ft != g_mapFileToInteger.end())
          {
            g_setKeyPositive.insert(ft->second);
          }
					/*else
          {
            g_mapFileToInteger.insert(make_pair(str,g_iHighestFile));
            g_setKeyPositive.insert(g_iHighestFile);
			      ++g_iHighestFile;
          }*/
        }			
      }
    }
    else
    {
      cerr<<"): Positivdateiliste '"<<st->c_str()<<"' nicht gefunden"<<endl;
      exit(-1);
    }  
  }

	///Einlesen der Negativliste
  for (st =  g_setNegative.begin(); st != g_setNegative.end(); ++st)
  {
    ifstream streamNegative(st->c_str());
    if(streamNegative) 
    {
		  char str[10000];
			while(streamNegative)
      {
			  streamNegative.getline(str, 10000);  // delim defaults to '\n'
			  if (streamNegative)
        {
          hash_map<string,unsigned int>::iterator ft;
					ft = g_mapFileToInteger.find(str);
					if (ft != g_mapFileToInteger.end())
          {
            g_setKeyNegative.insert(ft->second);
          }
					/*else
          {
            g_mapFileToInteger.insert(make_pair(str,g_iHighestFile));
            g_setKeyNegative.insert(g_iHighestFile);
			      ++g_iHighestFile;
          }*/
        }			
      }
    }
    else
    {
      cerr<<"): Negativdateiliste '"<<st->c_str()<<" nicht gefunden"<<endl;
      exit(-1);
    }  
  }

	///einlesen der lemmavariationen
	/*if (!g_strLemmaVariations.empty())
	{
		ifstream streamLemmaVariations(g_strLemmaVariations.c_str());
		if(streamLemmaVariations) 
		{
			char str[10000];
			while(streamLemmaVariations)
	    {
				streamLemmaVariations.getline(str, 1000);
				if(streamLemmaVariations) 
				{
					ReadTabInput CReadTabInput;
					if (CReadTabInput.read_line(str,2))
					{
						string strLemma =  CReadTabInput.get_field(1);
						string strVariation =  CReadTabInput.get_field(2);
						g_mapLemmaVariations.insert(make_pair(strVariation,strLemma));
					}
				}		
			}
		}
    else
    {
      cerr<<"): Lemmavariationliste '"<<g_strLemmaVariations<<" nicht gefunden"<<endl;
      exit(-1);
    }  
	}*/

  ///einlesen eine Liste mit Lemmaformen, die ausgeschlossen werden sollen
	/*if (!g_strStopLemma.empty())
	{
		ifstream streamStopLemma(g_strStopLemma.c_str());
		if(streamStopLemma) 
		{
			char str[10000];
			while(streamStopLemma)
	    {
				streamStopLemma.getline(str, 1000);
				if(streamStopLemma) 
				{
					ReadTabInput CReadTabInput;
					if (CReadTabInput.read_line(str,1))
					{
						string strLemma =  CReadTabInput.get_field(1);
						g_setStopLemma.insert(strLemma);
					}
				}		
			}
		}
    else
    {
      cerr<<"): Stoplemmaliste '"<<g_strStopLemma<<" nicht gefunden"<<endl;
      exit(-1);
    }  
	}*/

}

/**
 *
 * Schreiben und Sortieren der ID-Mappings: Lemma, Oberflächenform, Wortkategorie, Relationsnamen, Dateinamen, Korpusnamen
 *
 **/
void write_mappings()
{
	///write lemma forms
  hash_map<string,unsigned int>::iterator itMapLemma;
  string strOutputLemmaMapping = g_strTablePath+"/mapping_lemma.table";
  ofstream outputLemmaMapping(strOutputLemmaMapping.c_str());
  for (itMapLemma = g_mapLemmaToInteger.begin(); itMapLemma != g_mapLemmaToInteger.end(); ++itMapLemma)
  {
    outputLemmaMapping<<itMapLemma->second<<'\t'<<itMapLemma->first<<'\n';
  }

	///write surface forms
  hash_map<string,unsigned int>::iterator itMapSurface;
  string strOutputSurfaceMapping = g_strTablePath+"/mapping_surface.table";
  ofstream outputSurfaceMapping(strOutputSurfaceMapping.c_str());
  for (itMapSurface = g_mapSurfaceToInteger.begin(); itMapSurface != g_mapSurfaceToInteger.end(); ++itMapSurface)
  {
    outputSurfaceMapping<<itMapSurface->second<<'\t'<<itMapSurface->first<<'\n';
  }

	///write part-of-speechs
  hash_map<string,unsigned int>::iterator itMapPOS;
  string strOutputPOSMapping = g_strTablePath+"/mapping_POS.table";
  ofstream outputPOSMapping(strOutputPOSMapping.c_str());
  for (itMapPOS = g_mapPOSToInteger.begin(); itMapPOS != g_mapPOSToInteger.end(); ++itMapPOS)
  {
    outputPOSMapping<<itMapPOS->second<<'\t'<<itMapPOS->first<<'\n';
  }

	///write relations
  hash_map<string,unsigned int>::iterator itMapFunction;
  string strOutputFunctionMapping = g_strTablePath+"/mapping_function.table";
  ofstream outputFunctionMapping(strOutputFunctionMapping.c_str());
  for (itMapFunction = g_mapFunctionToInteger.begin(); itMapFunction != g_mapFunctionToInteger.end(); ++itMapFunction)
  {
    if (g_CReadSpecification.is_inverted_relation(itMapFunction->first))
    {
      outputFunctionMapping<<itMapFunction->second<<'\t'<<itMapFunction->first<<'\t'<<1<<'\t'<<g_CReadSpecification.get_snippet(itMapFunction->first)<<'\t'<<g_CReadSpecification.get_description(itMapFunction->first)<<'\t'<<g_CReadSpecification.get_example(itMapFunction->first)<<'\n';
    }
    else if (g_CReadSpecification.is_bidirected_relation(itMapFunction->first))
    {
      outputFunctionMapping<<itMapFunction->second<<'\t'<<itMapFunction->first<<'\t'<<2<<'\t'<<g_CReadSpecification.get_snippet(itMapFunction->first)<<'\t'<<g_CReadSpecification.get_description(itMapFunction->first)<<'\t'<<g_CReadSpecification.get_example(itMapFunction->first)<<'\n';
    }
    else
    {
      outputFunctionMapping<<itMapFunction->second<<'\t'<<itMapFunction->first<<'\t'<<0<<'\t'<<g_CReadSpecification.get_snippet(itMapFunction->first)<<'\t'<<g_CReadSpecification.get_description(itMapFunction->first)<<'\t'<<g_CReadSpecification.get_example(itMapFunction->first)<<'\n';
    }
  }

	///write file names
  hash_map<string,unsigned int>::iterator itMapFileToInteger;
  string strOutputFileMapping = g_strTablePath+"/mapping_file.table";
  ofstream outputFileMapping(strOutputFileMapping.c_str());
  for (itMapFileToInteger = g_mapFileToInteger.begin(); itMapFileToInteger != g_mapFileToInteger.end(); ++itMapFileToInteger)
  {
    outputFileMapping<<itMapFileToInteger->second<<'\t'<<itMapFileToInteger->first<<'\n';
  }

	///write corpus names
  hash_map<string,unsigned int>::iterator itg_mapCorpusToInteger;
  string strOutputCorpusMapping = g_strTablePath+"/mapping_corpus.table";
  ofstream outputCorpusMapping(strOutputCorpusMapping.c_str());
  for (itg_mapCorpusToInteger = g_mapCorpusToInteger.begin(); itg_mapCorpusToInteger != g_mapCorpusToInteger.end(); ++itg_mapCorpusToInteger)
  {
    outputCorpusMapping<<itg_mapCorpusToInteger->second<<'\t'<<itg_mapCorpusToInteger->first<<'\n';
  }

	///close files
  outputCorpusMapping.close();
  outputFileMapping.close();
  outputFunctionMapping.close();
  outputLemmaMapping.close();
  outputPOSMapping.close();  

  ///Sortieren der Korpustabelle
  int i = system(("sort -T "+g_strTmpPath+" -g -s -k 1,1 "+strOutputCorpusMapping+" > "+strOutputCorpusMapping+".sorted").c_str());
  check_error(i);
  i = system(("mv "+strOutputCorpusMapping+".sorted "+strOutputCorpusMapping).c_str());
  check_error(i);

  ///Sortieren der POS-Tablelle
  i = system(("sort -T "+g_strTmpPath+" -g -s -k 1,1 "+strOutputPOSMapping+" > "+strOutputPOSMapping+".sorted").c_str());
  check_error(i);
  i = system(("mv "+strOutputPOSMapping+".sorted "+strOutputPOSMapping).c_str());
  check_error(i);

  ///Sortieren der Relationsnamen-Tablelle
  i = system(("sort -T "+g_strTmpPath+" -g -s -k 1,1 "+strOutputFunctionMapping+" > "+strOutputFunctionMapping+".sorted").c_str());
  check_error(i);
  i = system(("mv "+strOutputFunctionMapping+".sorted "+strOutputFunctionMapping).c_str());
  check_error(i);
}

/**
 *
 * Abbilden der Zeichenketten aus den Relationsdateien vom Parser auf IDs
 *
 **/
int strings_to_numbers(const Specifications& CSpecifications, ifstream& stream, ofstream& outputRelations, ofstream& outputInfoMapping, const string& strCorpusName,const hash_set<string>* pSetPositiveFilter,const hash_set<string>* pSetNegativeFilter)
{
	///mapping corpus name
  unsigned int iCorpus;
  hash_map<string,unsigned int>::iterator itMapCorpus;
  itMapCorpus = g_mapCorpusToInteger.find(strCorpusName);
  if (itMapCorpus == g_mapCorpusToInteger.end())
  {
    g_mapCorpusToInteger.insert(make_pair(strCorpusName,g_iHighestCorpus));
    iCorpus = g_iHighestCorpus;
    ++g_iHighestCorpus;
  }
  else
  {
    iCorpus = itMapCorpus->second;
  }

	//g_mapCorpusToPath.insert(make_pair(iCorpus,strCorpusPath));


	///mapping relation name
  if (CSpecifications.invert()==InvertBidirect)
  {
    hash_map<string,unsigned int>::iterator itMapFunction;
    itMapFunction = g_mapFunctionToInteger.find(CSpecifications.CSpecification2.functionname());
    if (itMapFunction == g_mapFunctionToInteger.end())
    {
      g_mapFunctionToInteger.insert(make_pair(CSpecifications.CSpecification2.functionname(),g_iHighestFunction));
      ++g_iHighestFunction;
    }
  }
  hash_map<string,unsigned int>::iterator itMapFunction;
  itMapFunction = g_mapFunctionToInteger.find(CSpecifications.CSpecification1.functionname());
  if (itMapFunction == g_mapFunctionToInteger.end())
  {
    g_mapFunctionToInteger.insert(make_pair(CSpecifications.CSpecification1.functionname(),g_iHighestFunction));
    ++g_iHighestFunction;
  }

	string strRelation = CSpecifications.CSpecification1.functionname();       

	///processes the lines of the file
  char str[100000];
  ReadTabInput CReadTabInput;
  while(stream) 
  {
    stream.getline(str, 100000);
    if(stream) 
    {
      if (CReadTabInput.read_line(str,15))
      {

        bool bBaseformTrigger1=true;
        bool bBaseformTrigger2=true;

				float iTrigger(1.0);

        const char* szLemma1 = CReadTabInput.get_field(1);
        string szLemma2 = CReadTabInput.get_field(2);
        const char* szPrep = CReadTabInput.get_field(3);
        const char* szSurface1 = CReadTabInput.get_field(4);
        string szSurface2 = CReadTabInput.get_field(5);
        string szSurfacePrep = CReadTabInput.get_field(6);
        const char* szPOS1 = CReadTabInput.get_field(7);
        const char* szPOS2 = CReadTabInput.get_field(8);
        const char* szPrepPOS = CReadTabInput.get_field(9);

        const char* szWord1Position = CReadTabInput.get_field(10); //wortposition von wort 1
        const char* szWord2Position = CReadTabInput.get_field(11); //wortposition von wort 2
        string szPrepositionPosition = CReadTabInput.get_field(12); //praepositionsposition
        const char* szSentencePosition = CReadTabInput.get_field(13); //Satzposition
        const char* szFilename = CReadTabInput.get_field(14); //filename
        string szMessage = CReadTabInput.get_field(15); //message

        string strPOS1_orig = szPOS1;
        string strPOS2_orig = szPOS2;
        string strPrepPOS_orig = szPrepPOS;

        ///ausschliessen von Dateinamen über einen Positivfilter
        if (pSetPositiveFilter!=NULL)
        {
          if (pSetPositiveFilter->find(szFilename)==pSetPositiveFilter->end())
          {
            continue;
          }
        }

        ///ausschliessen von Dateinamen über einen Negativfilter
        if (pSetNegativeFilter!=NULL)
        {
          if (pSetNegativeFilter->find(szFilename)!=pSetNegativeFilter->end())
          {
            continue;
          }
        }

        ///umschreinben von POS-informationen im Kontext eines bestimmten Lemmas
        map<pair<string,string>,string>::iterator zt;
        zt = g_mapPOSRewrite.find(make_pair(szLemma1,strPOS1_orig));
        if (zt != g_mapPOSRewrite.end())
        {
          strPOS1_orig=zt->second;
        }
        zt = g_mapPOSRewrite.find(make_pair(szLemma2,strPOS2_orig));
        if (zt != g_mapPOSRewrite.end())
        {
          strPOS2_orig=zt->second;
        }
        zt = g_mapPOSRewrite.find(make_pair(szPrep,strPrepPOS_orig));
        if (zt != g_mapPOSRewrite.end())
        {
          strPrepPOS_orig=zt->second;
        }

        ///generelles umschreinben von POS-informationen
        string strPOS1(g_CReadSpecification.pos_mapping(strPOS1_orig));
        string strPOS2(g_CReadSpecification.pos_mapping(strPOS2_orig));
        string strPrepPOS(g_CReadSpecification.pos_mapping(strPrepPOS_orig));

        ///wenn ein POS durch die Umschreibung ausgeschlossen wird
        if (strPOS1=="" or strPOS2=="")
        {
          continue;
        }

        ///unterschiedliche behandlungsformen von Prep
        string strPrep(szPrep);
        bool bAppendPrep(false);
        bool bDeletePrep(false);
        if (g_eTernaryRelationMode == AttachToWord)
        {
          if (strPrep!="" && strPrep!="-")
          {
            bAppendPrep=true;
          }
        }
        if (CSpecifications.bIgnorePrep || g_eTernaryRelationMode == AttachToWord)
        {
          bDeletePrep=true;
        }

				///Überprüfen der Stop-Klassen anhand der syntaktischen Trigger in den Parserausgabedateien
				set<string> _reqClass;
				bool bFoundClass=false;
        string strDummy;
        int old=-1;
        int pos = 0;
        iTrigger=1.0;
        while (pos != string::npos)
        {
          pos = szMessage.find('|',old+1);
          strDummy=szMessage.substr(old+1,(pos)-old-1);

					if (!strDummy.empty())
					{
            hash_map<string,TriggerInfo>::iterator itTr;
            itTr = g_mapStopClass_func.find(strPOS1+"\x01"+strRelation+"\x01"+strDummy+"\x01"+strPOS2);
		        if (itTr!=g_mapStopClass_func.end())
		        {
							if (itTr->second.iScore < 0)
							{
							  bFoundClass=true;
		            break;
              }
							else
							{
								iTrigger=min(itTr->second.iScore,iTrigger);
							}
		        }
						_reqClass.insert(strDummy);
					}
          old = pos;
				}  
				if (bFoundClass==true)
				{
					continue;
				}    

				///Überprüfen der Require-Klassen anhand der syntaktischen Trigger in den Parserausgabedateien
				hash_map<string,map<string,TriggerInfo> >::iterator reqIt;
				map<string,TriggerInfo>::iterator reqSt;
				bool bNotRequire(false);

				reqIt = g_mapReqClass_func.find(strPOS1+"\x01"+strRelation+"\x01"+strPOS2);
				if (reqIt != g_mapReqClass_func.end())
				{
					for (reqSt = reqIt->second.begin();reqSt != reqIt->second.end(); ++reqSt)
					{
						if (_reqClass.find(reqSt->first)==_reqClass.end())
						{
							if (reqSt->second.iScore < 0)
							{
							  bNotRequire = true;
							  break;
							}
							else
							{
								iTrigger=min(reqSt->second.iScore,iTrigger);
							}
						}
					}
					if (bNotRequire)
					{
						continue;
					}
				}

        ///prüfen, ob eine Oberflächenform als Lemmaform verwendet werden soll
				hash_map<string,string>::iterator bt;
        bt = g_mapSurface1Trigger.find(strPOS1+"\x01"+strRelation);
        if (bt != g_mapSurface1Trigger.end())
        {
          bBaseformTrigger1=false;
					if (_reqClass.find(bt->second)!=_reqClass.end())
					{
            bBaseformTrigger1=true;
          }
        }

        bt = g_mapSurface1Stop.find(strPOS1+"\x01"+strRelation);
        if (bt != g_mapSurface1Stop.end())
        {
					if (_reqClass.find(bt->second)!=_reqClass.end())
					{
            bBaseformTrigger1=false;
          }
        }

        bt = g_mapSurface2Trigger.find(strPOS2+"\x01"+strRelation);
        if (bt != g_mapSurface2Trigger.end())
        {
          bBaseformTrigger2=false;
					if (_reqClass.find(bt->second)!=_reqClass.end())
					{
            bBaseformTrigger2=true;
          }
        }

        bt = g_mapSurface2Stop.find(strPOS2+"\x01"+strRelation);
        if (bt != g_mapSurface2Stop.end())
        {
					if (_reqClass.find(bt->second)!=_reqClass.end())
					{
            bBaseformTrigger2=false;
          }
        }
        
				if (bNotRequire)
				{
					continue;
				}

				string strFilenameOriginal = szFilename;

        hash_map<string,unsigned int>::iterator itMapFile;
        itMapFile = g_mapFileToInteger.find(strFilenameOriginal);
        if (itMapFile != g_mapFileToInteger.end())
        {
          unsigned int iFile = itMapFile->second;
     
          ///Prüfen, ob Metadaten vorhanden
          if (g_mapAvail.find(make_pair(iCorpus,iFile)) == g_mapAvail.end())
          {
            continue;
          }

          ///Prüfen, ob ein Duplikat vorliegt
          if (g_setKeyDoubles.find(HashTriple(iCorpus,iFile,atoi(szSentencePosition))) != g_setKeyDoubles.end())
          {
            ++g_doubleCounter;
            continue;
          }
					if (!g_setKeyPositive.empty())
          {
            ///Prüfen, ob in der Deitei-Positivliste vorhanden
		        if (g_setKeyPositive.find(iFile) == g_setKeyPositive.end())
		        {
		          continue;
		        }
          }
          ///Prüfen, ob in der Deitei-Negativliste vorhanden
	        if (g_setKeyNegative.find(iFile) != g_setKeyNegative.end())
	        {
	          continue;
	        }

          ///wenn kein Einfluss auf die Schwellwertbezogene Frequenz Einfluss genommen werden soll
          if (g_CReadSpecification.is_suppressed(strPOS1_orig))
          {
            iTrigger=0.0;
          }
          else if (g_CReadSpecification.is_suppressed(strPOS2_orig))
          {
            iTrigger=0.0;
          }
          else if (g_CReadSpecification.is_suppressed(strPrepPOS_orig))
          {
            iTrigger=0.0;
          }
          
          int iLemSurfPrep(-1);
          int iLemSurf1(-1);
          int iLemSurf2(-1);
          unsigned int iLemma1(0);
          unsigned int iLemma2(0);
          unsigned int iSurfacePrep(0);
          unsigned int iSurface1(0);
          unsigned int iSurface2(0);
          unsigned int iPOS1(0);
          unsigned int iPOS2(0);
          unsigned int iPrepPOS(0);
          unsigned int iPrep(0);

          string strSurface1; 
          string strSurface2;
          string strSurfacePrep;

          //ob die Objerflächenform als Lemma verwendet werden soll
          unsigned int bGrundform1=0;
          unsigned int bGrundform2=0;

          //Filtern der Lemmaform
          strPrep = g_CTXTLexer.parse_string(strPrep.c_str(),szSurfacePrep.c_str(),strPrepPOS_orig,g_CReadSpecification.pos_mapping(strPrepPOS_orig),LexerModeLemma);
          strPrep = g_CReadSpecification.prep_mapping(strPrep.c_str());

          string strLemma1 = g_CTXTLexer.parse_string(szLemma1,szSurface1,strPOS1_orig,g_CReadSpecification.pos_mapping(strPOS1_orig),LexerModeLemma);
          strLemma1 = g_CReadSpecification.lemma_mapping(strLemma1.c_str());

          string strLemma2 = g_CTXTLexer.parse_string(szLemma2.c_str(),szSurface2.c_str(),strPOS2_orig,g_CReadSpecification.pos_mapping(strPOS2_orig),LexerModeLemma);	
          strLemma2 = g_CReadSpecification.lemma_mapping(strLemma2.c_str());
          
          //Filtern der Oberflächenform
				  strSurface1 = g_CTXTLexer.parse_string(szSurface1,szLemma1,strPOS1_orig,g_CReadSpecification.pos_mapping(strPOS1_orig),LexerModeSurface);
				  strSurface2 = g_CTXTLexer.parse_string(szSurface2.c_str(),szLemma2.c_str(),strPOS2_orig,g_CReadSpecification.pos_mapping(strPOS2_orig),LexerModeSurface);
				  strSurfacePrep = g_CTXTLexer.parse_string(szSurfacePrep.c_str(),strPrep.c_str(),strPrepPOS_orig,g_CReadSpecification.pos_mapping(strPrepPOS_orig),LexerModeSurface);


          if (bBaseformTrigger1)
          {            
            bGrundform1=0;
				    if (g_CReadSpecification.use_surface_as_baseform_by_pos(strPOS1_orig))
				    {
              bGrundform1=1;
            }
          }
          else
          {
            bGrundform1=2;
          }

          if (bBaseformTrigger2)
          {            
            bGrundform2=0;
				    if (g_CReadSpecification.use_surface_as_baseform_by_pos(strPOS2_orig))
				    {
              bGrundform2=1;
            }
          }
          else
          {
            bGrundform2=2;
          }

          if (bAppendPrep)
          {
            if (!strLemma2.empty())
            {
              strLemma2 = strPrep+"^"+strLemma2;
            }
            if (!strSurface2.empty())
            {
              strSurface2 = strSurfacePrep+"^"+szSurface2;
            }
          }

          if (bDeletePrep)
          {
            strPrep="-";
            strPrepPOS="-";
            szPrepositionPosition="-";
            szSurfacePrep="-";
          }

          if (strLemma1.length() <= CSpecifications.max_string_length() && 
            strLemma2.length() <= CSpecifications.max_string_length() &&
            !strLemma1.empty() &&
            !strLemma2.empty() &&
            !strSurface1.empty() &&
            !strSurface2.empty() &&
            strLemma1.length() >= CSpecifications.min_string_length() && 
            strLemma2.length() >= CSpecifications.min_string_length() &&
            strSurface1.length() >= CSpecifications.min_string_length() && 
            strSurface2.length() >= CSpecifications.min_string_length() &&
            !strPOS1.empty() &&
            !strPOS2.empty())
          {  
					  ///mapping lemma
            hash_map<string,unsigned int>::iterator itMapLemma;
            itMapLemma = g_mapLemmaToInteger.find(strLemma1);
            if (itMapLemma == g_mapLemmaToInteger.end())
            {
              g_mapLemmaToInteger.insert(make_pair(strLemma1,g_iHighestLemma));
              iLemma1 = g_iHighestLemma;
              ++g_iHighestLemma;
            }
            else
            {
              iLemma1 = itMapLemma->second;
            }
            itMapLemma = g_mapLemmaToInteger.find(strLemma2);
            if (itMapLemma == g_mapLemmaToInteger.end())
            {
              g_mapLemmaToInteger.insert(make_pair(strLemma2,g_iHighestLemma));
              iLemma2 = g_iHighestLemma;
              ++g_iHighestLemma;
            }
            else
            {
              iLemma2 = itMapLemma->second;
            }
            itMapLemma = g_mapLemmaToInteger.find(strPrep);
            if (itMapLemma == g_mapLemmaToInteger.end())
            {
              g_mapLemmaToInteger.insert(make_pair(strPrep,g_iHighestLemma));
              iPrep = g_iHighestLemma;
              ++g_iHighestLemma;
            }
            else
            {
              iPrep = itMapLemma->second;
            }

					  ///mapping surface
            hash_map<string,unsigned int>::iterator itMapSurface;
            itMapSurface = g_mapSurfaceToInteger.find(strSurface1);
            if (itMapSurface == g_mapSurfaceToInteger.end())
            {
              g_mapSurfaceToInteger.insert(make_pair(strSurface1,g_iHighestSurface));
              iSurface1 = g_iHighestSurface;
              ++g_iHighestSurface;
            }
            else
            {
              iSurface1 = itMapSurface->second;
            }
            itMapSurface = g_mapSurfaceToInteger.find(strSurface2);
            if (itMapSurface == g_mapSurfaceToInteger.end())
            {
              g_mapSurfaceToInteger.insert(make_pair(strSurface2,g_iHighestSurface));
              iSurface2 = g_iHighestSurface;
              ++g_iHighestSurface;
            }
            else
            {
              iSurface2 = itMapSurface->second;
            }

            itMapSurface = g_mapSurfaceToInteger.find(strSurfacePrep);
            if (itMapSurface == g_mapSurfaceToInteger.end())
            {
              g_mapSurfaceToInteger.insert(make_pair(strSurfacePrep,g_iHighestSurface));
              iSurfacePrep = g_iHighestSurface;
              ++g_iHighestSurface;
            }
            else
            {
              iSurfacePrep = itMapSurface->second;
            }
                      
					  ///mapping part-of-speech
            hash_map<string,unsigned int>::iterator itMapPOS;
            itMapPOS = g_mapPOSToInteger.find(strPOS1);
            if (itMapPOS == g_mapPOSToInteger.end())
            {
              g_mapPOSToInteger.insert(make_pair(strPOS1,g_iHighestPOS));
              iPOS1 = g_iHighestPOS;
              ++g_iHighestPOS;
            }
            else
            {
              iPOS1 = itMapPOS->second;
            }
            
            itMapPOS = g_mapPOSToInteger.find(strPOS2);
            if (itMapPOS == g_mapPOSToInteger.end())
            {
              g_mapPOSToInteger.insert(make_pair(strPOS2,g_iHighestPOS));
              iPOS2 = g_iHighestPOS;
              ++g_iHighestPOS;
            }
            else
            {
              iPOS2 = itMapPOS->second;
            }

            itMapPOS = g_mapPOSToInteger.find(strPrepPOS);
            if (itMapPOS == g_mapPOSToInteger.end())
            {
              g_mapPOSToInteger.insert(make_pair(strPrepPOS,g_iHighestPOS));
              iPrepPOS = g_iHighestPOS;
              ++g_iHighestPOS;
            }
            else
            {
              iPrepPOS = itMapPOS->second;
            }

            bool bAvail=false;

            map<pair<unsigned int,unsigned int>,bool>::iterator at;
            at = g_mapAvail.find(make_pair(iCorpus,iFile));
            if (at != g_mapAvail.end())
            {
              if (at->second == true)
              {                
                if (g_setLimitCorpus.find(iCorpus) == g_setLimitCorpus.end())
                {
                  bAvail=true;
                }
                else
                {
                  if (g_setLimitSentences.find(HashTriple(iCorpus,iFile,atoi(szSentencePosition)))!= g_setLimitSentences.end())
                  {
                    bAvail=true;
                  }
                }
              }
            }

					  ///write relation information
            outputRelations<<iPrep<<'\t';
            outputRelations<<iLemma1<<'\t';
            outputRelations<<iLemma2<<'\t';
            outputRelations<<iSurfacePrep<<'\t';
            outputRelations<<iSurface1<<'\t';
            outputRelations<<iSurface2<<'\t';
            outputRelations<<iPrepPOS<<'\t';
            outputRelations<<iPOS1<<'\t';
            outputRelations<<iPOS2<<'\t';
            outputRelations<<iCorpus<<'\t';
            if (bAvail)
            {
              outputRelations<<g_iHighestInfo<<'\t';
            }
            else
            {
              outputRelations<<g_iHighestInfo<<'\t';
            }

            outputRelations<<iTrigger<<'\t';

            outputRelations<<bGrundform1<<'\t';
            outputRelations<<bGrundform2<<'\t';

            if (bAvail)
            {
              outputRelations<<1<<'\n';
            }
            else
            {
              outputRelations<<0<<'\n';
            }

				    ///write location information          
            outputInfoMapping<<g_iHighestInfo<<'\t';
            outputInfoMapping<<szWord1Position<<'\t';
            outputInfoMapping<<szWord2Position<<'\t';
            outputInfoMapping<<szPrepositionPosition<<'\t';
            outputInfoMapping<<szSentencePosition<<'\t';
            outputInfoMapping<<iFile<<'\t';
            outputInfoMapping<<iCorpus<<'\t';

            if (bAvail)
            {
              outputInfoMapping<<1<<'\n';
            }
            else
            {
              outputInfoMapping<<0<<'\n';
            }
            ++g_iHighestInfo;
          }
          else
          {
          }
        }
        else
        {
          cout<<"|: missing bibl-Info, skip: "<<strFilenameOriginal<<endl;
        }
      }
      else
      {
        cerr<<"): Fehler in der Tab-Anzahl in: "<<g_strRelationPath + "/" + CSpecifications.CSpecification1.functionname()<<endl;
        exit(-1);
      } 
    }
  }       
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

  cout<<"|: MAPPING of STRINGS to INTEGERS"<<endl;

	init_spec(argv[1]);
   
  vector<string>::reverse_iterator it;
  for (it = g_vCorpusOrder.rbegin(); it != g_vCorpusOrder.rend(); ++it)
  {
	  ///mapping corpus name
    unsigned int iCorpus=0;
    hash_map<string,unsigned int>::iterator itMapCorpus;
    itMapCorpus = g_mapCorpusToInteger.find(*it);
    if (itMapCorpus == g_mapCorpusToInteger.end())
    {
      g_mapCorpusToInteger.insert(make_pair(*it,g_iHighestCorpus));
      iCorpus = g_iHighestCorpus;
      ++g_iHighestCorpus;
    }
    else
    {
      iCorpus = itMapCorpus->second;
    }
  }

  if (mkdir(g_strTablePath.c_str(),0775) == 0)
  {
    cout<<"(: create dir: "<<g_strTablePath.c_str()<<endl;
	}    

  map<string,string>::iterator itMapCorpusName;
  ofstream outputCorpusName((g_strTablePath+"/mapping_corpus_name.table").c_str());
  for (itMapCorpusName=g_mapCorpusName.begin(); itMapCorpusName!=g_mapCorpusName.end(); ++itMapCorpusName)
  {
    outputCorpusName<<itMapCorpusName->first<<"\t"<<itMapCorpusName->second<<'\n';
  }
  outputCorpusName.close();

  ///read bibl info
  read_bibl();

  ///read doubles
	load_cutoff_files();

  ///read good examples
  read_good_examples();

  cout<<"|: read syntactic cooccurrences:"<<endl;

  const vector<Specifications> vSpecifications(g_CReadSpecification.get_specifications());
  vector<Specifications>::const_iterator itVSpecifications;

  string strOutputInfoMapping = g_strTablePath+"/mapping_position.table";
  ofstream outputInfoMapping(strOutputInfoMapping.c_str());

	///fuer jede Relation wird das Mapping vollzogen
  for (itVSpecifications = vSpecifications.begin(); 
    itVSpecifications != vSpecifications.end();
    ++itVSpecifications)
  {
		cout<<"|: process syntactic relation: "<<itVSpecifications->CSpecification1.functionname()<<endl;    
    string strOutputRelations =  g_strTablePath + "/" + itVSpecifications->CSpecification1.functionname() + ".relations.table";
    ofstream outputRelations(strOutputRelations.c_str());

    char str[100000];
    hash_set<string>* pSetPositiveFilter(NULL);
    hash_set<string> setPositiveFilter;
    if (itVSpecifications->strPositiveFilter.length()!=0)
    {
	    ifstream positiveFilterStream((g_strRelationPath + "/" + itVSpecifications->strPositiveFilter).c_str());      
      while(positiveFilterStream) 
      {
        positiveFilterStream.getline(str, 100000);
        if(positiveFilterStream) 
        {
          setPositiveFilter.insert(str);
        }
      }
      pSetPositiveFilter=&setPositiveFilter;
    }

    hash_set<string>* pSetNegativeFilter(NULL);
    hash_set<string> setNegativeFilter;
    if (itVSpecifications->strNegativeFilter.length()!=0)
    {
	    ifstream negativeFilterStream((g_strRelationPath + "/" + itVSpecifications->strNegativeFilter).c_str());      
      while(negativeFilterStream) 
      {
        negativeFilterStream.getline(str, 100000);
        if(negativeFilterStream) 
        {
          setNegativeFilter.insert(str);
        }
      }
      pSetNegativeFilter=&setNegativeFilter;
    }

		///fuer jedes Relationsfile wird das Mapping vollzogen
    set<pair<string,string> >::iterator gt;
    for (gt = itVSpecifications->setFilename.begin(); gt != itVSpecifications->setFilename.end(); ++gt)
    { 
      cout<<"(: process file: "<<g_strRelationPath + "/" + gt->first<<endl;
		  ifstream stream((g_strRelationPath + "/" + gt->first).c_str());      
		  strings_to_numbers(*itVSpecifications,stream,outputRelations,outputInfoMapping,gt->second,pSetPositiveFilter,pSetNegativeFilter);
		  stream.close();
    }
    outputRelations.close();
  }
  outputInfoMapping.close();
  
	write_mappings();

  cout<<"|: done"<<endl;  
}

