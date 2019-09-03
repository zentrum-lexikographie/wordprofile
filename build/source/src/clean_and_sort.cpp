/**
 * Programm zum Sortieren einzelner Tabellen für MySQL, um die Effizienz zu steigern.
 * Zudem werden Tabellen, die nicht mehr relevant sind gelöscht
 *
 **/

#include <iostream>
#include <vector>
#include <string.h>
#include <fstream>
#include <fstream>
#include <map>
#include <algorithm>

#include "hashes.h"
#include "read_specification.h"
#include "read_tab_input.h"

///verwendete Pfade
string g_strRelationPath = "";
string g_strTablePath = "";
string g_strTmpPath = "";
///hash-map fuer die corpus ID
hash_map<unsigned int,string> mapIdToCorpus;
///objekt zum einlesen der Specification
ReadSpecification g_CReadSpecification;

bool g_bUseSubcorpora;

///einlesen der Specification
void init_spec(const char* pcFile)
{
  g_CReadSpecification.parse_xml(pcFile);
  g_strRelationPath = g_CReadSpecification.relation_path();
  g_strTablePath = g_CReadSpecification.table_path();
  g_strTmpPath = g_CReadSpecification.tmp_path();
  g_bUseSubcorpora = g_CReadSpecification.use_subcorpora();
}

///eventuell einen Fehler werfen
void check_error(int iCode)
{
  if (iCode != 0)
  {
		exit(-1);
  }
}

///sortieren und bereinigen der Subcorpustabellen
void clean_and_sort_subcorpus()
{
  //if (mapIdToCorpus.size()>1)
  {
		hash_map<unsigned int,string>::iterator it;
		for (it = mapIdToCorpus.begin(); it != mapIdToCorpus.end(); ++it)
		{

      int i = system(("mv "+g_strTablePath+"/relations."+it->second+".optimized.table "+g_strTablePath+"/relations."+it->second+".table ").c_str());
      check_error(i);

      i = system(("sort -T "+g_strTmpPath+" -g -s -k 1,1 -k 3,3 -k 9,9 -k 13,13 "+g_strTablePath+"/relations."+it->second+".table > "+g_strTablePath+"/relations."+it->second+".sorted.table").c_str());
      check_error(i);
      i = system(("mv "+g_strTablePath+"/relations."+it->second+".sorted.table "+g_strTablePath+"/relations."+it->second+".table").c_str());
		  check_error(i);

			cout<<"(: sort head_pos_freq."+it->second+".table"<<endl;
			///sortieren frequency (head_pos_freq)"
			i = system(("sort -T "+g_strTmpPath+" -n -s -k 3,3 -r "+g_strTablePath+"/head_pos_freq."+it->second+".table > "+g_strTablePath+"/dummy1.table").c_str());
			check_error(i);
			///sortieren Head (head_pos_freq)"
			i = system(("sort -T "+g_strTmpPath+" -n -s -k 1,1 "+g_strTablePath+"/dummy1.table > "+g_strTablePath+"/head_pos_freq."+it->second+".table").c_str());
			check_error(i);
		  i = system(("rm "+g_strTablePath+"/dummy1.table").c_str());
		  check_error(i);

			cout<<"(: sort head_pos_rel_freq."+it->second+".table"<<endl;
			///sortieren frequency (head_pos_freq)"
			i = system(("sort -T "+g_strTmpPath+" -n -s -k 3,3 -r "+g_strTablePath+"/head_pos_rel_freq."+it->second+".table > "+g_strTablePath+"/dummy1.table").c_str());
			check_error(i);
			///sortieren Head (head_pos_freq)"
			i = system(("sort -T "+g_strTmpPath+" -n -s -k 1,1 "+g_strTablePath+"/dummy1.table > "+g_strTablePath+"/head_pos_rel_freq."+it->second+".table").c_str());
			check_error(i);
		  i = system(("rm "+g_strTablePath+"/dummy1.table").c_str());
		  check_error(i);
		}
  }
}

///sortieren und bereinigen der Corpustabellen
void clean_and_sort()
{
  int i;
  i = system(("rm "+g_strTablePath+"/*.freq.table").c_str());
  check_error(i);
  i = system(("rm "+g_strTablePath+"/*.relations.*").c_str());

  cout<<"(: remove tables"<<endl;
  i = system(("rm "+g_strTablePath+"/mapping_position.table").c_str());
  check_error(i);
  i = system(("rm "+g_strTablePath+"/mapping_info.table").c_str());
  check_error(i);
  i = system(("rm "+g_strTablePath+"/mapping_frequency.table").c_str());
  check_error(i);

  cout<<"(: rename tables"<<endl;
  i = system(("mv "+g_strTablePath+"/mapping_lemma.optimized.table "+g_strTablePath+"/mapping_lemma.table ").c_str());
  check_error(i);
  i = system(("mv "+g_strTablePath+"/mapping_surface.optimized.table "+g_strTablePath+"/mapping_surface.table ").c_str());
  check_error(i);
  i = system(("mv "+g_strTablePath+"/relations.optimized.table "+g_strTablePath+"/relations.table ").c_str());
  check_error(i);
  i = system(("mv "+g_strTablePath+"/mapping_file.optimized.table "+g_strTablePath+"/mapping_file.table ").c_str());
  check_error(i);
  
  cout<<"(: sort head_pos_freq.table"<<endl;
  ///sortieren frequency (head_pos_freq)
  i = system(("sort -T "+g_strTmpPath+" -n -s -k 3,3 -r "+g_strTablePath+"/head_pos_freq.table > "+g_strTablePath+"/dummy1.table").c_str());
  check_error(i);
  //echo "(: sortieren Head (head_pos_freq)
  i = system(("sort -T "+g_strTmpPath+" -n -s -k 1,1 "+g_strTablePath+"/dummy1.table > "+g_strTablePath+"/head_pos_freq.sorted.table").c_str());
  check_error(i);
  i = system(("mv "+g_strTablePath+"/head_pos_freq.sorted.table "+g_strTablePath+"/head_pos_freq.table").c_str());
  check_error(i);
  i = system(("rm "+g_strTablePath+"/dummy1.table").c_str());
  check_error(i);

  cout<<"(: sort head_pos_rel_freq.table"<<endl;
  ///sortieren frequency (head_pos_freq)
  i = system(("sort -T "+g_strTmpPath+" -n -s -k 3,3 -r "+g_strTablePath+"/head_pos_rel_freq.table > "+g_strTablePath+"/dummy1.table").c_str());
  check_error(i);
  ///sortieren Head (head_pos_freq)
  i = system(("sort -T "+g_strTmpPath+" -n -s -k 1,1 "+g_strTablePath+"/dummy1.table > "+g_strTablePath+"/head_pos_rel_freq.sorted.table").c_str());
  check_error(i);
  i = system(("mv "+g_strTablePath+"/head_pos_rel_freq.sorted.table "+g_strTablePath+"/head_pos_rel_freq.table").c_str());
  check_error(i);
  i = system(("rm "+g_strTablePath+"/dummy1.table").c_str());
  check_error(i);

  cout<<"(: sort relations.table"<<endl;
  ///sortieren nach FUNKTION
  ///sortieren nach w1
  ///sortieren nach POS
  ///sortieren nach frequenz
  i = system(("sort -T "+g_strTmpPath+" -g -s -k 1,1 -k 3,3 -k 9,9 -k 13,13 "+g_strTablePath+"/relations.table > "+g_strTablePath+"/relations.sorted.table").c_str());
  check_error(i);
  i = system(("mv "+g_strTablePath+"/relations.sorted.table "+g_strTablePath+"/relations.table").c_str());

  if (g_bUseSubcorpora)
  {
    clean_and_sort_subcorpus();
  }

  cout<<"(: sort mapping_position_info.table"<<endl;
  ///sortieren der Info
  i = system(("sort -T "+g_strTmpPath+" -n -s -k 1,1 "+g_strTablePath+"/mapping_position_info.table > "+g_strTablePath+"/mapping_position_info.sorted.table").c_str());
  check_error(i);
  i = system(("mv "+g_strTablePath+"/mapping_position_info.sorted.table "+g_strTablePath+"/mapping_position_info.table").c_str());
  check_error(i);

  cout<<"(: sort mapping_lemma.table"<<endl;
  ///sortieren der Lemma
  i = system(("sort -T "+g_strTmpPath+" -n -s -k 1,1 "+g_strTablePath+"/mapping_lemma.table > "+g_strTablePath+"/mapping_lemma.sorted.table").c_str());
  check_error(i);
  i = system(("mv "+g_strTablePath+"/mapping_lemma.sorted.table "+g_strTablePath+"/mapping_lemma.table").c_str());
  check_error(i);

  i = system(("sort -T "+g_strTmpPath+" -n -s -k 1,1 "+g_strTablePath+"/mapping_lemma_lower.table > "+g_strTablePath+"/mapping_lemma_lower.sorted.table").c_str());
  check_error(i);
  i = system(("mv "+g_strTablePath+"/mapping_lemma_lower.sorted.table "+g_strTablePath+"/mapping_lemma_lower.table").c_str());
  check_error(i);

  cout<<"(: sort mapping_surface.table"<<endl;
  ///sortieren der Surface
  i = system(("sort -T "+g_strTmpPath+" -n -s -k 1,1 "+g_strTablePath+"/mapping_surface.table > "+g_strTablePath+"/mapping_surface.sorted.table").c_str());
  check_error(i);
  i = system(("mv "+g_strTablePath+"/mapping_surface.sorted.table "+g_strTablePath+"/mapping_surface.table").c_str());
  check_error(i);

  cout<<"(: sort mapping_POS.table"<<endl;
  ///sortieren der POS
  i = system(("sort -T "+g_strTmpPath+" -n -s -k 1,1 "+g_strTablePath+"/mapping_POS.table > "+g_strTablePath+"/mapping_POS.sorted.table").c_str());
  check_error(i);
  i = system(("mv "+g_strTablePath+"/mapping_POS.sorted.table "+g_strTablePath+"/mapping_POS.table").c_str());
  check_error(i);

  cout<<"(: sort mapping_function.table"<<endl;
  ///sortieren der Function
  i = system(("sort -T "+g_strTmpPath+" -n -s -k 1,1 "+g_strTablePath+"/mapping_function.table > "+g_strTablePath+"/mapping_function.sorted.table").c_str());
  check_error(i);
  i = system(("mv "+g_strTablePath+"/mapping_function.sorted.table "+g_strTablePath+"/mapping_function.table").c_str());
  check_error(i);

  cout<<"(: sort mapping_file.table"<<endl;
  ///sortieren der File
  i = system(("sort -T "+g_strTmpPath+" -n -s -k 1,1 "+g_strTablePath+"/mapping_file.table > "+g_strTablePath+"/mapping_file.sorted.table").c_str());
  check_error(i);
  i = system(("mv "+g_strTablePath+"/mapping_file.sorted.table "+g_strTablePath+"/mapping_file.table").c_str());
  check_error(i);
};

int main(int argc, char* argv[])
{
  if (argc != 2)
  {
    cerr<<"): falscher Parameteraufruf -> die XML-Specification angeben"<<endl; 
    exit(-1);
  }  

  cout<<"|: SORT TABLES and CLEAN-UP"<<endl;

	init_spec(argv[1]);

  string strInputCorpusMapping = g_strTablePath+"/mapping_corpus.table";
  ifstream inputCorpusMapping(strInputCorpusMapping.c_str());

	///laden der Corpusinformationen
  char str[10000];
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
        mapIdToCorpus.insert(make_pair(iId,strName));
      }
    }
  }

	///sortieren und entfernen von Tabellen  
  clean_and_sort();
};

