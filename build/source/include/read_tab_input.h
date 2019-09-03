#ifndef READ_TAB_INPUT_H_
#define READ_TAB_INPUT_H_

/**
 * 
 * Klasse zum Einlesen einer TAB-separierten eingabe
 *
 **/
class ReadTabInput
{
  public:
  
    ReadTabInput()
    {
    }
    
    inline bool read_line(char* szObj, unsigned int iSize);
    inline unsigned int read_line(char* szObj);    
    inline const char* get_field(unsigned int iPos) const;
		inline unsigned int size() const;
    
  private:
    
    ///Vektor aus Zeichenketten für die Repräsentation einer TAB-separierten Zeile
    vector<char*> vpChar;  
};

/**
 * 
 * Zurückgeben der Anzahl der Felder
 *
 **/
inline unsigned int ReadTabInput::size() const
{
  return vpChar.size();
}

/**
 * 
 * Zurückgeben eines Feldes einer bestimmten Stelle
 *
 **/
inline const char* ReadTabInput::get_field(unsigned int iPos) const
{
  if ((iPos-1)>=0 && (iPos-1)<vpChar.size())
  {
    return vpChar[iPos-1];
  }
  else
  {
    return 0;
  }
}

/**
 * 
 * Eine Zeile bearbeiten, wobei die TAB-Anzahl vorgegeben ist
 *
 **/
inline bool ReadTabInput::read_line(char* szObj, unsigned int iSize)
{
  vpChar.clear();
  vpChar.push_back(szObj);

  char* pDummy(szObj);
  
  while (*pDummy != '\0')
  {
    if (*pDummy == '\t')
    {
      *pDummy = '\0';      
      vpChar.push_back(pDummy+1);
      if (vpChar.size() == iSize)
      {
        return true;
      }
    }      
    ++pDummy;
  }  
  if (vpChar.size() != iSize)
  {
    return false;
  }
  return true;
}

/**
 * 
 * Eine Zeile bearbeiten, wobei die TAB-Anzahl nicht vorgegeben ist
 *
 **/
inline unsigned int ReadTabInput::read_line(char* szObj)
{
  vpChar.clear();
  vpChar.push_back(szObj);

  char* pDummy(szObj);

  unsigned int iCounter(1);
  
  while (*pDummy != '\0')
  {
    if (*pDummy == '\t')
    {
      ++iCounter;
      *pDummy = '\0';      
      vpChar.push_back(pDummy+1);
    }      
    ++pDummy;
  }  
  return iCounter;
}


#endif /*READ_TAB_INPUT_H_*/
