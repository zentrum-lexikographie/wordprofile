/**
 * Über das Programm werden die Treffersätze aus den Korpora extrahiert und es werden TEI-Informationen verknüpft
 * und es werden entsprechende Tabellen für MySQL geschrieben
 * 
 * folgende Tabellen werden generiert: 
 *
 * + mapping_position_info_tei.table 
 *    -Texttreffer-ID
 *    -Position des ersten Wortes im Satz
 *    -Position des zweiten Wortes im Satz
 *    -Position der Präposition im Satz
 *    -Position des Satzes im Text (die Sätze sind durchnummeriert)
 *    -Dateinamen-ID
 *    -Korpus-ID
 *    -Rechteinformation (Rechtefrei=1)
 *    -Datum-ID (die IDs sind entsprechend der Datumssortierung angelegt)
 *    -negierte Datum-ID (für eine umgekehrte Sortierung bei MySQL)
 *    -Satzbewertung-Score (z.B. aus den "Guten Beispielen")
 *
 * + concord_sentences.table
 *    -Korpus-ID
 *    -Dateinamen-ID
 *    -Position des Satzes im Text (die Sätze sind durchnummeriert)
 *    -der Satz (Token sind durch '\x01' und '\x02' getrennt, wobei '\x01'=ohne Leerzeichen und '\x02'=mit Leerzeichen)
 *    -Seitenangabe
 *
 * + mapping_TEI_textclass.table 
 *   -ID
 *   -Texstklasse
 *
 * + mapping_TEI_sigle.table 
 *   -ID
 *   -Sigle
 *
 * + mapping_TEI_orig.table 
 *   -ID
 *   -Bibl-String der Ersterscheinung
 *
 * + mapping_TEI_scan.table 
 *   -ID
 *   -Bibl-String der Vorliegenden Version
 * 
 * + mapping_TEI_date.table 
 *   -ID
 *   -Datum (DDC-Format)
 *
 * + mapping_TEI_avail.table 
 *   -ID
 *   -Rechte-String (OR,MR,...)
 *
 * + mapping_TEI.table -> Datei eines Korpus auf TEI-Informationen abbilden
 *   -Korpus-ID
 *   -Datei-ID
 *   -Orig-String
 *   -Scan-String
 *   -Textklasse-ID
 *   -Avail-ID
 *
 * + TEI_types.table (Attribute \t Value) (MySQL: teiTypes)
 *  Anzahl von Einträgen in den Tablellen:
 *  -DateSize (Datumsangeben)
 *  -TextclassSize (Textklassen)
 *  -OrigSize (Orig-Angabe)
 *  -ScanSize (Orig-Angabe)
 *  -SigleSize (Sigle)
 *  -sentenceSize (Sätze)
 *  -infoSize (Texttreffer)
 *  maximale Zeichenkettenlängen innerhalb der Tabellen:
 *  -lengthDate (Datum-String)
 *  -lengthTextclass (Textklassenname)
 *  -lengthOrig (Orig-String)
 *  -lengthScan (Scan-String)
 *  -lengthAvail (Rechte-String)
 *  -lengthSigle (Siglenname)

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

/**
 *
 * ID-TEI-Information zu einem Dokument
 *
 **/
struct TEIinfo
{
  ///das Erscheinungsdatum
	string strDate;
  ///die Textklassen-ID
	unsigned int iTextclass;
  ///ID für den Orig-Bibl-String
	unsigned int iOrig;
  ///ID für den Scan-Bibl-String
	unsigned int iScan;
  ///der Rechtezugriffsstatus
	unsigned int iAvail;
  ///ID für das Erscheinungsdatum
	unsigned int iDate;
  ///ID für die Sigle
	unsigned int iSigle;
};

/**
 *
 * String-TEI-Information zu einem Dokument
 *
 **/
struct TEIinfoStr
{
  ///Textklasse
	string m_strTextClass; 
  ///das Erscheinungsdatum
	string m_strDate; 
  ///Orig-Bibl-String
	string m_strOrig; 
  ///Scan-Bibl-String
	string m_strScan; 
  ///der Rechtezugriffsstatus
	string m_strAvail; 
  ///die Sigle
	string m_strSigle; 
};

bool bCompact=true;
string g_strTmpPath = "";
int g_iConcordCut;

/*map<string,InfoPath> g_mapPathOrig;
map<string,InfoPath> g_mapPathScan;
map<string,InfoPath> g_mapPathAvail;
map<string,InfoPath> g_mapPathDate;
map<string,InfoPath> g_mapPathText;
map<string,InfoPath> g_mapPathTextclass;
map<string,InfoPath> g_mapPathSigle;*/

map<string,string> g_mapDefaultOrig;
map<string,string> g_mapDefaultScan;
map<string,string> g_mapDefaultAvail;
map<string,string> g_mapDefaultDate;
map<string,string> g_mapDefaultTextclass;
map<string,string> g_mapDefaultSigle;

int g_iCounterMappingPosition=0;
int g_iCounterSentences=0;


hash_map<unsigned int,string> g_mapIdToFile;
hash_map<unsigned int,string>::iterator g_itMapIdToFile;
hash_map<string,unsigned int> g_mapFileToId;
hash_map<string,unsigned int>::iterator g_itMapFileToId;

map<unsigned int,unsigned int>::iterator itSetSentences;
map<unsigned int,unsigned int>::iterator itSetSentences2;

unsigned int g_iSentenceCounter(0);
unsigned int g_iTokenCounter(0);

string g_strRelationPath = "";
string g_strTablePath = "";
string g_strCorpusPath = "";

unsigned int iHighestSentence(0);

hash_map<unsigned int,string> g_mapCorpusToPath;
hash_map<unsigned int,string>::iterator g_itMapCorpusToPath;

map<string,BiblField>::iterator g_itMapCBiblField;
map<string,BiblField> g_mapCBiblField;

hash_map<HashPair,map<string,string>,PSHashPair,PSEqualToPair> g_mapBiblInfo;


map<string, BiblInfo> g_mapBibl;

map<string,string>::iterator g_itMapCorpusPath;
map<string,string> g_mapCorpusPath;

ReadSpecification g_CReadSpecification;


///Map für die TEI-Informationen zu einem Dokument
hash_map<unsigned int,TEIinfo> mapTEIinfo;

///Mapping für die Korpus-IDs
map<int,string> mapCorpus;
map<string,int> mapCorpusInv;

///Mapping für die Erscheinungsdatum-IDs
map<string,unsigned int> mapDate;
///Mapping für die Textklassen-IDs
map<string,unsigned int> mapTextclass;
///Mapping für die Orig-Bibl-String-IDs
map<string,unsigned int> mapOrig;
///Mapping für die Scan-Bibl-String-IDs
map<string,unsigned int> mapScan;
///Mapping für den Rechtezugriffstatus
map<string,unsigned int> mapAvail;
///Mapping für die Sigle-Id
map<string,unsigned int> mapSigle;

///Zähler für die ID-Nummerierung
unsigned int iDateCounter = 0;
unsigned int iTextclassCounter = 0;
unsigned int iOrigCounter = 0;
unsigned int iScanCounter = 0;
unsigned int iAvailCounter = 0;
unsigned int iSigleCounter = 0;


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
 * Einlesen der Spezifikationsdatei
 *
 */
void init_spec(const char* pcFile)
{
  g_CReadSpecification.parse_xml(pcFile);
  g_strRelationPath = g_CReadSpecification.relation_path();
  g_strTablePath = g_CReadSpecification.table_path();
  g_strCorpusPath = g_CReadSpecification.global_corpus_path();

  g_mapCorpusPath = g_CReadSpecification.corpus_path();

  g_mapCBiblField = g_CReadSpecification.bibl_fields();

  g_mapBibl = g_CReadSpecification.bibl_info();
  g_strTmpPath = g_CReadSpecification.tmp_path();
  g_iConcordCut = g_CReadSpecification.concord_cut(); 

}

/**
 *
 * Einlesen einer WP-Datei und extrahieren der Satzinformationen und schreiben der Informationen zusammen mit den TEI-Informationen
 *
 **/
bool process_wp(const string& strFilename, hash_set<unsigned int>& setSentences, ofstream& ofstreamSentences, unsigned int iFileId, unsigned int iCorpusId, const string& strCorpus)
{    
  unsigned int iTokens(0);
  unsigned int iSentenceCounter(0);
  string strCurrentPage="-";
  string strSentence="";
  bool bIgnore=false;
  bool bFirst=true;
  char str[100000];

  ifstream is;
  is.open((strFilename+".wp").c_str());
  if (!is)
  {
    char a[1000];
    sprintf(a,"): Datei existiert nicht: %s",(strFilename+".wp").c_str());
    cerr<<a<<endl;
    //exit(-1);
    return false;
  }

  while(is) 
  {
    is.getline(str, 100000);  // delim defaults to '\n'
    if(is) 
    {
      ReadTabInput CReadTabInput;
      int iMode = CReadTabInput.read_line(str);
      switch (iMode)
      {
        case 1:
        {
          break;
        }
        case 2:
        {
          if (bFirst)
          {
            bFirst=false;
          }
          else if (bIgnore)
          {
          }
          else
          {
            ///Schreiben der Satzinformation
				    ofstreamSentences<<iCorpusId;
            ofstreamSentences<<'\t';
            ofstreamSentences<<iFileId;
            ofstreamSentences<<'\t';
            ofstreamSentences<<iSentenceCounter;
            ofstreamSentences<<'\t';
            ofstreamSentences<<strSentence;
            ofstreamSentences<<'\t';
            ofstreamSentences<<strCurrentPage;
            ofstreamSentences<<'\n';
            
            g_iCounterSentences+=1;
          }

          strCurrentPage = CReadTabInput.get_field(2);

			    strSentence.clear();
          iTokens=0;
          ++iSentenceCounter;

          ///prüfen, ob der Satz eine Fundstelle hat
		      if (setSentences.find(iSentenceCounter)==setSentences.end()
              ///auch den Satz vor einer Fundstelle als Kontext einbeziehen
              && setSentences.find(iSentenceCounter-1)==setSentences.end()
              ///auch den Satz nach einer Fundstelle als Kontext einbeziehen
              && setSentences.find(iSentenceCounter+1)==setSentences.end())
		      {
            bIgnore=true;
		      }
		      else
		      {
		        bIgnore=false;
		      }
         
          break;
        }
        case 4:
        {
          string strSurface = CReadTabInput.get_field(2);

          ++iTokens;

				  if (strSentence.empty())
				  {
					  strSentence = strSurface;
				  }
				  else
				  {
					  strSentence += "\x02";
				    strSentence += strSurface;
				  }
 
         break;
        }
        case 5:
        {
          string strSurface = CReadTabInput.get_field(2);
          string strBlank = CReadTabInput.get_field(5);

          ++iTokens;

				  if (strSentence.empty())
				  {
					  strSentence = strSurface;
				  }
				  else
				  {
            if (strBlank == "1")
            {
  					  strSentence += "\x02";
            }
            else
            {
  					  strSentence += "\x01";
            }
				    strSentence += strSurface;
				  }
 
         break;
        }
        default:
        {
          cerr<<"): internal Error"<<endl;
        }        
      }
    }
  }

  if (bFirst)
  {
    bFirst=false;
  }
  else if (bIgnore)
  {
  }
  else
  {
    ///Schreiben der Satzinformation
    ofstreamSentences<<iCorpusId;
    ofstreamSentences<<'\t';
    ofstreamSentences<<iFileId;
    ofstreamSentences<<'\t';
    ofstreamSentences<<iSentenceCounter;
    ofstreamSentences<<'\t';
    ofstreamSentences<<strSentence;
    ofstreamSentences<<'\t';
    ofstreamSentences<<strCurrentPage;
    ofstreamSentences<<'\n';

    g_iCounterSentences+=1;
  }

  return true;
};


/**
 *
 * Schreiben der Texttrefferinformationen angereichert mit TEI-Informationen
 *
 */
void write_hits()
{    

  cout<<"(: sort mapping_position_info.table"<<endl;
  int i = system(("sort -T "+g_strTmpPath+" -n -s -k 6,6 -k 2,2 "+g_strTablePath+"/mapping_position_info.table > "+g_strTablePath+"/mapping_position_info_dummy.table").c_str());
  check_error(i);
  i = system(("mv "+g_strTablePath+"/mapping_position_info_dummy.table "+g_strTablePath+"/mapping_position_info.table").c_str());


  cout<<"(: collect positions"<<endl;
  
  string strInFile = g_strTablePath+"/mapping_position_info.table";
  ifstream streamIn(strInFile.c_str());

  ofstream streamHandler;

  unsigned int iHighestRelationnumber=0;

  bool bFirst=true;
  int iCurrentFile(0);
  int iCurrentCorpus(0);
	string strCurrentCorpus;
  char str[100000];


	hash_set<unsigned int> setSentences;

  hash_map<HashPair,unsigned int,PSHashPair,PSEqualToPair> mapFuncCounter;
  hash_map<HashPair,unsigned int,PSHashPair,PSEqualToPair>::iterator itMapFuncCounter;

  hash_map<HashTriple,unsigned int,PSHashTriple,PSEqualToTriple> mapFuncExactCounter;
  hash_map<HashTriple,unsigned int,PSHashTriple,PSEqualToTriple>::iterator itMapFuncExactCounter;

  string strCurrentFile="";

  hash_map<HashPair,map<string,string>,PSHashPair,PSEqualToPair>::iterator lt;
  map<string,string>::iterator mt;
  map<string,unsigned int>::iterator itTEI;

  map<unsigned int,unsigned int> mapGlobalCount;
	ofstream streamSentences((g_strTablePath+"/concord_sentences.table").c_str());

  string strCorpus;

  int iInsertCounter(0);

  string strOutputTEI = g_strTablePath+"/mapping_TEI.table";
  ofstream outputTEI(strOutputTEI.c_str());

  unsigned int iFileCounter(0);
  while (streamIn)
  {
    streamIn.getline(str, 100000);  // delim defaults to '\n'
    if(streamIn) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,8))
      {
        unsigned int iId = atoi(CReadTabInput.get_field(1));
        unsigned int iPos1 = atoi(CReadTabInput.get_field(2));
        unsigned int iPos2 = atoi(CReadTabInput.get_field(3));
        unsigned int iPrepPos = atoi(CReadTabInput.get_field(4));
        unsigned int iSent = atoi(CReadTabInput.get_field(5));
        unsigned int iFile = atoi(CReadTabInput.get_field(6));
        unsigned int iCorpus = atoi(CReadTabInput.get_field(7));
        unsigned int iAvail = atoi(CReadTabInput.get_field(8));

        unsigned int iIDPos1;
        unsigned int iIDPos2;
        unsigned int iIDPrepPos;      

        map<int,string>::iterator ct; 
        ct = mapCorpus.find(iCorpus);
        if (ct == mapCorpus.end())
        {
          continue;
        }
 
        if (bFirst)
        {
          iCurrentFile = iFile;
          iCurrentCorpus = iCorpus;

          strCorpus = mapCorpus[iCorpus];
					strCurrentCorpus = strCorpus;

					setSentences.clear();
	 				setSentences.insert(iSent);
          bFirst=false;
        }
        else if (iFile != iCurrentFile)
        {
          streamHandler.close();

					if (!setSentences.empty())
          {

            string strLocalPath = g_mapCorpusToPath[iCurrentCorpus];

		        string strDummyOut =g_strCorpusPath + strLocalPath + "/" + g_mapIdToFile[iCurrentFile]; 

		        TEIinfoStr CTEIinfoStr;
		        cout<<"(: process file: "<<iFile<<": "<<strDummyOut<<".wp"<<endl;
		        strCurrentFile=strDummyOut;
		        process_wp(strDummyOut, setSentences, streamSentences , iCurrentFile, iCurrentCorpus, strCurrentCorpus);

						unsigned int iIdDate;
						unsigned int iIdOrig;
						unsigned int iIdScan;
						unsigned int iIdAvail;
						unsigned int iIdTextclass;
						unsigned int iIdSigle;

            BiblField CBiblField;
            g_itMapCBiblField= g_mapCBiblField.find(strCurrentCorpus);
            if (g_itMapCBiblField == g_mapCBiblField.end())
            {
              cout<<"): fehlende bibl-field-Spezifikation"<<endl;
              exit(-1);
            }
            else
            {
              CBiblField = g_mapCBiblField[strCurrentCorpus];
            }

            lt = g_mapBiblInfo.find(HashPair(iCurrentCorpus,iCurrentFile));
            if (lt != g_mapBiblInfo.end())
            {
              mt = lt ->second.find(CBiblField.strOrig);
              if (mt != lt->second.end())
              {
                CTEIinfoStr.m_strOrig = mt->second;
              }
              else
              {
                CTEIinfoStr.m_strOrig = "";
              }              
              mt = lt ->second.find(CBiblField.strScan);
              if (mt != lt->second.end())
              {
                CTEIinfoStr.m_strScan = mt->second;
              }
              else
              {
                CTEIinfoStr.m_strScan = "";
              }              
              mt = lt ->second.find(CBiblField.strAvail);
              if (mt != lt->second.end())
              {
                CTEIinfoStr.m_strAvail = mt->second;
              }
              else
              {
                CTEIinfoStr.m_strAvail = "";
              }              
              mt = lt ->second.find(CBiblField.strDate);
              if (mt != lt->second.end())
              {
                CTEIinfoStr.m_strDate = mt->second;
              }
              else
              {
                CTEIinfoStr.m_strDate = "";
              }              
              mt = lt ->second.find(CBiblField.strTextclass);
              if (mt != lt->second.end())
              {
                CTEIinfoStr.m_strTextClass = mt->second;
              }
              else
              {
                CTEIinfoStr.m_strTextClass = "";
              }              
              mt = lt ->second.find(CBiblField.strSigle);
              if (mt != lt->second.end())
              {
                CTEIinfoStr.m_strSigle = mt->second;
              }
              else
              {
                CTEIinfoStr.m_strSigle = "";
              }              
            }
            else
            {
              cout<<"): missing:"<<strCurrentCorpus<<" "<<iCurrentCorpus<<" "<<iCurrentFile<<endl;
            }

						itTEI=mapDate.find(CTEIinfoStr.m_strDate);
						if (itTEI != mapDate.end())
						{
							iIdDate = itTEI->second;
						}
					  else
						{
							mapDate.insert(make_pair(CTEIinfoStr.m_strDate,iDateCounter));
							iIdDate = iDateCounter;
							++iDateCounter;
						}
						itTEI=mapTextclass.find(CTEIinfoStr.m_strTextClass);
						if (itTEI != mapTextclass.end())
						{
							iIdTextclass = itTEI->second;
						}
					  else
						{
							mapTextclass.insert(make_pair(CTEIinfoStr.m_strTextClass,iTextclassCounter));
							iIdTextclass=iTextclassCounter;
							++iTextclassCounter;
						}
						itTEI=mapOrig.find(CTEIinfoStr.m_strOrig);
						if (itTEI != mapOrig.end())
						{
							iIdOrig = itTEI->second;
						}
					  else
						{
							mapOrig.insert(make_pair(CTEIinfoStr.m_strOrig,iOrigCounter));
							iIdOrig=iOrigCounter;
							++iOrigCounter;
						}
						itTEI=mapScan.find(CTEIinfoStr.m_strScan);
						if (itTEI != mapScan.end())
						{
							iIdScan = itTEI->second;
						}
					  else
						{
							mapScan.insert(make_pair(CTEIinfoStr.m_strScan,iScanCounter));
							iIdScan=iScanCounter;
							++iScanCounter;
						}
						itTEI=mapAvail.find(CTEIinfoStr.m_strAvail);
						if (itTEI != mapAvail.end())
						{
							iIdAvail = itTEI->second;
						}
					  else
						{
							mapAvail.insert(make_pair(CTEIinfoStr.m_strAvail,iAvailCounter));
							iIdAvail=iAvailCounter;
							++iAvailCounter;
						}
						itTEI=mapSigle.find(CTEIinfoStr.m_strSigle);
						if (itTEI != mapSigle.end())
						{
							iIdSigle = itTEI->second;
						}
					  else
						{
							mapSigle.insert(make_pair(CTEIinfoStr.m_strSigle,iSigleCounter));
							iIdSigle=iSigleCounter;
							++iSigleCounter;
						}


						TEIinfo CTEIinfo;
						CTEIinfo.strDate = CTEIinfoStr.m_strDate;
            CTEIinfo.iDate = iIdDate;
						CTEIinfo.iTextclass = iIdTextclass;
						CTEIinfo.iOrig = iIdOrig;
						CTEIinfo.iScan = iIdScan;
						CTEIinfo.iAvail = iIdAvail;
						CTEIinfo.iSigle = iIdSigle;
            ++iInsertCounter;
						mapTEIinfo.insert(make_pair(iCurrentFile,CTEIinfo));

            outputTEI<<iCurrentCorpus<<"\t";
            outputTEI<<iCurrentFile<<"\t";
            outputTEI<<CTEIinfoStr.m_strOrig<<"\t";
            outputTEI<<CTEIinfoStr.m_strScan<<"\t";
            outputTEI<<iIdTextclass<<"\t";
            outputTEI<<CTEIinfo.iAvail<<"\t";
            outputTEI<<CTEIinfoStr.m_strSigle<<"\n";

					}

          iCurrentFile = iFile;          
          iCurrentCorpus = iCorpus;          
          strCorpus = mapCorpus[iCorpus];
					strCurrentCorpus = strCorpus;
					setSentences.clear();

	 				setSentences.insert(iSent);
        }
				else
		    { 
	 				setSentences.insert(iSent);
        }
      }
      }
      else
      {
          streamHandler.close();

					if (!setSentences.empty())
          {
            string strLocalPath = g_mapCorpusToPath[iCurrentCorpus];

		        string strDummyOut =g_strCorpusPath + strLocalPath + "/" + g_mapIdToFile[iCurrentFile]; 

		        TEIinfoStr CTEIinfoStr;
		        cout<<"(: process file final: "<<strDummyOut<<".wp"<<endl;
		        strCurrentFile=strDummyOut;

		        process_wp(strDummyOut, setSentences, streamSentences , iCurrentFile, iCurrentCorpus, strCurrentCorpus);


            BiblField CBiblField;
            g_itMapCBiblField= g_mapCBiblField.find(strCurrentCorpus);
            if (g_itMapCBiblField == g_mapCBiblField.end())
            {
              cout<<"): fehlende bibl-field-Spezifikation"<<endl;
              exit(-1);
            }
            else
            {
              CBiblField = g_mapCBiblField[strCurrentCorpus];
            }


            lt = g_mapBiblInfo.find(HashPair(iCurrentCorpus,iCurrentFile));
            if (lt != g_mapBiblInfo.end())
            {
              mt = lt ->second.find(CBiblField.strOrig);
              if (mt != lt->second.end())
              {
                CTEIinfoStr.m_strOrig = mt->second;
              }
              else
              {
                CTEIinfoStr.m_strOrig = "";
              }              
              mt = lt ->second.find(CBiblField.strScan);
              if (mt != lt->second.end())
              {
                CTEIinfoStr.m_strScan = mt->second;
              }
              else
              {
                CTEIinfoStr.m_strScan = "";
              }              
              mt = lt ->second.find(CBiblField.strAvail);
              if (mt != lt->second.end())
              {
                CTEIinfoStr.m_strAvail = mt->second;
              }
              else
              {
                CTEIinfoStr.m_strAvail = "";
              }              
              mt = lt ->second.find(CBiblField.strDate);
              if (mt != lt->second.end())
              {
                CTEIinfoStr.m_strDate = mt->second;
              }
              else
              {
                CTEIinfoStr.m_strDate = "";
              }              
              mt = lt ->second.find(CBiblField.strTextclass);
              if (mt != lt->second.end())
              {
                CTEIinfoStr.m_strTextClass = mt->second;
              }
              else
              {
                CTEIinfoStr.m_strTextClass = "";
              }              
              mt = lt ->second.find(CBiblField.strSigle);
              if (mt != lt->second.end())
              {
                CTEIinfoStr.m_strSigle = mt->second;
              }
              else
              {
                CTEIinfoStr.m_strSigle = "";
              }              
            }

						unsigned int iIdDate;
						unsigned int iIdOrig;
						unsigned int iIdScan;
						unsigned int iIdAvail;
						unsigned int iIdTextclass;
						unsigned int iIdSigle;

						itTEI=mapDate.find(CTEIinfoStr.m_strDate);
						if (itTEI != mapDate.end())
						{
							iIdDate = itTEI->second;
						}
					  else
						{
							mapDate.insert(make_pair(CTEIinfoStr.m_strDate,iDateCounter));
							iIdDate = iDateCounter;
							++iDateCounter;
						}
						itTEI=mapTextclass.find(CTEIinfoStr.m_strTextClass);
						if (itTEI != mapTextclass.end())
						{
							iIdTextclass = itTEI->second;
						}
					  else
						{
							mapTextclass.insert(make_pair(CTEIinfoStr.m_strTextClass,iTextclassCounter));
							++iTextclassCounter;
							iIdTextclass=iTextclassCounter;
						}
						itTEI=mapOrig.find(CTEIinfoStr.m_strOrig);
						if (itTEI != mapOrig.end())
						{
							iIdOrig = itTEI->second;
						}
					  else
						{
							mapOrig.insert(make_pair(CTEIinfoStr.m_strOrig,iOrigCounter));
							++iOrigCounter;
							iIdOrig=iOrigCounter;
						}
						itTEI=mapScan.find(CTEIinfoStr.m_strScan);
						if (itTEI != mapScan.end())
						{
							iIdScan = itTEI->second;
						}
					  else
						{
							mapScan.insert(make_pair(CTEIinfoStr.m_strScan,iScanCounter));
							++iScanCounter;
							iIdScan=iScanCounter;
						}
						itTEI=mapAvail.find(CTEIinfoStr.m_strAvail);
						if (itTEI != mapAvail.end())
						{
							iIdAvail = itTEI->second;
						}
					  else
						{
							mapAvail.insert(make_pair(CTEIinfoStr.m_strAvail,iAvailCounter));
							++iAvailCounter;
							iIdAvail=iAvailCounter;
						}
						itTEI=mapSigle.find(CTEIinfoStr.m_strSigle);
						if (itTEI != mapSigle.end())
						{
							iIdSigle = itTEI->second;
						}
					  else
						{
							mapSigle.insert(make_pair(CTEIinfoStr.m_strSigle,iSigleCounter));
							++iSigleCounter;
							iIdSigle=iSigleCounter;
						}

						TEIinfo CTEIinfo;
						CTEIinfo.strDate = CTEIinfoStr.m_strDate;
            CTEIinfo.iDate = iIdDate;
						CTEIinfo.iTextclass = iIdTextclass;
						CTEIinfo.iOrig = iIdOrig;
						CTEIinfo.iScan = iIdScan;
						CTEIinfo.iAvail = iIdAvail;
						CTEIinfo.iSigle = iIdSigle;
            ++iInsertCounter;
						mapTEIinfo.insert(make_pair(iCurrentFile,CTEIinfo));

            outputTEI<<iCurrentCorpus<<"\t";
            outputTEI<<iCurrentFile<<"\t";
            outputTEI<<CTEIinfoStr.m_strOrig<<"\t";
            outputTEI<<CTEIinfoStr.m_strScan<<"\t";
            outputTEI<<iIdTextclass<<"\t";
            outputTEI<<CTEIinfo.iAvail<<"\t";
            outputTEI<<CTEIinfoStr.m_strSigle<<"\n";

					}
  				setSentences.clear();
    }
  }    
	streamSentences.close();
  streamIn.close();

  outputTEI.close();
}

int main(int argc, char* argv[])
{
  if (argc != 2)
  {
    cerr<<"): falscher Parameteraufruf -> die XML-Specification angeben"<<endl; 
    exit(-1);
  }  

  cout<<" --- CREATE CONCORDANCES --- "<<endl;
  char str[100000];
  char strLong[1000000];
  unsigned int i;

  ///Spezifikation einlesen
	init_spec(argv[1]);  
  
  ///Einlesen der Korpusmapping
  string strInFile = g_strTablePath+"/mapping_corpus.table";
  ifstream streamIn(strInFile.c_str());
  while (streamIn)
  {
    streamIn.getline(str, 100000);  // delim defaults to '\n'
    if(streamIn) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,2))
      {
        unsigned int iId = atoi(CReadTabInput.get_field(1));
        const char* strCorpus = CReadTabInput.get_field(2);

        mapCorpus.insert(make_pair(iId,strCorpus));
        mapCorpusInv.insert(make_pair(strCorpus,iId));
      }
    }
  }
  streamIn.close();

  ///Mapping von Korpusnamen auf Korpuspfad
  for (g_itMapCorpusPath = g_mapCorpusPath.begin(); g_itMapCorpusPath != g_mapCorpusPath.end(); ++g_itMapCorpusPath)
  {
    map<string,int>::iterator ot;
    ot = mapCorpusInv.find(g_itMapCorpusPath->first);  
    if (ot != mapCorpusInv.end())
    {
      g_mapCorpusToPath.insert(make_pair(ot->second,g_itMapCorpusPath->second));
    }   
  }

  ///Mapping der Dateinamen
  strInFile = g_strTablePath+"/mapping_file.table";
  streamIn.open(strInFile.c_str());
  while (streamIn)
  {
    streamIn.getline(str, 100000);  // delim defaults to '\n'
    if(streamIn) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,2))
      {
        unsigned int iId = atoi(CReadTabInput.get_field(1));
        const char* strFile = CReadTabInput.get_field(2);

        g_mapIdToFile.insert(make_pair(iId,strFile));
        g_mapFileToId.insert(make_pair(strFile,iId));
      }
    }
  }
  streamIn.close();
 
  ///Mapping der Bibliographischen Informationen
  map<string, BiblInfo>::iterator bt;
  hash_map<HashPair,map<string,string>,PSHashPair,PSEqualToPair>::iterator lt;
  map<string,string>::iterator mt;
  for (bt=g_mapBibl.begin() ; bt != g_mapBibl.end(); ++bt)
  {
    streamIn.open(bt->second.strFile.c_str());
    while (streamIn)
    {
      streamIn.getline(str, 100000);  // delim defaults to '\n'
      if(streamIn) 
      {
        ReadTabInput CReadTabInput;
        if (CReadTabInput.read_line(str,3))
        {
          ///mapping auf Korpus-ID
          string strCorpus = bt->first;
          unsigned int iCorpus(0);
          map<string,int>::iterator ct; 
          ct = mapCorpusInv.find(strCorpus);
          if (ct != mapCorpusInv.end())
          {
            iCorpus = ct->second;
          }
          else
          {
            continue;
          }

          ///mapping auf Dokument-ID
          string strFile = CReadTabInput.get_field(1);
          unsigned int iFile(0);
          hash_map<string,unsigned int>::iterator ft; 
          ft = g_mapFileToId.find(strFile);
          if (ft != g_mapFileToId.end())
          {
            iFile = ft->second;
          }
          else
          {
            continue;
          }

          ///Bibliographische Information für ein Korpusdokument ablegen
          string strFeature = CReadTabInput.get_field(2);
          string strValue = CReadTabInput.get_field(3);
          lt = g_mapBiblInfo.find(HashPair(iCorpus,iFile));
          if (lt != g_mapBiblInfo.end())
          {
            mt = lt->second.find(strFeature);
            if (mt == lt->second.end())
            {
              lt->second.insert(make_pair(strFeature,strValue));
            }
          }
          else
          {
            map<string,string> mapDummy;
            mapDummy.insert(make_pair(strFeature,strValue));
            g_mapBiblInfo.insert(make_pair(HashPair(iCorpus,iFile),mapDummy));
          }

        }
      }
    }
    streamIn.close();    
  }

  ///schreiben der Treffer-Sätze
  write_hits();


  ///Berechnung einer Datum-ID-Zuweisung die Numerisch der Datumssortierung entspricht
  map<string,unsigned int>::iterator itTEI;
	hash_map<unsigned int,unsigned int> mapOrder;
	hash_map<unsigned int,unsigned int>::iterator itOrder;
  unsigned int iOrderCounter=0;
	for (itTEI = mapDate.begin(); itTEI != mapDate.end(); ++itTEI)
  {
		mapOrder.insert(make_pair(itTEI->second,iOrderCounter));
		itTEI->second = iOrderCounter;
    ++iOrderCounter;
  }
  hash_map<unsigned int,TEIinfo>::iterator ot;
  for (ot = mapTEIinfo.begin(); ot != mapTEIinfo.end(); ++ot)
  {
    itOrder = mapOrder.find(ot->second.iDate);
    if (itOrder != mapOrder.end())
    {
      ot->second.iDate = itOrder->second;
    }
  }

  ///Anreichern der Texttrefferinformationen mit TEI-Informationen
	cout<<"(: add TEI information"<<endl;
  ifstream inputPositionMapping((g_strTablePath+"/mapping_position_info_score.table").c_str());
  ofstream outputPositionMapping((g_strTablePath+"/mapping_position_info_tei.table").c_str());
  while(inputPositionMapping) 
  {
    inputPositionMapping.getline(str, 100000);  // delim defaults to '\n'
    if(inputPositionMapping) 
    {
      ReadTabInput CReadTabInput;
      if (CReadTabInput.read_line(str,9))
      {
        unsigned int iId = atoi(CReadTabInput.get_field(1));
        unsigned int iPos1 = atoi(CReadTabInput.get_field(2));
        unsigned int iPos2 = atoi(CReadTabInput.get_field(3));
        unsigned int iPrepPos = atoi(CReadTabInput.get_field(4));
        unsigned int iSent = atoi(CReadTabInput.get_field(5));
        unsigned int iFile = atoi(CReadTabInput.get_field(6));
        unsigned int iCorpus = atoi(CReadTabInput.get_field(7));
        unsigned int iAvail = atoi(CReadTabInput.get_field(8));
        int iScore = atoi(CReadTabInput.get_field(9));
        //unsigned int iCounter = atoi(CReadTabInput.get_field(10));

				ot = mapTEIinfo.find(iFile);
				if (ot != mapTEIinfo.end())
				{				
          ///Schreiben einer Trefferinformation
					outputPositionMapping<<iId<<'\t';
          outputPositionMapping<<iPos1<<'\t';
          outputPositionMapping<<iPos2<<'\t';
          outputPositionMapping<<iPrepPos<<'\t';
          outputPositionMapping<<iSent<<'\t';
          outputPositionMapping<<iFile<<'\t';
          outputPositionMapping<<iCorpus<<'\t';
          outputPositionMapping<<iAvail<<'\t';
          outputPositionMapping<<ot->second.iDate<<'\t';
          outputPositionMapping<<-((int)(ot->second.iDate))<<'\t';
          outputPositionMapping<<-((int)iScore)<<'\n';

          g_iCounterMappingPosition+=1;
				}
				else
				{
					cout<<"): interner Fehler: "<<iFile<<endl;
				}
      }
    }
  }
	outputPositionMapping.close();
  inputPositionMapping.close();
  
  unsigned int iLengthOrig(0);
  unsigned int iLengthScan(0);
  unsigned int iLengthAvail(0);
  unsigned int iLengthDate(0);
  unsigned int iLengthTextclass(0);
  unsigned int iLengthSigle(0);

  ///berechnen von maximalen String-Längen bezüglich der TEI-Informationen
  string strOutputOrigMapping = g_strTablePath+"/mapping_TEI_orig.table";
  ofstream outputOrigMapping(strOutputOrigMapping.c_str());
  for (itTEI = mapOrig.begin(); itTEI != mapOrig.end(); ++itTEI)
  {
    outputOrigMapping<<itTEI->second<<'\t'<<itTEI->first<<'\n';
    if (iLengthOrig<itTEI->first.length())
		{
      iLengthOrig = itTEI->first.length();
		}
  }
  string strOutputScanMapping = g_strTablePath+"/mapping_TEI_scan.table";
  ofstream outputScanMapping(strOutputScanMapping.c_str());
  for (itTEI = mapScan.begin(); itTEI != mapScan.end(); ++itTEI)
  {
    outputScanMapping<<itTEI->second<<'\t'<<itTEI->first<<'\n';
    if (iLengthScan<itTEI->first.length())
		{
      iLengthScan = itTEI->first.length();
		}
  }
  string strOutputAvailMapping = g_strTablePath+"/mapping_TEI_avail.table";
  ofstream outputAvailMapping(strOutputAvailMapping.c_str());
  for (itTEI = mapAvail.begin(); itTEI != mapAvail.end(); ++itTEI)
  {
    outputAvailMapping<<itTEI->second<<'\t'<<itTEI->first<<'\n';
    if (iLengthAvail<itTEI->first.length())
		{
      iLengthAvail = itTEI->first.length();
		}
  }
  string strOutputDateMapping = g_strTablePath+"/mapping_TEI_date.table";
  ofstream outputDateMapping(strOutputDateMapping.c_str());
  for (itTEI = mapDate.begin(); itTEI != mapDate.end(); ++itTEI)
  {
    outputDateMapping<<itTEI->second<<'\t'<<itTEI->first<<'\n';
    if (iLengthDate<itTEI->first.length())
		{
      iLengthDate = itTEI->first.length();
		}
  }
  string strOutputTexttypeMapping = g_strTablePath+"/mapping_TEI_textclass.table";
  ofstream outputTexttypeMapping(strOutputTexttypeMapping.c_str());
  for (itTEI = mapTextclass.begin(); itTEI != mapTextclass.end(); ++itTEI)
  {
    outputTexttypeMapping<<itTEI->second<<'\t'<<itTEI->first<<'\n';
    if (iLengthTextclass<itTEI->first.length())
		{
      iLengthTextclass = itTEI->first.length();
		}
  }
  string strOutputSigleMapping = g_strTablePath+"/mapping_TEI_sigle.table";
  ofstream outputSigleMapping(strOutputSigleMapping.c_str());
  for (itTEI = mapSigle.begin(); itTEI != mapSigle.end(); ++itTEI)
  {
    outputSigleMapping<<itTEI->second<<'\t'<<itTEI->first<<'\n';
    if (iLengthSigle<itTEI->first.length())
		{
      iLengthSigle = itTEI->first.length();
		}
  }
  outputDateMapping.close();
  outputOrigMapping.close();
  outputScanMapping.close();
  outputAvailMapping.close();
  outputTexttypeMapping.close();
  outputSigleMapping.close();

  ///Sortieren der TEI-Informationen nach Korpus und Dateiname
  cout<<"(: sort TEI"<<endl;
  i = system(("sort -T "+g_strTmpPath+" -n -s -k 1,1 -k 2,2 "+g_strTablePath+"/mapping_TEI.table > "+g_strTablePath+"/mapping_TEI.dummy.table").c_str());
  i = system(("mv "+g_strTablePath+"/mapping_TEI.dummy.table "+g_strTablePath+"/mapping_TEI.table").c_str());

  ///Schreiben der Typinformationen für die MySQL-Datenbank
  string strOutputTEItypes = g_strTablePath+"/TEI_types.table";
  ofstream outputTEItypes(strOutputTEItypes.c_str());
	outputTEItypes<<"DateSize\t"<<mapDate.size()<<'\n';
	outputTEItypes<<"TextclassSize\t"<<mapTextclass.size()<<'\n';
	outputTEItypes<<"OrigSize\t"<<mapOrig.size()<<'\n';
	outputTEItypes<<"ScanSize\t"<<mapScan.size()<<'\n';
	outputTEItypes<<"AvailSize\t"<<mapAvail.size()<<'\n';
	outputTEItypes<<"SigleSize\t"<<mapSigle.size()<<'\n';
	outputTEItypes<<"lengthDate\t"<<iLengthDate<<'\n';
	outputTEItypes<<"lengthTextclass\t"<<iLengthTextclass<<'\n';
	outputTEItypes<<"lengthOrig\t"<<iLengthOrig<<'\n';
	outputTEItypes<<"lengthScan\t"<<iLengthScan<<'\n';
	outputTEItypes<<"lengthAvail\t"<<iLengthAvail<<'\n';
	outputTEItypes<<"lengthSigle\t"<<iLengthSigle<<'\n';
	outputTEItypes<<"sentenceSize\t"<<g_iCounterSentences<<'\n';
	outputTEItypes<<"infoSize\t"<<g_iCounterMappingPosition<<'\n';
  outputTEItypes.close();

  ///Sortieren der TEI-angereicherten Trefferinformationen 
  cout<<"(: sort mapping_position_info_tei.table"<<endl;
  i = system(("sort -T "+g_strTmpPath+" -n -s -k 1,1 -k 10,10 -k 7,7 -k 9,9 "+g_strTablePath+"/mapping_position_info_tei.table > "+g_strTablePath+"/mapping_position_info_tei.dummy.table").c_str());
  check_error(i);
  i = system(("mv "+g_strTablePath+"/mapping_position_info_tei.dummy.table "+g_strTablePath+"/mapping_position_info_tei.table").c_str());
  check_error(i);

  cout<<"(: sort sentences"<<endl;
  i = system(("sort -T "+g_strTmpPath+" -n -s -k 1,1 -k 2,2 -k 3,3 "+g_strTablePath+"/concord_sentences.table > "+g_strTablePath+"/concord_sentences.dummy.table").c_str());
  check_error(i);
  i = system(("mv "+g_strTablePath+"/concord_sentences.dummy.table "+g_strTablePath+"/concord_sentences.table").c_str());
  check_error(i);


  ///Entfernen temporärer Dateien
  i = system(("rm "+g_strTablePath+"/mapping_position_info_score.table").c_str());
  check_error(i);
  i = system(("rm "+g_strTablePath+"/mapping_position_info.table").c_str());
  check_error(i);
  
}
