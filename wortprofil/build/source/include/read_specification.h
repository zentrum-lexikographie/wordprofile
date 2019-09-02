/**
 * 
 * Klassen zum Einlesen der Wortprofil-Spezifikation (XML)
 *
 **/

#ifndef READ_SPECIFICATION_H_
#define READ_SPECIFICATION_H_

  #include <expat.h>
  #include <sstream>
  #include <set>
  #include <limits>
  
  ///mögliche Tags
  static const string TAG_CONNECTIONS = "connections";  
  static const string TAG_CHECK = "check";  
  static const string TAG_SPECIFICATION = "build-specification";  
  static const string TAG_INPUT_FILE = "input";  

  static const string TAG_RELATION = "relation";  
  static const string TAG_RELATION_INVERTED = "relation-inverted";  
  static const string TAG_RELATION_BIDIRECTED = "relation-symetric";  
  static const string TAG_RELATION_FILE = "file";  
  static const string TAG_FILE = "file";  
  static const string TAG_SHORT_NAME = "short-name";
  static const string TAG_NAME = "name";
  static const string TAG_PRECUT = "pre-cut";
  static const string TAG_CUT_FREQUENCY = "cut-frequency";
  static const string TAG_CUT_WORDCOUNT = "cut-wordcount";
  static const string TAG_CUT_STATISTIC = "cut";

  static const string TAG_BIBL_INFO = "bibl-info";
  static const string TAG_BIBL_INFO_ITEM = "item";

  static const string TAG_BIBL_FIELD = "bibl-field";
  static const string TAG_BIBL_FIELDS = "bibl-fields";
  static const string TAG_BIBL_FIELD_DATE = "date";
  static const string TAG_BIBL_FIELD_ORIG = "orig";
  static const string TAG_BIBL_FIELD_SCAN = "scan";
  static const string TAG_BIBL_FIELD_AVAIL = "avail";
  static const string TAG_BIBL_FIELD_TEXTCLASS = "textclass";
  static const string TAG_BIBL_FIELD_SIGLE = "sigle";

  static const string TAG_INFO_PATH = "info-path";
  static const string TAG_INFO_ITEM_DATE = "date";
  static const string TAG_INFO_ITEM_TEXT = "text";
  static const string TAG_INFO_ITEM_ORIG = "orig";
  static const string TAG_INFO_ITEM_SCAN = "scan";
  static const string TAG_INFO_ITEM_AVAIL = "avail";
  static const string TAG_INFO_ITEM_TEXTCLASS = "textclass";
  static const string TAG_INFO_ITEM_SIGLE = "sigle";

  static const string TAG_CUT_STATISTIC_CORPUS = "cut-statistic-corpus";

  static const string TAG_CORPUS_NAME = "corpus-name";
  static const string TAG_CORPUS_NAME_ITEM = "item";
  static const string TAG_CORPUS_PATH = "corpus-path";
  static const string TAG_CORPUS_PATH_ITEM = "item";
  static const string TAG_CORPUS_LIMIT = "corpus-limit";
  static const string TAG_CORPUS_LIMIT_ITEM = "item";

  static const string TAG_GOOD_EXAMPLES = "good-examples";
  static const string TAG_GOOD_EXAMPLES_ITEM = "item";

  static const string TAG_POSITIVE_LIST = "positive-list";
  static const string TAG_NEGATIVE_LIST = "negative-list";
  static const string TAG_POSITIVE_LIST_FILE = "file";
  static const string TAG_NEGATIVE_LIST_FILE = "file";

  static const string TAG_DOUBLES = "doubles";
  static const string TAG_DOUBLES_FILE = "file";

  static const string TAG_STOPWORDS = "stopwords";
  static const string TAG_WORD = "word";

  static const string TAG_EXAMPLE = "example";
  static const string TAG_DESCRIPTION = "description";
  static const string TAG_SNIPPET = "snippet";

  static const string TAG_STOP = "stop";
  static const string TAG_REQUIRE = "req";

  static const string TAG_STATISTIC_LIMITS = "statistic-limits";
  static const string TAG_STATISTIC_ADJUST = "statistic-adjust";

  static const string TAG_STOP_DEPENDENTS = "stop-dependents";
  static const string TAG_STOP_HEADS = "stop-heads";
  static const string TAG_STOP_RELATIONS = "stop-relations";
  static const string TAG_STOP_CLASS = "syn-trigger";
  static const string TAG_CLASS = "class";

  static const string TAG_EXTENDED_SURFACE_FORM = "extended-surface-form";
  static const string TAG_POS_MAPPING = "POS-mapping";
  static const string TAG_POS_REWRITE = "POS-rewrite";
  static const string TAG_PREP_MAPPING = "prep-mapping";
  static const string TAG_LEMMA_MAPPING = "lemma-mapping";
  static const string TAG_RULE = "rule";

  static const string TAG_LEMMA_VARIATIONS = "lemma-variations";
  static const string TAG_STOP_LEMMA = "stop-lemma";

  static const string TAG_COLUMNS = "surface-info";
  static const string TAG_COLUMN = "item";


  ///mögliche Attribute
  static const string ATTRIBUTE_NUMBER = "pos";
  static const string ATTRIBUTE_PATH = "path";

  static const string ATTRIBUTE_FROM = "from";
  static const string ATTRIBUTE_TO = "to";
  static const string ATTRIBUTE_USE_AS_LEMMA = "use-as-lemma";
  static const string ATTRIBUTE_USE_AS_BASEFORM = "use-as-baseform";
  static const string ATTRIBUTE_SUPPRESS = "suppress";

  static const string ATTRIBUTE_USE_GLOBAL_CUT = "global-cut";

  static const string ATTRIBUTE_REL1 = "rel1";
  static const string ATTRIBUTE_REL2 = "rel2";
  static const string ATTRIBUTE_MIN_PERCENT = "min";
  static const string ATTRIBUTE_MAX_PERCENT = "max";
  static const string ATTRIBUTE_MIN_PERCENT_global = "min-global";
  static const string ATTRIBUTE_MAX_PERCENT_global = "max-global";
  static const string ATTRIBUTE_MIN_PERCENT_global_inv = "min-global-inv";
  static const string ATTRIBUTE_MAX_PERCENT_global_inv = "max-global-inv";
    
  static const string ATTRIBUTE_USER = "user";
  static const string ATTRIBUTE_HOST = "host";
  static const string ATTRIBUTE_PASSWD = "passwd";
  static const string ATTRIBUTE_DATABASE = "db";
  static const string ATTRIBUTE_SURFACE_MODE = "surface-mode";
  static const string ATTRIBUTE_USE_SUBCORPORA = "use-subcorpora";
  static const string ATTRIBUTE_VERSION = "version";
  static const string ATTRIBUTE_AUTHOR = "author";
  static const string ATTRIBUTE_TERNARY_RELATION_MODE = "ternary-relation-mode";
  static const string ATTRIBUTE_LEMMA_CUT = "lemma-cut";
  static const string ATTRIBUTE_CUT_REL = "rel-cut";
  static const string ATTRIBUTE_CUT_CONCORD = "concord-cut";

  static const string ATTRIBUTE_RELATION_PATH = "relation-path";
  static const string ATTRIBUTE_TABLE_PATH = "table-path";
  static const string ATTRIBUTE_CORPUS_PATH = "corpus-path";

  static const string ATTRIBUTE_CORPUS = "corpus";
    
  static const string ATTRIBUTE_MIN_LOCAL_DEP = "min-dep";
  static const string ATTRIBUTE_MIN_LOCAL_HEAD = "min-head";
  static const string ATTRIBUTE_MIN_GLOBAL_DEP = "min-g-dep";
  static const string ATTRIBUTE_MIN_GLOBAL_HEAD = "min-g-head";

  static const string ATTRIBUTE_MAX_LOCAL_DEP = "max-dep";
  static const string ATTRIBUTE_MAX_LOCAL_HEAD = "max-head";
  static const string ATTRIBUTE_MAX_GLOBAL_DEP = "max-g-dep";
  static const string ATTRIBUTE_MAX_GLOBAL_HEAD = "max-g-head";

  static const string ATTRIBUTE_MAX_CONCORDANCE_LINES = "max-concordance-lines";
  static const string ATTRIBUTE_MAX_STRING_LENGTH = "max-string-length";
  static const string ATTRIBUTE_MIN_CONCORDANCE_LINES = "min-concordance-lines";
  static const string ATTRIBUTE_MIN_STRING_LENGTH = "min-string-length";

  static const string ATTRIBUTE_MIN_FREQUENCY_PRECUT = "min-frequency";
  static const string ATTRIBUTE_MIN_FREQUENCY = "min-frequency";

  static const string ATTRIBUTE_MAX_FREQUENCY_PRECUT = "max-frequency";
  static const string ATTRIBUTE_MAX_FREQUENCY = "max-frequency";

  static const string ATTRIBUTE_MIN_MILOGFREQ = "min-MiLogFreq";
  static const string ATTRIBUTE_MIN_MI3 = "min-MI3";
  static const string ATTRIBUTE_MIN_CHISQUARE = "min-TScore";
  static const string ATTRIBUTE_MIN_LOGDICE = "min-logDice";
  static const string ATTRIBUTE_MIN_LOGLIKE = "min-logLike";

  static const string ATTRIBUTE_ADJUST_MILOGFREQ = "MiLogFreq";
  static const string ATTRIBUTE_ADJUST_MI3 = "MI3";
  static const string ATTRIBUTE_ADJUST_CHISQUARE = "TScore";
  static const string ATTRIBUTE_ADJUST_LOGDICE = "logDice";
  static const string ATTRIBUTE_ADJUST_LOGLIKE = "logLike";

  static const string ATTRIBUTE_MAX_MILOGFREQ = "max-MiLogFreq";
  static const string ATTRIBUTE_MAX_MI3 = "max-MI3";
  static const string ATTRIBUTE_MAX_CHISQUARE = "max-TScore";
  static const string ATTRIBUTE_MAX_LOGDICE = "max-logDice";
  static const string ATTRIBUTE_MAX_LOGLIKE = "max-logLike";

  static const string ATTRIBUTE_MIN_MILOGFREQ_CON = "min-MiLogFreq-con";
  static const string ATTRIBUTE_MIN_MI3_CON = "min-MI3-con";
  static const string ATTRIBUTE_MIN_CHISQUARE_CON = "min-TScore-con";
  static const string ATTRIBUTE_MIN_LOGDICE_CON = "min-logDice-con";
  static const string ATTRIBUTE_MIN_LOGLIKE_CON = "min-logLike-con";

  static const string ATTRIBUTE_MAX_MILOGFREQ_CON = "max-MiLogFreq-con";
  static const string ATTRIBUTE_MAX_MI3_CON = "max-MI3-con";
  static const string ATTRIBUTE_MAX_CHISQUARE_CON = "max-TScore-con";
  static const string ATTRIBUTE_MAX_LOGDICE_CON = "max-logDice-con";
  static const string ATTRIBUTE_MAX_LOGLIKE_CON = "max-logLike-con";

  static const string ATTRIBUTE_REVERSED = "invert";
  static const string ATTRIBUTE_DIRECTION = "direction";
  static const string ATTRIBUTE_NAME = "name";
  static const string ATTRIBUTE_SHORT_NAME = "short-name";
  static const string ATTRIBUTE_SNIPPET = "snippet";

  static const string VALUE_YES = "yes";
  static const string VALUE_HEAD = "head";
  static const string VALUE_DEPENDENT = "dependent";
  static const string VALUE_NO = "no";
  static const string VALUE_BIDIRECTIONAL = "bidirect";

  class ReadSpecification;

  /**
   *
   * Modus der Oberflächenform
   *
   **/
  enum SurfaceMode
  {
    MostFrequentTightLocal=0,
    MostFrequentLocal=1,
    MostFrequentGlobal=2
  };

  /**
   *
   * Anbindung der Präposition (zur Relation oder zum zweiten Wort)
   *
   **/
  enum TernaryRelationMode
  {
    AttachToWord=0,
    AttachToRelation=1
  };

  /**
   *
   * Mogliche Fehler beim Parsen
   *
   **/
  enum Error
  {
    ErrorAttribute = 0,
    ErrorTag = 1,
    ErrorValue = 2,
    ErrorNone = 3,
    ErrorData = 4,
    ErrorPathname = 5,
    ErrorDouble = 6
  };

  /**
   *
   * Relationsrichtung
   *
   **/
  enum Invert
  {
    ///normal
    InvertNo = 0,
    ///invertiert
    InvertYes = 1,
    ///normal und invertiert als unterschiedliche Relation
    InvertBidirect = 2,
    ///normal und invertiert als gleiche Relation
    InvertBidirectEQ = 3,
    ///undefiniert
    InvertUndef = 4
  };
  
  /**
   *
   * Modus für die Stoppwörter (Kopf oder Dependent)
   *
   **/
  enum StopwordMode
  {
    StopwordModeHead = 0,
    StopwordModeDependent = 1
  };

  /**
   * 
   * Klassen zur Repräsentation der transrelationalen Bedingungen bezüglich zweier Relationen (Schwellwerte)
   *   Es werden zwei Relationen in Beziehung gesetzt und es werden Kookkurrrenzen anhand eines Anteilvergleiches ausgeschlossen
   *
   **/
  class Connection
  {
    public:
      Connection():iMax(100),iMin(0),iMax_global(100),iMin_global(0),iMax_global_inv(100),iMin_global_inv(0){};
      
      ///Relation1
      string strRel1;
      ///Relation2
      string strRel2;

      ///minimaler und maximaler Anteil bezüglich eines Konkreten ersten Wortes
      unsigned int iMax;
      unsigned int iMin;
      ///minimaler und maximaler Anteil bezüglich keines Konkreten ersten Wortes
      unsigned int iMax_global;
      unsigned int iMin_global;
      ///minimaler und maximaler Anteil bezüglich keines Konkreten zweiten Wortes
      unsigned int iMax_global_inv;
      unsigned int iMin_global_inv;
  };

  /**
   * 
   * Information über den Ort der Bibliographischen Information
   *
   **/
	struct BiblInfo
	{
    ///Korpusname
    string strCorpus;
    ///Dateiname
    string strFile;
  };

  /**
   * 
   * Information über ein Bibl-Eintrag
   *
   **/
	struct BiblField
	{
    void clear()
    {
      strDate.clear();
      strAvail.clear();
      setAvailValue.clear();
      strOrig.clear();
      strScan.clear();
      strCorpus.clear();
      strSigle.clear();
    }
    ///Erscheinungsdatum
    string strDate;
    ///Rechteinformation
    string strAvail;
    set<string> setAvailValue;
    ///Textklasse
    string strTextclass;
    ///Orig-Bibl-String
    string strOrig;
    ///Scan-Bibl-String
    string strScan;
    ///Korpusname
    string strCorpus;
    ///Sigle
    string strSigle;
  };

  /**
   * 
   * ein String mit Kommagetrennten Teilstrings wird auf ein Set aus Strings abbilden
   *
   **/
  set<string> string_to_set(string strObj)
  {
    string::iterator it;
    string strDummy;
    set<string> setDummy;
    for (it = strObj.begin(); it != strObj.end(); ++it)
    {
      if (*it==',')
      {
        setDummy.insert(strDummy);
        strDummy.clear();
      }
      else
      {
        strDummy += *it;
      }
    }
    if (strDummy != "")
    {
      setDummy.insert(strDummy);
    }
    return setDummy;
  }

  /**
   * 
   * Trigger-Informationen für das Gewichten der Kookkurrenzen
   *
   **/
	struct TriggerInfo
	{
    ///die betreffenden POS-Tags vom ersten und zweiten Wort
		set<string> setPOS1;
		set<string> setPOS2;
    ///Gewicht
		float iScore;
	};

  /**
   * 
   * Klasse zur Repräsentation einer Relationsspezifikation
   *
   **/
  class Specification
  {
    friend class ReadSpecification;
    
    public:

      Specification():
        ///minimale Schwellwerte
        iMinLocalDepFrequency(0),
        iMinGlobalHeadFrequency(0),
        iMinLocalHeadFrequency(0),
        iMinGlobalDepFrequency(0),
        iMinFrequency(0),
        iMinMiLogFreq(-numeric_limits<float>::max()),
        iMinMI3(-numeric_limits<float>::max()),
        iMinTScore(-numeric_limits<float>::max()),
        iMinLogDice(-numeric_limits<float>::max()),
        iMinLogLike(-numeric_limits<float>::max()),

        iMinMiLogFreq_con(-numeric_limits<float>::max()),
        iMinMI3_con(-numeric_limits<float>::max()),
        iMinTScore_con(-numeric_limits<float>::max()),
        iMinLogDice_con(-numeric_limits<float>::max()),
        iMinLogLike_con(-numeric_limits<float>::max()),

        iMinFrequencyCorpus(0),
        iMinMiLogFreqCorpus(-numeric_limits<float>::max()),
        iMinMI3Corpus(-numeric_limits<float>::max()),
        iMinTScoreCorpus(-numeric_limits<float>::max()),
        iMinLogDiceCorpus(-numeric_limits<float>::max()),
        iMinLogLikeCorpus(-numeric_limits<float>::max()),

        iMinMiLogFreqCorpus_con(-numeric_limits<float>::max()),
        iMinMI3Corpus_con(-numeric_limits<float>::max()),
        iMinTScoreCorpus_con(-numeric_limits<float>::max()),
        iMinLogDiceCorpus_con(-numeric_limits<float>::max()),
        iMinLogLikeCorpus_con(-numeric_limits<float>::max()),

        ///justieren der Statistikwerte
        iAdjustMiLogFreq(0),
        iAdjustMI3(0),
        iAdjustTScore(0),
        iAdjustLogDice(0),
        iAdjustLogLike(0),

        ///maximale Schwellwerte
        iMaxLocalDepFrequency(numeric_limits<unsigned int>::max()),
        iMaxGlobalHeadFrequency(numeric_limits<unsigned int>::max()),
        iMaxLocalHeadFrequency(numeric_limits<unsigned int>::max()),
        iMaxGlobalDepFrequency(numeric_limits<unsigned int>::max()),
        iMaxFrequency(numeric_limits<unsigned int>::max()),
        iMaxMiLogFreq(numeric_limits<float>::max()),
        iMaxMI3(numeric_limits<float>::max()),
        iMaxTScore(numeric_limits<float>::max()),
        iMaxLogDice(numeric_limits<float>::max()),
        iMaxLogLike(numeric_limits<float>::max()),
        iMaxMiLogFreq_con(numeric_limits<float>::max()),
        iMaxMI3_con(numeric_limits<float>::max()),
        iMaxTScore_con(numeric_limits<float>::max()),
        iMaxLogDice_con(numeric_limits<float>::max()),
        iMaxLogLike_con(numeric_limits<float>::max()),

        iMaxFrequencyCorpus(numeric_limits<unsigned int>::max()),
        iMaxMiLogFreqCorpus(numeric_limits<float>::max()),
        iMaxMI3Corpus(numeric_limits<float>::max()),
        iMaxTScoreCorpus(numeric_limits<float>::max()),
        iMaxLogDiceCorpus(numeric_limits<float>::max()),
        iMaxLogLikeCorpus(numeric_limits<float>::max()),
        iMaxMiLogFreqCorpus_con(numeric_limits<float>::max()),
        iMaxMI3Corpus_con(numeric_limits<float>::max()),
        iMaxTScoreCorpus_con(numeric_limits<float>::max()),
        iMaxLogDiceCorpus_con(numeric_limits<float>::max()),
        iMaxLogLikeCorpus_con(numeric_limits<float>::max()),

        ///Berechnungsmodi
        bUseGlobalCut(true),
        bUseLemmaCut(false)
      {
      }
      
      /**
       * Zurückgeben der Relationsbeschreibubg
       **/
      const string& description() const
      {
        return strDescription;
      }
      /**
       * Zurückgeben des Relationsbeispiels
       **/
      const string& example() const
      {
        return strExample;
      }
      /**
       * Zurückgeben des Relationssnippet
       **/
      const string& snippet() const
      {
        return strSnippet;
      }
      /**
       * Zurückgeben des Relationsnamens
       **/
      const string& functionname() const
      {
        return strFunctionname;
      }
      /**
       * ob die Relation ignoriert werden soll
       **/
      bool ignore() const
      {
        return bIgnore;
      }
      /**
       * Zurückgeben der Minimalen Frequenz der Dependenten über alle Relationen
       **/
      const unsigned int min_global_dep_frequency() const
      {
        return iMinGlobalDepFrequency;
      }
      /**
       * Zurückgeben der Minimalen Frequenz der Dependenten über die Bestimmte Relation
       **/
      const unsigned int min_local_dep_frequency() const
      {
        return iMinLocalDepFrequency;
      }
      /**
       * Zurückgeben der minimalen Frequenz der Köpfe über alle Relationen
       **/
      const unsigned int min_global_head_frequency() const
      {
        return iMinGlobalHeadFrequency;
      }
      /**
       * Zurückgeben der minimalen Frequenz der Köpfe über die Bestimmte Relation
       **/
      const unsigned int min_local_head_frequency() const
      {
        return iMinLocalHeadFrequency;
      }
      /**
       * Zurückgeben der minimalen Vorkommen (ohne Doppelte) der Dependenten über alle Relationen
       **/
      const unsigned int min_global_dep_wordcount() const
      {
        return iMinGlobalDepWordcount;
      }
      /**
       * Zurückgeben der minimalen Vorkommen (ohne Doppelte) der Dependenten über die bestimmte Relation
       **/
      const unsigned int min_local_dep_wordcount() const
      {
        return iMinLocalDepWordcount;
      }
      /**
       * Zurückgeben der minimalen Vorkommen (ohne Doppelte) der Köpfe über alle Relationen
       **/
      const unsigned int min_global_head_wordcount() const
      {
        return iMinGlobalHeadWordcount;
      }
      /**
       * Zurückgeben der minimalen Vorkommen (ohne Doppelte) der Köpfe über die bestimmte Relation
       **/
      const unsigned int min_local_head_wordcount() const
      {
        return iMinLocalHeadWordcount;
      }
      /**
       * Ob es einen globalen Schwellwert für die Lemmafrequenz gibt
       **/
      const bool use_lemma_cut() const
      {
        return bUseLemmaCut;
      }
      /**
       * Justierungswert für MiLogFreq
       **/
      const float adjust_MiLogFreq() const
      {
        return iAdjustMiLogFreq;
      }
      /**
       * Justierungswert für MI3
       **/
      const float adjust_MI3() const
      {
        return iAdjustMI3;
      }
      /**
       * Justierungswert für MI3
       **/
      const float adjust_TScore() const
      {
        return iAdjustTScore;
      }
      /**
       * Justierungswert für LogDice
       **/
      const float adjust_logDice() const
      {
        return iAdjustLogDice;
      }
      /**
       * Justierungswert für LogLike
       **/
      const float adjust_logLike() const
      {
        return iAdjustLogLike;
      }
      /**
       * Zurückgeben des minimalen Frequenzwertes
       **/
      const unsigned int min_frequency() const
      {
        return iMinFrequency;
      }
      /**
       * Zurückgeben des minimalen MiLogFreq-Wertes
       **/
      const float min_MiLogFreq() const
      {
        return iMinMiLogFreq;
      }
      /**
       * Zurückgeben des minimalen MI3-Wertes
       **/
      const float min_MI3() const
      {
        return iMinMI3;
      }
      /**
       * Zurückgeben des minimalen TScore-Wertes
       **/
      const float min_TScore() const
      {
        return iMinTScore;
      }
      /**
       * Zurückgeben des minimalen LogDice-Wertes
       **/
      const float min_logDice() const
      {
        return iMinLogDice;
      }
      /**
       * Zurückgeben des minimalen LogLike-Wertes
       **/
      const float min_logLike() const
      {
        return iMinLogLike;
      }
      /**
       * Zurückgeben des minimalen LogLike-Wertes (lokal für eine bestimmte syntaktische Relation)
       **/
      const float min_MiLogFreq_con() const
      {
        return iMinMiLogFreq_con;
      }
      /**
       * Zurückgeben des minimalen MI3-Wertes (lokal für eine bestimmte syntaktische Relation)
       **/
      const float min_MI3_con() const
      {
        return iMinMI3_con;
      }
      /**
       * Zurückgeben des minimalen TScore-Wertes (lokal für eine bestimmte syntaktische Relation)
       **/
      const float min_TScore_con() const
      {
        return iMinTScore_con;
      }
      /**
       * Zurückgeben des minimalen LogDice-Wertes (lokal für eine bestimmte syntaktische Relation)
       **/
      const float min_logDice_con() const
      {
        return iMinLogDice_con;
      }
      /**
       * Zurückgeben des minimalen LogLike-Wertes (lokal für eine bestimmte syntaktische Relation)
       **/
      const float min_logLike_con() const
      {
        return iMinLogLike_con;
      }
      /**
       * Zurückgeben des minimalen Frequenzwertes (für einen bestimmten Korpus)
       **/
      const unsigned int min_frequency_corpus() const
      {
        return iMinFrequencyCorpus;
      }
      /**
       * Zurückgeben des minimalen MiLogFreq-Wertes (für einen bestimmten Korpus)
       **/
      const float min_MiLogFreq_corpus() const
      {
        return iMinMiLogFreqCorpus;
      }
      /**
       * Zurückgeben des minimalen MI3-Wertes (für einen bestimmten Korpus)
       **/
      const float min_MI3_corpus() const
      {
        return iMinMI3Corpus;
      }
      /**
       * Zurückgeben des minimalen TScore-Wertes (für einen bestimmten Korpus)
       **/
      const float min_TScore_corpus() const
      {
        return iMinTScoreCorpus;
      }
      /**
       * Zurückgeben des minimalen LogDice-Wertes (für einen bestimmten Korpus)
       **/
      const float min_logDice_corpus() const
      {
        return iMinLogDiceCorpus;
      }
      /**
       * Zurückgeben des minimalen LogLike-Wertes (für einen bestimmten Korpus)
       **/
      const float min_logLike_corpus() const
      {
        return iMinLogLikeCorpus;
      }
      /**
       * Zurückgeben des minimalen MiLogFreq-Wertes (für einen bestimmten Korpus und eine bestimmte syntaktische Relation)
       **/
      const float min_MiLogFreq_corpus_con() const
      {
        return iMinMiLogFreqCorpus_con;
      }
      /**
       * Zurückgeben des minimalen MI3-Wertes (für einen bestimmten Korpus und eine bestimmte syntaktische Relation)
       **/
      const float min_MI3_corpus_con() const
      {
        return iMinMI3Corpus_con;
      }
      /**
       * Zurückgeben des minimalen TScore-Wertes (für einen bestimmten Korpus und eine bestimmte syntaktische Relation)
       **/
      const float min_TScore_corpus_con() const
      {
        return iMinTScoreCorpus_con;
      }
      /**
       * Zurückgeben des minimalen LogDice-Wertes (für einen bestimmten Korpus und eine bestimmte syntaktische Relation)
       **/
      const float min_logDice_corpus_con() const
      {
        return iMinLogDiceCorpus_con;
      }
      /**
       * Zurückgeben des minimalen LogLike-Wertes (für einen bestimmten Korpus und eine bestimmte syntaktische Relation)
       **/
      const float min_logLike_corpus_con() const
      {
        return iMinLogLikeCorpus_con;
      }
      /**
       * Zurückgeben des maximalen Frequenzwertes (für einen bestimmten Korpus)
       **/
      const unsigned int max_frequency_corpus() const
      {
        return iMaxFrequencyCorpus;
      }
      /**
       * Zurückgeben des maximalen MiLogFreq-Wertes (für einen bestimmten Korpus)
       **/
      const float max_MiLogFreq_corpus() const
      {
        return iMaxMiLogFreqCorpus;
      }
      /**
       * Zurückgeben des maximalen MI3-Wertes (für einen bestimmten Korpus)
       **/
      const float max_MI3_corpus() const
      {
        return iMaxMI3Corpus;
      }
      /**
       * Zurückgeben des maximalen TScore-Wertes (für einen bestimmten Korpus)
       **/
      const float max_TScore_corpus() const
      {
        return iMaxTScoreCorpus;
      }
      /**
       * Zurückgeben des maximalen LogDice-Wertes (für einen bestimmten Korpus)
       **/
      const float max_logDice_corpus() const
      {
        return iMaxLogDiceCorpus;
      }
      /**
       * Zurückgeben des maximalen LogLike-Wertes (für einen bestimmten Korpus)
       **/
      const float max_logLike_corpus() const
      {
        return iMaxLogLikeCorpus;
      }
      /**
       * Zurückgeben des maximalen MiLogFreq-Wertes (für einen bestimmten Korpus und eine bestimmte syntaktische Relation)
       **/
      const float max_MiLogFreq_corpus_con() const
      {
        return iMaxMiLogFreqCorpus_con;
      }
      /**
       * Zurückgeben des maximalen MI3-Wertes (für einen bestimmten Korpus und eine bestimmte syntaktische Relation)
       **/
      const float max_MI3_corpus_con() const
      {
        return iMaxMI3Corpus_con;
      }
      /**
       * Zurückgeben des maximalen TScore-Wertes (für einen bestimmten Korpus und eine bestimmte syntaktische Relation)
       **/
      const float max_TScore_corpus_con() const
      {
        return iMaxTScoreCorpus_con;
      }
      /**
       * Zurückgeben des maximalen LogDice-Wertes (für einen bestimmten Korpus und eine bestimmte syntaktische Relation)
       **/
      const float max_logDice_corpus_con() const
      {
        return iMaxLogDiceCorpus_con;
      }
      /**
       * Zurückgeben des maximalen LogLike-Wertes (für einen bestimmten Korpus und eine bestimmte syntaktische Relation)
       **/
      const float max_logLike_corpus_con() const
      {
        return iMaxLogLikeCorpus_con;
      }
      /**
       * Zurückgeben des maximalen Frequenz für einen Dependenten bezüglich allen Köpfen
       **/
      const unsigned int max_global_dep_frequency() const
      {
        return iMaxGlobalDepFrequency;
      }
      /**
       * Zurückgeben des maximalen Frequenz für einen Dependenten bezüglich eines bestimmten Kopfes
       **/
      const unsigned int max_local_dep_frequency() const
      {
        return iMaxLocalDepFrequency;
      }
      /**
       * Zurückgeben des maximalen Frequenz für einen Kopf
       **/
      const unsigned int max_global_head_frequency() const
      {
        return iMaxGlobalHeadFrequency;
      }
      /**
       * Zurückgeben des maximalen Frequenz für einen Kopf bezüglich eines bestimmten Dependenten
       **/
      const unsigned int max_local_head_frequency() const
      {
        return iMaxLocalHeadFrequency;
      }
      /**
       * Zurückgeben des maximalen Vorkommens (ohne Doppelte) für einen Dependenten
       **/
      const unsigned int max_global_dep_wordcount() const
      {
        return iMaxGlobalDepWordcount;
      }
      /**
       * Zurückgeben des maximalen Vorkommens (ohne Doppelte) für einen Dependenten bezüglich eines bestimmten Kopfes
       **/
      const unsigned int max_local_dep_wordcount() const
      {
        return iMaxLocalDepWordcount;
      }
      /**
       * Zurückgeben des maximalen Vorkommens (ohne Doppelte) für einen Kopf
       **/
      const unsigned int max_global_head_wordcount() const
      {
        return iMaxGlobalHeadWordcount;
      }
      /**
       * Zurückgeben des maximalen Vorkommens (ohne Doppelte) für einen Kopf bezüglich eines bestimmten Dependenten
       **/
      const unsigned int max_local_head_wordcount() const
      {
        return iMaxLocalHeadWordcount;
      }
      /**
       * Zurückgeben des maximalen Frequenzwertes
       **/
      const unsigned int max_frequency() const
      {
        return iMaxFrequency;
      }
      /**
       * Zurückgeben des maximalen MiLogFreq-Wertes
       **/
      const float max_MiLogFreq() const
      {
        return iMaxMiLogFreq;
      }
      /**
       * Zurückgeben des maximalen MI3-Wertes
       **/
      const float max_MI3() const
      {
        return iMaxMI3;
      }
      /**
       * Zurückgeben des maximalen TScore-Wertes
       **/
      const float max_TScore() const
      {
        return iMaxTScore;
      }
      /**
       * Zurückgeben des maximalen logDice-Wertes
       **/
      const float max_logDice() const
      {
        return iMaxLogDice;
      }
      /**
       * Zurückgeben des maximalen logLike-Wertes
       **/
      const float max_logLike() const
      {
        return iMaxLogLike;
      }
      /**
       * Zurückgeben des maximalen MiLogFreq-Wertes für eine bestimmte syntaktische Relation
       **/
      const float max_MiLogFreq_con() const
      {
        return iMaxMiLogFreq_con;
      }
      /**
       * Zurückgeben des maximalen MI3-Wertes für eine bestimmte syntaktische Relation
       **/
      const float max_MI3_con() const
      {
        return iMaxMI3_con;
      }
      /**
       * Zurückgeben des maximalen TScore-Wertes für eine bestimmte syntaktische Relation
       **/
      const float max_TScore_con() const
      {
        return iMaxTScore_con;
      }
      /**
       * Zurückgeben des maximalen LogDice-Wertes für eine bestimmte syntaktische Relation
       **/
      const float max_logDice_con() const
      {
        return iMaxLogDice_con;
      }
      /**
       * Zurückgeben des maximalen LogLike-Wertes für eine bestimmte syntaktische Relation
       **/
      const float max_logLike_con() const
      {
        return iMaxLogLike_con;
      }
      
      /**
       * Prüfen ob bei einem Kopf ein Stopwort vorliegt
       **/
      bool is_stopword_head(const string& strObj) const
      {
        map<string,StopwordMode>::const_iterator it;
        it = mapStopwords.find(strObj);
        if (it != mapStopwords.end())
        {
          if (it->second == StopwordModeHead)
          {
            return true;
          }
        }
        return false;
      }

      /**
       * Prüfen ob bei einem Dependenten ein Stopwort vorliegt
       **/
      bool is_stopword_dependent(const string& strObj) const
      {
        map<string,StopwordMode>::const_iterator it;
        it = mapStopwords.find(strObj);
        if (it != mapStopwords.end())
        {
          if (it->second == StopwordModeDependent)
          {
            return true;
          }
        }
        return false;
      }
      
      /**
       * Löschen und Default-Werte setzen
       **/
      void clear()
      {
        strFunctionname.clear();
        bIgnore=false;

        strSnippet.clear();
        iMinLocalHeadFrequency=0;
        iMinGlobalHeadFrequency=0;
        iMinLocalDepFrequency=0;
        iMinGlobalDepFrequency=0;
        iMinLocalHeadWordcount=0;
        iMinGlobalHeadWordcount=0;
        iMinLocalDepWordcount=0;
        iMinGlobalDepWordcount=0;
        iMinFrequency=0;
        iMinMiLogFreq=-numeric_limits<float>::max();
        iMinMI3=-numeric_limits<float>::max();
        iMinTScore=-numeric_limits<float>::max();
        iMinLogDice=-numeric_limits<float>::max();

        iAdjustMiLogFreq=0;
        iAdjustMI3=0;
        iAdjustTScore=0;
        iAdjustLogDice=0;

        iMinFrequencyCorpus=0;
        iMinMiLogFreqCorpus=-numeric_limits<float>::max();
        iMinMI3Corpus=-numeric_limits<float>::max();
        iMinTScoreCorpus=-numeric_limits<float>::max();
        iMinLogDiceCorpus=-numeric_limits<float>::max();
        iMinLogLikeCorpus=-numeric_limits<float>::max();

        iMaxLocalHeadFrequency=numeric_limits<unsigned int>::max();
        iMaxGlobalHeadFrequency=numeric_limits<unsigned int>::max();
        iMaxLocalDepFrequency=numeric_limits<unsigned int>::max();
        iMaxGlobalDepFrequency=numeric_limits<unsigned int>::max();
        iMaxLocalHeadWordcount=numeric_limits<unsigned int>::max();
        iMaxGlobalHeadWordcount=numeric_limits<unsigned int>::max();
        iMaxLocalDepWordcount=numeric_limits<unsigned int>::max();
        iMaxGlobalDepWordcount=numeric_limits<unsigned int>::max();
        iMaxFrequency=numeric_limits<unsigned int>::max();
        iMaxMiLogFreq=numeric_limits<float>::max();;
        iMaxMI3=numeric_limits<float>::max();
        iMaxTScore=numeric_limits<float>::max();;
        iMaxLogDice=numeric_limits<float>::max();;
        iMaxLogLike=numeric_limits<float>::max();

        bUseGlobalCut=true;
        bUseLemmaCut=false;
        mapStopwords.clear();

        strExample.clear();
        strDescription.clear();
      }

      map<string,Specification> mapSpec;
    private:
            
      ///Relationsbeschreibung  
      string strExample;
      string strDescription;
      string strFunctionname;
      string strSnippet;

      ///minimale Schwellwerte
      unsigned int iMinFrequency;
      float iMinMiLogFreq;
      float iMinMI3;
      float iMinTScore;
      float iMinLogDice;      
      float iMinLogLike;      

      ///minimale Schwellwerte für Dependenten und Köpfe
      unsigned int iMinLocalHeadFrequency;
      unsigned int iMinGlobalHeadFrequency;
      unsigned int iMinLocalDepFrequency;
      unsigned int iMinGlobalDepFrequency;
      unsigned int iMinLocalHeadWordcount;
      unsigned int iMinGlobalHeadWordcount;
      unsigned int iMinLocalDepWordcount;	
      unsigned int iMinGlobalDepWordcount;

      ///minimale Schwellwerte bezüglich syntaktischer Relationen
      float iMinMiLogFreq_con;
      float iMinMI3_con;
      float iMinTScore_con;
      float iMinLogDice_con;      
      float iMinLogLike_con;      

      ///minimale Schwellwerte bezüglich bestimmter Korpora
      unsigned int iMinFrequencyCorpus;
      float iMinMiLogFreqCorpus;
      float iMinMI3Corpus;
      float iMinTScoreCorpus;
      float iMinLogDiceCorpus;      
      float iMinLogLikeCorpus;      

      ///minimale Schwellwerte bezüglich bestimmter Korpora und syntaktischer Relation
      float iMinMiLogFreqCorpus_con;
      float iMinMI3Corpus_con;
      float iMinTScoreCorpus_con;
      float iMinLogDiceCorpus_con;      
      float iMinLogLikeCorpus_con;      

      ///maximale Schwellwerte
      unsigned int iMaxFrequency;
      float iMaxMiLogFreq;
      float iMaxMI3;
      float iMaxTScore;
      float iMaxLogDice;      
      float iMaxLogLike;      

      ///maximale Schwellwerte für Dependenten und Köpfe
      unsigned int iMaxLocalHeadFrequency;
      unsigned int iMaxGlobalHeadFrequency;
      unsigned int iMaxLocalDepFrequency;
      unsigned int iMaxGlobalDepFrequency;
      unsigned int iMaxLocalHeadWordcount;
      unsigned int iMaxGlobalHeadWordcount;
      unsigned int iMaxLocalDepWordcount;
      unsigned int iMaxGlobalDepWordcount;

      ///maximale Schwellwerte bezüglich syntaktischer Relationen
      float iMaxMiLogFreq_con;
      float iMaxMI3_con;
      float iMaxTScore_con;
      float iMaxLogDice_con;      
      float iMaxLogLike_con;      

      ///maximale Schwellwerte bezüglich bestimmter Korpora
      unsigned int iMaxFrequencyCorpus;
      float iMaxMiLogFreqCorpus;
      float iMaxMI3Corpus;
      float iMaxTScoreCorpus;
      float iMaxLogDiceCorpus;      
      float iMaxLogLikeCorpus;      

      ///maximale Schwellwerte bezüglich bestimmter Korpora und syntaktischer Relation
      float iMaxMiLogFreqCorpus_con;
      float iMaxMI3Corpus_con;
      float iMaxTScoreCorpus_con;
      float iMaxLogDiceCorpus_con;      
      float iMaxLogLikeCorpus_con;      
       
      ///justieren der Statistikwerte
      float iAdjustMiLogFreq;
      float iAdjustMI3;
      float iAdjustTScore;
      float iAdjustLogDice;      
      float iAdjustLogLike;      

      ///globale Schalter
      bool bUseGlobalCut;
      bool bUseLemmaCut;
      bool bIgnore;

      ///Map für die Stoppwörter
      map<string,StopwordMode> mapStopwords;
  };
  
  /**
   *
   * Klasse für die Repräsentation einer Input-Spezifikation (Relation)
   *
   **/
  class Specifications
  {
    public:
      Specifications():
        iMaxStringLength(numeric_limits<unsigned int>::max()),
        iMaxConcordanceLines(numeric_limits<unsigned int>::max()),
        iMinFrequency(0),      
        eInvert(InvertUndef),
        bIgnorePrep(false),
        bUseSurfaceAsLemma(false),
        bUseBaseformAsSurface1(false),
        bUseBaseformAsSurface2(false),
        strPositiveFilter(),
        strNegativeFilter()
      {
      }
      
      /**
       * Löschen und Default-Werte setzen
       **/
      void clear()
      {
        CSpecification1.clear();
        CSpecification2.clear();
        strPathname.clear();
        strFilename.clear();
        setFilename.clear();
        eInvert = InvertUndef;
        iMinFrequency = 0;
        iMaxStringLength=numeric_limits<unsigned int>::max();
        iMaxConcordanceLines=numeric_limits<unsigned int>::max();
        iMaxFrequency = numeric_limits<unsigned int>::max();
        iMinStringLength=0;
        iMinConcordanceLines=0;
        bIgnorePrep=false;
        bUseSurfaceAsLemma=false;
        bUseBaseformAsSurface1=false;
        bUseBaseformAsSurface2=false;
        strPositiveFilter.clear();
        strNegativeFilter.clear();
      }
      /**
       * Zürückgeben der involvierten Relationsdateien
       **/
      const set<pair<string,string> >& filenames() const
      {
        return setFilename;
      }
      /**
       * Zürückgeben der ersten Grundspezifikation (grundlegende Relation)
       **/
      const Specification& specification_1() const
      {
        return CSpecification1;
      }
      /**
       * Zürückgeben der zweiten Grundspezifikation (umgedrehte Relation)
       **/
      const Specification& specification_2() const
      {
        return CSpecification2;
      }
      /**
       * Zürückgeben des Modus der Relation (symmetrisch, gerichtet, ...)
       **/
      const Invert invert() const
      {
        return eInvert;
      }
      /**
       * minimaler Frequenzwert
       **/
      const unsigned int min_frequency() const
      {
        return iMinFrequency;
      }
      /**
       * maximale Zeichenkettenlänge
       **/
      const unsigned int max_string_length() const
      {
        return iMaxStringLength;
      }
      /**
       * maximale Anzahl an Fundstellen
       **/
      const unsigned int max_concordance_lines() const
      {
        return iMaxConcordanceLines;
      }
      /**
       * Dateiname für eine positive Filterdatei
       **/
      const string positive_filter() const
      {
        return strPositiveFilter;
      }
      /**
       * Dateiname für eine negative Filterdatei
       **/
      const string negative_filter() const
      {
        return strNegativeFilter;
      }
      /**
       * maximaler Frequenzwert
       **/
      const unsigned int max_frequency() const
      {
        return iMaxFrequency;
      }
      /**
       * minimale Zeichenkettenlänge
       **/
      const unsigned int min_string_length() const
      {
        return iMinStringLength;
      }
      /**
       * minimale Anzahl an Fundstellen
       **/
      const unsigned int min_concordance_lines() const
      {
        return iMinConcordanceLines;
      }
      ///erste Grundspezifikation
      Specification CSpecification1;
      ///zweite Grundspezifikation
      Specification CSpecification2;

      ///die einbezogenen Relationsdateinen
      string strPathname;
      string strFilename;
      set<pair<string,string> > setFilename;

      ///Schwellwerte
      unsigned int iMaxConcordanceLines;
      unsigned int iMaxStringLength;
      unsigned int iMinFrequency;
      unsigned int iMinConcordanceLines;
      unsigned int iMinStringLength;
      unsigned int iMaxFrequency;
      
      ///Filter für die Dateinamen
      string strPositiveFilter;
      string strNegativeFilter;

      ///globale Modi
      Invert eInvert;
      bool bIgnorePrep;
      bool bUseSurfaceAsLemma;
      bool bUseBaseformAsSurface1;
      bool bUseBaseformAsSurface2;
  };
  
  /**
   *
   * Klasse zum Einlesen der Spezifikation
   *
   **/
  class ReadSpecification
  {
    public:
    
      ReadSpecification():
      eSurfaceMode(MostFrequentTightLocal),    
      eTernaryRelationMode(AttachToRelation),
      iLemmaCut(numeric_limits<int>::max()),
      iRelCut(0),
      iConcordCut(0),
      bUseSubcorpora(false),
      strVersion(""),
      strEmpty("")
      {};
    
      /**  
      * @brief parsen der XML-Specification 
      * @param strFilename Dateiname der XML-Speccification
      * @param true, wenn kein Fehler aufgetreten ist
      */
      bool parse_xml(const string& strFilename);

      /**
      * @brief zurückgeben der spezifikationsinformationen 
      * @return die spezifikationsinformationen
      */
      const vector<Specifications>& get_specifications() const;
      const vector<Connection>& get_connections() const;
      
      hash_map<string,unsigned int> get_pos_mapping();
      const string& pos_mapping(const string& strObj);
      const string& prep_mapping(const string& strObj);
      const string& lemma_mapping(const string& strObj);
      const bool use_surface_as_lemma_by_pos(const string& strObj);
      const bool use_surface_as_baseform_by_pos(const string& strObj);
      const bool is_suppressed(const string& strObj);
      
      const map<string,vector<unsigned int> >& columns() const;
      const map<string,string >& corpus_path() const;
      const map<string,string >& corpus_name() const;
      const map<string,string >& corpus_limit() const;
      const vector<string >& corpus_order() const;
		  const hash_set<string>& stop_relations() const;
		  const hash_set<string>& stop_dependents() const;
		  const hash_set<string>& stop_heads() const;
		  const hash_map<string,TriggerInfo>& stop_class() const;
		  const hash_map<string,TriggerInfo>& stop_class_func() const;
		  const hash_map<string,string>& surface1_trigger() const;
		  const hash_map<string,string>& surface2_trigger() const;
		  const hash_map<string,string>& surface1_stop() const;
		  const hash_map<string,string>& surface2_stop() const;
		  const hash_map<string,TriggerInfo>& req_class() const;
		  const hash_map<string,map<string,TriggerInfo> >& req_class_func() const;
      const set<string>& doubles() const;
      const string& lemma_variations() const;
      const string& stop_lemma() const;

      const map<string,map<string,int> >& good_examples() const;

      const map<pair<string,string>,string >& get_pos_rewrite() const;

      const set<string>& positive_list() const;
      const set<string>& negative_list() const;

      const map<string,BiblInfo>& bibl_info() const;
      const map<string,BiblField>& bibl_fields() const;

      const BiblField& bibl_field() const;
      const string& user() const; 
      const string& host() const; 
      const string& passwd() const; 
      const string& database() const; 
      SurfaceMode surface_mode() const; 
      bool use_subcorpora() const; 
      string version() const; 
      string author() const; 
      TernaryRelationMode ternary_relation_mode() const; 
      int lemma_cut() const; 
      int rel_cut() const; 
      int concord_cut() const;


      string relation_path() const; 
      string table_path() const; 
      string global_corpus_path() const; 
      string tmp_path() const; 

      /**
       * Ob eine Relation umgedreht ist
       **/
      bool is_inverted_relation(const string& strObj) const
      {
	      set<string>::const_iterator it;
	      it = mapIsInverted.find(strObj);
	      if (it != mapIsInverted.end())
	      {
          return true;
	      }	
	      return false;
      }

      /**
       * Ob eine Relation symmetrisch ist
       **/
      bool is_bidirected_relation(const string& strObj) const
      {
	      set<string>::const_iterator it;
	      it = mapIsBidirected.find(strObj);
	      if (it != mapIsBidirected.end())
	      {
          return true;
	      }	
	      return false;
      }

      /**
       * Zurückgeben einer Relationskurzbeschreibung
       **/
      string get_snippet(const string& strObj) const
      {
        map<string,string>::const_iterator it;
        it = mapSnippet.find(strObj);
        if (it != mapSnippet.end())
        {
	        return it->second;
        }
        else 
        {
          return "";
        }
      }

      /**
       * Zurückgeben eines Relationsbeispiels
       **/
      string get_example(const string& strObj) const
      {
        map<string,string>::const_iterator it;
        it = mapExample.find(strObj);
        if (it != mapExample.end())
        {
	        return it->second;
        }
        else 
        {
          return "";
        }
      }

      /**
       * Zurückgeben einer Beschreibung
       **/
      string get_description(const string& strObj) const
      {
        map<string,string>::const_iterator it;
        it = mapDescription.find(strObj);
        if (it != mapDescription.end())
        {
	        return it->second;
        }
        else 
        {
          return "";
        }
      }
      
      
    private:    

      /**
      * @brief start-handler fuer den expat-xml-parser 
      * @param data slot fuer den parser
      * @param szName der xml-tag name
      * @param pAttribute die xml-attribute
      */
      static void start_hndl(void* data, const char* szName, const char** pAttribute);
      /**
      * @brief start-handler fuer den expat-xml-parser 
      * @param data slot fuer den parser
      * @param szName der xml-tag name
      */
      static void end_hndl(void* data, const char* strName);
      /**
      * @brief start-handler fuer den expat-xml-parser 
      * @param data slot fuer den parser
      * @param szText der xml-text
      * @param iLen die laenge des xml-text
      */
      static void char_hndl(void* data, const char* szText, int iLen);
      
      static string extract_filename_from_pathname(const string& strPathname);

        void error(Error eError);

      ///der expat-xml-parser
      XML_Parser p;


      ///Container für die Informationen des XML
      map<string,BiblInfo> mapCBiblInfo;
      BiblField CBiblField;
      map<string,BiblField> mapCBiblField;
                          
      Specification CSpecification;
      Specifications CSpecifications;
      string strPathname;
      string strFilename;
      Invert eInvert;
      
      map<string,pair<string,bool> > mapPOSMapping;
      map<pair<string,string>,string > mapPOSRewrite;
      map<string,pair<string,bool> > mapPOSMappingSurfaceAsLemma;
      map<string,pair<string,bool> > mapPOSMappingSurfaceAsBaseform;
      vector<pair<string,pair<string,bool> > > vPOSMapping;
      set<string> setSuppressPos;
      map<string,string> mapPrepMapping;
      map<string,string> mapLemmaMapping;
      
      vector<Connection> vCConnection;
            
      vector<Specifications> vCSpecifications;
      map<string,Invert> mapInvert;      
      string strCurrentFunction;

      map<string,string> mapExample;
      map<string,string> mapDescription;
      map<string,string> mapSnippet;
      
      ///zum steuern des Informationsextraktion aus dem XML
      bool bInfoPath;
      bool bBiblInfo;
      bool bBiblField;
      bool bBiblFields;
      bool bRelation;
      bool bRelationFile;
      bool bPOSMapping;
      bool bPOSRewrite;
      bool bExtendedSurfaceForm;
      bool bPrepMapping;
      bool bLemmaMapping;
      bool bSpecification;
      bool bConnection;
      bool bName;
      bool bFile;
      bool bExample;
      bool bSnippet;
      bool bDescription;
      bool bStopwords;
      bool bStopRelations;
      bool bStopDependents;
      bool bStopHeads;
      bool bStopClass;
      bool bWord;
      bool bInputFile;
      bool bCutWordcount;
      bool bCutFrequency;
      bool bCutStatistic;
      bool bCutStatisticCorpus;
      bool bPrecut;
      bool bStatisticLimits;
      bool bGoodExamples;
      bool bColumns;
      bool bColumn;
      bool bCorpusPath;
      bool bCorpusName;
      bool bCorpusLimit;

      string strCurrentCorpus;
      vector<unsigned int> setCurrentColumn;


      set<string> mapIsInverted;
      set<string> mapIsBidirected;
      
      string strUser;
      string strHost;
      string strPasswd;
      string strDatabase;
      SurfaceMode eSurfaceMode;
      bool bUseSubcorpora;
      string strVersion;
      string strEmpty;
      string strAuthor;
      TernaryRelationMode eTernaryRelationMode;
      int iLemmaCut;
      int iRelCut;
      int iConcordCut;

      string strRelationPath;
      string strTablePath;
      string strCorpusPath;
      string strCorpusLimit;
      string strTmpPath;

			hash_set<string> setStopDependents;
			hash_set<string> setStopRelations;
			hash_set<string> setStopHeads;

			hash_map<string,TriggerInfo> setStopClass;
			hash_map<string,TriggerInfo> setStopClass_func;
			hash_map<string,string> mapSurface1Trigger;
			hash_map<string,string> mapSurface2Trigger;
			hash_map<string,string> mapSurface1Stop;
			hash_map<string,string> mapSurface2Stop;


			hash_map<string,TriggerInfo> mapReqClass;
			hash_map<string,map<string,TriggerInfo> > mapReqClass_func;

			map<string,vector<unsigned int> > mapColumn;
			map<string,string> mapCorpusPath;
			map<string,string> mapCorpusName;
			map<string,string> mapCorpusLimit;
			vector<string> vCorpus;

      map<string,map<string,int> > mapGoodExamples;


      set<string> setDoublesFile;
			string strLemmaVariationsFile;
			string strStopLemmaFile;
      set<string> setPositiveFile;
      set<string> setNegativeFile;
      bool bLemmaVariations;
      bool bStopLemma;
      bool bDoubles;
      bool bDoublesFile;
      bool bPositiveList;
      bool bPositiveListFile;
      bool bNegativeList;
      bool bNegativeListFile;
      
      
      StopwordMode eStopwordModeCurrent; 
      
      string strExpression;
      
      Error eError;
      
      pair<unsigned int, unsigned int> pairErrorPosition;

      unsigned int iMinFrequency;
      float iMinMiLogFreq;
      float iMinMI3;
      float iMinTScore;
      float iMinLogDice;      
      float iMinLogLike;      

      unsigned int iMaxFrequency;
      float iMaxMiLogFreq;
      float iMaxMI3;
      float iMaxTScore;
      float iMaxLogDice;      
      float iMaxLogLike;      

      float iAdjustMiLogFreq;
      float iAdjustMI3;
      float iAdjustTScore;
      float iAdjustLogDice;      
      float iAdjustLogLike;      
  };
  
  /**
   * Klasse zum Einlesen der Spezifikation
   **/
  const string& ReadSpecification::user() const
  {
    return strUser;
  }

  /**
   * Mapping von Korpus zu Korpuspfad
   **/
  const map<string,string>& ReadSpecification::corpus_path() const
  {
    return mapCorpusPath;
  }

  /**
   * Mapping von Korpus zu Korpusname
   **/
  const map<string,string>& ReadSpecification::corpus_name() const
  {
    return mapCorpusName;
  }

  /**
   * Anordnung der Korpora in der Spezifikation
   **/
  const vector<string>& ReadSpecification::corpus_order() const
  {
    return vCorpus;
  }

  /**
   * Zurückgeben der Spoppwörter bezüglich der Dependenten
   **/
  const hash_set<string>& ReadSpecification::stop_dependents() const
  {
    return setStopDependents;
  }

  /**
   * Zurückgeben der Oberflächenform-Trigger-Information für die erste Oberflächenform (müssen die Oberfächenformen erfüllen)
   **/
  const hash_map<string,string>& ReadSpecification::surface1_trigger() const
  {
    return mapSurface1Trigger;
  }

  /**
   * Zurückgeben der Oberflächenform-Stop-Trigger-Information für die zweite Oberflächenform (müssen die Oberfächenformen erfüllen)
   **/
  const hash_map<string,string>& ReadSpecification::surface2_trigger() const
  {
    return mapSurface2Trigger;
  }

  /**
   * Zurückgeben der Oberflächenform-Stop-Information für die erste Oberflächenform (müssen die Oberfächenformen erfüllen)
   **/
  const hash_map<string,string>& ReadSpecification::surface1_stop() const
  {
    return mapSurface1Stop;
  }

  /**
   * Zurückgeben der Oberflächenform-Stop-Information für die zweite Oberflächenform (müssen die Oberfächenformen erfüllen)
   **/
  const hash_map<string,string>& ReadSpecification::surface2_stop() const
  {
    return mapSurface2Stop;
  }

  /**
   * Zurückgeben der syntaktischen Stop-Trigger-Information
   **/
  const hash_map<string,TriggerInfo>& ReadSpecification::stop_class_func() const
  {
    return setStopClass_func;
  }

  /**
   * Zurückgeben der syntaktischen Require-Trigger-Information
   **/
  const hash_map<string,map<string,TriggerInfo> >& ReadSpecification::req_class_func() const
  {
    return mapReqClass_func;
  }

  /**
   * Dateinamen der Doubles-XML-Files
   **/
  const set<string>& ReadSpecification::doubles() const
  {
    return setDoublesFile;
  }

  /**
   * Zurückgeben der Gute-Beispiele-Information (Satzgewichtung)
   **/ 
  const map<string,map<string,int> >& ReadSpecification::good_examples() const
  {
    return mapGoodExamples;
  }

  /**
   * Zurückgeben der Positiv-Dateiliste
   **/ 
  const set<string>& ReadSpecification::positive_list() const
  {
    return setPositiveFile;
  }

  /**
   * Zurückgeben der Negativ-Dateiliste
   **/ 
  const set<string>& ReadSpecification::negative_list() const
  {
    return setNegativeFile;
  }

  /**
   * Zurückgeben der Bibliographischen Informationen
   **/ 
  const map<string,BiblInfo>& ReadSpecification::bibl_info() const
	{
		return mapCBiblInfo;
	}

  /**
   * Zurückgeben der relevanten Feldinformationen fir die BiblAngaben
   **/ 
  const map<string,BiblField>& ReadSpecification::bibl_fields() const
	{
		return mapCBiblField;
	}

  /**
   * Ob Subkorpora berechnet werden sollen
   **/ 
  bool ReadSpecification::use_subcorpora() const
  {
    return bUseSubcorpora;
  }

  /**
   * Zurückgeben der Spezifikationsversion
   **/ 
  string ReadSpecification::version() const
  {
    return strVersion;
  }

  /**
   * Zurückgeben des Autors
   **/ 
  string ReadSpecification::author() const
  {
    return strAuthor;
  }

  /**
   * Zurückgeben des grundlegenden Pfades der Relationen
   **/ 
  string ReadSpecification::relation_path() const
  {
    if (!strRelationPath.empty())
    {
      if (strRelationPath[strRelationPath.length()-1]=='/')
      {
        return strRelationPath.substr(0,strRelationPath.length()-1);
      }
    }
    return strRelationPath;
  }

  /**
   * Zurückgeben des grundlegenden Pfades der Tabellen
   **/ 
  string ReadSpecification::table_path() const
  {
    if (!strTablePath.empty())
    {
      if (strTablePath[strTablePath.length()-1]=='/')
      {
        return strTablePath.substr(0,strTablePath.length()-1);
      }
    }
    return strTablePath;
  }

  /**
   * Zurückgeben des grundlegenden Pfades der Korpora
   **/ 
  string ReadSpecification::global_corpus_path() const
  {
    if (!strCorpusPath.empty())
    {
      if (strCorpusPath[strCorpusPath.length()-1]!='/')
      {
        return strCorpusPath + "/";
      }
    }
    return strCorpusPath;
  }

  /**
   * Zurückgeben des Pfades für die Temporären dateien (z.B. beim Sortieren)
   **/ 
  string ReadSpecification::tmp_path() const
  {
    if (!strTmpPath.empty())
    {
      if (strTmpPath[strTmpPath.length()-1]!='/')
      {
        return strTmpPath + "/";
      }
    }
    return strTmpPath;
  }

  /**
   * Modus für die behandlung der Präpositionen
   **/ 
  TernaryRelationMode ReadSpecification::ternary_relation_mode() const
  {
    return eTernaryRelationMode;
  }

  /**
   * Schwellwert für die Globale Lemmafrequenz
   **/ 
  int ReadSpecification::lemma_cut() const
  {
    return iLemmaCut;
  }

  /**
   * Schwellwert für die maximale Anzahl von Texttreffern
   **/ 
  int ReadSpecification::concord_cut() const
  {
    return iConcordCut;
  }

  /**
   * Zurückgeben des Mapping der Wortarten
   **/ 
  const string& ReadSpecification::pos_mapping(const string& strObj)
  {
    map<string,pair<string,bool> >::iterator it;
    it = mapPOSMapping.find(strObj);
    if (it != mapPOSMapping.end())
    {
      return it->second.first;
    }
    cout<<"): pos:"<<strObj<<" nicht behandelt"<<endl;
    /*for (it=mapPOSMapping.begin(); it != mapPOSMapping.end(); ++it)
    {
      cout<<it->first<<endl;
    }*/

    return strEmpty;
  } 

  /**
   * Zurückgeben der Umschreibungsinformation der Wortarten bezüglich eines bestimmten Lemmas
   **/ 
  const map<pair<string,string>,string >& ReadSpecification::get_pos_rewrite() const
  {
    return mapPOSRewrite;
  }

  /**
   * Zurückgeben des Mapping der Wortarten
   **/ 
  hash_map<string,unsigned int> ReadSpecification::get_pos_mapping()
  {
    set<string> setDouble;
    hash_map<string,unsigned int> mapPOSToInteger;
    vector<pair<string,pair<string,bool> > >::iterator it;
    int iCounter=0;
    for (it=vPOSMapping.begin(); it != vPOSMapping.end(); ++it)
    {
      if (setDouble.find(it->second.first) == setDouble.end())
      {
        mapPOSToInteger.insert(make_pair(it->second.first,iCounter));
        ++iCounter;
        setDouble.insert(it->second.first);
      }
    }
    return mapPOSToInteger;
  } 

  /**
   * Zurückgeben eines Sets von Wortarten die einen Triggerwert von 0.0 bekommen
   **/ 
  const bool ReadSpecification::is_suppressed(const string& strObj)
  {
    if (setSuppressPos.find(strObj) != setSuppressPos.end())
    {
      return true;
    }
    return false;
  } 

  /**
   * Ob die Oberfächenform in die Berechnung der häufigsten Oberflächenform eingehen soll
   **/ 
  const bool ReadSpecification::use_surface_as_baseform_by_pos(const string& strObj)
  {
    map<string,pair<string,bool> >::iterator it;
    it = mapPOSMappingSurfaceAsBaseform.find(strObj);
    if (it != mapPOSMappingSurfaceAsBaseform.end())
    {
      return true;
    }
    return false;
  } 

  /**
   * Umschreibung der Präpositionen
   **/ 
  const string& ReadSpecification::prep_mapping(const string& strObj)
  {
    map<string,string>::iterator it;
    it = mapPrepMapping.find(strObj);
    if (it != mapPrepMapping.end())
    {
      return it->second;
    }
    return strObj;
  } 

  /**
   * Umschreibung der Lemmaformen
   **/ 
  const string& ReadSpecification::lemma_mapping(const string& strObj)
  {
    map<string,string>::iterator it;
    it = mapLemmaMapping.find(strObj);
    if (it != mapLemmaMapping.end())
    {
      return it->second;
    }
    return strObj;
  } 
  

  /**
   * Parsen des XML
   **/ 
  bool ReadSpecification::parse_xml(const string& strFilename)
  {    
    ifstream is;
    is.open(strFilename.c_str());
    if (!is)
    {
      char a[1000];
      error(ErrorPathname);
      sprintf(a,"): Datei existiert nicht: %s",strFilename.c_str());
      cerr<<a<<endl;
      exit(-1);
      return false;
    }
    
    ///Defaults setzen
    iMinFrequency = 0;
    iMinMiLogFreq = -numeric_limits<float>::max();
    iMinMI3 = -numeric_limits<float>::max();
    iMinTScore = -numeric_limits<float>::max();
    iMinLogDice = -numeric_limits<float>::max();
    iMinLogLike = -numeric_limits<float>::max();//-10000000;      

    iMaxFrequency = numeric_limits<unsigned int>::max();
    iMaxMiLogFreq = numeric_limits<float>::max();
    iMaxMI3 = numeric_limits<float>::max();
    iMaxTScore = numeric_limits<float>::max();
    iMaxLogDice = numeric_limits<float>::max();
    iMaxLogLike = numeric_limits<float>::max();

    iAdjustMiLogFreq = 0;
    iAdjustMI3 = 0;
    iAdjustTScore = 0;
    iAdjustLogDice = 0;      
    iAdjustLogLike = 0;      

    bStopRelations=false;
    bStopDependents=false;
    bStopHeads=false;
    bStopClass=false;
    bRelation = false;
    bRelationFile = false;
    bSpecification = false;
    bConnection = false;
    bPOSMapping = false;
    bPOSRewrite = false;
    bExtendedSurfaceForm = false;
    bPrepMapping = false;
    bLemmaMapping = false;
    bName = false;
    bFile = false;
		bInfoPath = false;
		bBiblInfo = false;
		bBiblField = false;
		bBiblFields = false;
    bExample = false;
    bSnippet = false;
    bDescription = false;
    bInputFile = false;

    bLemmaVariations = false;
    bStopLemma = false;
    bDoubles = false;
    bDoublesFile = false;
    bPositiveList = false;
    bPositiveListFile = false;
    bNegativeList = false;
    bNegativeListFile = false;
    bGoodExamples=false;

    bColumns = false;
    bColumn = false;
    bCorpusPath = false;
    bCorpusName = false;
    bCorpusLimit = false;

    eError = ErrorNone;
    strExpression.clear();
    strLemmaVariationsFile.clear();
    strStopLemmaFile.clear();
    setDoublesFile.clear();
    mapGoodExamples.clear();

    setNegativeFile.clear();
    setPositiveFile.clear();
    vCSpecifications.clear();
    mapInvert.clear();
    strPathname.clear();
    this->strFilename.clear();
    eInvert = InvertUndef;
    
    std::stringbuf buffer;

    p = XML_ParserCreate(NULL);
  
    if (!p)
    {
      return false;
    }
      
    XML_SetUserData(p,(void*)this);
    XML_UseParserAsHandlerArg(p);
    XML_SetElementHandler(p,start_hndl, end_hndl);
    XML_SetCharacterDataHandler(p,char_hndl);
  
    is.get(buffer,EOF);
    
    const string& strBuffer = buffer.str();  
    if (!XML_Parse(p, strBuffer.c_str(),strBuffer.length(),0))
    {
       XML_ParserFree(p);
       return false;
    }
    
    vector<Specifications>::iterator it;

    ///Fehler abfangen    
    switch (eError)
    {
      char a[1000];
      case ErrorAttribute:
        sprintf(a,"): Fehler bei den Attributen in Zeile:%i, Position:%i",pairErrorPosition.first,pairErrorPosition.second);
        cerr<<a<<endl;
        exit(-1);
        break;
      case ErrorValue:
        sprintf(a,"): Fehler bei den Attributwerten in Zeile:%i, Position:%i",pairErrorPosition.first,pairErrorPosition.second);
        cerr<<a<<endl;
        exit(-1);
        break;
      case ErrorData:
        sprintf(a,"): Fehler bei den Textknoten in Zeile:%i, Position:%i",pairErrorPosition.first,pairErrorPosition.second);
        cerr<<a<<endl;
        exit(-1);
        break;
      case ErrorTag:
        sprintf(a,"): Fehler bei den Tags in Zeile:%i, Position:%i",pairErrorPosition.first,pairErrorPosition.second);
        cerr<<a<<endl;
        exit(-1);
        break;
      default:
        break;              
    }
  
    XML_ParserFree(p);

    return true;
  };

  /**
   * Zurückgeben eines Vektors aus Relationsspezifikationen
   **/ 
  const vector<Specifications>& ReadSpecification::get_specifications() const
  {
    return vCSpecifications;
  }
  
  /**
   * Zurückgeben der Spezifikation für die transrelationalen Bedingungen
   **/ 
  const vector<Connection>& ReadSpecification::get_connections() const
  {
    return vCConnection;
  }
  
  /**
   * Fehlerposition und Typ
   **/ 
  void ReadSpecification::error(Error _eError)
  {
    if (eError == ErrorNone)
    {
      pairErrorPosition.first = XML_GetCurrentLineNumber(p);
      pairErrorPosition.second = XML_GetCurrentColumnNumber(p);
      eError = _eError;
    }
  }

  /**
   * Dateiname aus einem Ppfad extrahierne
   **/ 
  string ReadSpecification::extract_filename_from_pathname(const string& strPathname)
  {
    int iPos = strPathname.rfind('/');
    if (iPos != string::npos)
    {
      return strPathname.substr(iPos+1,string::npos);
    }
    else
    {
      return strPathname;
    }
  }

  /**
   * Starthandler
   **/ 
  void ReadSpecification::start_hndl(void* data, const char* szName, const char** pAttribute)
  {
    string strName(szName);
    ReadSpecification* pThis = ((ReadSpecification*)XML_GetUserData((ReadSpecification*)data));
    pThis->strExpression.clear();
    
    if (strName == TAG_SPECIFICATION  && pThis->bSpecification == false)
    {

      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        
        if(strAttribute == ATTRIBUTE_USER)
        {
          pThis->strUser = strValue;          
        }
        else if(strAttribute == ATTRIBUTE_HOST)
        {
          pThis->strHost = strValue;
        }
        else if(strAttribute == ATTRIBUTE_PASSWD)
        {
          pThis->strPasswd = strValue;
        }
        else if(strAttribute == ATTRIBUTE_DATABASE)
        {
          pThis->strDatabase = strValue;
        }
        else if(strAttribute == ATTRIBUTE_SURFACE_MODE)
        {
          if (!strValue.compare("global"))
          {
            pThis->eSurfaceMode = MostFrequentGlobal;
          }
          else if (!strValue.compare("local"))
          {
            pThis->eSurfaceMode = MostFrequentLocal;
          }
          else if (!strValue.compare("tight-local"))
          {
            pThis->eSurfaceMode = MostFrequentTightLocal;
          }
          else
          {
            cout<<"falscher attributwert"<<endl;
          }
        }
        else if(strAttribute == ATTRIBUTE_USE_SUBCORPORA)
        {
          if (!strValue.compare("yes"))
          {
            pThis->bUseSubcorpora = true;
          }
          else
          {
            pThis->bUseSubcorpora = false;
          }
        }
        else if(strAttribute == ATTRIBUTE_VERSION)
        {
          pThis->strVersion = strValue;
        }
        else if(strAttribute == ATTRIBUTE_AUTHOR)
        {
          pThis->strAuthor = strValue;
        }
        else if(strAttribute == ATTRIBUTE_TERNARY_RELATION_MODE)
        {
          if (!strValue.compare("attach-to-dependent"))
          {
            pThis->eTernaryRelationMode = AttachToWord;
          }
          else if (!strValue.compare("attach-to-relation"))
          {
            pThis->eTernaryRelationMode = AttachToRelation;
          }
          else
          {
            cout<<"falscher attributwert"<<endl;
          }
        }
        else if(strAttribute == ATTRIBUTE_CUT_REL)
        {
          pThis->iRelCut = atoi(strValue.c_str());
        }
        else if(strAttribute == ATTRIBUTE_CUT_CONCORD)
        {
          pThis->iConcordCut = atoi(strValue.c_str());
        }
        else if(strAttribute == ATTRIBUTE_LEMMA_CUT)
        {
          if (atoi(strValue.c_str())!=-1)
          {
            pThis->iLemmaCut = atoi(strValue.c_str());
          }
        }
        else if(strAttribute == ATTRIBUTE_RELATION_PATH)
        {
          pThis->strRelationPath = strValue;
        }
        else if(strAttribute == ATTRIBUTE_TABLE_PATH)
        {
          pThis->strTablePath = strValue;
        }
        else if(strAttribute == ATTRIBUTE_CORPUS_PATH)
        {
          pThis->strCorpusPath = strValue;
        }
        else if(strAttribute == "tmp-path")
        {
          pThis->strTmpPath = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        ++pDummy;
      }

      pThis->bSpecification = true;
    }
    else if (strName == TAG_CONNECTIONS  && pThis->bSpecification == true)
    {
      pThis->vCConnection.clear();
      pThis->bConnection = true;
    }
    else if (strName == TAG_CHECK  && pThis->bConnection == true)
    {
      Connection CConnection;
      string strRel1;
      string strRel2;
      string strMin("0");
      string strMax("100");
      string strMin_global("0");
      string strMax_global("100");
      string strMin_global_inv("0");
      string strMax_global_inv("100");
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        if(strAttribute == ATTRIBUTE_REL1)
        {
          strRel1 = strValue;          
        }
        else if(strAttribute == ATTRIBUTE_REL2)
        {
          strRel2 = strValue;          
        }
        else if(strAttribute == ATTRIBUTE_MAX_PERCENT)
        {
          strMax = strValue;
        }
        else if(strAttribute == ATTRIBUTE_MIN_PERCENT)
        {
          strMin = strValue;
        }
        else if(strAttribute == ATTRIBUTE_MAX_PERCENT_global)
        {
          strMax_global = strValue;
        }
        else if(strAttribute == ATTRIBUTE_MIN_PERCENT_global)
        {
          strMin_global = strValue;
        }
        else if(strAttribute == ATTRIBUTE_MAX_PERCENT_global_inv)
        {
          strMax_global_inv = strValue;
        }
        else if(strAttribute == ATTRIBUTE_MIN_PERCENT_global_inv)
        {
          strMin_global_inv = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        ++pDummy;
      }
      CConnection.strRel1=strRel1;
      CConnection.strRel2=strRel2;
      CConnection.iMax=atoi(strMax.c_str());
      CConnection.iMin=atoi(strMin.c_str());
      CConnection.iMax_global=atoi(strMax_global.c_str());
      CConnection.iMin_global=atoi(strMin_global.c_str());
      CConnection.iMax_global_inv=atoi(strMax_global_inv.c_str());
      CConnection.iMin_global_inv=atoi(strMin_global_inv.c_str());
      pThis->vCConnection.push_back(CConnection);


    }
    else if (strName == TAG_POS_MAPPING  && pThis->bSpecification == true)
    {
      pThis->bPOSMapping = true;
    }
    else if (strName == TAG_POS_REWRITE  && pThis->bSpecification == true)
    {
      pThis->bPOSRewrite = true;
    }
    else if (strName == TAG_EXTENDED_SURFACE_FORM  && pThis->bSpecification == true)
    {
      pThis->bExtendedSurfaceForm = true;
    }
    else if (strName == TAG_PREP_MAPPING  && pThis->bSpecification == true)
    {
      pThis->bPrepMapping = true;
    }
    else if (strName == TAG_LEMMA_MAPPING  && pThis->bSpecification == true)
    {
      pThis->bLemmaMapping = true;
    }
    else if (strName == TAG_GOOD_EXAMPLES  && pThis->bSpecification == true)
    {
      pThis->bGoodExamples = true;
    }
    else if (strName == TAG_GOOD_EXAMPLES_ITEM  && pThis->bGoodExamples == true)
    {
      string strCorpus;
      string strPath;
      string strLimit;

      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
       

        if (strAttribute == "corpus")
        {
          strCorpus = strValue;
        }
        else if (strAttribute == "file")
        {
          strPath = strValue;
        }
        else if (strAttribute == "limit")
        {
          strLimit = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        ++pDummy;
      }

      int iLimit=numeric_limits<int>::max();
      if (!strLimit.empty())
      {
        if (strLimit!="-1")
        {
          iLimit = atoi(strLimit.c_str());
        }
      }
      map<string,map<string,int> >::iterator ft;
      ft = pThis->mapGoodExamples.find(strCorpus);
      if (ft == pThis->mapGoodExamples.end())
      {
        map<string,int> setDummy;
        setDummy.insert(make_pair(strPath,iLimit));
        pThis->mapGoodExamples.insert(make_pair(strCorpus,setDummy));
      }
      else
      {
        ft->second.insert(make_pair(strPath,iLimit));
      }

    }
    else if (strName == TAG_STATISTIC_LIMITS  && pThis->bSpecification == true)
    {
      pThis->bStatisticLimits = true;


      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        




        if (strAttribute == ATTRIBUTE_MIN_FREQUENCY)
        {
          pThis->iMinFrequency = atoi(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MAX_FREQUENCY)
        {
          pThis->iMaxFrequency = atof(strValue.c_str());
        }


        else if (strAttribute == ATTRIBUTE_MIN_MILOGFREQ)
        {
          if (strAttribute!="")
          {
            pThis->iMinMiLogFreq = atof(strValue.c_str());
          }
        }
        else if (strAttribute == ATTRIBUTE_MIN_MI3)
        {
          if (strAttribute!="")
          {
            pThis->iMinMI3 = atof(strValue.c_str());
          }
        }
        else if (strAttribute == ATTRIBUTE_MIN_CHISQUARE)
        {
          if (strAttribute!="")
          {
            pThis->iMinTScore = atof(strValue.c_str());
          }
        }
        else if (strAttribute == ATTRIBUTE_MIN_LOGDICE)
        {
          if (strAttribute!="")
          {
            pThis->iMinLogDice = atof(strValue.c_str());
          }
        }
        else if (strAttribute == ATTRIBUTE_MIN_LOGLIKE)
        {
          if (strAttribute!="")
          {
            pThis->iMinLogLike = atof(strValue.c_str());
          }
        }


        else if (strAttribute == ATTRIBUTE_MAX_MILOGFREQ)
        {
          pThis->iMaxMiLogFreq = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MAX_MI3)
        {
          pThis->iMaxMI3 = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MAX_CHISQUARE)
        {
          pThis->iMaxTScore = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MAX_LOGDICE)
        {
          pThis->iMaxLogDice = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MAX_LOGLIKE)
        {
          pThis->iMaxLogLike = atof(strValue.c_str());
        }

        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        ++pDummy;
      }



    }

    else if (strName == TAG_STATISTIC_ADJUST  && pThis->bSpecification == true)
    {

      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        
        if (strAttribute == ATTRIBUTE_ADJUST_MILOGFREQ)
        {
          pThis->iAdjustMiLogFreq = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_ADJUST_MI3)
        {
          pThis->iAdjustMI3 = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_ADJUST_CHISQUARE)
        {
          pThis->iAdjustTScore = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_ADJUST_LOGDICE)
        {
          pThis->iAdjustLogDice = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_ADJUST_LOGLIKE)
        {
          pThis->iAdjustLogLike = atof(strValue.c_str());
        }

        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        ++pDummy;
      }

    }

    else if (strName == TAG_RULE  && pThis->bPOSMapping == true)
    {
      string strFrom;
      string strTo;
      string strUseAsLemma("no");
      string strUseAsBaseform("no");
      string strSuppress("no");
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        
        if(strAttribute == ATTRIBUTE_FROM)
        {
          strFrom = strValue;          
        }
        else if(strAttribute == ATTRIBUTE_TO)
        {
          strTo = strValue;
        }
        else if(strAttribute == ATTRIBUTE_USE_AS_LEMMA)
        {
          strUseAsLemma = strValue;
        }
        else if(strAttribute == ATTRIBUTE_USE_AS_BASEFORM)
        {
          strUseAsBaseform = strValue;
        }
        else if(strAttribute == ATTRIBUTE_SUPPRESS)
        {
          strSuppress = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        ++pDummy;
      }
			if (!strUseAsLemma.compare("no"))
			{
        pThis->mapPOSMapping.insert(make_pair(strFrom,make_pair(strTo,false)));
        pThis->vPOSMapping.push_back(make_pair(strFrom,make_pair(strTo,false)));
			}
			else
			{
        pThis->mapPOSMapping.insert(make_pair(strFrom,make_pair(strTo,false)));
        pThis->mapPOSMappingSurfaceAsLemma.insert(make_pair(strFrom,make_pair(strTo,true)));
        pThis->vPOSMapping.push_back(make_pair(strFrom,make_pair(strTo,true)));
			}
			if (!strUseAsBaseform.compare("no"))
			{
			}
			else
			{
        pThis->mapPOSMappingSurfaceAsBaseform.insert(make_pair(strFrom,make_pair(strTo,true)));
			}
			if (!strSuppress.compare("yes"))
			{
        pThis->setSuppressPos.insert(strFrom);
			}
    }
    else if (strName == TAG_RULE  && pThis->bPOSRewrite == true)
    {
      string strLemma;
      string strFrom;
      string strTo;
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        
        if(strAttribute == ATTRIBUTE_FROM)
        {
          strFrom = strValue;          
        }
        else if(strAttribute == ATTRIBUTE_TO)
        {
          strTo = strValue;
        }
        else if(strAttribute == "lemma")
        {
          strLemma = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        ++pDummy;
      }

      pThis->mapPOSRewrite.insert(make_pair(make_pair(strLemma,strFrom),strTo));

    }
    else if (strName == TAG_RULE  && pThis->bPrepMapping == true)
    {
      string strFrom;
      string strTo;
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        
        if(strAttribute == ATTRIBUTE_FROM)
        {
          strFrom = strValue;          
        }
        else if(strAttribute == ATTRIBUTE_TO)
        {
          strTo = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        ++pDummy;
      }
      pThis->mapPrepMapping.insert(make_pair(strFrom,strTo));
    }
    else if (strName == TAG_RULE  && pThis->bLemmaMapping == true)
    {
      string strFrom;
      string strTo;
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        
        if(strAttribute == ATTRIBUTE_FROM)
        {
          strFrom = strValue;          
        }
        else if(strAttribute == ATTRIBUTE_TO)
        {
          strTo = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        ++pDummy;
      }
      pThis->mapLemmaMapping.insert(make_pair(strFrom,strTo));
    }
    else  if (strName == TAG_INPUT_FILE  && pThis->bSpecification == true)
    {
      pThis->bInputFile = true;
     

      string strUseBaseformAsSurface1 = "no";
      string strUseBaseformAsSurface2 = "no";

      string strPositiveFilter = "";
      string strNegativeFilter = "";
 
      pThis->CSpecifications.clear();

      pThis->CSpecifications.bUseBaseformAsSurface1 = false;
      pThis->CSpecifications.bUseBaseformAsSurface2 = false;
      
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));

        if(strAttribute == "use-baseform-as-surface1")
        {
          strUseBaseformAsSurface1 = strValue;
        }
        else if(strAttribute == "use-baseform-as-surface2")
        {
          strUseBaseformAsSurface2 = strValue;
        }
        else if(strAttribute == "positive-filter")
        {
          strPositiveFilter = strValue;
        }
        else if(strAttribute == "negative-filter")
        {
          strNegativeFilter = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        
        ++pDummy;
      }

      if (strUseBaseformAsSurface1 == "no")
      {
          pThis->CSpecifications.bUseBaseformAsSurface1 = false;
      }
      else
      {
          pThis->CSpecifications.bUseBaseformAsSurface1 = true;
      }

      if (strUseBaseformAsSurface2 == "no")
      {
          pThis->CSpecifications.bUseBaseformAsSurface2 = false;
      }
      else
      {
          pThis->CSpecifications.bUseBaseformAsSurface2 = true;
      }
      pThis->CSpecifications.strPositiveFilter = strPositiveFilter;
      pThis->CSpecifications.strNegativeFilter = strNegativeFilter;

    }
    else  if (strName == TAG_PRECUT  && pThis->bSpecification == true)
    {
      pThis->bPrecut = true;

      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        

        if(strAttribute == ATTRIBUTE_MAX_CONCORDANCE_LINES)
        {
          pThis->CSpecifications.iMaxConcordanceLines = atoi(strValue.c_str());
        }
        else if(strAttribute == ATTRIBUTE_MAX_STRING_LENGTH)
        {
          pThis->CSpecifications.iMaxStringLength = atoi(strValue.c_str());
        }
        else if(strAttribute == ATTRIBUTE_MIN_FREQUENCY_PRECUT)
        {
          pThis->CSpecifications.iMinFrequency = atoi(strValue.c_str());
        }

        else if(strAttribute == ATTRIBUTE_MIN_CONCORDANCE_LINES)
        {
          pThis->CSpecifications.iMinConcordanceLines = atoi(strValue.c_str());
        }
        else if(strAttribute == ATTRIBUTE_MIN_STRING_LENGTH)
        {
          pThis->CSpecifications.iMinStringLength = atoi(strValue.c_str());
        }
        else if(strAttribute == ATTRIBUTE_MAX_FREQUENCY_PRECUT)
        {
          pThis->CSpecifications.iMaxFrequency = atoi(strValue.c_str());
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        
        ++pDummy;
      }
    }
    else if(strName == TAG_RELATION && pThis->bInputFile == true)
    {
      pThis->bRelation = true;

      pThis->CSpecification.clear();

      string strIgnore= "no";
      string strIgnorePrep= "no";

      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        
        if(strAttribute == ATTRIBUTE_NAME)
        {
          pThis->CSpecification.strFunctionname = strValue;
        }
        else if(strAttribute == "ignore")
        {
          strIgnore = strValue;
        }
        else if(strAttribute == "ignore_prep")
        {
          strIgnorePrep = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        
        ++pDummy;
      }
      if (strIgnorePrep == "yes")
      {
        pThis->CSpecifications.bIgnorePrep=true;
      }
      else
      {
        pThis->CSpecifications.bIgnorePrep=false;
      }

      if (strIgnore == "no")
      {
          pThis->CSpecification.bIgnore = false;
      }
      else
      {
          pThis->CSpecification.bIgnore = true;
      }


    }
    else if(strName == TAG_RELATION_FILE && pThis->bInputFile == true)
    {
      pThis->bRelationFile = true;
      string strFilename;
      string strCorpusname;

      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        

        if(strAttribute == ATTRIBUTE_NAME)
        {
          strFilename = strValue;
        }
        else if(strAttribute == ATTRIBUTE_CORPUS)
        {
          strCorpusname = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        
        ++pDummy;
      }
      ifstream stream((pThis->strRelationPath + "/" + strFilename).c_str());
      if (!stream)
      {
        char a[1000];
        sprintf(a,"): Datei existiert nicht: %s",(pThis->strRelationPath + "/" + strFilename).c_str());
        cerr<<a<<endl;
      }
      else
      {
        pThis->CSpecifications.setFilename.insert(make_pair(strFilename,strCorpusname));         
      }
    }
    else if(strName == TAG_SNIPPET && pThis->bInputFile == true)
    {
     pThis->bSnippet = true;
    }
    else if(strName == TAG_EXAMPLE && pThis->bInputFile == true)
    {
     pThis->bExample = true;
    }
    else if(strName == TAG_DESCRIPTION && pThis->bInputFile == true)
    {
     pThis->bDescription = true;
    }
    else if(strName == TAG_BIBL_INFO)
    {
     pThis->mapCBiblInfo.clear();
     pThis->bBiblInfo = true;
    }
    else if(strName == TAG_BIBL_INFO_ITEM && pThis->bBiblInfo==true)
    {
			string strCorpus;
			string strFile;
			string strTextPath;
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));

        if(strAttribute == "corpus")
        {
          strCorpus = strValue;
        }
        else if(strAttribute == "file")
        {
          strFile = strValue;
				  ifstream stream(strValue.c_str());
				  if (!stream)
				  {
				    char a[1000];
				    sprintf(a,"): Datei existiert nicht: %s",strValue.c_str());
				    cerr<<a<<endl;
				    exit(-1);
				  }
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        
        ++pDummy;
      }
			BiblInfo CBiblInfo;
			CBiblInfo.strCorpus=strCorpus;
			CBiblInfo.strFile=strFile;
			pThis->mapCBiblInfo.insert(make_pair(strCorpus,CBiblInfo));

    }
    else if(strName == TAG_BIBL_FIELDS)
    {
      pThis->bBiblFields = true;
      pThis->mapCBiblField.clear();
    }
    else if(strName == TAG_BIBL_FIELD && pThis->bBiblFields==true)
    {
     pThis->bBiblField = true;
     pThis->CBiblField.clear();


			string strCorpus;
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));

        if(strAttribute == "corpus")
        {
          strCorpus = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        
        ++pDummy;
      }
      pThis->CBiblField.strCorpus = strCorpus;

    }
    else if(strName == TAG_BIBL_FIELD_DATE && pThis->bBiblField==true)
    {
			string strDefault;
			string strName;
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));

        if(strAttribute == "name")
        {
          strName = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        
        ++pDummy;
      }
      pThis->CBiblField.strDate = strName;
    }
    else if(strName == TAG_BIBL_FIELD_AVAIL && pThis->bBiblField==true)
    {
			string strDefault;
			string strName;
			string strNameValue;
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));

        if(strAttribute == "name")
        {
          strName = strValue;
        }
        else if(strAttribute == "value")
        {
          strNameValue = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        
        ++pDummy;
      }
      pThis->CBiblField.strAvail = strName;
      pThis->CBiblField.setAvailValue = string_to_set(strNameValue);
    }
    else if(strName == TAG_BIBL_FIELD_ORIG && pThis->bBiblField==true)
    {
			string strDefault;
			string strName;
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));

        if(strAttribute == "name")
        {
          strName = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        
        ++pDummy;
      }
      pThis->CBiblField.strOrig = strName;
    }
    else if(strName == TAG_BIBL_FIELD_SIGLE && pThis->bBiblField==true)
    {
			string strDefault;
			string strName;
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));

        if(strAttribute == "name")
        {
          strName = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        
        ++pDummy;
      }
      pThis->CBiblField.strSigle = strName;
    }
    else if(strName == TAG_BIBL_FIELD_SCAN && pThis->bBiblField==true)
    {
			string strDefault;
			string strName;
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));

        if(strAttribute == "name")
        {
          strName = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        
        ++pDummy;
      }
      pThis->CBiblField.strScan = strName;
    }
    else if(strName == TAG_BIBL_FIELD_TEXTCLASS && pThis->bBiblField==true)
    {
			string strDefault;
			string strName;
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));

        if(strAttribute == "name")
        {
          strName = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        
        ++pDummy;
      }
      pThis->CBiblField.strTextclass = strName;
    }

    else if(strName == TAG_INFO_PATH)
    {
     pThis->bInfoPath = true;
    }
    else if(strName == TAG_INFO_ITEM_DATE && pThis->bInfoPath==true)
    {
			string strDefault;
			string strCorpus;
			string strPath;
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));

        if(strAttribute == "corpus")
        {
          strCorpus = strValue;
        }
        else if(strAttribute == "path")
        {
          strPath = strValue;
        }
        else if(strAttribute == "default")
        {
          strDefault = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        
        ++pDummy;
      }
    }
    else if(strName == TAG_INFO_ITEM_TEXT && pThis->bInfoPath==true)
    {
			string strDefault;
			string strCorpus;
			string strPath;
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));

        if(strAttribute == "corpus")
        {
          strCorpus = strValue;
        }
        else if(strAttribute == "path")
        {
          strPath = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        
        ++pDummy;
      }
    }
    else if(strName == TAG_INFO_ITEM_ORIG && pThis->bInfoPath==true)
    {
			string strDefault;
			string strCorpus;
			string strPath;
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));

        if(strAttribute == "corpus")
        {
          strCorpus = strValue;
        }
        else if(strAttribute == "path")
        {
          strPath = strValue;
        }
        else if(strAttribute == "default")
        {
          strDefault = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        
        ++pDummy;
      }
    }
    else if(strName == TAG_INFO_ITEM_SIGLE && pThis->bInfoPath==true)
    {
			string strDefault;
			string strCorpus;
			string strPath;
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));

        if(strAttribute == "corpus")
        {
          strCorpus = strValue;
        }
        else if(strAttribute == "path")
        {
          strPath = strValue;
        }
        else if(strAttribute == "default")
        {
          strDefault = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        
        ++pDummy;
      }
    }
    else if(strName == TAG_INFO_ITEM_SCAN && pThis->bInfoPath==true)
    {
			string strDefault;
			string strCorpus;
			string strPath;
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));

        if(strAttribute == "corpus")
        {
          strCorpus = strValue;
        }
        else if(strAttribute == "path")
        {
          strPath = strValue;
        }
        else if(strAttribute == "default")
        {
          strDefault = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        
        ++pDummy;
      }
    }
    else if(strName == TAG_INFO_ITEM_AVAIL && pThis->bInfoPath==true)
    {
			string strDefault;
			string strCorpus;
			string strPath;
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));

        if(strAttribute == "corpus")
        {
          strCorpus = strValue;
        }
        else if(strAttribute == "path")
        {
          strPath = strValue;
        }
        else if(strAttribute == "default")
        {
          strDefault = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        
        ++pDummy;
      }
    }
    else if(strName == TAG_INFO_ITEM_TEXTCLASS && pThis->bInfoPath==true)
    {
			string strDefault;
			string strCorpus;
			string strPath;
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));

        if(strAttribute == "corpus")
        {
          strCorpus = strValue;
        }
        else if(strAttribute == "path")
        {
          strPath = strValue;
        }
        else if(strAttribute == "default")
        {
          strDefault = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        
        ++pDummy;
      }
    }
    else if(strName == TAG_RELATION_INVERTED && pThis->bInputFile == true)
    {
      pThis->bRelation = true;

      pThis->CSpecification.clear();

      string strIgnore("no");
      string strIgnorePrep("no");

      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        
        if(strAttribute == ATTRIBUTE_NAME)
        {
          pThis->CSpecification.strFunctionname = strValue;
          pThis->mapIsInverted.insert(strValue);
        }
        else if(strAttribute == "ignore")
        {
          strIgnore = strValue;
        }
        else if(strAttribute == "ignore_prep")
        {
          strIgnorePrep = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        
        ++pDummy;
      }
      if (strIgnorePrep == "yes")
      {
        pThis->CSpecifications.bIgnorePrep=true;
      }
      else
      {
        pThis->CSpecifications.bIgnorePrep=false;
      }
      if (strIgnore == "no")
      {
          pThis->CSpecification.bIgnore = false;
      }
      else
      {
          pThis->CSpecification.bIgnore = true;
      }

    }
    else if(strName == TAG_RELATION_BIDIRECTED && pThis->bInputFile == true)
    {
      pThis->bRelation = true;

      pThis->CSpecification.clear();

      string strIgnore("no");
      string strIgnorePrep("no");

      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        
        if(strAttribute == ATTRIBUTE_NAME)
        {
          pThis->CSpecification.strFunctionname = strValue;
	        pThis->mapIsBidirected.insert(strValue);
        }
        else if(strAttribute == "ignore")
        {
          strIgnore = strValue;
        }
        else if(strAttribute == "ignore_prep")
        {
          strIgnorePrep = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        
        ++pDummy;
      }
      if (strIgnorePrep == "yes")
      {
        pThis->CSpecifications.bIgnorePrep=true;
      }
      else
      {
        pThis->CSpecifications.bIgnorePrep=false;
      }


      if (strIgnore == "no")
      {
          pThis->CSpecification.bIgnore = false;
      }
      else
      {
          pThis->CSpecification.bIgnore = true;
      }
    }
    else if(strName == TAG_CUT_FREQUENCY && pThis->bRelation == true)
    {      
      pThis->bCutFrequency=true;
      
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        
        if (strAttribute == ATTRIBUTE_MIN_GLOBAL_DEP)
        {
          pThis->CSpecification.iMinGlobalDepFrequency = atoi(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MIN_GLOBAL_HEAD)
        {
          pThis->CSpecification.iMinGlobalHeadFrequency = atoi(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MIN_LOCAL_DEP)
        {
          pThis->CSpecification.iMinLocalDepFrequency = atoi(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MIN_LOCAL_HEAD)
        {
          pThis->CSpecification.iMinLocalHeadFrequency = atoi(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MIN_FREQUENCY)
        {
          pThis->CSpecification.iMinFrequency = atoi(strValue.c_str());
        }

        else if (strAttribute == ATTRIBUTE_MAX_GLOBAL_DEP)
        {
          pThis->CSpecification.iMaxGlobalDepFrequency = atoi(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MAX_GLOBAL_HEAD)
        {
          pThis->CSpecification.iMaxGlobalHeadFrequency = atoi(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MAX_LOCAL_DEP)
        {
          pThis->CSpecification.iMaxLocalDepFrequency = atoi(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MAX_LOCAL_HEAD)
        {
          pThis->CSpecification.iMaxLocalHeadFrequency = atoi(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MAX_FREQUENCY)
        {
          pThis->CSpecification.iMaxFrequency = atoi(strValue.c_str());
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        
        ++pDummy;
      }
    }
    else if(strName == TAG_CUT_WORDCOUNT && pThis->bRelation == true)
    {      
      pThis->bCutWordcount=true;
      
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        if (strAttribute == ATTRIBUTE_MIN_GLOBAL_DEP)
        {
          pThis->CSpecification.iMinGlobalDepWordcount = atoi(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MIN_GLOBAL_HEAD)
        {
          pThis->CSpecification.iMinGlobalHeadWordcount = atoi(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MIN_LOCAL_DEP)
        {
          pThis->CSpecification.iMinLocalDepWordcount = atoi(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MIN_LOCAL_HEAD)
        {
          pThis->CSpecification.iMinLocalHeadWordcount = atoi(strValue.c_str());
        }

        else if (strAttribute == ATTRIBUTE_MAX_GLOBAL_DEP)
        {
          pThis->CSpecification.iMaxGlobalDepWordcount = atoi(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MAX_GLOBAL_HEAD)
        {
          pThis->CSpecification.iMaxGlobalHeadWordcount = atoi(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MAX_LOCAL_DEP)
        {
          pThis->CSpecification.iMaxLocalDepWordcount = atoi(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MAX_LOCAL_HEAD)
        {
          pThis->CSpecification.iMaxLocalHeadWordcount = atoi(strValue.c_str());
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }
        ++pDummy;
      }
    }
    else if(strName == TAG_CUT_STATISTIC && pThis->bRelation == true)
    {     
      pThis->bCutStatistic=true;
       
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        
				pThis->CSpecification.iMinMiLogFreq_con = pThis->iMinMiLogFreq;
				pThis->CSpecification.iMinMI3_con = pThis->iMinMI3;
				pThis->CSpecification.iMinTScore_con = pThis->iMinTScore;
				pThis->CSpecification.iMinLogDice_con = pThis->iMinLogDice;
				pThis->CSpecification.iMinLogLike_con = pThis->iMinLogLike;


				pThis->CSpecification.iMaxMiLogFreq_con = pThis->iMaxMiLogFreq;
				pThis->CSpecification.iMaxMI3_con = pThis->iMaxMI3;
				pThis->CSpecification.iMaxTScore_con = pThis->iMaxTScore;
				pThis->CSpecification.iMaxLogDice_con = pThis->iMaxLogDice;
				pThis->CSpecification.iMaxLogLike_con = pThis->iMaxLogLike;

				pThis->CSpecification.iAdjustMiLogFreq = pThis->iAdjustMiLogFreq;
				pThis->CSpecification.iAdjustMI3 = pThis->iAdjustMI3;
				pThis->CSpecification.iAdjustTScore = pThis->iAdjustTScore;
				pThis->CSpecification.iAdjustLogDice = pThis->iAdjustLogDice;
				pThis->CSpecification.iAdjustLogLike = pThis->iAdjustLogLike;

        if (strAttribute == ATTRIBUTE_MIN_FREQUENCY)
        {
          pThis->CSpecification.iMinFrequency = atoi(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MAX_FREQUENCY)
        {
          pThis->CSpecification.iMaxFrequency = atof(strValue.c_str());
        }



        else if (strAttribute == ATTRIBUTE_MIN_MILOGFREQ)
        {
          pThis->CSpecification.iMinMiLogFreq = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MIN_MI3)
        {
          pThis->CSpecification.iMinMI3 = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MIN_CHISQUARE)
        {
          pThis->CSpecification.iMinTScore = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MIN_LOGDICE)
        {
          pThis->CSpecification.iMinLogDice = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MIN_LOGLIKE)
        {
          pThis->CSpecification.iMinLogLike = atof(strValue.c_str());
        }


        else if (strAttribute == ATTRIBUTE_MAX_MILOGFREQ)
        {
          pThis->CSpecification.iMaxMiLogFreq = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MAX_MI3)
        {
          pThis->CSpecification.iMaxMI3 = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MAX_CHISQUARE)
        {
          pThis->CSpecification.iMaxTScore = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MAX_LOGDICE)
        {
          pThis->CSpecification.iMaxLogDice = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MAX_LOGLIKE)
        {
          pThis->CSpecification.iMaxLogLike = atof(strValue.c_str());
        }


        else if(strAttribute == ATTRIBUTE_USE_GLOBAL_CUT)
        {
          if (!strValue.compare("yes"))
          {
            pThis->CSpecification.bUseGlobalCut = true;
          }
          else if (!strValue.compare("no"))
          {
            pThis->CSpecification.bUseGlobalCut = false;
          }
			    else
			    {
			      pThis->error(ErrorAttribute);
			      return;
			    }
        }

        else if(strAttribute == ATTRIBUTE_LEMMA_CUT)
        {
          if (!strValue.compare("yes"))
          {
            pThis->CSpecification.bUseLemmaCut = true;
          }
          else if (!strValue.compare("no"))
          {
            pThis->CSpecification.bUseLemmaCut = false;
          }
			    else
			    {
			      pThis->error(ErrorAttribute);
			      return;
			    }
        }

        ++pDummy;
      }
    }        
    else if(strName == TAG_CUT_STATISTIC_CORPUS && pThis->bRelation == true)
    {     
      pThis->bCutStatisticCorpus=true;

      Specification CSpecification;
      string strName;

       
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        
        if (strAttribute == ATTRIBUTE_MIN_MILOGFREQ)
        {
          CSpecification.iMinMiLogFreqCorpus = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MIN_FREQUENCY)
        {
          CSpecification.iMinFrequency = atoi(strValue.c_str());
        }
        else if(strAttribute == "name")
        {
          strName = strValue;
        }
        else if (strAttribute == ATTRIBUTE_MAX_FREQUENCY)
        {
          CSpecification.iMaxFrequency = atoi(strValue.c_str());
        }
        if (strAttribute == ATTRIBUTE_MIN_MI3)
        {
          CSpecification.iMinMI3Corpus = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MIN_CHISQUARE)
        {
          CSpecification.iMinTScoreCorpus = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MIN_LOGDICE)
        {
          CSpecification.iMinLogDiceCorpus = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MAX_MILOGFREQ)
        {
          CSpecification.iMaxMiLogFreqCorpus = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MAX_MI3)
        {
          CSpecification.iMaxMI3Corpus = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MAX_CHISQUARE)
        {
          CSpecification.iMaxTScoreCorpus = atof(strValue.c_str());
        }
        else if (strAttribute == ATTRIBUTE_MAX_LOGDICE)
        {
          CSpecification.iMaxLogDiceCorpus = atof(strValue.c_str());
        }

        ++pDummy;
      }

      pThis->CSpecification.mapSpec.insert(make_pair(strName,CSpecification));
    }        
    else if(strName == TAG_STOPWORDS && pThis->bRelation == true)
    {
      pThis->bStopwords = true;
    }
    else if(strName == TAG_STOP_RELATIONS && pThis->bSpecification == true)
    {
      pThis->bStopRelations = true;
    }
    else if(strName == TAG_STOP_DEPENDENTS && pThis->bSpecification == true)
    {
      pThis->bStopDependents = true;
    }
    else if(strName == TAG_STOP_HEADS && pThis->bSpecification == true)
    {
      pThis->bStopHeads = true;
    }
    else if(strName == TAG_STOP_CLASS && pThis->bSpecification == true)
    {
      pThis->bStopClass = true;
    }
    else if(strName == TAG_STOP && (pThis->bStopDependents == true ||pThis->bStopHeads == true))
    {
			string strRelation;
			string strPOS;
			string strLemma;

	    const char** pDummy (pAttribute);
	    while (*pDummy != 0 && pDummy != 0)
	    {
	      string strAttribute(*pDummy);
	      string strValue(*(++pDummy));
	      if(strAttribute == "rel")
	      {
					strRelation = strValue;
	      }
	      else if(strAttribute == "POS")
	      {
	        strPOS = strValue;
	      }
	      else if(strAttribute == "lemma")
	      {
	        strLemma = strValue;
	      }
	      else
	      {
	        pThis->error(ErrorAttribute);
	        return;
	      }
	      
	      ++pDummy;
	    }

			if (pThis->bStopDependents == true)
			{
				string strHash = strRelation + "\x01" + strPOS + "\x01" + strLemma;
				pThis->setStopDependents.insert(strHash);
			}
			if (pThis->bStopHeads == true)
			{
				string strHash = strRelation + "\x01" + strPOS + "\x01" + strLemma;
				pThis->setStopHeads.insert(strHash);
			}

    }
    else if(strName == TAG_STOP && (pThis->bStopRelations == true))
    {
			string strRelation;
			string strPOS1;
			string strLemma1;
			string strPOS2;
			string strLemma2;
			string strPrep;

	    const char** pDummy (pAttribute);
	    while (*pDummy != 0 && pDummy != 0)
	    {
	      string strAttribute(*pDummy);
	      string strValue(*(++pDummy));
	      if(strAttribute == "rel")
	      {
					strRelation = strValue;
	      }
	      else if(strAttribute == "POS1")
	      {
	        strPOS1 = strValue;
	      }
	      else if(strAttribute == "lemma1")
	      {
	        strLemma1 = strValue;
	      }
	      else if(strAttribute == "POS2")
	      {
	        strPOS2 = strValue;
	      }
	      else if(strAttribute == "lemma2")
	      {
	        strLemma2 = strValue;
	      }
	      else if(strAttribute == "prep")
	      {
	        strPrep = strValue;
	      }
	      else
	      {
	        pThis->error(ErrorAttribute);
	        return;
	      }
	      
	      ++pDummy;
	    }

				string strHash = strRelation + "\x01" + strPOS1 + "\x01" + strLemma1+ "\x01" + strPOS2 + "\x01" + strLemma2+ "\x01" + strPrep;
				pThis->setStopRelations.insert(strHash);

    }
    else if(strName == TAG_STOP && (pThis->bStopClass == true))
    {
			string strName;
			string strFunction;
			string strScore("-1");
			string strPOS1("#");
			string strPOS2("#");

	    const char** pDummy (pAttribute);
	    while (*pDummy != 0 && pDummy != 0)
	    {
	      string strAttribute(*pDummy);
	      string strValue(*(++pDummy));
	      if(strAttribute == "trigger")
	      {
					strName = strValue;
	      }
	      else if(strAttribute == "POS1")
	      {
					strPOS1 = strValue;
	      }
	      else if(strAttribute == "POS2")
	      {
					strPOS2 = strValue;
	      }
	      else if(strAttribute == "relation")
	      {
					strFunction = strValue;
	      }
	      else if(strAttribute == "score")
	      {
					strScore = strValue;
	      }
	      else
	      {
	        pThis->error(ErrorAttribute);
	        return;
	      }
	      
	      ++pDummy;
	    }

			float iScore=atof(strScore.c_str());
			TriggerInfo CTriggerInfo;
			CTriggerInfo.iScore = iScore;

			if (strFunction.empty())
      {
			  pThis->setStopClass.insert(make_pair(strName,CTriggerInfo));
      }
			else
			{
			  pThis->setStopClass_func.insert(make_pair(strPOS1+"\x01"+strFunction+"\x01"+strName+"\x01"+strPOS2,CTriggerInfo));
			}

    }
    else if(strName == "surface1-req" && (pThis->bExtendedSurfaceForm == true))
    {
			string strName;
			string strFunction;
			string strScore("-1");
			string strPOS("#");

	    const char** pDummy (pAttribute);
	    while (*pDummy != 0 && pDummy != 0)
	    {
	      string strAttribute(*pDummy);
	      string strValue(*(++pDummy));
	      if(strAttribute == "trigger")
	      {
					strName = strValue;
	      }
	      else if(strAttribute == "POS")
	      {
					strPOS = strValue;
	      }
	      else if(strAttribute == "relation")
	      {
					strFunction = strValue;
	      }
	      else
	      {
	        pThis->error(ErrorAttribute);
	        return;
	      }
	      
	      ++pDummy;
	    }

			float iScore=atof(strScore.c_str());
			TriggerInfo CTriggerInfo;
			CTriggerInfo.iScore = iScore;

			pThis->mapSurface1Trigger.insert(make_pair(strPOS+"\x01"+strFunction,strName));

    }
    else if(strName == "surface2-req" && (pThis->bExtendedSurfaceForm == true))
    {
			string strName;
			string strFunction;
			string strScore("-1");
			string strPOS("#");

	    const char** pDummy (pAttribute);
	    while (*pDummy != 0 && pDummy != 0)
	    {
	      string strAttribute(*pDummy);
	      string strValue(*(++pDummy));
	      if(strAttribute == "trigger")
	      {
					strName = strValue;
	      }
	      else if(strAttribute == "POS")
	      {
					strPOS = strValue;
	      }
	      else if(strAttribute == "relation")
	      {
					strFunction = strValue;
	      }
	      else
	      {
	        pThis->error(ErrorAttribute);
	        return;
	      }
	      
	      ++pDummy;
	    }

			float iScore=atof(strScore.c_str());
			TriggerInfo CTriggerInfo;
			CTriggerInfo.iScore = iScore;

			pThis->mapSurface2Trigger.insert(make_pair(strPOS+"\x01"+strFunction,strName));

    }
    else if(strName == "surface1-stop" && (pThis->bExtendedSurfaceForm == true))
    {
			string strName;
			string strFunction;
			string strScore("-1");
			string strPOS("#");

	    const char** pDummy (pAttribute);
	    while (*pDummy != 0 && pDummy != 0)
	    {
	      string strAttribute(*pDummy);
	      string strValue(*(++pDummy));
	      if(strAttribute == "trigger")
	      {
					strName = strValue;
	      }
	      else if(strAttribute == "POS")
	      {
					strPOS = strValue;
	      }
	      else if(strAttribute == "relation")
	      {
					strFunction = strValue;
	      }
	      else
	      {
	        pThis->error(ErrorAttribute);
	        return;
	      }
	      
	      ++pDummy;
	    }

			float iScore=atof(strScore.c_str());
			TriggerInfo CTriggerInfo;
			CTriggerInfo.iScore = iScore;

			pThis->mapSurface1Stop.insert(make_pair(strPOS+"\x01"+strFunction,strName));

    }
    else if(strName == "surface2-stop" && (pThis->bExtendedSurfaceForm == true))
    {
			string strName;
			string strFunction;
			string strScore("-1");
			string strPOS("#");

	    const char** pDummy (pAttribute);
	    while (*pDummy != 0 && pDummy != 0)
	    {
	      string strAttribute(*pDummy);
	      string strValue(*(++pDummy));
	      if(strAttribute == "trigger")
	      {
					strName = strValue;
	      }
	      else if(strAttribute == "POS")
	      {
					strPOS = strValue;
	      }
	      else if(strAttribute == "relation")
	      {
					strFunction = strValue;
	      }
	      else
	      {
	        pThis->error(ErrorAttribute);
	        return;
	      }
	      
	      ++pDummy;
	    }

			float iScore=atof(strScore.c_str());
			TriggerInfo CTriggerInfo;
			CTriggerInfo.iScore = iScore;

			pThis->mapSurface2Stop.insert(make_pair(strPOS+"\x01"+strFunction,strName));

    }
    else if(strName == TAG_REQUIRE)
    {
			string strName;
			string strFunction;
			string strScore("-1");
			string strPOS1("#");
			string strPOS2("#");

	    const char** pDummy (pAttribute);
	    while (*pDummy != 0 && pDummy != 0)
	    {
	      string strAttribute(*pDummy);
	      string strValue(*(++pDummy));
	      if(strAttribute == "trigger")
	      {
					strName = strValue;
	      }
	      else if(strAttribute == "relation")
	      {
					strFunction = strValue;
	      }
	      else if(strAttribute == "POS1")
	      {
					strPOS1 = strValue;
	      }
	      else if(strAttribute == "POS2")
	      {
					strPOS2 = strValue;
	      }
	      else if(strAttribute == "relation")
	      {
					strFunction = strValue;
	      }
	      else if(strAttribute == "score")
	      {
					strScore = strValue;
	      }
	      else
	      {
	        pThis->error(ErrorAttribute);
	        return;
	      }
	      
	      ++pDummy;
	    }
			
			float iScore=atof(strScore.c_str());
			TriggerInfo CTriggerInfo;
			CTriggerInfo.iScore = iScore;

			if (strFunction.empty())
      {
			  pThis->mapReqClass.insert(make_pair(strName,CTriggerInfo));
      }
			else
			{

        strFunction = strPOS1 + "\x01"+ strFunction +"\x01"+ strPOS2;

				hash_map<string, map<string,TriggerInfo> >::iterator pt;
				pt = pThis->mapReqClass_func.find(strFunction);
				if (pt != pThis->mapReqClass_func.end())
				{
					pt->second.insert(make_pair(strName,CTriggerInfo));
				}
				else
				{
					map<string,TriggerInfo> setDummy;
					setDummy.insert(make_pair(strName,CTriggerInfo));
			    pThis->mapReqClass_func.insert(make_pair(strFunction,setDummy));
				}
			}

    }
    else if(strName == TAG_NEGATIVE_LIST &&  pThis->bSpecification == true)
    {
      pThis->bNegativeList=true;
    }
    else if(strName == TAG_NEGATIVE_LIST_FILE && pThis->bNegativeList == true)
    {
      pThis->bNegativeListFile=true;
    }
    else if(strName == TAG_POSITIVE_LIST &&  pThis->bSpecification == true)
    {
      pThis->bPositiveList=true;
    }
    else if(strName == TAG_POSITIVE_LIST_FILE && pThis->bPositiveList == true)
    {
      pThis->bPositiveListFile=true;
    }
    else if(strName == TAG_CORPUS_PATH &&  pThis->bSpecification == true)
    {
      pThis->bCorpusPath = true;
    } 
    else if(strName == TAG_CORPUS_NAME &&  pThis->bSpecification == true)
    {
      pThis->bCorpusName = true;
    } 
    else if(strName == TAG_CORPUS_LIMIT &&  pThis->bSpecification == true)
    {
      pThis->bCorpusLimit = true;
    } 
    else if(strName == TAG_CORPUS_NAME_ITEM &&  pThis->bCorpusName == true)
    {
      string strCorpus;
      string strName;

      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        if (strAttribute == ATTRIBUTE_CORPUS)
        {
          strCorpus = strValue;
        }
        else if (strAttribute == "name")
        {
          strName = strValue;
        }
        ++pDummy;
      }
      pThis->mapCorpusName.insert(make_pair(strCorpus,strName));
    }
    else if(strName == TAG_CORPUS_PATH_ITEM &&  pThis->bCorpusPath == true)
    {
      string strCorpus;
      string strPath;

      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        if (strAttribute == ATTRIBUTE_CORPUS)
        {
          strCorpus = strValue;
        }
        else if (strAttribute == ATTRIBUTE_PATH)
        {
          strPath = strValue;
        }
        ++pDummy;
      }
      pThis->mapCorpusPath.insert(make_pair(strCorpus,strPath));
      pThis->vCorpus.push_back(strCorpus);
    }
    else if(strName == TAG_CORPUS_LIMIT_ITEM &&  pThis->bCorpusLimit == true)
    {
      string strCorpus;
      string strPath;

      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        if (strAttribute == ATTRIBUTE_CORPUS)
        {
          strCorpus = strValue;
        }
        else if (strAttribute == "limit")
        {
          strPath = strValue;
        }
        ++pDummy;
      }
      pThis->mapCorpusLimit.insert(make_pair(strCorpus,strPath));
    }
    else if(strName == TAG_COLUMNS &&  pThis->bSpecification == true)
    {
       pThis->bColumns = true;
    }
    else if(strName == TAG_COLUMN &&  pThis->bColumns == true)
    {
      string strTextPath; 
      string strCorpus;

      pThis->setCurrentColumn.clear();
      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        if (strAttribute == ATTRIBUTE_CORPUS)
        {
          pThis->strCurrentCorpus = strValue;
          strCorpus = strValue;
        }
        else if (strAttribute == ATTRIBUTE_NUMBER)
        {
          pThis->setCurrentColumn.push_back(atoi(strValue.c_str()));
        }
        else if(strAttribute == "text-path")
        {
          strTextPath = strValue;
        }
        else
        {
          pThis->error(ErrorAttribute);
          return;
        }

        ++pDummy;
      }

      pThis->mapColumn.insert(make_pair(strCorpus,pThis->setCurrentColumn));

    }
    else if(strName == TAG_LEMMA_VARIATIONS &&  pThis->bSpecification == true)
    {
      pThis->bLemmaVariations=true;

      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        
        if (strAttribute == "file")
        {
          pThis->strLemmaVariationsFile = strValue;
				  ifstream stream(strValue.c_str());
				  if (!stream)
				  {
				    char a[1000];
				    sprintf(a,"): Datei existiert nicht: %s",strValue.c_str());
				    cerr<<a<<endl;
				  }
        }
        ++pDummy;
      }
    }
    else if(strName == TAG_STOP_LEMMA &&  pThis->bSpecification == true)
    {
      pThis->bStopLemma=true;

      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        
        if (strAttribute == "file")
        {
          pThis->strStopLemmaFile = strValue;
				  ifstream stream(strValue.c_str());
				  if (!stream)
				  {
				    char a[1000];
				    sprintf(a,"): Datei existiert nicht: %s",strValue.c_str());
				    cerr<<a<<endl;
				  }
        }
        ++pDummy;
      }

    }
    else if(strName == TAG_DOUBLES &&  pThis->bSpecification == true)
    {
      pThis->bDoubles=true;
    }
    else if(strName == TAG_DOUBLES_FILE && pThis->bDoubles == true)
    {
      pThis->bDoublesFile=true;
    }
    else if(strName == TAG_WORD && pThis->bStopwords == true)
    {
      pThis->bWord = true;

      const char** pDummy (pAttribute);
      while (*pDummy != 0 && pDummy != 0)
      {
        string strAttribute(*pDummy);
        string strValue(*(++pDummy));
        
        if (strAttribute == ATTRIBUTE_MIN_GLOBAL_DEP)
        {
          if (strValue == VALUE_DEPENDENT)
          {
            pThis->eStopwordModeCurrent = StopwordModeDependent;
          }
          else if (strValue == VALUE_HEAD)
          {
            pThis->eStopwordModeCurrent = StopwordModeHead;
          }
          else
          {
            pThis->error(ErrorValue);
          }                             
        }
        ++pDummy;
      }
    }
    else
    {
      pThis->error(ErrorTag);
      return;
    }
  }

  /**
   * Endhandler
   **/ 
  void ReadSpecification::end_hndl(void* data, const char* szName)
  {
    string strName(szName);
    ReadSpecification* pThis = ((ReadSpecification*)XML_GetUserData((ReadSpecification*)data));

    if (strName == TAG_SPECIFICATION && pThis->bSpecification==true)
    {
      pThis->bSpecification = false;
    }
    else if (strName == TAG_POS_MAPPING && pThis->bPOSMapping==true)
    {
      pThis->bPOSMapping = false;
    }
    else if (strName == TAG_POS_REWRITE && pThis->bPOSRewrite==true)
    {
      pThis->bPOSRewrite = false;
    }
    else if (strName == TAG_EXTENDED_SURFACE_FORM && pThis->bExtendedSurfaceForm==true)
    {
      pThis->bExtendedSurfaceForm = false;
    }
    else if (strName == TAG_PREP_MAPPING && pThis->bPrepMapping==true)
    {
      pThis->bPrepMapping = false;
    }
    else if (strName == TAG_LEMMA_MAPPING && pThis->bLemmaMapping==true)
    {
      pThis->bLemmaMapping = false;
    }
    else if (strName == TAG_RULE)
    {
    }
    else if (strName == TAG_CONNECTIONS && pThis->bConnection==true)
    {
      pThis->bConnection=false;
    }
    else if (strName == TAG_CHECK)
    {
    }
    else if(strName == TAG_INPUT_FILE && pThis->bInputFile==true)
    {
      pThis->bInputFile = false;
      
      pThis->vCSpecifications.push_back(pThis->CSpecifications);
    }
    else if(strName == TAG_RELATION && pThis->bRelation==true)
    {
      pThis->bRelation = false;
      if (pThis->CSpecifications.eInvert==InvertUndef)
      {
        pThis->CSpecifications.CSpecification1 = pThis->CSpecification; 
        pThis->CSpecifications.CSpecification2 = pThis->CSpecification; 
        pThis->CSpecifications.eInvert = InvertNo; 
      }
      else if (pThis->CSpecifications.eInvert==InvertYes)
      {
        pThis->CSpecifications.eInvert = InvertBidirect;
        pThis->CSpecifications.CSpecification1 = pThis->CSpecification; 
      }
      else
      {
        cout<<"fehler 12161"<<endl;
        exit(-1);
      }
    }
    else if(strName == TAG_RELATION_FILE && pThis->bRelationFile==true)
    {
      pThis->bRelationFile = false;
    }
    else if(strName == TAG_RELATION_INVERTED && pThis->bRelation==true)
    {
      pThis->bRelation = false;
      if (pThis->CSpecifications.eInvert==InvertUndef)
      {
        pThis->CSpecifications.CSpecification1 = pThis->CSpecification; 
        pThis->CSpecifications.CSpecification2 = pThis->CSpecification;
        pThis->CSpecifications.eInvert = InvertYes; 
      }
      else if (pThis->CSpecifications.eInvert==InvertNo)
      {
        pThis->CSpecifications.eInvert = InvertBidirect;
        pThis->CSpecifications.CSpecification2 = pThis->CSpecification; 
      }
      else
      {
        cout<<"): interner Fehler"<<endl;
        exit(-1);
      }
    }
    else if(strName == TAG_RELATION_BIDIRECTED && pThis->bRelation==true)
    {
      pThis->bRelation = false;
      if (pThis->CSpecifications.eInvert==InvertUndef)
      {
        pThis->CSpecifications.CSpecification1 = pThis->CSpecification; 
        pThis->CSpecifications.CSpecification2 = pThis->CSpecification;
        pThis->CSpecifications.eInvert = InvertBidirectEQ; 
      }
      else
      {
        cout<<"): interner Fehler"<<endl;
        exit(-1);
      }
    }
    else if(strName == TAG_SNIPPET && pThis->bSnippet==true)
    {
      pThis->bSnippet=false;
      pThis->CSpecification.strSnippet = pThis->strExpression;
      pThis->mapSnippet.insert(make_pair(pThis->CSpecification.strFunctionname,pThis->CSpecification.strSnippet));
    }
    else if(strName == TAG_EXAMPLE && pThis->bExample==true)
    {
      pThis->bExample=false;
      pThis->CSpecification.strExample = pThis->strExpression;
      pThis->mapExample.insert(make_pair(pThis->CSpecification.strFunctionname,pThis->CSpecification.strExample));
    }
    else if(strName == TAG_DESCRIPTION && pThis->bDescription==true)
    {
      pThis->bDescription=false;
      pThis->CSpecification.strDescription = pThis->strExpression;
      pThis->mapDescription.insert(make_pair(pThis->CSpecification.strFunctionname,pThis->CSpecification.strDescription));
    }
    else if(strName == TAG_BIBL_INFO)
    {
      pThis->bBiblInfo=false;
    }
    else if(strName == TAG_BIBL_INFO_ITEM && pThis->bBiblInfo==true)
    {
    }
    else if(strName == TAG_BIBL_FIELDS)
    {
      pThis->bBiblFields=false;
    }
    else if(strName == TAG_BIBL_FIELD && pThis->bBiblFields==true)
    {
      pThis->bBiblField=false;
      pThis->mapCBiblField.insert(make_pair(pThis->CBiblField.strCorpus,pThis->CBiblField));
    }
    else if(strName == TAG_BIBL_FIELD_DATE && pThis->bBiblField==true)
    {
    }
    else if(strName == TAG_BIBL_FIELD_AVAIL && pThis->bBiblField==true)
    {
    }
    else if(strName == TAG_BIBL_FIELD_ORIG && pThis->bBiblField==true)
    {
    }
    else if(strName == TAG_BIBL_FIELD_SIGLE && pThis->bBiblField==true)
    {
    }
    else if(strName == TAG_BIBL_FIELD_SCAN && pThis->bBiblField==true)
    {
    }
    else if(strName == TAG_BIBL_FIELD_TEXTCLASS && pThis->bBiblField==true)
    {
    }

    else if(strName == TAG_INFO_PATH)
    {
      pThis->bInfoPath=false;
    }
    else if(strName == TAG_INFO_ITEM_TEXT && pThis->bInfoPath==true)
    {
    }
    else if(strName == TAG_INFO_ITEM_DATE && pThis->bInfoPath==true)
    {
    }
    else if(strName == TAG_INFO_ITEM_ORIG && pThis->bInfoPath==true)
    {
    }
    else if(strName == TAG_INFO_ITEM_SIGLE && pThis->bInfoPath==true)
    {
    }
    else if(strName == TAG_INFO_ITEM_SCAN && pThis->bInfoPath==true)
    {
    }
    else if(strName == TAG_INFO_ITEM_AVAIL && pThis->bInfoPath==true)
    {
    }
    else if(strName == TAG_INFO_ITEM_TEXTCLASS && pThis->bInfoPath==true)
    {
    }
    else if(strName == TAG_PRECUT && pThis->bPrecut==true)
    {
      pThis->bPrecut = false;
    }
    else if(strName == TAG_CUT_FREQUENCY && pThis->bCutFrequency==true)
    {
      pThis->bCutFrequency = false;
    }
    else if(strName == TAG_CUT_WORDCOUNT && pThis->bCutWordcount==true)
    {
      pThis->bCutWordcount = false;
    }
    else if(strName == TAG_CUT_STATISTIC && pThis->bCutStatistic==true)
    {
      pThis->bCutStatistic = false;
    }
    else if(strName == TAG_CUT_STATISTIC_CORPUS && pThis->bCutStatisticCorpus==true)
    {
      pThis->bCutStatisticCorpus = false;
    }
    else if(strName == TAG_STOPWORDS && pThis->bStopwords==true)
    {
      pThis->bStopwords = false;
    }
    else if(strName == TAG_WORD && pThis->bWord==true)
    {
      pThis->bWord == false;
      pThis->CSpecification.mapStopwords.insert(make_pair(pThis->strExpression,pThis->eStopwordModeCurrent));
    }
    else if(strName == TAG_STOP_RELATIONS && pThis->bStopRelations==true)
    {
      pThis->bStopRelations = false;
    }
    else if(strName == TAG_STOP_DEPENDENTS &&  pThis->bStopDependents ==true)
    {
      pThis->bStopDependents = false;
    }
    else if(strName == TAG_STOP_HEADS && pThis->bStopHeads==true)
    {
      pThis->bStopHeads = false;
    }
    else if(strName == TAG_STOP_CLASS && pThis->bStopClass==true)
    {
      pThis->bStopClass = false;
    }
    else if(strName == TAG_POSITIVE_LIST && pThis->bPositiveList==true)
    {
      pThis->bPositiveList=false;
    }
    else if(strName == TAG_POSITIVE_LIST_FILE && pThis->bPositiveListFile==true)
    {
      pThis->bPositiveListFile=false;
      pThis->setPositiveFile.insert(pThis->strExpression);
    }
    else if(strName == TAG_NEGATIVE_LIST && pThis->bNegativeList==true)
    {
      pThis->bNegativeList=false;
    }
    else if(strName == TAG_NEGATIVE_LIST_FILE && pThis->bNegativeListFile==true)
    {
      pThis->bNegativeListFile=false;
      pThis->setNegativeFile.insert(pThis->strExpression);
    }
    else if(strName == TAG_DOUBLES && pThis->bDoubles==true)
    {
      pThis->bDoubles=false;
    }
    else if(strName == TAG_LEMMA_VARIATIONS && pThis->bLemmaVariations==true)
    {
      pThis->bLemmaVariations=false;
    }
    else if(strName == TAG_STOP_LEMMA && pThis->bStopLemma==true)
    {
      pThis->bStopLemma=false;
    }
    else if (strName == TAG_GOOD_EXAMPLES  && pThis->bGoodExamples==true)
    {
      pThis->bGoodExamples = false;
    }
    else if (strName == TAG_GOOD_EXAMPLES_ITEM  && pThis->bGoodExamples==true)
    {
    }
    else if(strName == TAG_STATISTIC_LIMITS && pThis->bStatisticLimits==true)
    {
      pThis->bStatisticLimits=false;
    }
    else if(strName == TAG_STATISTIC_ADJUST)
    {
    }

    else if(strName == TAG_CORPUS_NAME && pThis->bCorpusName==true)
    {
      pThis->bCorpusName=false;
    }

    else if(strName == TAG_CORPUS_PATH && pThis->bCorpusPath==true)
    {
      pThis->bCorpusPath=false;
    }
    else if(strName == TAG_CORPUS_NAME_ITEM && pThis->bCorpusName==true)
    {
    }
    else if(strName == TAG_CORPUS_PATH_ITEM && pThis->bCorpusPath==true)
    {
    }
    else if(strName == TAG_CORPUS_LIMIT && pThis->bCorpusLimit==true)
    {
      pThis->bCorpusLimit=false;
    }
    else if(strName == TAG_CORPUS_LIMIT_ITEM && pThis->bCorpusLimit==true)
    {
    }
    else if(strName == TAG_COLUMNS && pThis->bColumns==true)
    {
      pThis->bColumns=false;
    }
    else if(strName == TAG_COLUMN && pThis->bColumns==true)
    {
    }
    else if(strName == TAG_DOUBLES_FILE && pThis->bDoublesFile==true)
    {
      pThis->bDoublesFile=false;
      pThis->setDoublesFile.insert(pThis->strExpression);
    }
    else if(strName == TAG_STOP)
    {
    }
    else if(strName == "surface1-req")
    {
    }
    else if(strName == "surface2-req")
    {
    }
    else if(strName == "surface1-stop")
    {
    }
    else if(strName == "surface2-stop")
    {
    }
    else if(strName == TAG_REQUIRE)
    {
    }
    else
    {
      pThis->error(ErrorTag);
      return;
    }
  }
      
  /**
   * Char-Handler
   **/ 
  void ReadSpecification::char_hndl(void* data, const char* szText, int iLen)
  {
    ReadSpecification* pThis = ((ReadSpecification*)XML_GetUserData((ReadSpecification*)data));
    if (pThis->bName == true || pThis->bFile == true || pThis->bWord == true||pThis->bExample == true||pThis->bDescription == true||pThis->bSnippet == true )
    {
      pThis->strExpression += string(szText,iLen);
    }
    else if (pThis->bDoublesFile == true || pThis->bPositiveListFile == true || pThis->bNegativeListFile == true)
    {
      pThis->strExpression += string(szText,iLen);
    }
  }



#endif /*READ_SPECIFICATION_H_*/
