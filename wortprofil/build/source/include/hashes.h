/**
 *
 * HASH-Objekte für die Tuple-Hash-Maps
 *
 */

#ifndef HASHES_H_
#define HASHES_H_

#include <backward/hash_fun.h>

/* Include hash_* headers and import namespace */
#if defined __BORLANDC__
  #include <stlport/hash_map>
  #include <stlport/hash_set>

#elif defined _MSC_VER
  #include <hash_map>
  #include <hash_set>

#elif defined __ICC
  #include <hash_map>
  #include <hash_set>

#elif defined(__GNUC__) && __GNUC__ >= 3
  #include <ext/hash_map>
  #include <ext/hash_set>

#elif defined(__GNUC__) && __GNUC__ < 3
  #include <hash_map>
  #include <hash_set>

#else // unknown build environment
 # include <stlport/hash_map>
 # include <stlport/hash_set>
#endif

using namespace std;
using namespace __gnu_cxx;

namespace __gnu_cxx
{
  template<> struct hash< std::string >
  {
    size_t operator()( const std::string& x ) const
    {
      return hash< const char* >()( x.c_str() );
    }
  };
}


/// Encode a pair of integers bijectively as an integer
unsigned long pair_encoding(unsigned int x, unsigned int y)
{
  return ((x*x) + (y*y) + (2*x*y) + x + y)/2 + x;
}


/**
 *
 * Hash für ein Paar
 *
 */
struct HashPair
{
  HashPair():
    first(0),
    second(0)
  {
  }
  HashPair(unsigned int _first,unsigned int _second):
    first(_first),
    second(_second)
  {
  }

  inline bool operator<(const HashPair& obj) const
  {
     if (this->first < obj.first)
     {
       return true;
     }
     else if (this->first == obj.first)
     {
       if (this->second < obj.second)
       {
         return true;
       }
     }
     return false;
  }

  unsigned int first;
  //unsigned short second;
  unsigned second;
}; 

struct PSEqualToPair
{
  inline bool operator()(const HashPair& obj1, const HashPair& obj2) const;
};
inline bool PSEqualToPair::operator()(const HashPair& obj1, const HashPair& obj2) const
{
  return obj1.first == obj2.first && obj1.second == obj2.second;
}    
struct PSHashPair
{
  inline size_t operator()(const HashPair& obj) const;
};
inline size_t PSHashPair::operator()(const HashPair& obj) const
{
  return pair_encoding(obj.first,obj.second);
}


/**
 *
 * Hash für ein Tripel
 *
 */
struct HashTriple
{
  HashTriple():
    first(0),
    second(0),
    third(0)
  {
  }
  HashTriple(unsigned int _first,unsigned int _second,unsigned int _third):
    first(_first),
    second(_second),
    third(_third)
  {
  }

  inline bool operator<(const HashTriple& obj) const
  {
     if (this->first < obj.first)
     {
       return true;
     }
     else if (this->first == obj.first)
     {
       if (this->second < obj.second)
       {
         return true;
       }
       else if (this->second == obj.second)
       {  
         if (this->third < obj.third)
         {
           return true;
         }
       }
     }
     return false;
  }

  unsigned int first;
  unsigned int second;
  //unsigned short third;
  unsigned third;
}; 

struct PSEqualToTriple
{
  inline bool operator()(const HashTriple& obj1, const HashTriple& obj2) const;
};
inline bool PSEqualToTriple::operator()(const HashTriple& obj1, const HashTriple& obj2) const
{
  return obj1.first == obj2.first && obj1.second == obj2.second && obj1.third == obj2.third;
}    
struct PSHashTriple
{
  inline size_t operator()(const HashTriple& obj) const;
};
inline size_t PSHashTriple::operator()(const HashTriple& obj) const
{
  return pair_encoding(pair_encoding(obj.first,obj.second),obj.third);
}

/**
 *
 * Hash für ein vierstelliges Tupel
 *
 */
struct HashQuad
{
  HashQuad():
    first(0),
    second(0),
    third(0),
    fourth(0)
  {
  }
  HashQuad(unsigned int _first,unsigned int _second,unsigned int _third,unsigned int _fourth):
    first(_first),
    second(_second),
    third(_third),
    fourth(_fourth)
  {
  }

  inline bool operator<(const HashQuad& obj) const
  {
     if (this->first < obj.first)
     {
       return true;
     }
     else if (this->first == obj.first)
     {
       if (this->second < obj.second)
       {
         return true;
       }
       else if (this->second == obj.second)
       {  
         if (this->third < obj.third)
         {
           return true;
         }
         else if (this->third < obj.third)
         {
           if (this->fourth < obj.fourth)
           {
             return true;
           }
         }
       }
     }
     return false;
  }

  unsigned int first;
  unsigned int second;
  unsigned int third;
  //unsigned short fourth;
  unsigned fourth;
}; 

struct PSEqualToQuad
{
  inline bool operator()(const HashQuad& obj1, const HashQuad& obj2) const;
};
inline bool PSEqualToQuad::operator()(const HashQuad& obj1, const HashQuad& obj2) const
{
  return obj1.first == obj2.first && obj1.second == obj2.second && obj1.third == obj2.third && obj1.fourth == obj2.fourth;
}    
struct PSHashQuad
{
  inline size_t operator()(const HashQuad& obj) const;
};
inline size_t PSHashQuad::operator()(const HashQuad& obj) const
{
  return pair_encoding(pair_encoding(pair_encoding(obj.first,obj.second),obj.third),obj.fourth);
}

/**
 *
 * Hash für ein fünfstelliges Tupel
 *
 */
struct HashQuint
{
  HashQuint():
    first(0),
    second(0),
    third(0),
    fourth(0),
    fifth(0)
  {
  }
  HashQuint(unsigned int _first,unsigned int _second,unsigned int _third,unsigned int _fourth,unsigned int _fifth):
    first(_first),
    second(_second),
    third(_third),
    fourth(_fourth),
    fifth(_fifth)
  {
  }

  inline bool operator<(const HashQuint& obj) const
  {
     if (this->first < obj.first)
     {
       return true;
     }
     else if (this->first == obj.first)
     {
       if (this->second < obj.second)
       {
         return true;
       }
       else if (this->second == obj.second)
       {  
         if (this->third < obj.third)
         {
           return true;
         }
         else if (this->third < obj.third)
         {
           if (this->fourth < obj.fourth)
           {
             return true;
           }
           else if (this->fourth == obj.fourth)
           {
             if (this->fifth < obj.fifth)
             {
               return true;
             }
           }
         }
       }
     }
     return false;
  }

  unsigned int first;
  unsigned int second;
  unsigned int third;
  unsigned fourth;
  unsigned fifth;
}; 

struct PSEqualToQuint
{
  inline bool operator()(const HashQuint& obj1, const HashQuint& obj2) const;
};
inline bool PSEqualToQuint::operator()(const HashQuint& obj1, const HashQuint& obj2) const
{
  return obj1.first == obj2.first && obj1.second == obj2.second && obj1.third == obj2.third && obj1.fourth == obj2.fourth && obj1.fifth == obj2.fifth;
}    
struct PSHashQuint
{
  inline size_t operator()(const HashQuint& obj) const;
};
inline size_t PSHashQuint::operator()(const HashQuint& obj) const
{
  return pair_encoding(pair_encoding(pair_encoding(pair_encoding(obj.first,obj.second),obj.third),obj.fourth),obj.fifth);
}

/**
 *
 * Hash für ein sechsstelliges Tupel
 *
 */
struct HashSix
{
  HashSix():
    first(0),
    second(0),
    third(0),
    fourth(0),
    fifth(0),
    sixth(0)
  {
  }
  HashSix(unsigned int _first,unsigned int _second,unsigned int _third,unsigned int _fourth,unsigned int _fifth,unsigned int _sixth):
    first(_first),
    second(_second),
    third(_third),
    fourth(_fourth),
    fifth(_fifth),
    sixth(_sixth)
  {
  }

  inline bool operator<(const HashSix& obj) const
  {
     if (this->first < obj.first)
     {
       return true;
     }
     else if (this->first == obj.first)
     {
       if (this->second < obj.second)
       {
         return true;
       }
       else if (this->second == obj.second)
       {  
         if (this->third < obj.third)
         {
           return true;
         }
         else if (this->third < obj.third)
         {
           if (this->fourth < obj.fourth)
           {
             return true;
           }
           else if (this->fourth == obj.fourth)
           {
             if (this->fifth < obj.fifth)
             {
               return true;
             }
             else if (this->sixth == obj.sixth)
             {
               if (this->sixth < obj.sixth)
               {
                 return true;
               }
             }
           }
         }
       }
     }
     return false;
  }

  unsigned int first;
  unsigned int second;
  unsigned int third;
  unsigned fourth;
  unsigned fifth;
  unsigned sixth;
}; 

struct PSEqualToSix
{
  inline bool operator()(const HashSix& obj1, const HashSix& obj2) const;
};
inline bool PSEqualToSix::operator()(const HashSix& obj1, const HashSix& obj2) const
{
  return obj1.first == obj2.first && obj1.second == obj2.second && obj1.third == obj2.third && obj1.fourth == obj2.fourth && obj1.fifth == obj2.fifth&& obj1.sixth == obj2.sixth;
}    
struct PSHashSix
{
  inline size_t operator()(const HashSix& obj) const;
};
inline size_t PSHashSix::operator()(const HashSix& obj) const
{
  return pair_encoding(pair_encoding(pair_encoding(pair_encoding(pair_encoding(obj.first,obj.second),obj.third),obj.fourth),obj.fifth),obj.sixth);
}

#endif /*HASHES_H_*/
