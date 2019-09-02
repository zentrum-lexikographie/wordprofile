/** @page re2cScanner RE2CLexer Documentation
 * \section scannerdef re2c scanner definition
 *
 * A re2c input file may look like this:
 * \verbatim
 * int TestFlexer::yylex()
 * {
 * #define YYFILL(count) { if (m_fill(count) == false) return 0; }
 * start:
 *         m_tok_begin = m_cursor;
 *         /*!re2c
 *         re2c:define:YYCTYPE  = "CHAR";
 *         re2c:define:YYCURSOR = m_cursor;
 *         re2c:define:YYLIMIT  = m_limit;
 *
 *         [A-Za-z]+      { return m_return(TOK_WORD);}
 *         [\000-\377]    { goto start; }
 *         \*\/
 * }
 * \endverbatim
 *
 * When needed, you can define \p YYMARKER and \p YYCTXMARKER:
 *
 * \verbatim
 *         re2c:define:YYMARKER    = m_marker;
 *         re2c:define:YYCTXMARKER = m_ctx_marker;
 * \endverbatim
 *
 * \par Template parameter
 *
 * The template parameter CHAR specifies the underlying character type.
 * By default it is set to \p char.
 *
 * \section re2cunicode Unicode aware scanners
 *
 * When dealing with unicode input, it is assumed to be UTF-8 encoded. 
 * \note No other unicode encoding (e.g. UTF-16) is supported. 
 *
 * There are the following two ways to scan unicode (UTF-8 encoded)
 *
 * \subsection re2cunicode1 Unicode - way 1
 *
 * One way to deal with utf8 encoded input is to leave it as it is (that is a
 * squence of bytes, where one character may be represented by multiple bytes).
 *
 * Then your re2c-code must handle the multy-byte sequences. For example as
 * follows:
 * 
 * \verbatim
 * auml  = (\xC3\xA4)|(\xC3\x84); // ä, Ä
 * ouml  = (\xC3\xB6)|(\xC3\x96); // ö, Ö 
 * uuml  = (\xC3\xBC)|(\xC3\x9C); // ü, Ü
 * sz    = (\xC3\x9F); // ß
 *
 * wordchar = ([A-Za-z]|auml|ouml|uuml|sz);
 * any      = [^];
 *
 * wordchar+   { return m_return(WORD); }
 * any         { return m_return(OTHER); }
 * \endverbatim
 *
 * You could generate the byte sequences for the characters with a script.
 *
 * The text that is returned by YYText() will contain the original matched
 * byte sequence.
 *
 * This method is the fastest, since no character conversion is needed. The 
 * drawback is, that you must hand-code the used utf8-characters. But you may
 * use utf-8 sequences in the following way:
 *
 * \verbatim
 *  ascii       = [A-Za-z];
 *  latin1      = (\xC3[\x80-\x96\x98-\xB6\xB8-BF]);
 *              // excluded \xC3\x97 (\u00D7 = cart. prod)
 *              // excluded \xC3\xB7 (\u00F7 = division sign)
 *  latin_extA  = ([\xC4-\xC5][\x80-\xBF]);
 *
 *  wordchar    = (ascii|latin1|latin1_extA)+;
 *  any         = [^];
 * \endverbatim
 *
 * \subsection re2cunicode2 Unicode - way 2
 *
 * Use \p uint32_t (a unsigned 32 bit integer) as the template parameter CHAR
 * for full unicode support (0x00 - 0x10FFFF). Then the input must be encoded
 * in UTF-8 and will be decoded to a 32-bit unicode code point. Other unicode
 * encodings (e.g. UTF-16) are not supported.
 *
 * Please note that \p wchar_t should not be used, since it is not portable.
 * On windows \p wchar_t is a 16-bit type. Characters may be represented by a 
 * surrogate pair (two consecutive \p wchar_t items). On linux, \p wchar_t is
 * typically 32-bit wide.
 *
 * The re2c scanner must be generated with the appropirate switch (<tt>re2c
 * -u</tt> should be used for <tt>RE2CLexer<uint32_t></tt>).
 *
 * When working with character classes, you cannot just write '&auml;'. Instead
 * of <tt>wordchars = [A-Za-z&auml;&Auml;&ouml;&Ouml;&uuml;&Uuml;&szlig;];</tt>
 *
 * You have to write:
 * \verbatim
 *      wordchars = [A-Za-z\u00E4\u00C4\u00F6\u00D6\u00FC\u00DC\u00DF];
 * \endverbatim
 *
 * Unicode code points with more than 4 digits must be written as
 * <tt>\\U012345678</tt> (a backslash, an uppercase U and the eight hexadecimal
 * digits of the code point).  You can simplify this by writing
 * <tt>wordchars = [A-Za-z&auml;&Auml;&ouml;&Ouml;&uuml;&Uuml;&szlig;];</tt> in
 * your re2c scanner definition and preprocessing it with the following python
 * script (<tt>re2cu8.py</tt>):
 *
 * \verbatim
 *  #!/bin/env python
 *  import sys
 *  for line in sys.stdin:
 *      line = unicode(line, "UTF-8")
 *      for c in line:
 *          if ord(c) < 128:
 *              sys.stdout.write(c)
 *          elif ord(c) < 2**16:
 *              sys.stdout.write(r"\u%04X" % ord(c))
 *          else:
 *              sys.stdout.write(r"\U%08X" & ord(c))
 * \endverbatim
 *
 * And call it in the following way:
 * \verbatim
 *  python re2cu8.py < scanner.re.u8 > scanner.re
 *  re2c -u -o scanner.inc scanner.re
 * \endverbatim
 */

#include "utf8.h"
//#include <cassert>

/** 
 * @brief Class for wrapping a re2c-based scanner.
 *
 * Modeled after the C++-Interface of Flex.
 *
 * Following function from the flex interface are not implemented:
 * - yy_switch_to_buffer()
 * - yy_create_buffer()
 * - yy_flush_buffer()
 * - yy_delete_buffer()
 * - yyrestart()
 * - set_debug()
 * - debug()
 *
 * See \ref re2cScanner for details.
 *
 */
#include <stdint.h>
namespace SynCoP
{    

template<typename CHAR=char>
class MyRE2CLexer {
    public:
        typedef CHAR        char_type;                      //!< template parameter
        static const size_t char_width = sizeof(char_type); ///< size of template parameter in bytes

    public:
        /**
         * @brief Constructs a new Re2cFlexer with optional input/output streams.
         * When \b in or \p out are NULL, they correspond to std::cin or std::cout respectively.
         * @param in Pointer to input stream. When NULL, &std::cin is used.
         * @param out Pointer to output stream. Whenn NULL, &std::cout is used.
         */
        MyRE2CLexer(std::istream* in = NULL, std::ostream* out = NULL);

        /**
         * @brief Deletes instance.
         */
        virtual ~MyRE2CLexer();

        /** 
         * @brief Assign new input/output streams.
         * Reassign the internal input stream to \b new_in and the internal output buffer to \b new_out when not NULL.
         * Resets the internal input buffers.
         * @param new_in new input stream. When NULL, input stream is not changed, but buffer is reset.
         * @param new_out new output stream.
        */
        virtual void switch_streams(std::istream* new_in = NULL, std::ostream* new_out = NULL);

        /**
         * When state is false, the data returned by YYText() is not null-terminated.
         * Setting to false will improve performance, since no copying of matched input to temp buffer is necessary.
         * Use YYLeng() to get the length of the matched text.
         */
        virtual void set_yytext_null_terminated(bool state) { m_yytext_null_terminated = state; }

        /*!
         * @brief Scans the input stream, consuming tokens, until a rule's action returns a value.
         * - By convention, a return value of 0 means EOF.
         * - empty rules must jump to the beginning of the yylex() function.
         * - set the token start with m_set_token(m_cursor)
         * - Only return tokens through <tt>return m_return(TOK_WORD)</tt>
         * @note Subclasses must override this method.
         *
         * \par Example of yylex definition in subclass
         *   (Remove backslashes (\\) before / and *)
         * \code
         *  class MyFlexLexer : public RE2CLexer<char> {
         *      public:
         *          virtual int yylex() {
         *  start:
         *              m_set_token(m_cursor);
         *              \/\*!re2c
         *              re2c:define:YYCTYPE  = "unsigned char";
         *              re2c:define:YYCURSOR = m_yycursor;
         *              re2c:define:YYLIMIT  = m_yylimit;
         *              re2c:define:YYFILL   = m_yyfill;
         *              re2c:yych:conversion = 1;
         * 
         *              [A-Za-z]+      { return m_return(1);     }
         *              [\000]         { if (m_eof) 
         *                                   return m_return(0); 
         *                               else
         *                                   goto start;  
         *                             }
         *              [^]            { goto start;             }
         *              \*\/
         *  }
         * \endcode
         *
         * \par Example of Unicode scanner
         * 
         * \code
         *  enum TokenType {
         *      TOK_EOF = 0,
         *      TOK_WORD
         *  };
         *
         *  class TestFlexer2 : public RE2CLexer<uint32_t> {
         *      public:
         *          virtual int yylex();
         *  };
         *
         *  int TestFlexer2::yylex()
         *  {
         *  start:
         *      m_set_token(m_yycursor);
         *      \/\*!re2c
         *      re2c:define:YYCTYPE  = "uint32_t";
         *      re2c:define:YYCURSOR = m_yycursor;
         *      re2c:define:YYLIMIT  = m_yylimit;
         *      re2c:define:YYMARKER = m_yymarker;
         *      re2c:define:YYFILL   = m_yyfill;
         *
         *      [A-Za-z\u00C4\u00D6\u00DC\u00E4\u00F6\u00FC\u00DF]+   { return m_return(TOK_WORD);}
         *      [\000]      { if (m_eof) 
         *                        return m_return(TOK_EOF); 
         *                    else
         *                        goto start; 
         *                  }
         *      [^]         { goto start;}
         *      \*\/
         *  }
         * \endcode
         * @return The matched rule's action return value.
        */
        //virtual bool yylex() = 0;

        /*!
         * @brief Returns the text (a pointer to CHAR) of the most recently matched token.
         * The returned string is null-terminated.
         *
         * @note When set_yytext_null_terminated() is set to false, the returned string is
         * not null-terminated. Use the function YYLeng() to get the length of the matched token.
         * @return Matched input
         */
        inline const string& YYText();

        /*!
         * @brief returnes the original input bytes of the matched token.
         * Useful for getting the original UTF8 encoded input in unicde scanners.
         * @see YYLeng_bytes for the length of the returned buffer.
         * @note The returned data is not null-terminated.
         * @return Original bytes that matched input.
         */
        inline const char* YYText_bytes() const;

        /*!
         * @brief Returns the length of the most recently matched token (in terms of CHAR items).
         * @return Length of matched token.
         */
        inline int YYLeng() const;
        inline int YYMBLeng() const;

        /*!
         * @brief Returns the length of the underlying byte buffer of the matched token.
         * Useful for YYText_bytes().
         */
        inline int YYLeng_bytes() const;

        /*!
         * @brief Returns the current input line number.
         * Underlying re2c scanner must update the protected member lineno, 
         * otherwise this functionr will always return 1.
         * @return Current line number.
         */
        inline int lineno() const;

        /*!
         * @brief Returns the current column number.
         * Underlying re2c scanner must update the protected member colno,
         * otherwise this function will always return 1.
         */
        inline int colno() const;

    protected:
        /** 
         * @brief Provide more input (byte-based).
         * Subclasses may override this method to read from another input
         * source than the internal input stream buffer (e.g. a string). 
         *   
         * \par Example:
         * 
         * \code
         * class MyFlexLexer : public RE2CLexer<char> {
         *     public:
         *         MyFlexLexer(const std::string& s) 
         *           : m_str(str), m_it(m_str.begin())
         *         {}
         *
         *         void switch_input(const std::string& s) 
         *         { 
         *             m_str = str;
         *             m_it = m_str.begin();
         *         }
         *         
         *         virtual int LexerInput(char* buf, int size);
         *     private:
         *         const std::string                 m_str;
         *         const std::string::const_iterator m_it;
         * }
         *
         * int MyFlexLexer::LexerInput(char* buf, int size)
         * {
         *     int read = 0;
         *     while (m_it != m_str.end() && size > 0) {
         *         *buf++ = *m_it++;
         *         size--;
         *         read++;
         *     }
         *     return read;
         * }
         * \endcode
         *
         * @param buf Destination buffer.
         * @param size Number of bytes to read.
         * @return Number of bytes read. -1 on error. 0 when end of input is reached.
         */
        virtual int LexerInput(char * buf, int size);

        /**
         * @brief Write size elements of buf to current output stream.
         * @param buf Destination buffer.
         * @param size Number of elements in buf to write
        */
        virtual void LexerOutput(const char* buf, int size);

        /** 
         * @brief Reports a fatal error message.
         * The default implementation writes msg to std::cerr and optionally exits the program.
         * @param msg Error message to write (0-terminated).
         * @param fatal When true, the program exists.
        */
        virtual void LexerError(const char* msg, bool fatal);


    protected:
        /*!
         * @brief Set current token.
         * This function is called from your yylex() function for setting the
         * beginning of the next token.
         */
        inline void set_token(CHAR* token_begin);

        inline void init_multi_byte_counter();

        /*!
         * @brief Fill internal buffer (called from yylex()).
         * When less than count bytes were made available, m_eof is set to 
         * \p true and \p 0 is appended to the input.
         *
         * @param count Number of CHAR-items, that the internal buffer must contain (at least) after this call.
         * @return The number of items available. When this is less than the requested count, end of input is reached.
         */ 
        inline size_t m_yyfill(size_t count);

        /*!
         * @brief Internal routine for reading CHAR-items from a byte based input.
         */
        inline void m_yyfill_internal(size_t wanted);

        //! Save current cursor position (end of token) and return token type
        inline void process_token();

        std::istream* m_input;      //!< current input stream
        std::ostream* m_output;     //!< current output stream (unused)

        //std::basic_string<CHAR>   m_result;                 //!< contains matched token
        string m_result;                 //!< contains matched token
        bool                      m_yytext_null_terminated; //!< Do not use internal token buffer, reported tokens are NOT null-terminated

        static const size_t m_bsize   = 8192;                   //!< size for internal buffer
        static const size_t m_bsize_b = (m_bsize*char_width)+1; //!< size for internal byte buffer (only unicode mode)

        char     *m_bytes;         //!< byte buffer for unicode mode. This is 4*m_size+1 large.
        char     *m_bytes_lim;     //!< pointer behind last byte in m_bytes. Note that (*m_bytes_lim) should always contain a 0
        char	 *m_bytes_p;	   //!< pointer to next unextracted byte

        CHAR     *m_yybuffer;      //!< buffer for input
        CHAR     *m_yycursor;      //!< pointer to current input symbol in m_buffer
        CHAR     *m_yylimit;       //!< pointer behind last available input symbol in m_buffer
        CHAR     *m_yymarker;      //!< pointer into input for backtracking information
        CHAR     *m_yyctxmarker;   //!< pointer into input for trailing context backtracking
        bool      m_eof;           //!< reached end of current input

        CHAR     *m_token;         //!< pointer to beginning of current token
        char     *m_token_b;       //!< pointer to beginning of current token in low-level byte buffer

        int       m_lineno;        //!< current line number
        int       m_colno;         //!< current column number


        size_t m_iMultyByteIgnore;

};

    

template<>
inline MyRE2CLexer<char>::MyRE2CLexer(std::istream* in, std::ostream* out)
{
    m_yybuffer    = new char[m_bsize];
    m_bytes       = NULL;
    m_bytes_lim   = NULL;
    m_bytes_p	  = NULL;

    m_yytext_null_terminated = true;

    switch_streams(in ? in : &std::cin, out ? out : &std::cout);
}

template<>
inline MyRE2CLexer<uint32_t>::MyRE2CLexer(std::istream* in, std::ostream* out)
{
    m_yybuffer       = new uint32_t[m_bsize];
    m_bytes          = new char[m_bsize_b];
    m_bytes_lim      = m_bytes;
    m_bytes_p        = m_bytes;

    m_yytext_null_terminated = true;

    switch_streams(in ? in : &std::cin, out ? out : &std::cout);
}

template<class CHAR>
inline MyRE2CLexer<CHAR>::~MyRE2CLexer()
{
    if (m_yybuffer)
        delete[] m_yybuffer;
    if (m_bytes)
        delete[] m_bytes;
}

template<class CHAR>
inline void MyRE2CLexer<CHAR>::switch_streams(std::istream* new_in, std::ostream* new_out) 
{ 
    if (new_in)
        m_input = new_in; 

    if (new_out)
        m_output = new_out;

    m_bytes_lim   = m_bytes;
    m_bytes_p     = m_bytes;

    m_yycursor    = m_yybuffer;
    m_yylimit     = m_yybuffer;
    m_yymarker    = m_yybuffer;
    m_yyctxmarker = m_yybuffer;
    m_eof         = false;

    m_token       = m_yybuffer;
    m_token_b     = m_bytes;

    m_lineno      = 1;
    m_colno       = 1;
}


template<class CHAR>
inline const string& MyRE2CLexer<CHAR>::YYText()
{ 
    //return  m_token;
    //m_result.assign(m_token , m_yycursor - m_token);
    //m_yytext_null_terminated ? m_result.c_str() :
    //if (m_yytext_null_terminated)
    //{
      return m_result.assign(m_token , m_yycursor - m_token);
    //}
    //else
    //{
    //  return m_token;
    //}
} 

template<>
inline const char* MyRE2CLexer<char>::YYText_bytes() const
{
    return m_token;
}

template<>
inline const char* MyRE2CLexer<uint32_t>::YYText_bytes() const
{
    return m_token_b;
}

template<class CHAR>
inline int MyRE2CLexer<CHAR>::YYLeng() const
{ 
    return m_yycursor - m_token;
}

template<class CHAR>
inline int MyRE2CLexer<CHAR>::YYMBLeng() const
{ 
    return m_yycursor - m_token - m_iMultyByteIgnore;
}

template<>
inline int MyRE2CLexer<char>::YYLeng_bytes() const
{
    return m_yycursor - m_token;
}

template<>
inline int MyRE2CLexer<uint32_t>::YYLeng_bytes() const
{
    char* m_cursor_b = (char*)utf8_skip_n((unsigned char*)m_token_b, YYLeng());
    return m_cursor_b - m_token_b;
}

template<class CHAR>
inline int MyRE2CLexer<CHAR>::lineno() const 
{ 
    return m_lineno;
}

template<class CHAR>
inline int MyRE2CLexer<CHAR>::colno() const 
{ 
    return m_colno;
}

template<class CHAR>
inline int MyRE2CLexer<CHAR>::LexerInput(char* buf, int size)
{
    if (m_input->eof() || m_input->fail())
        return 0;

    m_input->read(buf, size); 

    return m_input->bad() ? -1 : m_input->gcount();
}

template<class CHAR>
inline void MyRE2CLexer<CHAR>::LexerOutput(const char* buf, int size)
{
    m_output->write(buf, size);
}

template<class CHAR>
inline void MyRE2CLexer<CHAR>::LexerError(const char* msg, bool fatal)
{
    std::cerr << msg;
    if (fatal)
        exit(1);
}

template<>
inline void MyRE2CLexer<char>::set_token(char* token)
{
    m_token = token;
}

template<>
inline void MyRE2CLexer<char>::init_multi_byte_counter()
{
    m_iMultyByteIgnore=0;    
}

template<>
inline void MyRE2CLexer<uint32_t>::set_token(uint32_t* token)
{
    m_token_b = (char*) utf8_skip_n((unsigned char*)m_token_b, token - m_token);
    m_token = token;
}

template<>
inline void MyRE2CLexer<char>::m_yyfill_internal(size_t wanted)
{
    size_t read = LexerInput(m_yylimit, wanted); 
    if (read > 0)
        m_yylimit += read;
}

template<>
inline void MyRE2CLexer<uint32_t>::m_yyfill_internal(size_t wanted)
{
    if (m_eof)
        return;

    // buffers are left-aligned

    // fill byte buffer
    size_t bytes_avail = m_bytes_lim - m_bytes;
    size_t bytes_free  = m_bsize_b - bytes_avail;
    
    int x = LexerInput(m_bytes_lim, bytes_free - 1);
    if (x > 0)
        m_bytes_lim += x;
    *m_bytes_lim = 0;

    uint32_t c;

    // read characters
    while (wanted > 0) {
        x = utf8_read((unsigned char*)m_bytes_p, &c);
        if (x == 0) {
            // end of input
            return;
        }
        else if (x > 4) {
        	std::cerr << "Error: Invalid UTF-Character in line " << m_lineno 
        		      << " col " << m_colno << ". Replaced by U+FFFD." << std::endl;
            c = 0xFFFD; // UTF8 3 bytes: 0xEF 0xBF 0xBD
            utf8_write((unsigned char*)m_bytes_p, c);
            memmove(m_bytes_p+3, m_bytes_p+x, m_bytes_lim - m_bytes_p + x);
            m_bytes_lim -= (x-3);
            x = LexerInput(m_bytes_lim, m_bsize - (m_bytes_lim - m_bytes) -1);
            if (x > 0)
                m_bytes_lim += x;
            *m_bytes_lim = 0;
            m_bytes_p += 3;
        }
        else {
            *m_yylimit++ = c;
            wanted--;
            m_bytes_p += x;
        }
    }
}

template<class CHAR>
inline size_t MyRE2CLexer<CHAR>::m_yyfill(size_t count)
{
    // TODO: Check that m_marker and m_ctx marker are not always >= m_cursor and <= m_limit
    size_t avail  = m_yylimit - m_yycursor; // available (until now unprovided) elements
    size_t len    = m_yylimit - m_token;  // number of used bytes. (no old bytes at beginning of buffer)
    size_t offset = m_token   - m_yybuffer; // number of unused bytes at beginning of buffer

    if (avail >= count)
        return avail;

    // move remaining buffer content to beginning
    if (offset > 0) {
        if (m_bytes) {
            // first copy remaining byte buffer
            size_t len_b    = m_bytes_lim - m_token_b;
            size_t offset_b = m_token_b   - m_bytes;

            memmove(m_bytes, m_token_b, len_b);

            m_bytes_lim -= offset_b;
            m_bytes_p   -= offset_b;
            m_token_b   -= offset_b;
        }
        //  x x x x x x x x x x x x x x x x
        // |           |       |         |
        // m_buffer    m_token m_cursor  m_limit
        //                     |- avail -|
        //             |- len -----------|
        // |- offset --|         
        if (len > 0)
            memmove(m_yybuffer, m_token, len*char_width);
        m_yycursor     = m_yybuffer;
        m_yylimit     -= offset;
        m_yymarker    -= offset;
        m_yyctxmarker -= offset;
        m_token       -= offset;
    }

    // get data
    //  0 1 2 3 4 5 6 7 8 9 0
    // |       |       | 
    // m_tok   m_cur   m_lim
    size_t needed = m_bsize - len;
    m_yyfill_internal(needed);

    // 0 1 2 3 4 5 6 7 8 9 0
    // |             | 
    // m_cur      m_lim
    avail = m_yylimit - m_yycursor;

    if (avail < count) {
        m_eof = true;
        *m_yylimit = 0;
        return avail+1;
    }
    return avail;
}


template<class CHAR>
inline void MyRE2CLexer<CHAR>::process_token()
{ 
    if (m_yytext_null_terminated) 
        m_result.assign(m_token , m_yycursor - m_token); 
}

}
