%{
// (C) 2009 Mark Frohnmayer.  The use of this code is governed by its license.  See /license/info.txt in the source distribution for the full license agreement.

%}

%option c++
%option prefix="kt_"
%option outfile="lexical_analyzer.cpp"
%option 8bit
%option batch
%option yyclass="kt_lexer"
%option noyywrap
%pointer

%{
// %option debug

#define YSSTYPE parse_node_ptr
#define yywrap kt_wrap
#include "kt.h"
#include "parser.hpp"

int kt_wrap();

// #define FLEX_DEBUG 1

extern int kt_debug;

static int get_hex_digit(char c)
{
	if(c >= '0' && c <= '9')
		return c - '0';
	if(c >= 'A' && c <= 'F')
		return c - 'A' + 10;
	if(c >= 'a' && c <= 'f')
		return c - 'a' + 10;
	return -1;
}

static char * collapse_escape(char *start, char *end)
{
	char *read_ptr = start;
	char *write_ptr = start;
	
	while(read_ptr < end)
	{
		char c = *read_ptr++;
		if(c == '\\')
		{
			if(read_ptr + 1 > end)
				break;
			char token = *read_ptr++;
			if(token == 'n')
			{
				*write_ptr++ = '\n';
				continue;
			}
			else if(token == 'r')
			{
				*write_ptr++ = '\r';
				continue;
			}
			else if(token == 't')
			{
				*write_ptr++ = '\t';
				continue;
			}
			else if(token == 'x')
			{
				if(read_ptr + 2 > end)
					break;
				int dig1 = get_hex_digit(*read_ptr++);
				int dig2 = get_hex_digit(*read_ptr++);
				*write_ptr++ = dig1 * 16 + dig2;
			}
			else
				*write_ptr++ = c;
		}
		else
			*write_ptr++ = c;
	}
	return write_ptr;
}

class kt_lexer : public yyFlexLexer
{
public:
	kt_lexer(const char *parse_string, uint parse_string_len, parse_result *result)
	{
		_result = result;
		_pending_indent = 0;
		_depth_stack_size = 1;
		_depth_stack[0] = 0;
		_indent_error = false;
		_line_index = 1;
		_trailing_return_emitted = 0;

		_parse_string = parse_string;
		_parse_string_len = parse_string_len;
		_parse_string_index = 0;

		// lexer debug flag
		//set_debug(1);
		// parser debug flag
		//kt_debug = 1;
	}
	int yylex();
	
	int do_lex(parse_node_ptr *lvalp, YYLTYPE *llocp)
	{
		if( _pending_indent != 0 || _indent_error)
		{
			return emit_indentation();
		}

		_lvalue = lvalp;
		_l_loc = llocp;
		llocp->first_line = _line_index;
		return yylex();
	}
protected:
	int LexerInput( char* buf, int max_size )
	{
		uint max_bytes = _parse_string_len - _parse_string_index;
		if(max_bytes > max_size)
			max_bytes = max_size;
		memcpy(buf, _parse_string + _parse_string_index, max_bytes);
		_parse_string_index += max_bytes;
		if(max_bytes == 0 && !_trailing_return_emitted)
		{
			buf[0] = '\n';
			_trailing_return_emitted = 1;
			return 1;
		}
		return max_bytes;
	}

private:
	int _trailing_return_emitted;
	uint _line_index;
	parse_node_ptr *_lvalue;
	YYLTYPE *_l_loc;
	int _pending_indent;
	const char *_parse_string;
	uint _parse_string_len;
	uint _parse_string_index;
	parse_result *_result;
	
	enum
	{
		_max_depth_stack_size = 128,
	};
	
	int _depth_stack[_max_depth_stack_size+1];
	int _depth_stack_size;
	
	bool _indent_error;
	
	void scan_string(int start, int end, bool collapse)
	{
		char *start_str = yytext + start;
		char *end_str = yytext + end;
		if(collapse)
			end_str = collapse_escape(start_str, end_str);

		*_lvalue = _result->add_string(start_str, end_str - start_str);
	}
   
	void scan_float()
	{
		yytext[yyleng] = 0;
		*_lvalue = _result->add_float(atof(yytext));
	}

	void scan_hex()
	{
		int val = 0;
		sscanf(yytext, "%x", &val);
		set_int(val);
	}
	
	void scan_int()
	{
		set_int(atoi(yytext));
	}
	
	void set_int(int value)
	{
		*_lvalue = _result->add_int(value);
	}
	
	int _INDENT()
	{
		if(debug())
		{
			printf("INDENT, new stack top: %i\n", _depth_stack[_depth_stack_size-1]);
			fflush(stdout);
		}
		return INDENT;
	}

	int _DEDENT()
	{
		if(debug())
		{
			printf("DEDENT, new stack top: %i\n", _depth_stack[_depth_stack_size - 1]);
			fflush(stdout);
		}
		return DEDENT;
	}

	int _ILLEGAL_TOKEN()
	{
		if(debug())
		{
			printf("Parse error, illegal token.\n");
			fflush(stdout);
		}
		return ILLEGAL_TOKEN;
	}

	int _END_TOK()
	{
		if(debug())
		{
			printf("emitting end tok\n");
			fflush(stdout);
		}
		return END_TOK;
	}
   
	int emit_indentation()
	{
		if(debug())
		{
			printf("doing indentation... "); 
			fflush(stdout);
		}

		if(_indent_error)
		{
			_indent_error = false;
			return ILLEGAL_TOKEN;
		}

		if(_pending_indent > 0)
		{
			_pending_indent--;
			return _INDENT();
		}
		else if(_pending_indent < 0)
		{
			_pending_indent++;
			return _DEDENT();
		}
		return ILLEGAL_TOKEN;
	}

	void increment_line_count()
	{
		_line_index++;
		if(debug())
		{
			printf("line count: %i\n",_line_index);
			fflush(stdout);
		}
	}
};

int kt_lex(parse_node_ptr *lvalp, YYLTYPE *llocp, kt_lexer *lexer)
{
   return lexer->do_lex(lvalp, llocp);
}

%}

DIGIT		[0-9]
INTEGER		{DIGIT}+
FLOAT		({INTEGER}\.{INTEGER})|({INTEGER}(\.{INTEGER})?[eE][+-]?{INTEGER})
LETTER		[A-Za-z_]
FILECHAR	[A-Za-z_\.]
IDTAIL		[A-Za-z0-9_]
ID			{LETTER}{IDTAIL}*
PATHSEG		[A-Za-z_0-9 ]+
PATHSEC		(\.?{PATHSEG})+
PATHSTART	("../"*)|("/")|("./")|""
PATHSECTION	"/"{PATHSEC}
PATH_IDENT	{PATHSTART}{PATHSEC}{PATHSECTION}*
FILENAME	{FILECHAR}+
WHITESPACE	[ \t\v\f]
SPACE		[ ]
HEXDIGIT	[a-fA-F0-9]

COMMENT		"//"[^\n\r]*

%x str

%%

{COMMENT} /* ignore comments for now. */ ;

 /* convert mac & win newlines to unix newlines */
"\r"	{ unput('\n'); }
"\r\n"	{ unput('\n'); } 

 /* indentation handling : */
 /* ------------------------------------------------------------------------- */

 /* find the next line with indentation */
((([ \t]*)|([ \t]*"//"[^\n]*))"\n")+[ \t\n]* {
	// scan back from end to find last newline to find space count (spc = 1, tab = 4 )
	int depth = 0;
	int i;

	for(i = yyleng; i >= 0; i--)
	{
		if( yytext[i] == '\n' )
			break;

		switch( yytext[i] )
		{
			case ' ':
				depth++;
				break;
			case '\t':
				depth += 4;
				break;
		}
	}

	for( ; i >= 0; i--)
	{
		if(yytext[i] == '\n')
			increment_line_count();
	}

	// we don't need to do indentation if we == the stack top
	if( depth != _depth_stack[_depth_stack_size - 1] )
	{
		// we need to indent
		if( depth > _depth_stack[_depth_stack_size - 1] )
		{
			if(_depth_stack_size >= _max_depth_stack_size)
				_indent_error = true;
			else
			{
				_depth_stack[_depth_stack_size++] = depth;
				_pending_indent = 1;
			}
		}
		// we need to dedent, maybe multitple times.
		else 
		{
			_pending_indent = 0;
			while( depth < _depth_stack[_depth_stack_size - 1] )
			{
				_depth_stack_size--;
				_pending_indent--;
			}
		}

		if(depth != _depth_stack[_depth_stack_size - 1])
		{
			// if depth & the stack do not agree, we have an error.
			// we can recover from this error, but the script is probably bad anyway.
			//BEGIN(illegal);
			_indent_error = true;
		}
	}

	return _END_TOK();
}
 
 /* ignore all other whitespace */
{WHITESPACE}+	{ } 

 /* ------------------------------------------------------------------------- */

 

\"		BEGIN(str);

\'(\\.|[^/\\'\n\r])*\'	{ scan_string(1, yyleng - 1, true); return IDENTIFIER; } 
\'{PATH_IDENT}\'		{ scan_string(1, yyleng - 1, false); return PATH; };

"=="	return opEQ;
"$="	return opEQ;
"!="	return opNE;
"!$="	return opNE;
">="	return opGE;
"<="	return opLE;
"&&"	return opAND;
"||"	return opOR;
"::"	return opCOLONCOLON;
"--"	return opMINUSMINUS;
"++"	return opPLUSPLUS;
"<<"	return opSHL;
">>"	return opSHR;
"+="	return opPLASN;
"-="	return opMIASN;
"*="	return opMLASN;
"/="	return opDVASN;
"%="	return opMODASN;
"&="	return opANDASN;
"^="	return opXORASN;
"|="	return opORASN;
"<<="	return opSLASN;
">>="	return opSRASN;
"NL"	return opCATNEWLINE;
"TAB"	return opCATTAB;
"SPC"	return opCATSPACE;
"@" |
"?" |
"[" |
"]" |
"(" |
")" |
"+" |
"-" |
"*" |
"/" |
"<" |
">" |
"|" |
"." |
"!" |
":" |
";" |
"{" |
"}" |
"," |
"&" |
"%" |
"^" |
"~" |
"="		return yytext[0];

"class"			return rwCLASS;
"object"		return rwOBJECT;
"connection"	return rwCONNECTION;
"directory"		return rwDIRECTORY;
"between"		return rwBETWEEN;
"alias"			return rwALIAS;
"image"			return rwIMAGE;
"in"			return rwIN;
"from"			return rwFROM;
"to"			return rwTO;
"via"			return rwVIA;
"try"			return rwTRY;
"catch"			return rwCATCH;
"finally"		return rwFINALLY;
"when"			return rwWHEN;
"state"			return rwSTATE;
"function"		return rwFUNCTION;
"return"		return rwRETURN;
"while"			return rwWHILE;
"for"			return rwFOR;
"break"			return rwBREAK;
"continue"		return rwCONTINUE;
"if"			return rwIF;
"else"			return rwELSE;
"switch"		return rwSWITCH;
"case"			return rwCASE;
"default"		return rwDEFAULT;
"new"			return rwNEW;
"var"			return rwVAR;
"file"			return rwFILE;

"true"				{ set_int(1); return INT_CONSTANT; }
"false"				{ set_int(0); return INT_CONSTANT; }
{ID}				{ scan_string(0, yyleng, false); return(IDENTIFIER); }
0[xX]{HEXDIGIT}+	{ scan_hex(); return INT_CONSTANT; }
{INTEGER}			{ scan_int(); return INT_CONSTANT; }
{FLOAT}				{ scan_float(); return FLOAT_CONSTANT; }
.					{ return(_ILLEGAL_TOKEN()); }


<str>(\\.|[^\\"\n\r$])*	{ scan_string(0, yyleng, true); return STRING_FRAGMENT; }
<str>[$]{ID}			{ scan_string(1, yyleng, false); return(IDENTIFIER); }
<str>[$]+				{ scan_string(0, yyleng, true); return STRING_FRAGMENT; }
<str>\"					{ BEGIN(INITIAL); return(STRING_END); }

%%

int kt_wrap()
{
	return 1;
}

extern int kt_parse(kt_lexer *lexer, parse_result *result);

void kt_parse(const char *parse_string, uint parse_string_len, parse_result &result)
{
	kt_lexer lexer(parse_string, parse_string_len, &result);
	kt_parse(&lexer, &result);
}

