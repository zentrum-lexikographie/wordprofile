#ifndef TXTLexer_H_
#define TXTLexer_H_

#include "RE2CLexer.h" 
//#include "Normalization.h" 

enum Normalize
{
  NormalizeUpper = 0,
  NormalizeLower = 1,
  NormalizeCapitalize = 2,
  NormalizeNo = 3
};

enum LexerMode
{
  LexerModeLemma =0,
  LexerModeSurface =1,
  LexerModeLemSurf =2,
  LexerModeLemmatizer =3
};

namespace SynCoP
{
  class TXTLexer : public MyRE2CLexer<char> 
  {
    public:
        
      /**
      * @brief erstellen eines regelbasierten substringizers für einen ShallowParser
      * @param CShallowParser der entsprechende ShallowParser
      */
      TXTLexer()
      {
      };        
      /**
      * @brief einlesen und substringisieren des eingabe-streams
      * @param stream der eingabe-stream 
      * @param strFilename der dateiname fuer debuginformationen
      * @return true, wenn keine fehler auftraten
      */
      const string& parse_string(const char* strObj,const char* strObj2, const string& currentPOSOriginal, const string& currentPOS, LexerMode eLexerMode);      
      
    protected:
                  
      /**
      * @brief hinzufügen eines substrings mit einem bestimmten typ und einer bestimmten oberflächenform
      * @param strType der substringtyp
      * @param strSurface die oberflächenform
      * @param bNewline true, wenn eine neue zeile angefangen werden soll
      * @return der returnwert ist immer true
      */
      inline bool substring(const string& strSurface);
      /**
      * @brief überspringen eines substrings
      * @param bNewline true, wenn eine neue zeile angefangen werden soll
      * @return der returnwert ist immer true
      */
      inline bool substring();    
      /**
      * @brief mitteilen, wenn das ende des dokuments erreicht ist
      * @return der returnwert ist immer false
      */
      inline bool end();
      inline const string& YYPOS() const;
      inline const string& YYPOS_orig() const;
      inline const string& YYToken() const;
      inline const string& YYToken2() const;
      inline LexerMode YYMode() const;
      inline bool invalid();
      
   private:  
       
      /**
      * @brief regeln für die substringisierung mit der verwendung der methoden: substring(...), end(...) und block(...)
      * @return false, wenn das substringisieren gestoppt werden soll
      */
      bool substring_rules();
      /**
      * @brief das nächste substring bearbeiten
      * @return false, wenn das substringisieren gestoppt werden soll
      */
      inline bool yylex();      

      ///merken des zeichens nach einem entsprechendem substring (die substring vom lexer sind nicht 0-terminiert)
      char m_cRemember;
      ///merken der zeichenposition nach einem entsprechendem substring (die substring vom lexer sind nicht 0-terminiert)
      char* m_pcRemember;
      
      string strInputWord;
      string strInputWord2;
      string strCurrent;
      unsigned int iLength;
      string strCurrentPOS;
      string strCurrentPOSOriginal;
      LexerMode eLexerMode;
      bool bIsValid;
  };

  inline const string& TXTLexer::YYToken() const
  {
    return strInputWord;
  }
  inline const string& TXTLexer::YYToken2() const
  {
    return strInputWord2;
  }


  inline bool TXTLexer::invalid()
  {
    bIsValid=false;
    return false;
  }

  inline bool TXTLexer::yylex()
  {
    ///rückgängigmachen der terminierung des substring
    //*m_pcRemember = m_cRemember;
    ///setzen der aktuellen position im dokument   
    set_token(m_yycursor);    
    ///anwenden ter substringregeln
    return substring_rules();    
  } 
  
  inline bool TXTLexer::substring(const string& strSurface)
  {
    ///hinzufuegen des erkannten substrings
    strCurrent += strSurface;
    return true;
  }

  inline bool TXTLexer::substring()
  {
    ///setzen der substringlänge
    iLength=YYLeng();

    ///terminieren des flex-substrings und merken des zeichens und der position    
    /*m_pcRemember=&YYText()[iLength];
    m_cRemember=*m_pcRemember;
    *m_pcRemember='\0';*/

    ///hinzufuegen des erkannten substrings        
     strCurrent += YYText();      

    return true;
  }
    
  inline const string& TXTLexer::YYPOS() const
  {
    return strCurrentPOS;
  }

  inline const string& TXTLexer::YYPOS_orig() const
  {
    return strCurrentPOSOriginal;
  }
  
  inline LexerMode TXTLexer::YYMode() const
  {
    return eLexerMode;
  }


  inline bool TXTLexer::end()
  {
    return false;
  }
  
  const string& TXTLexer::parse_string(const char* strObj, const char* strObj2, const string& currentPOSOriginal, const string& currentPOS, LexerMode _eLexerMode)
  {
    strInputWord = strObj;
    strInputWord2 = strObj2;
    string strDummy = (string)"$<$" + strInputWord + (string)"$>$";
    stringstream stream(strDummy);
    bIsValid = true;
    eLexerMode = _eLexerMode;
    strCurrentPOS = currentPOS;
    strCurrentPOSOriginal = currentPOSOriginal;
    strCurrent.clear();
    ///prüfen ob der stream ok ist        
    if (!stream)
    {
      return strCurrent;
    }           
    ///setzen des streams für das substringisieren        
    switch_streams(&stream);
    
    set_yytext_null_terminated(true);
    
    iLength = 0;
  
    ///setzen des stringendepointer auf ein zeichen, damit der zugriff gültig bleibt
    m_pcRemember=&m_cRemember;
    
    ///substringisieren des textes
    while (yylex()){}
    
    if (!bIsValid)
    {
      strCurrent.clear();
    }
    else
    {
//if(YYMode() == LexerModeSurface && YYPOS() != "Substantiv")
 //   cout<<strCurrent<<endl;
      //strCurrent = strCurrent.substr(3,strCurrent.length()-6);
    }
    /*if (((string)strObj)=="deutsch/V#Land")
    {
     cout<<"hier:"<<strObj<<" .. "<<YYMode()<<" "<<strCurrent<<" "<<YYPOS()<<endl;

    }*/


    return strCurrent;
  }  
  
  
  #ifndef ShallowParser_H
  
  #undef YYCURSOR
  #undef YYCTYPE
  #undef YYLIMIT
  #undef YYMARKER
  #undef conversion
  #undef YYFILL
  #undef YYCTXMARKER  

  #define YYCTYPE unsigned char
  #define YYCURSOR m_yycursor
  #define YYLIMIT m_yylimit
  #define YYMARKER m_yymarker
  #define YYFILL m_yyfill
  #define conversion 1
  #define YYMARKER m_yymarker
  #define YYCTXMARKER m_yyctxmarker
    
  #include "LexerRules.h"
  
  #endif      
}

#endif /*ASCIILEXER_H_*/
