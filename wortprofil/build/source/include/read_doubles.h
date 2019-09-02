/**
 * 
 * Klasse zum Einlesen der Dubletteninformationen (XML)
 *
 **/
class ReadDoubles
{
  public:
  
    ReadDoubles(hash_map<string,unsigned int>& mapCorpusnames,hash_map<string,unsigned int>& mapFilenames,hash_set<HashTriple,PSHashTriple,PSEqualToTriple>& setDoubles):
      m_setDoubles(setDoubles),
      m_mapFilenames(mapFilenames),
      m_mapCorpusnames(mapCorpusnames)
    {
    };
  
    string m_strLine;
		bool m_bLine;
    string m_strCurrentFile;
    bool m_bFirst;

    ///der expat-xml-parser
    XML_Parser p;

    bool parse_xml(const string& strFilename);

    static void start_hndl(void* data, const char* szName, const char** pAttribute);
    static void end_hndl(void* data, const char* szName);
    static void char_hndl(void* data, const char* szText, int iLen);

    hash_set<HashTriple,PSHashTriple,PSEqualToTriple>& m_setDoubles;
    hash_map<string,unsigned int>& m_mapFilenames;
    hash_map<string,unsigned int>& m_mapCorpusnames;
    
};

/**
 * 
 * Einlesen der XML-Datei
 *
 **/
bool ReadDoubles::parse_xml(const string& strFilename)
{    
  ///Datei öffnen
  ifstream is;
  is.open(strFilename.c_str());
  if (!is)
  {
    char a[1000];
    sprintf(a,"): Datei existiert nicht: %s",strFilename.c_str());
    cerr<<a<<endl;
    return false;
  }

  m_bLine=false;
  m_strCurrentFile=strFilename;

  unsigned int iBufferSize(1000000);
  char buffer[iBufferSize];

  ///XML-Parser erstellen
  p = XML_ParserCreate(NULL);

  if (!p)
  {
    return false;
  }
    
  XML_SetUserData(p,(void*)this);
  XML_UseParserAsHandlerArg(p);
  XML_SetElementHandler(p,start_hndl, end_hndl);
  XML_SetCharacterDataHandler(p,char_hndl);

  ///Parsen
  while (!is.eof())
  {
    is.read(buffer,iBufferSize);
    
    if (!XML_Parse(p, buffer,iBufferSize,is.eof()))
    {
       XML_ParserFree(p);
       return false;
    }
  }
  
  XML_ParserFree(p);

  return true;
};


/**
 * 
 * Starthandler
 *
 **/
void ReadDoubles::start_hndl(void* data, const char* szName, const char** pAttribute)
{
  string strName(szName);
  ReadDoubles* pThis = ((ReadDoubles*)XML_GetUserData((ReadDoubles*)data));

	if (!strName.compare("double"))
  {
    pThis->m_bFirst=true;
  }
	else if (!strName.compare("item"))
  {     
    if (pThis->m_bFirst)
    {
      pThis->m_bFirst=false;
      return;
    } 

    string strFile;
    string strCorpus;
    unsigned int iSentence;


    const char** pDummy (pAttribute);
    while (*pDummy != 0 && pDummy != 0)
    {
      string strAttribute(*pDummy);
      string strValue(*(++pDummy));
      if (strAttribute == "file")
      {
        strFile = strValue;
      }
      else if (strAttribute == "sentence")
      {
        iSentence = atoi(strValue.c_str());
      }
      else if (strAttribute == "corpus")
      {
        strCorpus = strValue;
      }
      else
      {
        cout<<"): Fehler bei den XML-Attributen"<<endl;
        return;
      }
      ++pDummy;
    }

    unsigned int iIdFile(0);
    unsigned int iIdCorpus(0);
    hash_map<string,unsigned int>::iterator it;
    it = pThis->m_mapFilenames.find(strFile);
    if (it != pThis->m_mapFilenames.end())
    {
      iIdFile = it->second;

      it = pThis->m_mapCorpusnames.find(strCorpus);
      if (it != pThis->m_mapCorpusnames.end())
      {
        iIdCorpus = it->second;
        pThis->m_setDoubles.insert(HashTriple(iIdCorpus,iIdFile,iSentence));
      }
    }

  }
	else
  {
  }
}

/**
 * 
 * Endhandler
 *
 **/
void ReadDoubles::end_hndl(void* data, const char* szName)
{
  string strName(szName);
  ReadDoubles* pThis = ((ReadDoubles*)XML_GetUserData((ReadDoubles*)data));

	if (!strName.compare("double"))
  {
  }
	else if (!strName.compare("item"))
  {
  }
	else
  {
  }
}

/**
 * 
 * Charhandler
 *
 **/
void ReadDoubles::char_hndl(void* data, const char* szText, int iLen)
{
}

