#ifndef FILE_MyUTF8_H_INCLUDED__
#define FILE_MyUTF8_H_INCLUDED__


namespace SynCoP {

typedef unsigned int SynCoP_uint32_t;
/**
 * This lookup table is used to help decode the first byte of a multi-byte UTF8 character.
 */
static const unsigned char sqlite3UtfTrans1[] = {
  0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
  0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f,
  0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17,
  0x18, 0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f,
  0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
  0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f,
  0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
  0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x00, 0x00,
};


    /** Zählt multi byte character im utf-8
     * @param str die zeichenkette in der gezählt werden soll
     * @return number of multi byte characters
     */
    inline size_t MB_position(const char* str)
    {
      const char* sp=str;
      int iResult(0);
      while (*sp != 0) 
      {
          if ((unsigned char) *sp < 128) 
          {
            ++iResult;
            ++sp;
          }
          else
          {
            ++iResult;
            if ( ((unsigned char)*(sp++)) >= 0xc0 )
            {
              while( ((unsigned char)*sp & 0xc0)==0x80 )
              {
                ++sp;
              }
            }
          }
      }
      return iResult;
    }

    /** Read a UTF8 encoded unicode character.
     * @param src Source byte buffer (must be null terminated)
     * @param c   Desination unicode character.
     * @return number of bytes read (without last null)
     */
    inline int utf8_read(const unsigned char* src, SynCoP_uint32_t* c)
    {
        const unsigned char* beg = src;
        if (*src == 0)
            return 0;

        *c = *(src++);
        if( *c >= 0xc0 ){
            *c = sqlite3UtfTrans1[*c-0xc0];
            while( (*src & 0xc0)==0x80 )
                *c = ((*c)<<6) + (0x3f & *(src++));
            if( *c<0x80
                    || ((*c)&0xFFFFF800)==0xD800
                    || ((*c)&0xFFFFFFFE)==0xFFFE )
                *c = 0xFFFD;
        }
        return src-beg;
    }

    /** Skip one character in a UTF8 encoded string (const version).
     * @param src UTF8 encoded string (null terminated)
     * @return advanced src
     */
    inline const unsigned char* utf8_skip(const unsigned char* src) {
        if( (*(src++))>=0xc0 )
            while( (*src & 0xc0)==0x80 )
                src++;
        return src;
    }

    /** Skip one character in a UTF8 encoded string (non-const version).
     * @param src UTF8 encoded string (null terminated)
     * @return advanced src
     */
    inline unsigned char* utf8_skip(unsigned char* src) {
        if( (*(src++))>=0xc0 )
            while( (*src & 0xc0)==0x80 )
                src++;
        return src;
    }

    /** Skip n characters in a UTF8 encoded string (const version).
     * @param src UTF8 encoded string (null terminated)
     * @param n Number of characters to skip
     * @return src skipped by n characters.
     */
    inline const unsigned char* utf8_skip_n(const unsigned char* src, int n) {
        while (n-- > 0)
            src = utf8_skip(src);
        return src;
    }

    /** Skip n characters in a UTF8 encoded string (non-const version).
     * @param src UTF8 encoded string (null terminated)
     * @param n Number of characters to skip
     * @return src skipped by n characters.
     */
    inline unsigned char* utf8_skip_n(unsigned char* src, int n) {
        while (n-- > 0)
            src = utf8_skip(src);
        return src;
    }

    /** Returns the number of bytes a UTF8 encoding of a unicode character needs.
     * @param c a unicode character (code point)
     * @return number of needed bytes.
     */
    inline int utf8_len(SynCoP_uint32_t c) {
        if (c < 0x0080)
            return 1;
        else if (c < 0x00800)
            return 2;
        else if (c < 0x10000)
            return 3;
        else
            return 4;
    }

    /** Writes unicode character c to byte buffer dst.
     * @param dst destination byte buffer must at hold at least utf8_len(c) characters.
     * @param c unicode character to write.
     * @return number of bytes written (equal to utf8_len(c)
     */
    inline int utf8_write(unsigned char* dst, SynCoP_uint32_t c) {
        const unsigned char* beg = dst;
        if( c<0x00080 ){
            *dst++ = (c&0xFF);
        }
        else if( c<0x00800 ){
            *dst++ = 0xC0 + ((c>>6)&0x1F);
            *dst++ = 0x80 + (c & 0x3F);
        }
        else if( c<0x10000 ){
            *dst++ = 0xE0 + ((c>>12)&0x0F);
            *dst++ = 0x80 + ((c>>6) & 0x3F);
            *dst++ = 0x80 + (c & 0x3F);
        }else{
            *dst++ = 0xF0 + ((c>>18) & 0x07);
            *dst++ = 0x80 + ((c>>12) & 0x3F);
            *dst++ = 0x80 + ((c>>6) & 0x3F);
            *dst++ = 0x80 + (c & 0x3F);
        }
        return dst - beg;
    }
}

#endif
