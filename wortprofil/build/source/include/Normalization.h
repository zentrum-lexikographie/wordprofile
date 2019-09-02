#ifndef NORMALIZATION_H_
#define NORMALIZATION_H_

//namespace SynCoP
//{
  /**
  * @brief Die Großbuchstaben innerhalb eines Strings werden zu Kleinbuchstaben transformiert
  * @param strObj der zu transformierende string
  */
  static string& normalize_to_lower_ref(string& strObj);
  static string normalize_to_lower(string strObj);
  /**
  * @brief Die Kleinbuchstaben innerhalb eines Strings werden zu Großbuchstaben transformiert
  * @param strObj der zu transformierende string
  */
  static string& normalize_to_upper_ref(string& strObj);
  static string normalize_to_upper(string strObj);
  /**
  * @brief Das erste Zeichen wird zu einem Großbuchstaben, der Rest zu Kleinbuchstaben
  * @param strObj der zu transformierende string
  */
  static string& normalize_capitalize_ref(string& strObj);
  static string normalize_capitalize(string strObj);
  /**
  * @brief Die Großbuchstaben innerhalb eines Strings werden innerhalb eines bestimten Bereichs zu Kleinbuchstaben transformiert
  * @param strObj der zu transformierende string
  * @param i Position, ab der die transformation beginnen soll 
  * @param j Position, ab der die transformation enden soll
  */
  static string& normalize_to_lower(string& strObj, size_t i, size_t j);
  /**
  * @brief Die Kleinbuchstaben innerhalb eines Strings werden  innerhalb eines bestimten Bereichs zu Großbuchstaben transformiert
  * @param strObj der zu transformierende string
  * @param i Position, ab der die transformation beginnen soll 
  * @param j Position, ab der die transformation enden soll
  */
  static string& normalize_to_upper(string& strObj, size_t i, size_t j);
  
  static string& normalize_to_lower_ref(string& strObj)
  {
    return normalize_to_lower(strObj, 0, strObj.size()-1);
  }
  
  static string& normalize_to_upper_ref(string& strObj)
  {
    return normalize_to_upper(strObj, 0, strObj.size()-1);
  }

  static string normalize_to_lower(string strObj)
  {
    return normalize_to_lower(strObj, 0, strObj.size()-1);
  }
  
  static string normalize_to_upper(string strObj)
  {
    return normalize_to_upper(strObj, 0, strObj.size()-1);
  }  
  static string& normalize_capitalize_ref(string& strObj)
  {
    if (!strObj.empty())
    {
      if (strObj[0]<128)
      {
        return normalize_to_lower(normalize_to_upper(strObj, 0, 1),1,strObj.size()-1);
      }
      else
      {
        return normalize_to_lower(normalize_to_upper(strObj, 0, 2),1,strObj.size()-1);
      }
    }
    else
    {
      return strObj;
    }
  }

  static string normalize_capitalize(string strObj)
  {
    if (!strObj.empty())
    {
      if (strObj[0]<128)
      {
        return normalize_to_lower(normalize_to_upper(strObj, 0, 1),1,strObj.size()-1);
      }
      else
      {
        return normalize_to_lower(normalize_to_upper(strObj, 0, 2),1,strObj.size()-1);
      }
    }
    else
    {
      return strObj;
    }
  }

  static string& normalize_to_lower(string& strObj, size_t i, size_t j)
  {
    if (strObj.length()==0)
    {
      return strObj;
    }
    for (; i < j; ++i)
    {
        switch(strObj[i])
        {
/* A -> a */ case (char)0x41: strObj[i] = 0x61; break;
/* B -> b */ case (char)0x42: strObj[i] = 0x62; break;
/* C -> c */ case (char)0x43: strObj[i] = 0x63; break;
/* D -> d */ case (char)0x44: strObj[i] = 0x64; break;
/* E -> e */ case (char)0x45: strObj[i] = 0x65; break;
/* F -> f */ case (char)0x46: strObj[i] = 0x66; break;
/* G -> g */ case (char)0x47: strObj[i] = 0x67; break;
/* H -> h */ case (char)0x48: strObj[i] = 0x68; break;
/* I -> i */ case (char)0x49: strObj[i] = 0x69; break;
/* J -> j */ case (char)0x4a: strObj[i] = 0x6a; break;
/* K -> k */ case (char)0x4b: strObj[i] = 0x6b; break;
/* L -> l */ case (char)0x4c: strObj[i] = 0x6c; break;
/* M -> m */ case (char)0x4d: strObj[i] = 0x6d; break;
/* N -> n */ case (char)0x4e: strObj[i] = 0x6e; break;
/* O -> o */ case (char)0x4f: strObj[i] = 0x6f; break;
/* P -> p */ case (char)0x50: strObj[i] = 0x70; break;
/* Q -> q */ case (char)0x51: strObj[i] = 0x71; break;
/* R -> r */ case (char)0x52: strObj[i] = 0x72; break;
/* S -> s */ case (char)0x53: strObj[i] = 0x73; break;
/* T -> t */ case (char)0x54: strObj[i] = 0x74; break;
/* U -> u */ case (char)0x55: strObj[i] = 0x75; break;
/* V -> v */ case (char)0x56: strObj[i] = 0x76; break;
/* W -> w */ case (char)0x57: strObj[i] = 0x77; break;
/* X -> x */ case (char)0x58: strObj[i] = 0x78; break;
/* Y -> y */ case (char)0x59: strObj[i] = 0x79; break;
/* Z -> z */ case (char)0x5a: strObj[i] = 0x7a; break;
             case (char)0xc3:
               switch(strObj[i+1])
               {
       /* À -> à */ case (char)0x80: strObj[i+1]=0xa0; ++i; break;
       /* Á -> á */ case (char)0x81: strObj[i+1]=0xa1; ++i; break;
       /* Â -> â */ case (char)0x82: strObj[i+1]=0xa2; ++i; break;
       /* Ã -> ã */ case (char)0x83: strObj[i+1]=0xa3; ++i; break;
       /* Ä -> ä */ case (char)0x84: strObj[i+1]=0xa4; ++i; break;
       /* Å -> å */ case (char)0x85: strObj[i+1]=0xa5; ++i; break;
       /* Æ -> æ */ case (char)0x86: strObj[i+1]=0xa6; ++i; break;
       /* Ç -> ç */ case (char)0x87: strObj[i+1]=0xa7; ++i; break;
       /* È -> è */ case (char)0x88: strObj[i+1]=0xa8; ++i; break;
       /* É -> é */ case (char)0x89: strObj[i+1]=0xa9; ++i; break;
       /* Ê -> ê */ case (char)0x8a: strObj[i+1]=0xaa; ++i; break;
       /* Ë -> ë */ case (char)0x8b: strObj[i+1]=0xab; ++i; break;
       /* Ì -> ì */ case (char)0x8c: strObj[i+1]=0xac; ++i; break;
       /* Í -> í */ case (char)0x8d: strObj[i+1]=0xad; ++i; break;
       /* Î -> î */ case (char)0x8e: strObj[i+1]=0xae; ++i; break;
       /* Ï -> ï */ case (char)0x8f: strObj[i+1]=0xaf; ++i; break;
       /* Ð -> ð */ case (char)0x90: strObj[i+1]=0xb0; ++i; break;
       /* Ñ -> ñ */ case (char)0x91: strObj[i+1]=0xb1; ++i; break;
       /* Ò -> ò */ case (char)0x92: strObj[i+1]=0xb2; ++i; break;
       /* Ó -> ó */ case (char)0x93: strObj[i+1]=0xb3; ++i; break;
       /* Ô -> ô */ case (char)0x94: strObj[i+1]=0xb4; ++i; break;
       /* Õ -> õ */ case (char)0x95: strObj[i+1]=0xb5; ++i; break;
       /* Ö -> ö */ case (char)0x96: strObj[i+1]=0xb6; ++i; break;
       /* Ø -> ø */ case (char)0x98: strObj[i+1]=0xb8; ++i; break;
       /* Ù -> ù */ case (char)0x99: strObj[i+1]=0xb9; ++i; break;
       /* Ú -> ú */ case (char)0x9a: strObj[i+1]=0xba; ++i; break;
       /* Û -> û */ case (char)0x9b: strObj[i+1]=0xbb; ++i; break;
       /* Ü -> ü */ case (char)0x9c: strObj[i+1]=0xbc; ++i; break;
       /* Ý -> ý */ case (char)0x9d: strObj[i+1]=0xbd; ++i; break;
       /* Þ -> þ */ case (char)0x9e: strObj[i+1]=0xbe; ++i; break;
               }
               break;
             case (char)0xc4:
               switch(strObj[i+1])
               {
       /* Ā -> ā */ case (char)0x80: strObj[i+1]=0x81; ++i; break;
       /* Ă -> ă */ case (char)0x82: strObj[i+1]=0x83; ++i; break;
       /* Ą -> ą */ case (char)0x84: strObj[i+1]=0x85; ++i; break;
       /* Ć -> ć */ case (char)0x86: strObj[i+1]=0x87; ++i; break;
       /* Ĉ -> ĉ */ case (char)0x88: strObj[i+1]=0x89; ++i; break;
       /* Ċ -> ċ */ case (char)0x8a: strObj[i+1]=0x8b; ++i; break;
       /* Č -> č */ case (char)0x8c: strObj[i+1]=0x8d; ++i; break;
       /* Ď -> ď */ case (char)0x8e: strObj[i+1]=0x8f; ++i; break;
       /* Đ -> đ */ case (char)0x90: strObj[i+1]=0x91; ++i; break;
       /* Ē -> ē */ case (char)0x92: strObj[i+1]=0x93; ++i; break;
       /* Ĕ -> ĕ */ case (char)0x94: strObj[i+1]=0x95; ++i; break;
       /* Ė -> ė */ case (char)0x96: strObj[i+1]=0x97; ++i; break;
       /* Ę -> ę */ case (char)0x98: strObj[i+1]=0x99; ++i; break;
       /* Ě -> ě */ case (char)0x9a: strObj[i+1]=0x9b; ++i; break;
       /* Ĝ -> ĝ */ case (char)0x9c: strObj[i+1]=0x9d; ++i; break;
       /* Ğ -> ğ */ case (char)0x9e: strObj[i+1]=0x9f; ++i; break;
       /* Ġ -> ġ */ case (char)0xa0: strObj[i+1]=0xa1; ++i; break;
       /* Ģ -> ģ */ case (char)0xa2: strObj[i+1]=0xa3; ++i; break;
       /* Ĥ -> ĥ */ case (char)0xa4: strObj[i+1]=0xa5; ++i; break;
       /* Ħ -> ħ */ case (char)0xa6: strObj[i+1]=0xa7; ++i; break;
       /* Ĩ -> ĩ */ case (char)0xa8: strObj[i+1]=0xa9; ++i; break;
       /* Ī -> ī */ case (char)0xaa: strObj[i+1]=0xab; ++i; break;
       /* Ĭ -> ĭ */ case (char)0xac: strObj[i+1]=0xad; ++i; break;
       /* Į -> į */ case (char)0xae: strObj[i+1]=0xaf; ++i; break;
       /* Ĳ -> ĳ */ case (char)0xb2: strObj[i+1]=0xb3; ++i; break;
       /* Ĵ -> ĵ */ case (char)0xb4: strObj[i+1]=0xb5; ++i; break;
       /* Ķ -> ķ */ case (char)0xb6: strObj[i+1]=0xb7; ++i; break;
       /* Ĺ -> ĺ */ case (char)0xb9: strObj[i+1]=0xba; ++i; break;
       /* Ļ -> ļ */ case (char)0xbb: strObj[i+1]=0xbc; ++i; break;
       /* Ľ -> ľ */ case (char)0xbd: strObj[i+1]=0xbe; ++i; break;
       /* Ŀ -> ŀ */ case (char)0xbf: strObj[i]=0xc5; strObj[i+1]=0x80; ++i; break;
               }
               break;
             case (char)0xc5:
               switch(strObj[i+1])
               {
       /* Ł -> ł */ case (char)0x81: strObj[i+1]=0x82; ++i; break;
       /* Ń -> ń */ case (char)0x83: strObj[i+1]=0x84; ++i; break;
       /* Ņ -> ņ */ case (char)0x85: strObj[i+1]=0x86; ++i; break;
       /* Ň -> ň */ case (char)0x87: strObj[i+1]=0x88; ++i; break;
       /* Ŋ -> ŋ */ case (char)0x8a: strObj[i+1]=0x8b; ++i; break;
       /* Ō -> ō */ case (char)0x8c: strObj[i+1]=0x8d; ++i; break;
       /* Ŏ -> ŏ */ case (char)0x8e: strObj[i+1]=0x8f; ++i; break;
       /* Ő -> ő */ case (char)0x90: strObj[i+1]=0x91; ++i; break;
       /* Œ -> œ */ case (char)0x92: strObj[i+1]=0x93; ++i; break;
       /* Ŕ -> ŕ */ case (char)0x94: strObj[i+1]=0x95; ++i; break;
       /* Ŗ -> ŗ */ case (char)0x96: strObj[i+1]=0x97; ++i; break;
       /* Ř -> ř */ case (char)0x98: strObj[i+1]=0x99; ++i; break;
       /* Ś -> ś */ case (char)0x9a: strObj[i+1]=0x9b; ++i; break;
       /* Ŝ -> ŝ */ case (char)0x9c: strObj[i+1]=0x9d; ++i; break;
       /* Ş -> ş */ case (char)0x9e: strObj[i+1]=0x9f; ++i; break;
       /* Š -> š */ case (char)0xa0: strObj[i+1]=0xa1; ++i; break;
       /* Ţ -> ţ */ case (char)0xa2: strObj[i+1]=0xa3; ++i; break;
       /* Ť -> ť */ case (char)0xa4: strObj[i+1]=0xa5; ++i; break;
       /* Ŧ -> ŧ */ case (char)0xa6: strObj[i+1]=0xa7; ++i; break;
       /* Ũ -> ũ */ case (char)0xa8: strObj[i+1]=0xa9; ++i; break;
       /* Ū -> ū */ case (char)0xaa: strObj[i+1]=0xab; ++i; break;
       /* Ŭ -> ŭ */ case (char)0xac: strObj[i+1]=0xad; ++i; break;
       /* Ů -> ů */ case (char)0xae: strObj[i+1]=0xaf; ++i; break;
       /* Ű -> ű */ case (char)0xb0: strObj[i+1]=0xb1; ++i; break;
       /* Ų -> ų */ case (char)0xb2: strObj[i+1]=0xb3; ++i; break;
       /* Ŵ -> ŵ */ case (char)0xb4: strObj[i+1]=0xb5; ++i; break;
       /* Ŷ -> ŷ */ case (char)0xb6: strObj[i+1]=0xb7; ++i; break;
       /* Ÿ -> ÿ */ case (char)0xb8: strObj[i]=0xc3; strObj[i+1]=0xbf; ++i; break;
       /* Ź -> ź */ case (char)0xb9: strObj[i+1]=0xba; ++i; break;
       /* Ż -> ż */ case (char)0xbb: strObj[i+1]=0xbc; ++i; break;
       /* Ž -> ž */ case (char)0xbd: strObj[i+1]=0xbe; ++i; break;
               }
               break;
             case (char)0xc6:
               switch(strObj[i+1])
               {
       /* Ɓ -> ɓ */ case (char)0x81: strObj[i]=0xc9; strObj[i+1]=0x93; ++i; break;
       /* Ƃ -> ƃ */ case (char)0x82: strObj[i+1]=0x83; ++i; break;
       /* Ƅ -> ƅ */ case (char)0x84: strObj[i+1]=0x85; ++i; break;
       /* Ɔ -> ɔ */ case (char)0x86: strObj[i]=0xc9; strObj[i+1]=0x94; ++i; break;
       /* Ƈ -> ƈ */ case (char)0x87: strObj[i+1]=0x88; ++i; break;
       /* Ɗ -> ɗ */ case (char)0x8a: strObj[i]=0xc9; strObj[i+1]=0x97; ++i; break;
       /* Ƌ -> ƌ */ case (char)0x8b: strObj[i+1]=0x8c; ++i; break;
       /* Ǝ -> ɘ */ case (char)0x8e: strObj[i]=0xc9; strObj[i+1]=0x98; ++i; break;
       /* Ə -> ə */ case (char)0x8f: strObj[i]=0xc9; strObj[i+1]=0x99; ++i; break;
       /* Ɛ -> ɛ */ case (char)0x90: strObj[i]=0xc9; strObj[i+1]=0x9b; ++i; break;
       /* Ƒ -> ƒ */ case (char)0x91: strObj[i+1]=0x92; ++i; break;
       /* Ɠ -> ɠ */ case (char)0x93: strObj[i]=0xc9; strObj[i+1]=0xa0; ++i; break;
       /* Ɣ -> ɣ */ case (char)0x94: strObj[i]=0xc9; strObj[i+1]=0xa3; ++i; break;
       /* Ɩ -> ɩ */ case (char)0x96: strObj[i]=0xc9; strObj[i+1]=0xa9; ++i; break;
       /* Ɨ -> ɨ */ case (char)0x97: strObj[i]=0xc9; strObj[i+1]=0xa8; ++i; break;
       /* Ƙ -> ƙ */ case (char)0x98: strObj[i+1]=0x99; ++i; break;
       /* Ɯ -> ɯ */ case (char)0x9c: strObj[i]=0xc9; strObj[i+1]=0xaf; ++i; break;
       /* Ɲ -> ɲ */ case (char)0x9d: strObj[i]=0xc9; strObj[i+1]=0xb2; ++i; break;
       /* Ơ -> ơ */ case (char)0xa0: strObj[i+1]=0xa1; ++i; break;
       /* Ƣ -> ƣ */ case (char)0xa2: strObj[i+1]=0xa3; ++i; break;
       /* Ƥ -> ƥ */ case (char)0xa4: strObj[i+1]=0xa5; ++i; break;
       /* Ƨ -> ƨ */ case (char)0xa7: strObj[i+1]=0xa8; ++i; break;
       /* Ʃ -> ʃ */ case (char)0xa9: strObj[i]=0xca; strObj[i+1]=0x83; ++i; break;
       /* Ƭ -> ƭ */ case (char)0xac: strObj[i+1]=0xad; ++i; break;
       /* Ʈ -> ʈ */ case (char)0xae: strObj[i]=0xca; strObj[i+1]=0x88; ++i; break;
       /* Ư -> ư */ case (char)0xaf: strObj[i+1]=0xb0; ++i; break;
       /* Ʊ -> ʊ */ case (char)0xb1: strObj[i]=0xca; strObj[i+1]=0x8a; ++i; break;
       /* Ʋ -> ʋ */ case (char)0xb2: strObj[i]=0xca; strObj[i+1]=0x8b; ++i; break;
       /* Ƴ -> ƴ */ case (char)0xb3: strObj[i+1]=0xb4; ++i; break;
       /* Ƶ -> ƶ */ case (char)0xb5: strObj[i+1]=0xb6; ++i; break;
       /* Ʒ -> ʒ */ case (char)0xb7: strObj[i]=0xca; strObj[i+1]=0x92; ++i; break;
       /* Ƹ -> ƹ */ case (char)0xb8: strObj[i+1]=0xb9; ++i; break;
       /* Ƽ -> ƽ */ case (char)0xbc: strObj[i+1]=0xbd; ++i; break;
               }
               break;
             case (char)0xc7:
               switch(strObj[i+1])
               {
       /* Ǆ -> ǆ */ case (char)0x84: strObj[i+1]=0x86; ++i; break;
       /* Ǉ -> ǉ */ case (char)0x87: strObj[i+1]=0x89; ++i; break;
       /* Ǌ -> ǌ */ case (char)0x8a: strObj[i+1]=0x8c; ++i; break;
       /* Ǎ -> ǎ */ case (char)0x8d: strObj[i+1]=0x8e; ++i; break;
       /* Ǐ -> ǐ */ case (char)0x8f: strObj[i+1]=0x90; ++i; break;
       /* Ǒ -> ǒ */ case (char)0x91: strObj[i+1]=0x92; ++i; break;
       /* Ǔ -> ǔ */ case (char)0x93: strObj[i+1]=0x94; ++i; break;
       /* Ǖ -> ǖ */ case (char)0x95: strObj[i+1]=0x96; ++i; break;
       /* Ǘ -> ǘ */ case (char)0x97: strObj[i+1]=0x98; ++i; break;
       /* Ǚ -> ǚ */ case (char)0x99: strObj[i+1]=0x9a; ++i; break;
       /* Ǜ -> ǜ */ case (char)0x9b: strObj[i+1]=0x9c; ++i; break;
       /* Ǟ -> ǟ */ case (char)0x9e: strObj[i+1]=0x9f; ++i; break;
       /* Ǡ -> ǡ */ case (char)0xa0: strObj[i+1]=0xa1; ++i; break;
       /* Ǣ -> ǣ */ case (char)0xa2: strObj[i+1]=0xa3; ++i; break;
       /* Ǥ -> ǥ */ case (char)0xa4: strObj[i+1]=0xa5; ++i; break;
       /* Ǧ -> ǧ */ case (char)0xa6: strObj[i+1]=0xa7; ++i; break;
       /* Ǩ -> ǩ */ case (char)0xa8: strObj[i+1]=0xa9; ++i; break;
       /* Ǫ -> ǫ */ case (char)0xaa: strObj[i+1]=0xab; ++i; break;
       /* Ǭ -> ǭ */ case (char)0xac: strObj[i+1]=0xad; ++i; break;
       /* Ǯ -> ǯ */ case (char)0xae: strObj[i+1]=0xaf; ++i; break;
       /* Ǳ -> ǳ */ case (char)0xb1: strObj[i+1]=0xb3; ++i; break;
       /* Ǵ -> ǵ */ case (char)0xb4: strObj[i+1]=0xb5; ++i; break;
       /* Ǹ -> ǹ */ case (char)0xb8: strObj[i+1]=0xb9; ++i; break;
       /* Ǻ -> ǻ */ case (char)0xba: strObj[i+1]=0xbb; ++i; break;
       /* Ǽ -> ǽ */ case (char)0xbc: strObj[i+1]=0xbd; ++i; break;
       /* Ǿ -> ǿ */ case (char)0xbe: strObj[i+1]=0xbf; ++i; break;
               }
               break;
             case (char)0xc8:
               switch(strObj[i+1])
               {
       /* Ȁ -> ȁ */ case (char)0x80: strObj[i+1]=0x81; ++i; break;
       /* Ȃ -> ȃ */ case (char)0x82: strObj[i+1]=0x83; ++i; break;
       /* Ȅ -> ȅ */ case (char)0x84: strObj[i+1]=0x85; ++i; break;
       /* Ȇ -> ȇ */ case (char)0x86: strObj[i+1]=0x87; ++i; break;
       /* Ȉ -> ȉ */ case (char)0x88: strObj[i+1]=0x89; ++i; break;
       /* Ȋ -> ȋ */ case (char)0x8a: strObj[i+1]=0x8b; ++i; break;
       /* Ȍ -> ȍ */ case (char)0x8c: strObj[i+1]=0x8d; ++i; break;
       /* Ȏ -> ȏ */ case (char)0x8e: strObj[i+1]=0x8f; ++i; break;
       /* Ȑ -> ȑ */ case (char)0x90: strObj[i+1]=0x91; ++i; break;
       /* Ȓ -> ȓ */ case (char)0x92: strObj[i+1]=0x93; ++i; break;
       /* Ȕ -> ȕ */ case (char)0x94: strObj[i+1]=0x95; ++i; break;
       /* Ȗ -> ȗ */ case (char)0x96: strObj[i+1]=0x97; ++i; break;
       /* Ș -> ș */ case (char)0x98: strObj[i+1]=0x99; ++i; break;
       /* Ț -> ț */ case (char)0x9a: strObj[i+1]=0x9b; ++i; break;
       /* Ȝ -> ȝ */ case (char)0x9c: strObj[i+1]=0x9d; ++i; break;
       /* Ȟ -> ȟ */ case (char)0x9e: strObj[i+1]=0x9f; ++i; break;
       /* Ƞ -> ƞ */ case (char)0xa0: strObj[i]=0xc6; strObj[i+1]=0x9e; ++i; break;
       /* Ȣ -> ȣ */ case (char)0xa2: strObj[i+1]=0xa3; ++i; break;
       /* Ȥ -> ȥ */ case (char)0xa4: strObj[i+1]=0xa5; ++i; break;
       /* Ȧ -> ȧ */ case (char)0xa6: strObj[i+1]=0xa7; ++i; break;
       /* Ȩ -> ȩ */ case (char)0xa8: strObj[i+1]=0xa9; ++i; break;
       /* Ȫ -> ȫ */ case (char)0xaa: strObj[i+1]=0xab; ++i; break;
       /* Ȭ -> ȭ */ case (char)0xac: strObj[i+1]=0xad; ++i; break;
       /* Ȯ -> ȯ */ case (char)0xae: strObj[i+1]=0xaf; ++i; break;
       /* Ȱ -> ȱ */ case (char)0xb0: strObj[i+1]=0xb1; ++i; break;
       /* Ȳ -> ȳ */ case (char)0xb2: strObj[i+1]=0xb3; ++i; break;
       /* Ȼ -> ȼ */ case (char)0xbb: strObj[i+1]=0xbc; ++i; break;
       /* Ƚ -> ƚ */ case (char)0xbd: strObj[i]=0xc6; strObj[i+1]=0x9a; ++i; break;
               }
               break;
             case (char)0xc9:
               switch(strObj[i+1])
               {
       /* Ɂ -> ɂ */ case (char)0x81: strObj[i+1]=0x82; ++i; break;
       /* Ƀ -> ƀ */ case (char)0x83: strObj[i]=0xc6; strObj[i+1]=0x80; ++i; break;
       /* Ʉ -> ʉ */ case (char)0x84: strObj[i]=0xca; strObj[i+1]=0x89; ++i; break;
       /* Ʌ -> ʌ */ case (char)0x85: strObj[i]=0xca; strObj[i+1]=0x8c; ++i; break;
       /* Ɇ -> ɇ */ case (char)0x86: strObj[i+1]=0x87; ++i; break;
       /* Ɉ -> ɉ */ case (char)0x88: strObj[i+1]=0x89; ++i; break;
       /* Ɍ -> ɍ */ case (char)0x8c: strObj[i+1]=0x8d; ++i; break;
       /* Ɏ -> ɏ */ case (char)0x8e: strObj[i+1]=0x8f; ++i; break;
               }
               break;
             case (char)0xcd:
               switch(strObj[i+1])
               {
       /* Ͱ -> ͱ */ case (char)0xb0: strObj[i+1]=0xb1; ++i; break;
       /* Ͳ -> ͳ */ case (char)0xb2: strObj[i+1]=0xb3; ++i; break;
       /* Ͷ -> ͷ */ case (char)0xb6: strObj[i+1]=0xb7; ++i; break;
               }
               break;
             case (char)0xce:
               switch(strObj[i+1])
               {
       /* Ά -> ά */ case (char)0x86: strObj[i+1]=0xac; ++i; break;
       /* Έ -> έ */ case (char)0x88: strObj[i+1]=0xad; ++i; break;
       /* Ή -> ή */ case (char)0x89: strObj[i+1]=0xae; ++i; break;
       /* Ί -> ί */ case (char)0x8a: strObj[i+1]=0xaf; ++i; break;
       /* Ό -> ό */ case (char)0x8c: strObj[i]=0xcf; strObj[i+1]=0x8c; ++i; break;
       /* Ύ -> ύ */ case (char)0x8e: strObj[i]=0xcf; strObj[i+1]=0x8d; ++i; break;
       /* Ώ -> ώ */ case (char)0x8f: strObj[i]=0xcf; strObj[i+1]=0x8e; ++i; break;
       /* Α -> α */ case (char)0x91: strObj[i+1]=0xb1; ++i; break;
       /* Β -> β */ case (char)0x92: strObj[i+1]=0xb2; ++i; break;
       /* Γ -> γ */ case (char)0x93: strObj[i+1]=0xb3; ++i; break;
       /* Δ -> δ */ case (char)0x94: strObj[i+1]=0xb4; ++i; break;
       /* Ε -> ε */ case (char)0x95: strObj[i+1]=0xb5; ++i; break;
       /* Ζ -> ζ */ case (char)0x96: strObj[i+1]=0xb6; ++i; break;
       /* Η -> η */ case (char)0x97: strObj[i+1]=0xb7; ++i; break;
       /* Θ -> θ */ case (char)0x98: strObj[i+1]=0xb8; ++i; break;
       /* Ι -> ι */ case (char)0x99: strObj[i+1]=0xb9; ++i; break;
       /* Κ -> κ */ case (char)0x9a: strObj[i+1]=0xba; ++i; break;
       /* Λ -> λ */ case (char)0x9b: strObj[i+1]=0xbb; ++i; break;
       /* Μ -> μ */ case (char)0x9c: strObj[i+1]=0xbc; ++i; break;
       /* Ν -> ν */ case (char)0x9d: strObj[i+1]=0xbd; ++i; break;
       /* Ξ -> ξ */ case (char)0x9e: strObj[i+1]=0xbe; ++i; break;
       /* Ο -> ο */ case (char)0x9f: strObj[i+1]=0xbf; ++i; break;
       /* Π -> π */ case (char)0xa0: strObj[i]=0xcf; strObj[i+1]=0x80; ++i; break;
       /* Ρ -> ρ */ case (char)0xa1: strObj[i]=0xcf; strObj[i+1]=0x81; ++i; break;
       /* Σ -> σ */ case (char)0xa3: strObj[i]=0xcf; strObj[i+1]=0x83; ++i; break;
       /* Τ -> τ */ case (char)0xa4: strObj[i]=0xcf; strObj[i+1]=0x84; ++i; break;
       /* Υ -> υ */ case (char)0xa5: strObj[i]=0xcf; strObj[i+1]=0x85; ++i; break;
       /* Φ -> φ */ case (char)0xa6: strObj[i]=0xcf; strObj[i+1]=0x86; ++i; break;
       /* Χ -> χ */ case (char)0xa7: strObj[i]=0xcf; strObj[i+1]=0x87; ++i; break;
       /* Ψ -> ψ */ case (char)0xa8: strObj[i]=0xcf; strObj[i+1]=0x88; ++i; break;
       /* Ω -> ω */ case (char)0xa9: strObj[i]=0xcf; strObj[i+1]=0x89; ++i; break;
       /* Ϊ -> ϊ */ case (char)0xaa: strObj[i]=0xcf; strObj[i+1]=0x8a; ++i; break;
       /* Ϋ -> ϋ */ case (char)0xab: strObj[i]=0xcf; strObj[i+1]=0x8b; ++i; break;
               }
               break;
             case (char)0xcf:
               switch(strObj[i+1])
               {
       /* Ϣ -> ϣ */ case (char)0xa2: strObj[i+1]=0xa3; ++i; break;
       /* Ϥ -> ϥ */ case (char)0xa4: strObj[i+1]=0xa5; ++i; break;
       /* Ϧ -> ϧ */ case (char)0xa6: strObj[i+1]=0xa7; ++i; break;
       /* Ϩ -> ϩ */ case (char)0xa8: strObj[i+1]=0xa9; ++i; break;
       /* Ϫ -> ϫ */ case (char)0xaa: strObj[i+1]=0xab; ++i; break;
       /* Ϭ -> ϭ */ case (char)0xac: strObj[i+1]=0xad; ++i; break;
       /* Ϯ -> ϯ */ case (char)0xae: strObj[i+1]=0xaf; ++i; break;
       /* Ϸ -> ϸ */ case (char)0xb7: strObj[i+1]=0xb8; ++i; break;
       /* Ϻ -> ϻ */ case (char)0xba: strObj[i+1]=0xbb; ++i; break;
       /* Ͻ -> ͻ */ case (char)0xbd: strObj[i]=0xcd; strObj[i+1]=0xbb; ++i; break;
       /* Ͼ -> ͼ */ case (char)0xbe: strObj[i]=0xcd; strObj[i+1]=0xbc; ++i; break;
       /* Ͽ -> ͽ */ case (char)0xbf: strObj[i]=0xcd; strObj[i+1]=0xbd; ++i; break;
               }
               break;
             case (char)0xd0:
               switch(strObj[i+1])
               {
       /* Ѐ -> ѐ */ case (char)0x80: strObj[i]=0xd1; strObj[i+1]=0x90; ++i; break;
       /* Ё -> ё */ case (char)0x81: strObj[i]=0xd1; strObj[i+1]=0x91; ++i; break;
       /* Ђ -> ђ */ case (char)0x82: strObj[i]=0xd1; strObj[i+1]=0x92; ++i; break;
       /* Ѓ -> ѓ */ case (char)0x83: strObj[i]=0xd1; strObj[i+1]=0x93; ++i; break;
       /* Є -> є */ case (char)0x84: strObj[i]=0xd1; strObj[i+1]=0x94; ++i; break;
       /* Ѕ -> ѕ */ case (char)0x85: strObj[i]=0xd1; strObj[i+1]=0x95; ++i; break;
       /* І -> і */ case (char)0x86: strObj[i]=0xd1; strObj[i+1]=0x96; ++i; break;
       /* Ї -> ї */ case (char)0x87: strObj[i]=0xd1; strObj[i+1]=0x97; ++i; break;
       /* Ј -> ј */ case (char)0x88: strObj[i]=0xd1; strObj[i+1]=0x98; ++i; break;
       /* Љ -> љ */ case (char)0x89: strObj[i]=0xd1; strObj[i+1]=0x99; ++i; break;
       /* Њ -> њ */ case (char)0x8a: strObj[i]=0xd1; strObj[i+1]=0x9a; ++i; break;
       /* Ћ -> ћ */ case (char)0x8b: strObj[i]=0xd1; strObj[i+1]=0x9b; ++i; break;
       /* Ќ -> ќ */ case (char)0x8c: strObj[i]=0xd1; strObj[i+1]=0x9c; ++i; break;
       /* Ѝ -> ѝ */ case (char)0x8d: strObj[i]=0xd1; strObj[i+1]=0x9d; ++i; break;
       /* Ў -> ў */ case (char)0x8e: strObj[i]=0xd1; strObj[i+1]=0x9e; ++i; break;
       /* Џ -> џ */ case (char)0x8f: strObj[i]=0xd1; strObj[i+1]=0x9f; ++i; break;
       /* А -> а */ case (char)0x90: strObj[i+1]=0xb0; ++i; break;
       /* Б -> б */ case (char)0x91: strObj[i+1]=0xb1; ++i; break;
       /* В -> в */ case (char)0x92: strObj[i+1]=0xb2; ++i; break;
       /* Г -> г */ case (char)0x93: strObj[i+1]=0xb3; ++i; break;
       /* Д -> д */ case (char)0x94: strObj[i+1]=0xb4; ++i; break;
       /* Е -> е */ case (char)0x95: strObj[i+1]=0xb5; ++i; break;
       /* Ж -> ж */ case (char)0x96: strObj[i+1]=0xb6; ++i; break;
       /* З -> з */ case (char)0x97: strObj[i+1]=0xb7; ++i; break;
       /* И -> и */ case (char)0x98: strObj[i+1]=0xb8; ++i; break;
       /* Й -> й */ case (char)0x99: strObj[i+1]=0xb9; ++i; break;
       /* К -> к */ case (char)0x9a: strObj[i+1]=0xba; ++i; break;
       /* Л -> л */ case (char)0x9b: strObj[i+1]=0xbb; ++i; break;
       /* М -> м */ case (char)0x9c: strObj[i+1]=0xbc; ++i; break;
       /* Н -> н */ case (char)0x9d: strObj[i+1]=0xbd; ++i; break;
       /* О -> о */ case (char)0x9e: strObj[i+1]=0xbe; ++i; break;
       /* П -> п */ case (char)0x9f: strObj[i+1]=0xbf; ++i; break;
       /* Р -> р */ case (char)0xa0: strObj[i]=0xd1; strObj[i+1]=0x80; ++i; break;
       /* С -> с */ case (char)0xa1: strObj[i]=0xd1; strObj[i+1]=0x81; ++i; break;
       /* Т -> т */ case (char)0xa2: strObj[i]=0xd1; strObj[i+1]=0x82; ++i; break;
       /* У -> у */ case (char)0xa3: strObj[i]=0xd1; strObj[i+1]=0x83; ++i; break;
       /* Ф -> ф */ case (char)0xa4: strObj[i]=0xd1; strObj[i+1]=0x84; ++i; break;
       /* Х -> х */ case (char)0xa5: strObj[i]=0xd1; strObj[i+1]=0x85; ++i; break;
       /* Ц -> ц */ case (char)0xa6: strObj[i]=0xd1; strObj[i+1]=0x86; ++i; break;
       /* Ч -> ч */ case (char)0xa7: strObj[i]=0xd1; strObj[i+1]=0x87; ++i; break;
       /* Ш -> ш */ case (char)0xa8: strObj[i]=0xd1; strObj[i+1]=0x88; ++i; break;
       /* Щ -> щ */ case (char)0xa9: strObj[i]=0xd1; strObj[i+1]=0x89; ++i; break;
       /* Ъ -> ъ */ case (char)0xaa: strObj[i]=0xd1; strObj[i+1]=0x8a; ++i; break;
       /* Ы -> ы */ case (char)0xab: strObj[i]=0xd1; strObj[i+1]=0x8b; ++i; break;
       /* Ь -> ь */ case (char)0xac: strObj[i]=0xd1; strObj[i+1]=0x8c; ++i; break;
       /* Э -> э */ case (char)0xad: strObj[i]=0xd1; strObj[i+1]=0x8d; ++i; break;
       /* Ю -> ю */ case (char)0xae: strObj[i]=0xd1; strObj[i+1]=0x8e; ++i; break;
       /* Я -> я */ case (char)0xaf: strObj[i]=0xd1; strObj[i+1]=0x8f; ++i; break;
               }
               break;
             case (char)0xd1:
               switch(strObj[i+1])
               {
       /* Ѡ -> ѡ */ case (char)0xa0: strObj[i+1]=0xa1; ++i; break;
       /* Ѣ -> ѣ */ case (char)0xa2: strObj[i+1]=0xa3; ++i; break;
       /* Ѥ -> ѥ */ case (char)0xa4: strObj[i+1]=0xa5; ++i; break;
       /* Ѧ -> ѧ */ case (char)0xa6: strObj[i+1]=0xa7; ++i; break;
       /* Ѩ -> ѩ */ case (char)0xa8: strObj[i+1]=0xa9; ++i; break;
       /* Ѫ -> ѫ */ case (char)0xaa: strObj[i+1]=0xab; ++i; break;
       /* Ѭ -> ѭ */ case (char)0xac: strObj[i+1]=0xad; ++i; break;
       /* Ѯ -> ѯ */ case (char)0xae: strObj[i+1]=0xaf; ++i; break;
       /* Ѱ -> ѱ */ case (char)0xb0: strObj[i+1]=0xb1; ++i; break;
       /* Ѳ -> ѳ */ case (char)0xb2: strObj[i+1]=0xb3; ++i; break;
       /* Ѵ -> ѵ */ case (char)0xb4: strObj[i+1]=0xb5; ++i; break;
       /* Ѷ -> ѷ */ case (char)0xb6: strObj[i+1]=0xb7; ++i; break;
       /* Ѹ -> ѹ */ case (char)0xb8: strObj[i+1]=0xb9; ++i; break;
       /* Ѻ -> ѻ */ case (char)0xba: strObj[i+1]=0xbb; ++i; break;
       /* Ѽ -> ѽ */ case (char)0xbc: strObj[i+1]=0xbd; ++i; break;
       /* Ѿ -> ѿ */ case (char)0xbe: strObj[i+1]=0xbf; ++i; break;
               }
               break;
             case (char)0xd2:
               switch(strObj[i+1])
               {
       /* Ҁ -> ҁ */ case (char)0x80: strObj[i+1]=0x81; ++i; break;
       /* Ҋ -> ҋ */ case (char)0x8a: strObj[i+1]=0x8b; ++i; break;
       /* Ҍ -> ҍ */ case (char)0x8c: strObj[i+1]=0x8d; ++i; break;
       /* Ҏ -> ҏ */ case (char)0x8e: strObj[i+1]=0x8f; ++i; break;
       /* Ґ -> ґ */ case (char)0x90: strObj[i+1]=0x91; ++i; break;
       /* Ғ -> ғ */ case (char)0x92: strObj[i+1]=0x93; ++i; break;
       /* Ҕ -> ҕ */ case (char)0x94: strObj[i+1]=0x95; ++i; break;
       /* Җ -> җ */ case (char)0x96: strObj[i+1]=0x97; ++i; break;
       /* Ҙ -> ҙ */ case (char)0x98: strObj[i+1]=0x99; ++i; break;
       /* Қ -> қ */ case (char)0x9a: strObj[i+1]=0x9b; ++i; break;
       /* Ҝ -> ҝ */ case (char)0x9c: strObj[i+1]=0x9d; ++i; break;
       /* Ҟ -> ҟ */ case (char)0x9e: strObj[i+1]=0x9f; ++i; break;
       /* Ҡ -> ҡ */ case (char)0xa0: strObj[i+1]=0xa1; ++i; break;
       /* Ң -> ң */ case (char)0xa2: strObj[i+1]=0xa3; ++i; break;
       /* Ҥ -> ҥ */ case (char)0xa4: strObj[i+1]=0xa5; ++i; break;
       /* Ҧ -> ҧ */ case (char)0xa6: strObj[i+1]=0xa7; ++i; break;
       /* Ҩ -> ҩ */ case (char)0xa8: strObj[i+1]=0xa9; ++i; break;
       /* Ҫ -> ҫ */ case (char)0xaa: strObj[i+1]=0xab; ++i; break;
       /* Ҭ -> ҭ */ case (char)0xac: strObj[i+1]=0xad; ++i; break;
       /* Ү -> ү */ case (char)0xae: strObj[i+1]=0xaf; ++i; break;
       /* Ұ -> ұ */ case (char)0xb0: strObj[i+1]=0xb1; ++i; break;
       /* Ҳ -> ҳ */ case (char)0xb2: strObj[i+1]=0xb3; ++i; break;
       /* Ҵ -> ҵ */ case (char)0xb4: strObj[i+1]=0xb5; ++i; break;
       /* Ҷ -> ҷ */ case (char)0xb6: strObj[i+1]=0xb7; ++i; break;
       /* Ҹ -> ҹ */ case (char)0xb8: strObj[i+1]=0xb9; ++i; break;
       /* Һ -> һ */ case (char)0xba: strObj[i+1]=0xbb; ++i; break;
       /* Ҽ -> ҽ */ case (char)0xbc: strObj[i+1]=0xbd; ++i; break;
       /* Ҿ -> ҿ */ case (char)0xbe: strObj[i+1]=0xbf; ++i; break;
               }
               break;
             case (char)0xd3:
               switch(strObj[i+1])
               {
       /* Ӂ -> ӂ */ case (char)0x81: strObj[i+1]=0x82; ++i; break;
       /* Ӄ -> ӄ */ case (char)0x83: strObj[i+1]=0x84; ++i; break;
       /* Ӆ -> ӆ */ case (char)0x85: strObj[i+1]=0x86; ++i; break;
       /* Ӈ -> ӈ */ case (char)0x87: strObj[i+1]=0x88; ++i; break;
       /* Ӊ -> ӊ */ case (char)0x89: strObj[i+1]=0x8a; ++i; break;
       /* Ӌ -> ӌ */ case (char)0x8b: strObj[i+1]=0x8c; ++i; break;
       /* Ӎ -> ӎ */ case (char)0x8d: strObj[i+1]=0x8e; ++i; break;
       /* Ӑ -> ӑ */ case (char)0x90: strObj[i+1]=0x91; ++i; break;
       /* Ӓ -> ӓ */ case (char)0x92: strObj[i+1]=0x93; ++i; break;
       /* Ӕ -> ӕ */ case (char)0x94: strObj[i+1]=0x95; ++i; break;
       /* Ӗ -> ӗ */ case (char)0x96: strObj[i+1]=0x97; ++i; break;
       /* Ә -> ә */ case (char)0x98: strObj[i+1]=0x99; ++i; break;
       /* Ӛ -> ӛ */ case (char)0x9a: strObj[i+1]=0x9b; ++i; break;
       /* Ӝ -> ӝ */ case (char)0x9c: strObj[i+1]=0x9d; ++i; break;
       /* Ӟ -> ӟ */ case (char)0x9e: strObj[i+1]=0x9f; ++i; break;
       /* Ӡ -> ӡ */ case (char)0xa0: strObj[i+1]=0xa1; ++i; break;
       /* Ӣ -> ӣ */ case (char)0xa2: strObj[i+1]=0xa3; ++i; break;
       /* Ӥ -> ӥ */ case (char)0xa4: strObj[i+1]=0xa5; ++i; break;
       /* Ӧ -> ӧ */ case (char)0xa6: strObj[i+1]=0xa7; ++i; break;
       /* Ө -> ө */ case (char)0xa8: strObj[i+1]=0xa9; ++i; break;
       /* Ӫ -> ӫ */ case (char)0xaa: strObj[i+1]=0xab; ++i; break;
       /* Ӭ -> ӭ */ case (char)0xac: strObj[i+1]=0xad; ++i; break;
       /* Ӯ -> ӯ */ case (char)0xae: strObj[i+1]=0xaf; ++i; break;
       /* Ӱ -> ӱ */ case (char)0xb0: strObj[i+1]=0xb1; ++i; break;
       /* Ӳ -> ӳ */ case (char)0xb2: strObj[i+1]=0xb3; ++i; break;
       /* Ӵ -> ӵ */ case (char)0xb4: strObj[i+1]=0xb5; ++i; break;
       /* Ӷ -> ӷ */ case (char)0xb6: strObj[i+1]=0xb7; ++i; break;
       /* Ӹ -> ӹ */ case (char)0xb8: strObj[i+1]=0xb9; ++i; break;
       /* Ӻ -> ӻ */ case (char)0xba: strObj[i+1]=0xbb; ++i; break;
       /* Ӽ -> ӽ */ case (char)0xbc: strObj[i+1]=0xbd; ++i; break;
       /* Ӿ -> ӿ */ case (char)0xbe: strObj[i+1]=0xbf; ++i; break;
               }
               break;
             case (char)0xd4:
               switch(strObj[i+1])
               {
       /* Ԁ -> ԁ */ case (char)0x80: strObj[i+1]=0x81; ++i; break;
       /* Ԃ -> ԃ */ case (char)0x82: strObj[i+1]=0x83; ++i; break;
       /* Ԅ -> ԅ */ case (char)0x84: strObj[i+1]=0x85; ++i; break;
       /* Ԇ -> ԇ */ case (char)0x86: strObj[i+1]=0x87; ++i; break;
       /* Ԉ -> ԉ */ case (char)0x88: strObj[i+1]=0x89; ++i; break;
       /* Ԋ -> ԋ */ case (char)0x8a: strObj[i+1]=0x8b; ++i; break;
       /* Ԍ -> ԍ */ case (char)0x8c: strObj[i+1]=0x8d; ++i; break;
       /* Ԏ -> ԏ */ case (char)0x8e: strObj[i+1]=0x8f; ++i; break;
       /* Ԑ -> ԑ */ case (char)0x90: strObj[i+1]=0x91; ++i; break;
       /* Ԓ -> ԓ */ case (char)0x92: strObj[i+1]=0x93; ++i; break;
       /* Ԕ -> ԕ */ case (char)0x94: strObj[i+1]=0x95; ++i; break;
       /* Ԗ -> ԗ */ case (char)0x96: strObj[i+1]=0x97; ++i; break;
       /* Ԙ -> ԙ */ case (char)0x98: strObj[i+1]=0x99; ++i; break;
       /* Ԛ -> ԛ */ case (char)0x9a: strObj[i+1]=0x9b; ++i; break;
       /* Ԝ -> ԝ */ case (char)0x9c: strObj[i+1]=0x9d; ++i; break;
       /* Ԟ -> ԟ */ case (char)0x9e: strObj[i+1]=0x9f; ++i; break;
       /* Ԡ -> ԡ */ case (char)0xa0: strObj[i+1]=0xa1; ++i; break;
       /* Ԣ -> ԣ */ case (char)0xa2: strObj[i+1]=0xa3; ++i; break;
       /* Ա -> ա */ case (char)0xb1: strObj[i]=0xd5; strObj[i+1]=0xa1; ++i; break;
       /* Բ -> բ */ case (char)0xb2: strObj[i]=0xd5; strObj[i+1]=0xa2; ++i; break;
       /* Գ -> գ */ case (char)0xb3: strObj[i]=0xd5; strObj[i+1]=0xa3; ++i; break;
       /* Դ -> դ */ case (char)0xb4: strObj[i]=0xd5; strObj[i+1]=0xa4; ++i; break;
       /* Ե -> ե */ case (char)0xb5: strObj[i]=0xd5; strObj[i+1]=0xa5; ++i; break;
       /* Զ -> զ */ case (char)0xb6: strObj[i]=0xd5; strObj[i+1]=0xa6; ++i; break;
       /* Է -> է */ case (char)0xb7: strObj[i]=0xd5; strObj[i+1]=0xa7; ++i; break;
       /* Ը -> ը */ case (char)0xb8: strObj[i]=0xd5; strObj[i+1]=0xa8; ++i; break;
       /* Թ -> թ */ case (char)0xb9: strObj[i]=0xd5; strObj[i+1]=0xa9; ++i; break;
       /* Ժ -> ժ */ case (char)0xba: strObj[i]=0xd5; strObj[i+1]=0xaa; ++i; break;
       /* Ի -> ի */ case (char)0xbb: strObj[i]=0xd5; strObj[i+1]=0xab; ++i; break;
       /* Լ -> լ */ case (char)0xbc: strObj[i]=0xd5; strObj[i+1]=0xac; ++i; break;
       /* Խ -> խ */ case (char)0xbd: strObj[i]=0xd5; strObj[i+1]=0xad; ++i; break;
       /* Ծ -> ծ */ case (char)0xbe: strObj[i]=0xd5; strObj[i+1]=0xae; ++i; break;
       /* Կ -> կ */ case (char)0xbf: strObj[i]=0xd5; strObj[i+1]=0xaf; ++i; break;
               }
               break;
             case (char)0xd5:
               switch(strObj[i+1])
               {
       /* Հ -> հ */ case (char)0x80: strObj[i+1]=0xb0; ++i; break;
       /* Ձ -> ձ */ case (char)0x81: strObj[i+1]=0xb1; ++i; break;
       /* Ղ -> ղ */ case (char)0x82: strObj[i+1]=0xb2; ++i; break;
       /* Ճ -> ճ */ case (char)0x83: strObj[i+1]=0xb3; ++i; break;
       /* Մ -> մ */ case (char)0x84: strObj[i+1]=0xb4; ++i; break;
       /* Յ -> յ */ case (char)0x85: strObj[i+1]=0xb5; ++i; break;
       /* Ն -> ն */ case (char)0x86: strObj[i+1]=0xb6; ++i; break;
       /* Շ -> շ */ case (char)0x87: strObj[i+1]=0xb7; ++i; break;
       /* Ո -> ո */ case (char)0x88: strObj[i+1]=0xb8; ++i; break;
       /* Չ -> չ */ case (char)0x89: strObj[i+1]=0xb9; ++i; break;
       /* Պ -> պ */ case (char)0x8a: strObj[i+1]=0xba; ++i; break;
       /* Ջ -> ջ */ case (char)0x8b: strObj[i+1]=0xbb; ++i; break;
       /* Ռ -> ռ */ case (char)0x8c: strObj[i+1]=0xbc; ++i; break;
       /* Ս -> ս */ case (char)0x8d: strObj[i+1]=0xbd; ++i; break;
       /* Վ -> վ */ case (char)0x8e: strObj[i+1]=0xbe; ++i; break;
       /* Տ -> տ */ case (char)0x8f: strObj[i+1]=0xbf; ++i; break;
               }
               break;
        }
    }
    if (i == j)
    {
      switch(strObj[j])
      {
/* A -> a */ case (char)0x41: strObj[i] = 0x61; break;
/* B -> b */ case (char)0x42: strObj[i] = 0x62; break;
/* C -> c */ case (char)0x43: strObj[i] = 0x63; break;
/* D -> d */ case (char)0x44: strObj[i] = 0x64; break;
/* E -> e */ case (char)0x45: strObj[i] = 0x65; break;
/* F -> f */ case (char)0x46: strObj[i] = 0x66; break;
/* G -> g */ case (char)0x47: strObj[i] = 0x67; break;
/* H -> h */ case (char)0x48: strObj[i] = 0x68; break;
/* I -> i */ case (char)0x49: strObj[i] = 0x69; break;
/* J -> j */ case (char)0x4a: strObj[i] = 0x6a; break;
/* K -> k */ case (char)0x4b: strObj[i] = 0x6b; break;
/* L -> l */ case (char)0x4c: strObj[i] = 0x6c; break;
/* M -> m */ case (char)0x4d: strObj[i] = 0x6d; break;
/* N -> n */ case (char)0x4e: strObj[i] = 0x6e; break;
/* O -> o */ case (char)0x4f: strObj[i] = 0x6f; break;
/* P -> p */ case (char)0x50: strObj[i] = 0x70; break;
/* Q -> q */ case (char)0x51: strObj[i] = 0x71; break;
/* R -> r */ case (char)0x52: strObj[i] = 0x72; break;
/* S -> s */ case (char)0x53: strObj[i] = 0x73; break;
/* T -> t */ case (char)0x54: strObj[i] = 0x74; break;
/* U -> u */ case (char)0x55: strObj[i] = 0x75; break;
/* V -> v */ case (char)0x56: strObj[i] = 0x76; break;
/* W -> w */ case (char)0x57: strObj[i] = 0x77; break;
/* X -> x */ case (char)0x58: strObj[i] = 0x78; break;
/* Y -> y */ case (char)0x59: strObj[i] = 0x79; break;
/* Z -> z */ case (char)0x5a: strObj[i] = 0x7a; break;
      }
    }
    return strObj;
  }

  static string& normalize_to_upper(string& strObj, size_t i, size_t j)
  {
    if (strObj.length()==0)
    {
      return strObj;
    }
    for (; i < j; ++i)
    {
        switch(strObj[i])
        {
/* a -> A */ case (char)0x61: strObj[i] = (char)0x41; break;
/* b -> B */ case (char)0x62: strObj[i] = (char)0x42; break;
/* c -> C */ case (char)0x63: strObj[i] = (char)0x43; break;
/* d -> D */ case (char)0x64: strObj[i] = (char)0x44; break;
/* e -> E */ case (char)0x65: strObj[i] = (char)0x45; break;
/* f -> F */ case (char)0x66: strObj[i] = (char)0x46; break;
/* g -> G */ case (char)0x67: strObj[i] = (char)0x47; break;
/* h -> H */ case (char)0x68: strObj[i] = (char)0x48; break;
/* i -> I */ case (char)0x69: strObj[i] = (char)0x49; break;
/* j -> J */ case (char)0x6a: strObj[i] = (char)0x4a; break;
/* k -> K */ case (char)0x6b: strObj[i] = (char)0x4b; break;
/* l -> L */ case (char)0x6c: strObj[i] = (char)0x4c; break;
/* m -> M */ case (char)0x6d: strObj[i] = (char)0x4d; break;
/* n -> N */ case (char)0x6e: strObj[i] = (char)0x4e; break;
/* o -> O */ case (char)0x6f: strObj[i] = (char)0x4f; break;
/* p -> P */ case (char)0x70: strObj[i] = (char)0x50; break;
/* q -> Q */ case (char)0x71: strObj[i] = (char)0x51; break;
/* r -> R */ case (char)0x72: strObj[i] = (char)0x52; break;
/* s -> S */ case (char)0x73: strObj[i] = (char)0x53; break;
/* t -> T */ case (char)0x74: strObj[i] = (char)0x54; break;
/* u -> U */ case (char)0x75: strObj[i] = (char)0x55; break;
/* v -> V */ case (char)0x76: strObj[i] = (char)0x56; break;
/* w -> W */ case (char)0x77: strObj[i] = (char)0x57; break;
/* x -> X */ case (char)0x78: strObj[i] = (char)0x58; break;
/* y -> Y */ case (char)0x79: strObj[i] = (char)0x59; break;
/* z -> Z */ case (char)0x7a: strObj[i] = (char)0x5a; break;
             case (char)0xc3:
               switch(strObj[i+1])
               {
       /* à -> À */ case (char)0xa0: strObj[i+1]=0x80; ++i; break;
       /* á -> Á */ case (char)0xa1: strObj[i+1]=0x81; ++i; break;
       /* â -> Â */ case (char)0xa2: strObj[i+1]=0x82; ++i; break;
       /* ã -> Ã */ case (char)0xa3: strObj[i+1]=0x83; ++i; break;
       /* ä -> Ä */ case (char)0xa4: strObj[i+1]=0x84; ++i; break;
       /* å -> Å */ case (char)0xa5: strObj[i+1]=0x85; ++i; break;
       /* æ -> Æ */ case (char)0xa6: strObj[i+1]=0x86; ++i; break;
       /* ç -> Ç */ case (char)0xa7: strObj[i+1]=0x87; ++i; break;
       /* è -> È */ case (char)0xa8: strObj[i+1]=0x88; ++i; break;
       /* é -> É */ case (char)0xa9: strObj[i+1]=0x89; ++i; break;
       /* ê -> Ê */ case (char)0xaa: strObj[i+1]=0x8a; ++i; break;
       /* ë -> Ë */ case (char)0xab: strObj[i+1]=0x8b; ++i; break;
       /* ì -> Ì */ case (char)0xac: strObj[i+1]=0x8c; ++i; break;
       /* í -> Í */ case (char)0xad: strObj[i+1]=0x8d; ++i; break;
       /* î -> Î */ case (char)0xae: strObj[i+1]=0x8e; ++i; break;
       /* ï -> Ï */ case (char)0xaf: strObj[i+1]=0x8f; ++i; break;
       /* ð -> Ð */ case (char)0xb0: strObj[i+1]=0x90; ++i; break;
       /* ñ -> Ñ */ case (char)0xb1: strObj[i+1]=0x91; ++i; break;
       /* ò -> Ò */ case (char)0xb2: strObj[i+1]=0x92; ++i; break;
       /* ó -> Ó */ case (char)0xb3: strObj[i+1]=0x93; ++i; break;
       /* ô -> Ô */ case (char)0xb4: strObj[i+1]=0x94; ++i; break;
       /* õ -> Õ */ case (char)0xb5: strObj[i+1]=0x95; ++i; break;
       /* ö -> Ö */ case (char)0xb6: strObj[i+1]=0x96; ++i; break;
       /* ø -> Ø */ case (char)0xb8: strObj[i+1]=0x98; ++i; break;
       /* ù -> Ù */ case (char)0xb9: strObj[i+1]=0x99; ++i; break;
       /* ú -> Ú */ case (char)0xba: strObj[i+1]=0x9a; ++i; break;
       /* û -> Û */ case (char)0xbb: strObj[i+1]=0x9b; ++i; break;
       /* ü -> Ü */ case (char)0xbc: strObj[i+1]=0x9c; ++i; break;
       /* ý -> Ý */ case (char)0xbd: strObj[i+1]=0x9d; ++i; break;
       /* þ -> Þ */ case (char)0xbe: strObj[i+1]=0x9e; ++i; break;
       /* ÿ -> Ÿ */ case (char)0xbf: strObj[i]=0xc5; strObj[i+1]=0xb8; ++i; break;
               }
               break;
             case (char)0xc4:
               switch(strObj[i+1])
               {
       /* ā -> Ā */ case (char)0x81: strObj[i+1]=0x80; ++i; break;
       /* ă -> Ă */ case (char)0x83: strObj[i+1]=0x82; ++i; break;
       /* ą -> Ą */ case (char)0x85: strObj[i+1]=0x84; ++i; break;
       /* ć -> Ć */ case (char)0x87: strObj[i+1]=0x86; ++i; break;
       /* ĉ -> Ĉ */ case (char)0x89: strObj[i+1]=0x88; ++i; break;
       /* ċ -> Ċ */ case (char)0x8b: strObj[i+1]=0x8a; ++i; break;
       /* č -> Č */ case (char)0x8d: strObj[i+1]=0x8c; ++i; break;
       /* ď -> Ď */ case (char)0x8f: strObj[i+1]=0x8e; ++i; break;
       /* đ -> Đ */ case (char)0x91: strObj[i+1]=0x90; ++i; break;
       /* ē -> Ē */ case (char)0x93: strObj[i+1]=0x92; ++i; break;
       /* ĕ -> Ĕ */ case (char)0x95: strObj[i+1]=0x94; ++i; break;
       /* ė -> Ė */ case (char)0x97: strObj[i+1]=0x96; ++i; break;
       /* ę -> Ę */ case (char)0x99: strObj[i+1]=0x98; ++i; break;
       /* ě -> Ě */ case (char)0x9b: strObj[i+1]=0x9a; ++i; break;
       /* ĝ -> Ĝ */ case (char)0x9d: strObj[i+1]=0x9c; ++i; break;
       /* ğ -> Ğ */ case (char)0x9f: strObj[i+1]=0x9e; ++i; break;
       /* ġ -> Ġ */ case (char)0xa1: strObj[i+1]=0xa0; ++i; break;
       /* ģ -> Ģ */ case (char)0xa3: strObj[i+1]=0xa2; ++i; break;
       /* ĥ -> Ĥ */ case (char)0xa5: strObj[i+1]=0xa4; ++i; break;
       /* ħ -> Ħ */ case (char)0xa7: strObj[i+1]=0xa6; ++i; break;
       /* ĩ -> Ĩ */ case (char)0xa9: strObj[i+1]=0xa8; ++i; break;
       /* ī -> Ī */ case (char)0xab: strObj[i+1]=0xaa; ++i; break;
       /* ĭ -> Ĭ */ case (char)0xad: strObj[i+1]=0xac; ++i; break;
       /* į -> Į */ case (char)0xaf: strObj[i+1]=0xae; ++i; break;
       /* ĳ -> Ĳ */ case (char)0xb3: strObj[i+1]=0xb2; ++i; break;
       /* ĵ -> Ĵ */ case (char)0xb5: strObj[i+1]=0xb4; ++i; break;
       /* ķ -> Ķ */ case (char)0xb7: strObj[i+1]=0xb6; ++i; break;
       /* ĺ -> Ĺ */ case (char)0xba: strObj[i+1]=0xb9; ++i; break;
       /* ļ -> Ļ */ case (char)0xbc: strObj[i+1]=0xbb; ++i; break;
       /* ľ -> Ľ */ case (char)0xbe: strObj[i+1]=0xbd; ++i; break;
               }
               break;
             case (char)0xc5:
               switch(strObj[i+1])
               {
       /* ŀ -> Ŀ */ case (char)0x80: strObj[i]=0xc4; strObj[i+1]=0xbf; ++i; break;
       /* ł -> Ł */ case (char)0x82: strObj[i+1]=0x81; ++i; break;
       /* ń -> Ń */ case (char)0x84: strObj[i+1]=0x83; ++i; break;
       /* ņ -> Ņ */ case (char)0x86: strObj[i+1]=0x85; ++i; break;
       /* ň -> Ň */ case (char)0x88: strObj[i+1]=0x87; ++i; break;
       /* ŋ -> Ŋ */ case (char)0x8b: strObj[i+1]=0x8a; ++i; break;
       /* ō -> Ō */ case (char)0x8d: strObj[i+1]=0x8c; ++i; break;
       /* ŏ -> Ŏ */ case (char)0x8f: strObj[i+1]=0x8e; ++i; break;
       /* ő -> Ő */ case (char)0x91: strObj[i+1]=0x90; ++i; break;
       /* œ -> Œ */ case (char)0x93: strObj[i+1]=0x92; ++i; break;
       /* ŕ -> Ŕ */ case (char)0x95: strObj[i+1]=0x94; ++i; break;
       /* ŗ -> Ŗ */ case (char)0x97: strObj[i+1]=0x96; ++i; break;
       /* ř -> Ř */ case (char)0x99: strObj[i+1]=0x98; ++i; break;
       /* ś -> Ś */ case (char)0x9b: strObj[i+1]=0x9a; ++i; break;
       /* ŝ -> Ŝ */ case (char)0x9d: strObj[i+1]=0x9c; ++i; break;
       /* ş -> Ş */ case (char)0x9f: strObj[i+1]=0x9e; ++i; break;
       /* š -> Š */ case (char)0xa1: strObj[i+1]=0xa0; ++i; break;
       /* ţ -> Ţ */ case (char)0xa3: strObj[i+1]=0xa2; ++i; break;
       /* ť -> Ť */ case (char)0xa5: strObj[i+1]=0xa4; ++i; break;
       /* ŧ -> Ŧ */ case (char)0xa7: strObj[i+1]=0xa6; ++i; break;
       /* ũ -> Ũ */ case (char)0xa9: strObj[i+1]=0xa8; ++i; break;
       /* ū -> Ū */ case (char)0xab: strObj[i+1]=0xaa; ++i; break;
       /* ŭ -> Ŭ */ case (char)0xad: strObj[i+1]=0xac; ++i; break;
       /* ů -> Ů */ case (char)0xaf: strObj[i+1]=0xae; ++i; break;
       /* ű -> Ű */ case (char)0xb1: strObj[i+1]=0xb0; ++i; break;
       /* ų -> Ų */ case (char)0xb3: strObj[i+1]=0xb2; ++i; break;
       /* ŵ -> Ŵ */ case (char)0xb5: strObj[i+1]=0xb4; ++i; break;
       /* ŷ -> Ŷ */ case (char)0xb7: strObj[i+1]=0xb6; ++i; break;
       /* ź -> Ź */ case (char)0xba: strObj[i+1]=0xb9; ++i; break;
       /* ż -> Ż */ case (char)0xbc: strObj[i+1]=0xbb; ++i; break;
       /* ž -> Ž */ case (char)0xbe: strObj[i+1]=0xbd; ++i; break;
               }
               break;
             case (char)0xc6:
               switch(strObj[i+1])
               {
       /* ƀ -> Ƀ */ case (char)0x80: strObj[i]=0xc9; strObj[i+1]=0x83; ++i; break;
       /* ƃ -> Ƃ */ case (char)0x83: strObj[i+1]=0x82; ++i; break;
       /* ƅ -> Ƅ */ case (char)0x85: strObj[i+1]=0x84; ++i; break;
       /* ƈ -> Ƈ */ case (char)0x88: strObj[i+1]=0x87; ++i; break;
       /* ƌ -> Ƌ */ case (char)0x8c: strObj[i+1]=0x8b; ++i; break;
       /* ƒ -> Ƒ */ case (char)0x92: strObj[i+1]=0x91; ++i; break;
       /* ƙ -> Ƙ */ case (char)0x99: strObj[i+1]=0x98; ++i; break;
       /* ƚ -> Ƚ */ case (char)0x9a: strObj[i]=0xc8; strObj[i+1]=0xbd; ++i; break;
       /* ƞ -> Ƞ */ case (char)0x9e: strObj[i]=0xc8; strObj[i+1]=0xa0; ++i; break;
       /* ơ -> Ơ */ case (char)0xa1: strObj[i+1]=0xa0; ++i; break;
       /* ƣ -> Ƣ */ case (char)0xa3: strObj[i+1]=0xa2; ++i; break;
       /* ƥ -> Ƥ */ case (char)0xa5: strObj[i+1]=0xa4; ++i; break;
       /* ƨ -> Ƨ */ case (char)0xa8: strObj[i+1]=0xa7; ++i; break;
       /* ƭ -> Ƭ */ case (char)0xad: strObj[i+1]=0xac; ++i; break;
       /* ư -> Ư */ case (char)0xb0: strObj[i+1]=0xaf; ++i; break;
       /* ƴ -> Ƴ */ case (char)0xb4: strObj[i+1]=0xb3; ++i; break;
       /* ƶ -> Ƶ */ case (char)0xb6: strObj[i+1]=0xb5; ++i; break;
       /* ƹ -> Ƹ */ case (char)0xb9: strObj[i+1]=0xb8; ++i; break;
       /* ƽ -> Ƽ */ case (char)0xbd: strObj[i+1]=0xbc; ++i; break;
               }
               break;
             case (char)0xc7:
               switch(strObj[i+1])
               {
       /* ǆ -> Ǆ */ case (char)0x86: strObj[i+1]=0x84; ++i; break;
       /* ǉ -> Ǉ */ case (char)0x89: strObj[i+1]=0x87; ++i; break;
       /* ǌ -> Ǌ */ case (char)0x8c: strObj[i+1]=0x8a; ++i; break;
       /* ǎ -> Ǎ */ case (char)0x8e: strObj[i+1]=0x8d; ++i; break;
       /* ǐ -> Ǐ */ case (char)0x90: strObj[i+1]=0x8f; ++i; break;
       /* ǒ -> Ǒ */ case (char)0x92: strObj[i+1]=0x91; ++i; break;
       /* ǔ -> Ǔ */ case (char)0x94: strObj[i+1]=0x93; ++i; break;
       /* ǖ -> Ǖ */ case (char)0x96: strObj[i+1]=0x95; ++i; break;
       /* ǘ -> Ǘ */ case (char)0x98: strObj[i+1]=0x97; ++i; break;
       /* ǚ -> Ǚ */ case (char)0x9a: strObj[i+1]=0x99; ++i; break;
       /* ǜ -> Ǜ */ case (char)0x9c: strObj[i+1]=0x9b; ++i; break;
       /* ǟ -> Ǟ */ case (char)0x9f: strObj[i+1]=0x9e; ++i; break;
       /* ǡ -> Ǡ */ case (char)0xa1: strObj[i+1]=0xa0; ++i; break;
       /* ǣ -> Ǣ */ case (char)0xa3: strObj[i+1]=0xa2; ++i; break;
       /* ǥ -> Ǥ */ case (char)0xa5: strObj[i+1]=0xa4; ++i; break;
       /* ǧ -> Ǧ */ case (char)0xa7: strObj[i+1]=0xa6; ++i; break;
       /* ǩ -> Ǩ */ case (char)0xa9: strObj[i+1]=0xa8; ++i; break;
       /* ǫ -> Ǫ */ case (char)0xab: strObj[i+1]=0xaa; ++i; break;
       /* ǭ -> Ǭ */ case (char)0xad: strObj[i+1]=0xac; ++i; break;
       /* ǯ -> Ǯ */ case (char)0xaf: strObj[i+1]=0xae; ++i; break;
       /* ǳ -> Ǳ */ case (char)0xb3: strObj[i+1]=0xb1; ++i; break;
       /* ǵ -> Ǵ */ case (char)0xb5: strObj[i+1]=0xb4; ++i; break;
       /* ǹ -> Ǹ */ case (char)0xb9: strObj[i+1]=0xb8; ++i; break;
       /* ǻ -> Ǻ */ case (char)0xbb: strObj[i+1]=0xba; ++i; break;
       /* ǽ -> Ǽ */ case (char)0xbd: strObj[i+1]=0xbc; ++i; break;
       /* ǿ -> Ǿ */ case (char)0xbf: strObj[i+1]=0xbe; ++i; break;
               }
               break;
             case (char)0xc8:
               switch(strObj[i+1])
               {
       /* ȁ -> Ȁ */ case (char)0x81: strObj[i+1]=0x80; ++i; break;
       /* ȃ -> Ȃ */ case (char)0x83: strObj[i+1]=0x82; ++i; break;
       /* ȅ -> Ȅ */ case (char)0x85: strObj[i+1]=0x84; ++i; break;
       /* ȇ -> Ȇ */ case (char)0x87: strObj[i+1]=0x86; ++i; break;
       /* ȉ -> Ȉ */ case (char)0x89: strObj[i+1]=0x88; ++i; break;
       /* ȋ -> Ȋ */ case (char)0x8b: strObj[i+1]=0x8a; ++i; break;
       /* ȍ -> Ȍ */ case (char)0x8d: strObj[i+1]=0x8c; ++i; break;
       /* ȏ -> Ȏ */ case (char)0x8f: strObj[i+1]=0x8e; ++i; break;
       /* ȑ -> Ȑ */ case (char)0x91: strObj[i+1]=0x90; ++i; break;
       /* ȓ -> Ȓ */ case (char)0x93: strObj[i+1]=0x92; ++i; break;
       /* ȕ -> Ȕ */ case (char)0x95: strObj[i+1]=0x94; ++i; break;
       /* ȗ -> Ȗ */ case (char)0x97: strObj[i+1]=0x96; ++i; break;
       /* ș -> Ș */ case (char)0x99: strObj[i+1]=0x98; ++i; break;
       /* ț -> Ț */ case (char)0x9b: strObj[i+1]=0x9a; ++i; break;
       /* ȝ -> Ȝ */ case (char)0x9d: strObj[i+1]=0x9c; ++i; break;
       /* ȟ -> Ȟ */ case (char)0x9f: strObj[i+1]=0x9e; ++i; break;
       /* ȣ -> Ȣ */ case (char)0xa3: strObj[i+1]=0xa2; ++i; break;
       /* ȥ -> Ȥ */ case (char)0xa5: strObj[i+1]=0xa4; ++i; break;
       /* ȧ -> Ȧ */ case (char)0xa7: strObj[i+1]=0xa6; ++i; break;
       /* ȩ -> Ȩ */ case (char)0xa9: strObj[i+1]=0xa8; ++i; break;
       /* ȫ -> Ȫ */ case (char)0xab: strObj[i+1]=0xaa; ++i; break;
       /* ȭ -> Ȭ */ case (char)0xad: strObj[i+1]=0xac; ++i; break;
       /* ȯ -> Ȯ */ case (char)0xaf: strObj[i+1]=0xae; ++i; break;
       /* ȱ -> Ȱ */ case (char)0xb1: strObj[i+1]=0xb0; ++i; break;
       /* ȳ -> Ȳ */ case (char)0xb3: strObj[i+1]=0xb2; ++i; break;
       /* ȼ -> Ȼ */ case (char)0xbc: strObj[i+1]=0xbb; ++i; break;
               }
               break;
             case (char)0xc9:
               switch(strObj[i+1])
               {
       /* ɂ -> Ɂ */ case (char)0x82: strObj[i+1]=0x81; ++i; break;
       /* ɇ -> Ɇ */ case (char)0x87: strObj[i+1]=0x86; ++i; break;
       /* ɉ -> Ɉ */ case (char)0x89: strObj[i+1]=0x88; ++i; break;
       /* ɍ -> Ɍ */ case (char)0x8d: strObj[i+1]=0x8c; ++i; break;
       /* ɏ -> Ɏ */ case (char)0x8f: strObj[i+1]=0x8e; ++i; break;
       /* ɓ -> Ɓ */ case (char)0x93: strObj[i]=0xc6; strObj[i+1]=0x81; ++i; break;
       /* ɔ -> Ɔ */ case (char)0x94: strObj[i]=0xc6; strObj[i+1]=0x86; ++i; break;
       /* ɗ -> Ɗ */ case (char)0x97: strObj[i]=0xc6; strObj[i+1]=0x8a; ++i; break;
       /* ɘ -> Ǝ */ case (char)0x98: strObj[i]=0xc6; strObj[i+1]=0x8e; ++i; break;
       /* ə -> Ə */ case (char)0x99: strObj[i]=0xc6; strObj[i+1]=0x8f; ++i; break;
       /* ɛ -> Ɛ */ case (char)0x9b: strObj[i]=0xc6; strObj[i+1]=0x90; ++i; break;
       /* ɠ -> Ɠ */ case (char)0xa0: strObj[i]=0xc6; strObj[i+1]=0x93; ++i; break;
       /* ɣ -> Ɣ */ case (char)0xa3: strObj[i]=0xc6; strObj[i+1]=0x94; ++i; break;
       /* ɨ -> Ɨ */ case (char)0xa8: strObj[i]=0xc6; strObj[i+1]=0x97; ++i; break;
       /* ɩ -> Ɩ */ case (char)0xa9: strObj[i]=0xc6; strObj[i+1]=0x96; ++i; break;
       /* ɯ -> Ɯ */ case (char)0xaf: strObj[i]=0xc6; strObj[i+1]=0x9c; ++i; break;
       /* ɲ -> Ɲ */ case (char)0xb2: strObj[i]=0xc6; strObj[i+1]=0x9d; ++i; break;
               }
               break;
             case (char)0xca:
               switch(strObj[i+1])
               {
       /* ʃ -> Ʃ */ case (char)0x83: strObj[i]=0xc6; strObj[i+1]=0xa9; ++i; break;
       /* ʈ -> Ʈ */ case (char)0x88: strObj[i]=0xc6; strObj[i+1]=0xae; ++i; break;
       /* ʉ -> Ʉ */ case (char)0x89: strObj[i]=0xc9; strObj[i+1]=0x84; ++i; break;
       /* ʊ -> Ʊ */ case (char)0x8a: strObj[i]=0xc6; strObj[i+1]=0xb1; ++i; break;
       /* ʋ -> Ʋ */ case (char)0x8b: strObj[i]=0xc6; strObj[i+1]=0xb2; ++i; break;
       /* ʌ -> Ʌ */ case (char)0x8c: strObj[i]=0xc9; strObj[i+1]=0x85; ++i; break;
       /* ʒ -> Ʒ */ case (char)0x92: strObj[i]=0xc6; strObj[i+1]=0xb7; ++i; break;
               }
               break;
             case (char)0xcd:
               switch(strObj[i+1])
               {
       /* ͱ -> Ͱ */ case (char)0xb1: strObj[i+1]=0xb0; ++i; break;
       /* ͳ -> Ͳ */ case (char)0xb3: strObj[i+1]=0xb2; ++i; break;
       /* ͷ -> Ͷ */ case (char)0xb7: strObj[i+1]=0xb6; ++i; break;
       /* ͻ -> Ͻ */ case (char)0xbb: strObj[i]=0xcf; strObj[i+1]=0xbd; ++i; break;
       /* ͼ -> Ͼ */ case (char)0xbc: strObj[i]=0xcf; strObj[i+1]=0xbe; ++i; break;
       /* ͽ -> Ͽ */ case (char)0xbd: strObj[i]=0xcf; strObj[i+1]=0xbf; ++i; break;
               }
               break;
             case (char)0xce:
               switch(strObj[i+1])
               {
       /* ά -> Ά */ case (char)0xac: strObj[i+1]=0x86; ++i; break;
       /* έ -> Έ */ case (char)0xad: strObj[i+1]=0x88; ++i; break;
       /* ή -> Ή */ case (char)0xae: strObj[i+1]=0x89; ++i; break;
       /* ί -> Ί */ case (char)0xaf: strObj[i+1]=0x8a; ++i; break;
       /* α -> Α */ case (char)0xb1: strObj[i+1]=0x91; ++i; break;
       /* β -> Β */ case (char)0xb2: strObj[i+1]=0x92; ++i; break;
       /* γ -> Γ */ case (char)0xb3: strObj[i+1]=0x93; ++i; break;
       /* δ -> Δ */ case (char)0xb4: strObj[i+1]=0x94; ++i; break;
       /* ε -> Ε */ case (char)0xb5: strObj[i+1]=0x95; ++i; break;
       /* ζ -> Ζ */ case (char)0xb6: strObj[i+1]=0x96; ++i; break;
       /* η -> Η */ case (char)0xb7: strObj[i+1]=0x97; ++i; break;
       /* θ -> Θ */ case (char)0xb8: strObj[i+1]=0x98; ++i; break;
       /* ι -> Ι */ case (char)0xb9: strObj[i+1]=0x99; ++i; break;
       /* κ -> Κ */ case (char)0xba: strObj[i+1]=0x9a; ++i; break;
       /* λ -> Λ */ case (char)0xbb: strObj[i+1]=0x9b; ++i; break;
       /* μ -> Μ */ case (char)0xbc: strObj[i+1]=0x9c; ++i; break;
       /* ν -> Ν */ case (char)0xbd: strObj[i+1]=0x9d; ++i; break;
       /* ξ -> Ξ */ case (char)0xbe: strObj[i+1]=0x9e; ++i; break;
       /* ο -> Ο */ case (char)0xbf: strObj[i+1]=0x9f; ++i; break;
               }
               break;
             case (char)0xcf:
               switch(strObj[i+1])
               {
       /* π -> Π */ case (char)0x80: strObj[i]=0xce; strObj[i+1]=0xa0; ++i; break;
       /* ρ -> Ρ */ case (char)0x81: strObj[i]=0xce; strObj[i+1]=0xa1; ++i; break;
       /* σ -> Σ */ case (char)0x83: strObj[i]=0xce; strObj[i+1]=0xa3; ++i; break;
       /* τ -> Τ */ case (char)0x84: strObj[i]=0xce; strObj[i+1]=0xa4; ++i; break;
       /* υ -> Υ */ case (char)0x85: strObj[i]=0xce; strObj[i+1]=0xa5; ++i; break;
       /* φ -> Φ */ case (char)0x86: strObj[i]=0xce; strObj[i+1]=0xa6; ++i; break;
       /* χ -> Χ */ case (char)0x87: strObj[i]=0xce; strObj[i+1]=0xa7; ++i; break;
       /* ψ -> Ψ */ case (char)0x88: strObj[i]=0xce; strObj[i+1]=0xa8; ++i; break;
       /* ω -> Ω */ case (char)0x89: strObj[i]=0xce; strObj[i+1]=0xa9; ++i; break;
       /* ϊ -> Ϊ */ case (char)0x8a: strObj[i]=0xce; strObj[i+1]=0xaa; ++i; break;
       /* ϋ -> Ϋ */ case (char)0x8b: strObj[i]=0xce; strObj[i+1]=0xab; ++i; break;
       /* ό -> Ό */ case (char)0x8c: strObj[i]=0xce; strObj[i+1]=0x8c; ++i; break;
       /* ύ -> Ύ */ case (char)0x8d: strObj[i]=0xce; strObj[i+1]=0x8e; ++i; break;
       /* ώ -> Ώ */ case (char)0x8e: strObj[i]=0xce; strObj[i+1]=0x8f; ++i; break;
       /* ϣ -> Ϣ */ case (char)0xa3: strObj[i+1]=0xa2; ++i; break;
       /* ϥ -> Ϥ */ case (char)0xa5: strObj[i+1]=0xa4; ++i; break;
       /* ϧ -> Ϧ */ case (char)0xa7: strObj[i+1]=0xa6; ++i; break;
       /* ϩ -> Ϩ */ case (char)0xa9: strObj[i+1]=0xa8; ++i; break;
       /* ϫ -> Ϫ */ case (char)0xab: strObj[i+1]=0xaa; ++i; break;
       /* ϭ -> Ϭ */ case (char)0xad: strObj[i+1]=0xac; ++i; break;
       /* ϯ -> Ϯ */ case (char)0xaf: strObj[i+1]=0xae; ++i; break;
       /* ϸ -> Ϸ */ case (char)0xb8: strObj[i+1]=0xb7; ++i; break;
       /* ϻ -> Ϻ */ case (char)0xbb: strObj[i+1]=0xba; ++i; break;
               }
               break;
             case (char)0xd0:
               switch(strObj[i+1])
               {
       /* а -> А */ case (char)0xb0: strObj[i+1]=0x90; ++i; break;
       /* б -> Б */ case (char)0xb1: strObj[i+1]=0x91; ++i; break;
       /* в -> В */ case (char)0xb2: strObj[i+1]=0x92; ++i; break;
       /* г -> Г */ case (char)0xb3: strObj[i+1]=0x93; ++i; break;
       /* д -> Д */ case (char)0xb4: strObj[i+1]=0x94; ++i; break;
       /* е -> Е */ case (char)0xb5: strObj[i+1]=0x95; ++i; break;
       /* ж -> Ж */ case (char)0xb6: strObj[i+1]=0x96; ++i; break;
       /* з -> З */ case (char)0xb7: strObj[i+1]=0x97; ++i; break;
       /* и -> И */ case (char)0xb8: strObj[i+1]=0x98; ++i; break;
       /* й -> Й */ case (char)0xb9: strObj[i+1]=0x99; ++i; break;
       /* к -> К */ case (char)0xba: strObj[i+1]=0x9a; ++i; break;
       /* л -> Л */ case (char)0xbb: strObj[i+1]=0x9b; ++i; break;
       /* м -> М */ case (char)0xbc: strObj[i+1]=0x9c; ++i; break;
       /* н -> Н */ case (char)0xbd: strObj[i+1]=0x9d; ++i; break;
       /* о -> О */ case (char)0xbe: strObj[i+1]=0x9e; ++i; break;
       /* п -> П */ case (char)0xbf: strObj[i+1]=0x9f; ++i; break;
               }
               break;
             case (char)0xd1:
               switch(strObj[i+1])
               {
       /* р -> Р */ case (char)0x80: strObj[i]=0xd0; strObj[i+1]=0xa0; ++i; break;
       /* с -> С */ case (char)0x81: strObj[i]=0xd0; strObj[i+1]=0xa1; ++i; break;
       /* т -> Т */ case (char)0x82: strObj[i]=0xd0; strObj[i+1]=0xa2; ++i; break;
       /* у -> У */ case (char)0x83: strObj[i]=0xd0; strObj[i+1]=0xa3; ++i; break;
       /* ф -> Ф */ case (char)0x84: strObj[i]=0xd0; strObj[i+1]=0xa4; ++i; break;
       /* х -> Х */ case (char)0x85: strObj[i]=0xd0; strObj[i+1]=0xa5; ++i; break;
       /* ц -> Ц */ case (char)0x86: strObj[i]=0xd0; strObj[i+1]=0xa6; ++i; break;
       /* ч -> Ч */ case (char)0x87: strObj[i]=0xd0; strObj[i+1]=0xa7; ++i; break;
       /* ш -> Ш */ case (char)0x88: strObj[i]=0xd0; strObj[i+1]=0xa8; ++i; break;
       /* щ -> Щ */ case (char)0x89: strObj[i]=0xd0; strObj[i+1]=0xa9; ++i; break;
       /* ъ -> Ъ */ case (char)0x8a: strObj[i]=0xd0; strObj[i+1]=0xaa; ++i; break;
       /* ы -> Ы */ case (char)0x8b: strObj[i]=0xd0; strObj[i+1]=0xab; ++i; break;
       /* ь -> Ь */ case (char)0x8c: strObj[i]=0xd0; strObj[i+1]=0xac; ++i; break;
       /* э -> Э */ case (char)0x8d: strObj[i]=0xd0; strObj[i+1]=0xad; ++i; break;
       /* ю -> Ю */ case (char)0x8e: strObj[i]=0xd0; strObj[i+1]=0xae; ++i; break;
       /* я -> Я */ case (char)0x8f: strObj[i]=0xd0; strObj[i+1]=0xaf; ++i; break;
       /* ѐ -> Ѐ */ case (char)0x90: strObj[i]=0xd0; strObj[i+1]=0x80; ++i; break;
       /* ё -> Ё */ case (char)0x91: strObj[i]=0xd0; strObj[i+1]=0x81; ++i; break;
       /* ђ -> Ђ */ case (char)0x92: strObj[i]=0xd0; strObj[i+1]=0x82; ++i; break;
       /* ѓ -> Ѓ */ case (char)0x93: strObj[i]=0xd0; strObj[i+1]=0x83; ++i; break;
       /* є -> Є */ case (char)0x94: strObj[i]=0xd0; strObj[i+1]=0x84; ++i; break;
       /* ѕ -> Ѕ */ case (char)0x95: strObj[i]=0xd0; strObj[i+1]=0x85; ++i; break;
       /* і -> І */ case (char)0x96: strObj[i]=0xd0; strObj[i+1]=0x86; ++i; break;
       /* ї -> Ї */ case (char)0x97: strObj[i]=0xd0; strObj[i+1]=0x87; ++i; break;
       /* ј -> Ј */ case (char)0x98: strObj[i]=0xd0; strObj[i+1]=0x88; ++i; break;
       /* љ -> Љ */ case (char)0x99: strObj[i]=0xd0; strObj[i+1]=0x89; ++i; break;
       /* њ -> Њ */ case (char)0x9a: strObj[i]=0xd0; strObj[i+1]=0x8a; ++i; break;
       /* ћ -> Ћ */ case (char)0x9b: strObj[i]=0xd0; strObj[i+1]=0x8b; ++i; break;
       /* ќ -> Ќ */ case (char)0x9c: strObj[i]=0xd0; strObj[i+1]=0x8c; ++i; break;
       /* ѝ -> Ѝ */ case (char)0x9d: strObj[i]=0xd0; strObj[i+1]=0x8d; ++i; break;
       /* ў -> Ў */ case (char)0x9e: strObj[i]=0xd0; strObj[i+1]=0x8e; ++i; break;
       /* џ -> Џ */ case (char)0x9f: strObj[i]=0xd0; strObj[i+1]=0x8f; ++i; break;
       /* ѡ -> Ѡ */ case (char)0xa1: strObj[i+1]=0xa0; ++i; break;
       /* ѣ -> Ѣ */ case (char)0xa3: strObj[i+1]=0xa2; ++i; break;
       /* ѥ -> Ѥ */ case (char)0xa5: strObj[i+1]=0xa4; ++i; break;
       /* ѧ -> Ѧ */ case (char)0xa7: strObj[i+1]=0xa6; ++i; break;
       /* ѩ -> Ѩ */ case (char)0xa9: strObj[i+1]=0xa8; ++i; break;
       /* ѫ -> Ѫ */ case (char)0xab: strObj[i+1]=0xaa; ++i; break;
       /* ѭ -> Ѭ */ case (char)0xad: strObj[i+1]=0xac; ++i; break;
       /* ѯ -> Ѯ */ case (char)0xaf: strObj[i+1]=0xae; ++i; break;
       /* ѱ -> Ѱ */ case (char)0xb1: strObj[i+1]=0xb0; ++i; break;
       /* ѳ -> Ѳ */ case (char)0xb3: strObj[i+1]=0xb2; ++i; break;
       /* ѵ -> Ѵ */ case (char)0xb5: strObj[i+1]=0xb4; ++i; break;
       /* ѷ -> Ѷ */ case (char)0xb7: strObj[i+1]=0xb6; ++i; break;
       /* ѹ -> Ѹ */ case (char)0xb9: strObj[i+1]=0xb8; ++i; break;
       /* ѻ -> Ѻ */ case (char)0xbb: strObj[i+1]=0xba; ++i; break;
       /* ѽ -> Ѽ */ case (char)0xbd: strObj[i+1]=0xbc; ++i; break;
       /* ѿ -> Ѿ */ case (char)0xbf: strObj[i+1]=0xbe; ++i; break;
               }
               break;
             case (char)0xd2:
               switch(strObj[i+1])
               {
       /* ҁ -> Ҁ */ case (char)0x81: strObj[i+1]=0x80; ++i; break;
       /* ҋ -> Ҋ */ case (char)0x8b: strObj[i+1]=0x8a; ++i; break;
       /* ҍ -> Ҍ */ case (char)0x8d: strObj[i+1]=0x8c; ++i; break;
       /* ҏ -> Ҏ */ case (char)0x8f: strObj[i+1]=0x8e; ++i; break;
       /* ґ -> Ґ */ case (char)0x91: strObj[i+1]=0x90; ++i; break;
       /* ғ -> Ғ */ case (char)0x93: strObj[i+1]=0x92; ++i; break;
       /* ҕ -> Ҕ */ case (char)0x95: strObj[i+1]=0x94; ++i; break;
       /* җ -> Җ */ case (char)0x97: strObj[i+1]=0x96; ++i; break;
       /* ҙ -> Ҙ */ case (char)0x99: strObj[i+1]=0x98; ++i; break;
       /* қ -> Қ */ case (char)0x9b: strObj[i+1]=0x9a; ++i; break;
       /* ҝ -> Ҝ */ case (char)0x9d: strObj[i+1]=0x9c; ++i; break;
       /* ҟ -> Ҟ */ case (char)0x9f: strObj[i+1]=0x9e; ++i; break;
       /* ҡ -> Ҡ */ case (char)0xa1: strObj[i+1]=0xa0; ++i; break;
       /* ң -> Ң */ case (char)0xa3: strObj[i+1]=0xa2; ++i; break;
       /* ҥ -> Ҥ */ case (char)0xa5: strObj[i+1]=0xa4; ++i; break;
       /* ҧ -> Ҧ */ case (char)0xa7: strObj[i+1]=0xa6; ++i; break;
       /* ҩ -> Ҩ */ case (char)0xa9: strObj[i+1]=0xa8; ++i; break;
       /* ҫ -> Ҫ */ case (char)0xab: strObj[i+1]=0xaa; ++i; break;
       /* ҭ -> Ҭ */ case (char)0xad: strObj[i+1]=0xac; ++i; break;
       /* ү -> Ү */ case (char)0xaf: strObj[i+1]=0xae; ++i; break;
       /* ұ -> Ұ */ case (char)0xb1: strObj[i+1]=0xb0; ++i; break;
       /* ҳ -> Ҳ */ case (char)0xb3: strObj[i+1]=0xb2; ++i; break;
       /* ҵ -> Ҵ */ case (char)0xb5: strObj[i+1]=0xb4; ++i; break;
       /* ҷ -> Ҷ */ case (char)0xb7: strObj[i+1]=0xb6; ++i; break;
       /* ҹ -> Ҹ */ case (char)0xb9: strObj[i+1]=0xb8; ++i; break;
       /* һ -> Һ */ case (char)0xbb: strObj[i+1]=0xba; ++i; break;
       /* ҽ -> Ҽ */ case (char)0xbd: strObj[i+1]=0xbc; ++i; break;
       /* ҿ -> Ҿ */ case (char)0xbf: strObj[i+1]=0xbe; ++i; break;
               }
               break;
             case (char)0xd3:
               switch(strObj[i+1])
               {
       /* ӂ -> Ӂ */ case (char)0x82: strObj[i+1]=0x81; ++i; break;
       /* ӄ -> Ӄ */ case (char)0x84: strObj[i+1]=0x83; ++i; break;
       /* ӆ -> Ӆ */ case (char)0x86: strObj[i+1]=0x85; ++i; break;
       /* ӈ -> Ӈ */ case (char)0x88: strObj[i+1]=0x87; ++i; break;
       /* ӊ -> Ӊ */ case (char)0x8a: strObj[i+1]=0x89; ++i; break;
       /* ӌ -> Ӌ */ case (char)0x8c: strObj[i+1]=0x8b; ++i; break;
       /* ӎ -> Ӎ */ case (char)0x8e: strObj[i+1]=0x8d; ++i; break;
       /* ӑ -> Ӑ */ case (char)0x91: strObj[i+1]=0x90; ++i; break;
       /* ӓ -> Ӓ */ case (char)0x93: strObj[i+1]=0x92; ++i; break;
       /* ӕ -> Ӕ */ case (char)0x95: strObj[i+1]=0x94; ++i; break;
       /* ӗ -> Ӗ */ case (char)0x97: strObj[i+1]=0x96; ++i; break;
       /* ә -> Ә */ case (char)0x99: strObj[i+1]=0x98; ++i; break;
       /* ӛ -> Ӛ */ case (char)0x9b: strObj[i+1]=0x9a; ++i; break;
       /* ӝ -> Ӝ */ case (char)0x9d: strObj[i+1]=0x9c; ++i; break;
       /* ӟ -> Ӟ */ case (char)0x9f: strObj[i+1]=0x9e; ++i; break;
       /* ӡ -> Ӡ */ case (char)0xa1: strObj[i+1]=0xa0; ++i; break;
       /* ӣ -> Ӣ */ case (char)0xa3: strObj[i+1]=0xa2; ++i; break;
       /* ӥ -> Ӥ */ case (char)0xa5: strObj[i+1]=0xa4; ++i; break;
       /* ӧ -> Ӧ */ case (char)0xa7: strObj[i+1]=0xa6; ++i; break;
       /* ө -> Ө */ case (char)0xa9: strObj[i+1]=0xa8; ++i; break;
       /* ӫ -> Ӫ */ case (char)0xab: strObj[i+1]=0xaa; ++i; break;
       /* ӭ -> Ӭ */ case (char)0xad: strObj[i+1]=0xac; ++i; break;
       /* ӯ -> Ӯ */ case (char)0xaf: strObj[i+1]=0xae; ++i; break;
       /* ӱ -> Ӱ */ case (char)0xb1: strObj[i+1]=0xb0; ++i; break;
       /* ӳ -> Ӳ */ case (char)0xb3: strObj[i+1]=0xb2; ++i; break;
       /* ӵ -> Ӵ */ case (char)0xb5: strObj[i+1]=0xb4; ++i; break;
       /* ӷ -> Ӷ */ case (char)0xb7: strObj[i+1]=0xb6; ++i; break;
       /* ӹ -> Ӹ */ case (char)0xb9: strObj[i+1]=0xb8; ++i; break;
       /* ӻ -> Ӻ */ case (char)0xbb: strObj[i+1]=0xba; ++i; break;
       /* ӽ -> Ӽ */ case (char)0xbd: strObj[i+1]=0xbc; ++i; break;
       /* ӿ -> Ӿ */ case (char)0xbf: strObj[i+1]=0xbe; ++i; break;
               }
               break;
             case (char)0xd4:
               switch(strObj[i+1])
               {
       /* ԁ -> Ԁ */ case (char)0x81: strObj[i+1]=0x80; ++i; break;
       /* ԃ -> Ԃ */ case (char)0x83: strObj[i+1]=0x82; ++i; break;
       /* ԅ -> Ԅ */ case (char)0x85: strObj[i+1]=0x84; ++i; break;
       /* ԇ -> Ԇ */ case (char)0x87: strObj[i+1]=0x86; ++i; break;
       /* ԉ -> Ԉ */ case (char)0x89: strObj[i+1]=0x88; ++i; break;
       /* ԋ -> Ԋ */ case (char)0x8b: strObj[i+1]=0x8a; ++i; break;
       /* ԍ -> Ԍ */ case (char)0x8d: strObj[i+1]=0x8c; ++i; break;
       /* ԏ -> Ԏ */ case (char)0x8f: strObj[i+1]=0x8e; ++i; break;
       /* ԑ -> Ԑ */ case (char)0x91: strObj[i+1]=0x90; ++i; break;
       /* ԓ -> Ԓ */ case (char)0x93: strObj[i+1]=0x92; ++i; break;
       /* ԕ -> Ԕ */ case (char)0x95: strObj[i+1]=0x94; ++i; break;
       /* ԗ -> Ԗ */ case (char)0x97: strObj[i+1]=0x96; ++i; break;
       /* ԙ -> Ԙ */ case (char)0x99: strObj[i+1]=0x98; ++i; break;
       /* ԛ -> Ԛ */ case (char)0x9b: strObj[i+1]=0x9a; ++i; break;
       /* ԝ -> Ԝ */ case (char)0x9d: strObj[i+1]=0x9c; ++i; break;
       /* ԟ -> Ԟ */ case (char)0x9f: strObj[i+1]=0x9e; ++i; break;
       /* ԡ -> Ԡ */ case (char)0xa1: strObj[i+1]=0xa0; ++i; break;
       /* ԣ -> Ԣ */ case (char)0xa3: strObj[i+1]=0xa2; ++i; break;
               }
               break;
             case (char)0xd5:
               switch(strObj[i+1])
               {
       /* ա -> Ա */ case (char)0xa1: strObj[i]=0xd4; strObj[i+1]=0xb1; ++i; break;
       /* բ -> Բ */ case (char)0xa2: strObj[i]=0xd4; strObj[i+1]=0xb2; ++i; break;
       /* գ -> Գ */ case (char)0xa3: strObj[i]=0xd4; strObj[i+1]=0xb3; ++i; break;
       /* դ -> Դ */ case (char)0xa4: strObj[i]=0xd4; strObj[i+1]=0xb4; ++i; break;
       /* ե -> Ե */ case (char)0xa5: strObj[i]=0xd4; strObj[i+1]=0xb5; ++i; break;
       /* զ -> Զ */ case (char)0xa6: strObj[i]=0xd4; strObj[i+1]=0xb6; ++i; break;
       /* է -> Է */ case (char)0xa7: strObj[i]=0xd4; strObj[i+1]=0xb7; ++i; break;
       /* ը -> Ը */ case (char)0xa8: strObj[i]=0xd4; strObj[i+1]=0xb8; ++i; break;
       /* թ -> Թ */ case (char)0xa9: strObj[i]=0xd4; strObj[i+1]=0xb9; ++i; break;
       /* ժ -> Ժ */ case (char)0xaa: strObj[i]=0xd4; strObj[i+1]=0xba; ++i; break;
       /* ի -> Ի */ case (char)0xab: strObj[i]=0xd4; strObj[i+1]=0xbb; ++i; break;
       /* լ -> Լ */ case (char)0xac: strObj[i]=0xd4; strObj[i+1]=0xbc; ++i; break;
       /* խ -> Խ */ case (char)0xad: strObj[i]=0xd4; strObj[i+1]=0xbd; ++i; break;
       /* ծ -> Ծ */ case (char)0xae: strObj[i]=0xd4; strObj[i+1]=0xbe; ++i; break;
       /* կ -> Կ */ case (char)0xaf: strObj[i]=0xd4; strObj[i+1]=0xbf; ++i; break;
       /* հ -> Հ */ case (char)0xb0: strObj[i+1]=0x80; ++i; break;
       /* ձ -> Ձ */ case (char)0xb1: strObj[i+1]=0x81; ++i; break;
       /* ղ -> Ղ */ case (char)0xb2: strObj[i+1]=0x82; ++i; break;
       /* ճ -> Ճ */ case (char)0xb3: strObj[i+1]=0x83; ++i; break;
       /* մ -> Մ */ case (char)0xb4: strObj[i+1]=0x84; ++i; break;
       /* յ -> Յ */ case (char)0xb5: strObj[i+1]=0x85; ++i; break;
       /* ն -> Ն */ case (char)0xb6: strObj[i+1]=0x86; ++i; break;
       /* շ -> Շ */ case (char)0xb7: strObj[i+1]=0x87; ++i; break;
       /* ո -> Ո */ case (char)0xb8: strObj[i+1]=0x88; ++i; break;
       /* չ -> Չ */ case (char)0xb9: strObj[i+1]=0x89; ++i; break;
       /* պ -> Պ */ case (char)0xba: strObj[i+1]=0x8a; ++i; break;
       /* ջ -> Ջ */ case (char)0xbb: strObj[i+1]=0x8b; ++i; break;
       /* ռ -> Ռ */ case (char)0xbc: strObj[i+1]=0x8c; ++i; break;
       /* ս -> Ս */ case (char)0xbd: strObj[i+1]=0x8d; ++i; break;
       /* վ -> Վ */ case (char)0xbe: strObj[i+1]=0x8e; ++i; break;
       /* տ -> Տ */ case (char)0xbf: strObj[i+1]=0x8f; ++i; break;
               }
               break;
        }
    }
    if (i == j)
    {
      switch(strObj[j])
      {
/* a -> A */ case (char)0x61: strObj[i] = 0x41; break;
/* b -> B */ case (char)0x62: strObj[i] = 0x42; break;
/* c -> C */ case (char)0x63: strObj[i] = 0x43; break;
/* d -> D */ case (char)0x64: strObj[i] = 0x44; break;
/* e -> E */ case (char)0x65: strObj[i] = 0x45; break;
/* f -> F */ case (char)0x66: strObj[i] = 0x46; break;
/* g -> G */ case (char)0x67: strObj[i] = 0x47; break;
/* h -> H */ case (char)0x68: strObj[i] = 0x48; break;
/* i -> I */ case (char)0x69: strObj[i] = 0x49; break;
/* j -> J */ case (char)0x6a: strObj[i] = 0x4a; break;
/* k -> K */ case (char)0x6b: strObj[i] = 0x4b; break;
/* l -> L */ case (char)0x6c: strObj[i] = 0x4c; break;
/* m -> M */ case (char)0x6d: strObj[i] = 0x4d; break;
/* n -> N */ case (char)0x6e: strObj[i] = 0x4e; break;
/* o -> O */ case (char)0x6f: strObj[i] = 0x4f; break;
/* p -> P */ case (char)0x70: strObj[i] = 0x50; break;
/* q -> Q */ case (char)0x71: strObj[i] = 0x51; break;
/* r -> R */ case (char)0x72: strObj[i] = 0x52; break;
/* s -> S */ case (char)0x73: strObj[i] = 0x53; break;
/* t -> T */ case (char)0x74: strObj[i] = 0x54; break;
/* u -> U */ case (char)0x75: strObj[i] = 0x55; break;
/* v -> V */ case (char)0x76: strObj[i] = 0x56; break;
/* w -> W */ case (char)0x77: strObj[i] = 0x57; break;
/* x -> X */ case (char)0x78: strObj[i] = 0x58; break;
/* y -> Y */ case (char)0x79: strObj[i] = 0x59; break;
/* z -> Z */ case (char)0x7a: strObj[i] = 0x5a; break;
      }
    }
    return strObj;
  }

//}

#endif /*NORMALIZATION_H_*/
