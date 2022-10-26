%name-prefix="kt_"
%output="parser.cpp"
%defines
%pure-parser
%locations
%parse-param {kt_lexer *lexer}
%lex-param {kt_lexer *lexer}
%parse-param {parse_result *result}
%verbose
%debug

%{

// The kt programming language.  Parser grammar © 2012 Mark Frohnmayer.  The use of this code is governed by its license.  See /license/info.txt in the source distribution for the full license agreement.

#include "kt.h"

#define YYSTYPE parse_node_ptr
#define KT
class kt_lexer;
void kt_error (struct YYLTYPE *loc, kt_lexer *lexer, parse_result *result, const char *format, ...);
#ifndef YYDEBUG
#define YYDEBUG 1
#endif

#define YYSSIZE 350

#define nil 0
#undef YY_ARGS
#define YY_ARGS(x)	x
%}

%token START_TOK_SCRIPT
%token START_TOK_GDECL

/* Reserved Word Definitions */

%token rwSTATE "state"
%token rwBETWEEN "between"
%token rwOBJECT "object"
%token rwCLASS "class"
%token rwRECORD "record"
%token rwDIRECTORY "directory"
%token rwCONNECTION "connection"
%token rwALIAS "alias"
%token rwFACET "facet"
%token rwIN "in"
%token rwFROM "from"
%token rwTO "to"
%token rwVIA "via"
%token rwTRY "try"
%token rwCATCH "catch"
%token rwFINALLY "finally"
%token rwWHEN "when"
%token rwFUNCTION "function"
%token rwMETHOD "method"
%token rwRETURN "return"
%token rwWHILE "while"
%token rwFOR "for"
%token rwBREAK "break"
%token rwCONTINUE "continue"
%token rwIF "if"
%token rwELSE "else"
%token rwSWITCH "switch"
%token rwCASE "case"
%token rwDEFAULT "default"
%token rwVAR "var"
%token rwINTEGER "integer"
%token rwFLOAT "float"
%token rwBOOL "boolean"
%token rwSTRING "string"
%token rwSHARED "shared"
%token rwPUBLIC "public"
%token rwFILE "file"

%token ILLEGAL_TOKEN

/* Constants and Identifier Definitions */

%token INT_CONSTANT
%token IDENTIFIER
%token STRING_CONSTANT
%token FLOAT_CONSTANT
%token PATH

%token STRING_FRAGMENT
%token STRING_END

%token INDENT
%token DEDENT

/* Operator Definitions */

%token '+' '-' '*' '/' '<' '>' '=' '.' '|' '&' '%'
%token '(' ')' ',' ':' ';' '{' '}' '^' '~' '!' '@'
%token opARROW "->"
%token opMINUSMINUS "--"
%token opPLUSPLUS "++"
%token opSHL "<<"
%token opSHR ">>"
%token opPLASN "+="
%token opMIASN "-="
%token opMLASN "*="
%token opDVASN "/="
%token opMODASN "%="
%token opANDASN "&="
%token opXORASN "^="
%token opORASN "|="
%token opSLASN "<<="
%token opSRASN ">>="
%token opEQ "=="
%token opNE "!="
%token opGE ">="
%token opLE "<="
%token opAND "&&"
%token opOR "||"
%token opCOLONCOLON "::"
%token opCATNEWLINE "NL"
%token opCATSPACE "SPC"
%token opCATTAB "TAB"

%token END_TOK

%{
extern int kt_lex (YYSTYPE *lvalp, YYLTYPE *llocp, kt_lexer *lexer);
#define node(name) result->add_node(#name)
#define field(obj, fieldName, value) obj->set_property(result, #fieldName, value)
#define integer(num) result->add_int(num)
#define boolean(num) result->add_int(num)
#define string(str) result->add_string(str, strlen(str))
#define list(firstElem) result->add_list(firstElem)
#define empty_list() result->add_list(0)
#define append(list, elem) list->append(elem)
#define root(rootNode) result->root = rootNode
#define integer_value(node) node->int_data
%}

%%

/*-----------------------------------------------------------------------------------------*/  
start: declaration_list
		{ root($$); }
	;


declaration_list
	: declaration
		{ $$ = list($1); }
	| declaration_list declaration
		{ $$ = $1; append($1, $2); }
	;

declaration
	: compound_declaration
	| state_declaration
	| facet_declaration
	| type_declaration
	| slot_declaration
	| slot_assignment_declaration
	| function_declaration
	| method_declaration
	;

compound_declaration
	: class_declaration
	| object_declaration
	| record_declaration
	| connection_declaration
	;
   
/*-----------------------------------------------------------------------------------------*/  
class_declaration
	: is_public "class" IDENTIFIER declaration_parameters parent_specifier facet_list_specifier transmission_list_specifier end_token compound_body optional_end_token
		{
			$$ = node(class);
			field($$, name, $3);
			field($$, decl_flags, $1);
			field($$, parameter_list, $4);
			field($$, parent_decl, $5);
			field($$, facet_list, $6);
			field($$, transmission_list, $7);
			field($$, body, $9);
		}
	;
	
is_public
   :
      { $$ = boolean(false); }
   | "public"
      { $$ = boolean(true); }
   ;

declaration_parameters
	:
		{ $$ = empty_list(); }
	| '(' optional_parameter_list ')'
		{ $$ = $2; }
	;

optional_parameter_list
	:
		{ $$ = empty_list(); }
	| parameter_list
	;

parameter_list
	: IDENTIFIER optional_type_specifier
	{
		YYSTYPE var;
		var = node(parameter);
		field(var, name, $1);
		field(var, type_spec, $2);
		$$ = list(var);
	}
	| parameter_list ',' IDENTIFIER optional_type_specifier
	{
		YYSTYPE var;
		var = node(parameter);
		field(var, name, $3);
		field(var, type_spec, $4);
		$$ = $1;
		append($1, var);
	}
	;


parent_specifier
	:
	{
		$$ = node(parent_specifier);
		field($$, name, nil);
		field($$, args, nil);
	}
	| ':' locator
	{
		$$ = node(parent_specifier);
		field($$, name, $2);
		field($$, args, list(nil));
	}
	| ':' locator '(' expression_list ')'
	{
		$$ = node(parent_specifier);
		field($$, name, $2);
		field($$, args, $4);
	}
	;
	
locator
	: IDENTIFIER
		{ $$ = $1; }
	| PATH
		{ $$ = $1; }
	;

facet_list_specifier
	:
		{ $$ = nil; }
	| "in" facet_name_list
		{ $$ = $2; }
	;

facet_name_list
	: IDENTIFIER
	   { $$ = list($1); }
	| facet_name_list ',' IDENTIFIER
		{ $$ = $1; append($1, $3); }
	;

transmission_list_specifier
	:
		{ $$ = nil; }
	| transmission_list
	;

transmission_list
	: transmission_specifier
	   { $$ = list($1); }
	| transmission_list ',' transmission_specifier
		{ $$ = $1; append($1, $3); }
	;

transmission_specifier
	: "from" IDENTIFIER "to" IDENTIFIER "via" locator
		{
         $$ = node(transmission_specifier);
         field($$, from_facet, $2);
         field($$, to_facet, $4);
         field($$, via, $6);
      }
	;

compound_body
	: 
		{ $$ = empty_list(); }
	| INDENT DEDENT
		{ $$ = empty_list(); }
	| INDENT declaration_list DEDENT 
		{ $$ = $2; }
	;

/*-----------------------------------------------------------------------------------------*/  
object_declaration
	: is_public "object" IDENTIFIER parent_specifier facet_list_specifier end_token compound_body optional_end_token
		{ 
			$$ = node(object);
			field($$, is_public, $1);
			field($$, name, $3);
			field($$, parent_decl, $4);
			field($$, facet_list, $5);
			field($$, body, $7);
		}
	| IDENTIFIER parent_specifier facet_list_specifier end_token compound_body optional_end_token
		{ 
			$$ = node(object);
			field($$, is_public, boolean(false));
			field($$, name, $1);
			field($$, parent_decl, $2);
			field($$, facet_list, $3);
			field($$, body, $5);
		}
	;

/*-----------------------------------------------------------------------------------------*/  
record_declaration
   : is_public "record" IDENTIFIER declaration_parameters parent_specifier facet_list_specifier end_token
     compound_body optional_end_token
      {
         $$ = node(record);
         field($$, is_public, $1);
         field($$, name, $3);
         field($$, parameter_list, $4);
         field($$, parent_decl, $5);
         field($$, facet_list, $6);
         field($$, body, $8);
      }
   ;
   
/*-----------------------------------------------------------------------------------------*/  
connection_declaration
   : is_public "connection" IDENTIFIER parent_specifier between_specifier end_token compound_body optional_end_token
      {
         $$ = node(connection);
         field($$, is_public, $1);
         field($$, name, $3);
         field($$, parent_decl, $4);
         field($$, transmission_list, $5);
         field($$, body, $7);
      }
   ;

/*-----------------------------------------------------------------------------------------*/  
between_specifier
	: "between" IDENTIFIER ',' IDENTIFIER
      {
         $$ = node(transmission_specifier);
         field($$, from_facet, $2);
         field($$, to_facet, $4);
         $$ = list($$);
      }
   ;

/*-----------------------------------------------------------------------------------------*/  
state_declaration
	: is_public "state" IDENTIFIER transmission_list_specifier end_token compound_body optional_end_token
		{
			$$ = node(state);
			field($$, is_public, $1);
			field($$, name, $3);
			field($$, transmission_list, $4);
			field($$, body, $6);
		}
	;
   
/*-----------------------------------------------------------------------------------------*/  
facet_declaration
	: "facet" IDENTIFIER end_token compound_body optional_end_token
		{
			$$ = node(facet);
			field($$, name, $2);
			field($$, body, $4);
		}
   ;
 
/*-----------------------------------------------------------------------------------------*/  
type_declaration
   : is_public "type" IDENTIFIER type_specifier end_token optional_end_token
      {
         $$ = node(type);
         field($$, is_public, $1);
         field($$, name, $3);
         field($$, type_spec, $4);
      }
   ;

type_specifier
   : locator
      {
         $$ = node(locator_type_specifier);
         field($$, locator, $1);
      }
   | type_specifier "&"
      {
         $$ = node(reference_type_specifier);
         field($$, base_type, $1);
      }
   | type_specifier array_specifier
      {
         $$ = node(array_type_specifier);
         field($$, base_type, $1);
         field($$, size_expr, $2);
      }
   | map_specifier
   ;

array_specifier
   : '[' ']'
      { $$ = nil; }
   | '[' expression ']'
      { $$ = $2; }
   ;
   
map_specifier
   : '{' '}'
   | '{' type_specifier ',' type_specifier '}'
   ;

optional_type_specifier
   :
     { $$ = nil; }
   | ':' type_specifier
     { $$ = $2; }
   ;
   
/*-----------------------------------------------------------------------------------------*/  
slot_declaration
   : is_public is_shared "var" IDENTIFIER optional_assignment_expression end_token
      {
         $$ = node(slot_declaration);
         field($$, is_public, $1);
         field($$, is_shared, $2);
         field($$, name, $4);
         field($$, assign_expr, $5);
         field($$, type_spec, nil);
      }
   | is_public is_shared "var" IDENTIFIER ':' type_specifier optional_assignment_expression end_token
      {
         $$ = node(slot_declaration);
         field($$, is_public, $1);
         field($$, is_shared, $2);
         field($$, name, $4);
         field($$, type_spec, $6);
         field($$, assign_expr, $7);
      }
   ;
   
variable_declaration_statement
   : is_shared "var" IDENTIFIER optional_assignment_expression end_token
		{
			$$ = node(variable_declaration_stmt);
			field($$, is_shared, $1);
			field($$, name, $3);
			field($$, assign_expr, $4);
			field($$, type_spec, nil);
		}
   | is_shared "var" IDENTIFIER ':' type_specifier optional_assignment_expression end_token
		{
			$$ = node(variable_declaration_stmt);
			field($$, is_shared, $1);
			field($$, name, $3);
			field($$, type_spec, $5);
			field($$, assign_expr, $6);
		}
   ;
   
is_shared
   :
      { $$ = boolean(false); }
   | "shared"
      { $$ = boolean(true); }
   ;

optional_assignment_expression
   :
      { $$ = nil; }
   | '=' expression
      { $$ = $2; }
   ;

/*-----------------------------------------------------------------------------------------*/  
slot_assignment_declaration
   : IDENTIFIER '=' expression end_token
      {
	     $$ = node(slot_assignment);
		 field($$, name, $1);
		 field($$, assign_expr, $3);
      }
   ;
   
/*-----------------------------------------------------------------------------------------*/  
function_declaration
	: is_public is_shared "function" IDENTIFIER '(' optional_parameter_list ')' optional_return_type facet_list_specifier end_token function_body optional_end_token
		{
			$$ = node(function);
			field($$, name, $4);
			field($$, is_public, $1);
			field($$, is_shared, $2);
			field($$, parameter_list, $6);
			field($$, return_type, $8);
			field($$, facet_list, $9);
			field($$, statements, $11);
		}
	;

method_declaration
	: is_public is_shared "method" IDENTIFIER selector_decl_args optional_return_type facet_list_specifier end_token function_body optional_end_token
		{
			$$ = node(function);
			field($$, primary_name, $4);
			field($$, selector_decl_list, $5);
			field($$, is_public, $1);
			field($$, is_shared, $2);
			field($$, return_type, $6);
			field($$, facet_list, $7);
			field($$, statements, $9);
		}
	| is_public is_shared "method" IDENTIFIER optional_return_type facet_list_specifier end_token function_body optional_end_token
		{
			$$ = node(function);
			field($$, primary_name, $4);
			field($$, selector_decl_list, empty_list());
			field($$, is_public, $1);
			field($$, is_shared, $2);
			field($$, return_type, $5);
			field($$, facet_list, $6);
			field($$, statements, $8);
		}
	;

selector_decl_args
	: ':' optional_selector_type_spec IDENTIFIER
		{
			YYSTYPE pair;
			pair = node(selector_pair);
			field(pair, string, nil);
			field(pair, type_spec, $2);
			field(pair, name, $3);
			$$ = list(pair);
		}	
	| selector_decl_args ':' optional_selector_type_spec IDENTIFIER
		{
			YYSTYPE pair;
			pair = node(selector_pair);
			field(pair, string, nil);
			field(pair, type_spec, $3);
			field(pair, name, $4);
			append($1, pair);
			$$ = $1;
		}
	| selector_decl_args IDENTIFIER ':' optional_selector_type_spec IDENTIFIER
		{
			YYSTYPE pair;
			pair = node(selector_pair);
			field(pair, string, $2);
			field(pair, type_spec, $4);
			field(pair, name, $5);
			append($1, pair);
			$$ = $1;
		}
	;

optional_selector_type_spec
	:
		{ $$ = nil; }
	| '(' type_specifier ')'
		{ $$ = $1; }
	;

optional_end_token
   :
   | END_TOK
   ;
   
end_token 
   :  END_TOK
   ;

function_declaration_statement
   : "function" IDENTIFIER '(' optional_parameter_list ')' optional_return_type end_token function_body
      {
         $$ = node(function_declaration_stmt);
         field($$, name, $2);
         field($$, parameter_list, $4);
         field($$, return_type, $6);
         field($$, statements, $8);
      }

optional_return_type
   :
      { $$ = nil; }
   | "->" type_specifier
      { $$ = $2; }
   ;
	
/*---------------------------------------------------------------------
/* Declaration body descriptions
 *--------------------------------------------------------------------*/

function_body
   :
      { $$ = nil; }
   | INDENT statement_list DEDENT
      { $$ = $2; }
   ;
   
/*---------------------------------------------------------------------
/* Function Body Nodes
 *--------------------------------------------------------------------*/

statement_list
	:
		{ $$ = nil; }
	| non_empty_statement_list
	;

non_empty_statement_list
	: statement
	   { $$ = list($1); }
	| non_empty_statement_list statement
		{ $$ = $1; append($1, $2); }
	;

statement
   : if_statement
	| while_statement
	| do_while_statement
	| for_statement
	| switch_statement
	| function_declaration_statement
	| variable_declaration_statement
	| "break" end_token
		{ $$ = node(break_stmt); }
	| "continue" end_token
		{ $$ = node(continue_stmt); }
	| "return" end_token
		{ 
			$$ = node(return_stmt);
			field($$, return_expression_list, empty_list());
		}
	| "return" expression end_token
		{
			$$ = node(return_stmt);
			field($$, return_expression, $2);
		}
	| expression_statement end_token
		{ $$ = $1; }
	;

statement_block
   : INDENT statement_list DEDENT
      { $$ = $2; }
   ;

switch_statement
   : "switch" expression end_token INDENT switch_list optional_default DEDENT
      {
         $$ = node(switch_stmt);
         field($$, test_expression, $2);
         field($$, element_list, $5);
		 field($$, default_block, $6);
      }
   ;

switch_list
	: switch_element
	   { $$ = list($1); }
	| switch_list switch_element
		{ $$ = $1; append($1, $2); }
	;
	
optional_default
	:
		{ $$ = nil; }
	| "default" end_token statement_block
		{ $$ = $3; }
	;

switch_element
	: switch_label_list statement_block
		{
         $$ = node(switch_element);
         field($$, label_list, $1);
         field($$, statement_list, $2); }
	;
	
switch_label_list
	: switch_label
	   { $$ = list($1); }
	| switch_label_list switch_label
		{ $$ = $1; append($1, $2); }
	;

constant_atom
	: INT_CONSTANT
		{
			$$ = node(int_constant_expr);
			field($$, value, $1);
		}
	| FLOAT_CONSTANT
		{
			$$ = node(float_constant_expr);
			field($$, value, $1);
		}
	| fragmented_string
		{
			$$ = $1;
		}
	;

switch_label
	: "case" constant_atom end_token
		{
			$$ = node(switch_label);
			field($$, test_constant, $2);
		}
	;

if_statement
	: "if" expression end_token statement_block
		{
			$$ = node(if_stmt);
			field($$, test_expression, $2);
			field($$, if_block, $4);
		}
	| "if" expression end_token statement_block "else" end_token statement_block
		{
			$$ = node(if_stmt);
			field($$, test_expression, $2);
			field($$, if_block, $4);
			field($$, else_block, $7);
		}
	;

while_statement
	: "while" expression end_token statement_block
		{
			$$ = node(while_stmt);
			field($$, test_expression, $2);
			field($$, statement_list, $4);
		}
	;
	
do_while_statement
	: "do" end_token statement_block "while" expression end_token
		{
			$$ = node(do_while_stmt);
			field($$, statement_list, $3);
			field($$, test_expression, $5);
		}

for_statement
	: "for" expression ';' expression ';' expression end_token statement_block
		{
			$$ = node(for_stmt);
			field($$, test_expression, $4);
			field($$, init_expression, $2);
			field($$, end_loop_expression, $6);
			field($$, statement_list, $8);
		}
	| "for" "var" IDENTIFIER optional_type_specifier '=' expression ';' expression ';' expression end_token statement_block
		{
			$$ = node(for_stmt);
			field($$, variable_initializer, $3);
			field($$, variable_type_spec, $4);
			parse_node_ptr var_node = node(locator_expr);
			field(var_node, string, $3);
			parse_node_ptr assignment_expr = node(assign_expr);
			field(assignment_expr, left, var_node);
			field(assignment_expr, right, $6);
			field($$, init_expression, assignment_expr);

			field($$, test_expression, $8);
			field($$, end_loop_expression, $10);
			field($$, statement_list, $12);
		}
	;

/*---------------------------------------------------------------------
/* expression Nodes
 *--------------------------------------------------------------------*/

primary_expression
	: IDENTIFIER
		{
         $$ = node(locator_expr);
         field($$, string, $1);
      }
	| PATH
		{
         $$ = node(locator_expr);
         field($$, string, $1);
      }
	| INT_CONSTANT
		{
         $$ = node(int_constant_expr);
         field($$, value, $1);
      }
	| method_call
	| FLOAT_CONSTANT
		{
         $$ = node(float_constant_expr);
         field($$, value, $1);
      }
	| fragmented_string
		{ $$ = $1; }
	| '(' expression ')'
		{ $$ = $2; }
	| array_expression
	| map_expression
	;

method_call
	: '[' expression IDENTIFIER selector_args ']'
		{
			$$ = node(method_call);
			field($$, object_expr, $2);
			field($$, primary_name, $3);
			field($$, selector_list, $4);
		}
	| '[' expression IDENTIFIER ']'
		{
			$$ = node(method_call);
			field($$, object_expr, $2);
			field($$, primary_name, $3);
			field($$, selector_list, empty_list());
		}
	;

selector_args
	: ':' expression
		{
			YYSTYPE pair;
			pair = node(selector_pair);
			field(pair, string, nil);
			field(pair, expr, $2);
			$$ = list(pair);
		}	
	| selector_args ':' expression
		{
			YYSTYPE pair;
			pair = node(selector_pair);
			field(pair, string, nil);
			field(pair, expr, $3);
			append($1, pair);
			$$ = $1;
		}
	| selector_args IDENTIFIER ':' expression
		{
			YYSTYPE pair;
			pair = node(selector_pair);
			field(pair, string, $2);
			field(pair, expr, $4);
			append($1, pair);
			$$ = $1;
		}
	;

fragmented_string
	: STRING_FRAGMENT fragment_or_ident_or_empty_list STRING_END
		{
		  if($2)
		  {
		     $$ = node(strcat_expr);
           YYSTYPE frag = node(string_constant);
           field(frag, value, $1);
           field($$, left, frag);
           field($$, right, $2);
		   field($$, op, string("cat_none"));
		  }
		  else
		  {
		     $$ = node(string_constant);
           field($$, value, $1);
		  }
	   }
	;

fragment_or_ident_or_empty_list
	:
		{ $$ = nil; }
	| fragment_or_ident_list
		{ $$ = $1; }
	;

fragment_or_ident_list
	: STRING_FRAGMENT
		{
         $$ = node(string_constant);
         field($$, value, $1); }
	| IDENTIFIER
		{
         $$ = node(locator_expr);
         field($$, string, $1);
      }
	| fragment_or_ident_list STRING_FRAGMENT
      {
         $$ = node(strcat_expr);
         YYSTYPE frag = node(string_constant);
         field(frag, value, $2);
         field($$, left, $1);
         field($$, right, frag);
		 field($$, op, string("cat_none"));
      }
	| fragment_or_ident_list IDENTIFIER
		{
         $$ = node(strcat_expr);
         field($$, left, $1);
         YYSTYPE ident = node(locator_expr);
         field(ident, string, $2);
         field($$, right, ident);
		 field($$, op, string("cat_none"));
      }
	;
	
postfix_expression
	: primary_expression
	| postfix_expression '[' expression ']'
		{
         $$ = node(array_index_expr);
         field($$, array_expr, $1);
         field($$, index_expr, $3);
      }
	| postfix_expression '(' ')'
		{
         $$ = node(func_call_expr);
         field($$, func_expr, $1);
         field($$, args, empty_list());
      }
	| postfix_expression '(' argument_expression_list ')'
		{
         $$ = node(func_call_expr);
         field($$, func_expr, $1);
         field($$, args, $3);
      }
	| postfix_expression '.' IDENTIFIER
		{
         $$ = node(slot_expr);
         field($$, object_expr, $1);
         field($$, slot_name, $3);
      }
	| postfix_expression "++"
		{
         $$ = node(unary_lvalue_op_expr);
         field($$, expression, $1);
         field($$, op, string("post_increment"));
      }
	| postfix_expression "--"
		{
         $$ = node(unary_lvalue_op_expr);
         field($$, expression, $1);
         field($$, op, string("post_decrement"));
      }
   ;
	
argument_expression_list
	: assignment_expression
	   { $$ = list($1); }
	| argument_expression_list ',' assignment_expression
		{ $$ = $1; append($1, $3); }
	;
	
unary_expression
	: postfix_expression
	| "++" unary_expression
		{
         $$ = node(unary_lvalue_op_expr);
         field($$, expression, $2);
         field($$, op, string("pre_increment"));
      }
	| "--" unary_expression
		{
         $$ = node(unary_lvalue_op_expr);
         field($$, expression, $2);
         field($$, op, string("pre_decrement"));
      }
	| '-' unary_expression
		{
         $$ = node(unary_minus_expr);
         field($$, expression, $2);
      }
	| '!' unary_expression
		{
         $$ = node(logical_not_expr);
         field($$, expression, $2);
      }
	| '~' unary_expression
		{
         $$ = node(bitwise_not_expr);
         field($$, expression, $2);
      }
	;

multiplicative_expression
	: unary_expression
	| multiplicative_expression '*' unary_expression
		{
         $$ = node(float_binary_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, string("multiply"));
      }
	| multiplicative_expression '/' unary_expression
		{
         $$ = node(float_binary_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, string("divide"));
      }
	| multiplicative_expression '%' unary_expression
		{
         $$ = node(int_binary_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, string("modulus"));
      }
	;

additive_expression
	: multiplicative_expression
	| additive_expression '+' multiplicative_expression
		{
         $$ = node(float_binary_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, string("add"));
      }
	| additive_expression '-' multiplicative_expression
		{
         $$ = node(float_binary_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, string("subtract")); }
	;

shift_expression
	: additive_expression
	| shift_expression "<<" additive_expression
		{
         $$ = node(int_binary_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, string("shift_left"));
      }
	| shift_expression ">>" additive_expression
		{
         $$ = node(int_binary_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, string("shift_right"));
      }
	;

relational_expression
	: shift_expression
	| relational_expression '<' shift_expression
		{
         $$ = node(bool_binary_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, string("compare_less"));
      }
	| relational_expression '>' shift_expression
		{
         $$ = node(bool_binary_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, string("compare_greater"));
      }
	| relational_expression "<=" shift_expression
		{
         $$ = node(bool_binary_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, string("compare_less_or_equal"));
      }
	| relational_expression ">=" shift_expression
		{
         $$ = node(bool_binary_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, string("compare_greater_or_equal"));
      }
	;
	
equality_expression
	: relational_expression
	| equality_expression "==" relational_expression
		{
         $$ = node(bool_binary_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, string("compare_equal"));
      }
	| equality_expression "!=" relational_expression
		{
         $$ = node(bool_binary_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, string("compare_not_equal"));
      }
	;

and_expression
	: equality_expression
	| and_expression '&' equality_expression
		{
         $$ = node(int_binary_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, string("bitwise_and"));
      }
	;
	
exclusive_or_expression
	: and_expression
	| exclusive_or_expression '^' and_expression
		{
         $$ = node(int_binary_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, string("bitwise_xor"));
      }
	;

inclusive_or_expression
	: exclusive_or_expression
	| inclusive_or_expression '|' exclusive_or_expression
		{
         $$ = node(int_binary_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, string("bitwise_or"));
      }
	;

logical_and_expression
	: inclusive_or_expression
	| logical_and_expression "&&" inclusive_or_expression
		{
         $$ = node(bool_binary_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, string("logical_and"));
      }
	;
	
logical_or_expression
	: logical_and_expression
	| logical_or_expression "||" logical_and_expression
		{
         $$ = node(bool_binary_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, string("logical_or"));
      }
	;

strcat_expression
	: logical_or_expression
	| strcat_expression '@' logical_or_expression
		{
         $$ = node(strcat_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, string("cat_none"));
      }
	| strcat_expression "NL" logical_or_expression
		{
         $$ = node(strcat_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, string("cat_newline"));
      }
	| strcat_expression "SPC" logical_or_expression	
		{
         $$ = node(strcat_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, string("cat_space"));
      }
	| strcat_expression "TAB" logical_or_expression
		{
         $$ = node(strcat_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, string("cat_tab"));
      }
	;
	
strcat_or_func_expression
	: strcat_expression
	| function_expression
	;

conditional_expression
	: strcat_or_func_expression
	| strcat_or_func_expression '?' expression ':' conditional_expression
		{
         $$ = node(conditional_expr);
         field($$, test_expression, $1);
         field($$, true_expression, $3);
         field($$, false_expression, $5);
      }
	;

assignment_expression
	: conditional_expression
	| unary_expression '=' assignment_expression
		{
         $$ = node(assign_expr);
         field($$, left, $1);
         field($$, right, $3);
      }
	| unary_expression float_assignment_operator assignment_expression
		{
         $$ = node(float_assign_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, $2);
      }
	| unary_expression int_assignment_operator assignment_expression
		{
         $$ = node(int_assign_expr);
         field($$, left, $1);
         field($$, right, $3);
         field($$, op, $2);
      }
	;
	
float_assignment_operator
	: "*="
		{ $$ = string("multiply"); }
	| "/="
		{ $$ = string("divide"); }
	| "+="
		{ $$ = string("add"); }
	| "-="
		{ $$ = string("subtract"); }
	;

int_assignment_operator
	: "%="
		{ $$ = string("modulus"); }
	| "<<="
		{ $$ = string("shift_left"); }
	| ">>="
		{ $$ = string("shift_right"); }
	| "&="
		{ $$ = string("bitwise_and"); }
	| "^="
		{ $$ = string("bitwise_xor"); }
	| "|="
		{ $$ = string("bitwise_or"); }
	;

expression
	: assignment_expression
	;	

expression_statement
	: expression
		{
			$$ = node(expression_stmt);
			field($$, expr, $1);
		}
	;

array_expression
	: '[' ']'
		{
		 $$ = node(array_expr);
		 field($$, array_values, empty_list());
		}
	| '[' expression_list ']'
		{
         $$ = node(array_expr);
         field($$, array_values, $2);
      }
	| '[' expression_list ',' ']'
		{
         $$ = node(array_expr);
         field($$, array_values, $2);
      }
	;		

map_expression
	: '{' '}'
		{ $$ = node(map_expr); }
	| '{' map_pair_list '}'
		{
         $$ = node(map_expr);
         field($$, map_pairs, $2);
      }
	| '{' map_pair_list ',' '}'
		{
         $$ = node(map_expr);
         field($$, map_pairs, $2);
      }
	;

expression_list
	: expression
	   { $$ = list($1); }
	| expression_list ',' expression
		{ $$ = $1; append($1, $3); }
	;

map_pair_list
	: map_pair
	   { $$ = list($1); }
	| map_pair_list ',' map_pair
		{ $$ = $1; append($1, $3); }
	;

map_pair
	: expression ':' expression
		{
         $$ = node(map_pair);
         field($$, key, $1);
         field($$, value, $3);
      }
	;

function_expression
	: "function" '(' optional_parameter_list ')' optional_return_type '(' expression ')'
		{
         $$ = node(function_expr);
         field($$, parameter_list, $3);
         field($$, return_type, $5);
         field($$, expr, $7);
      }
	;

%%

void kt_error (struct YYLTYPE *loc, kt_lexer *lexer, parse_result *result, const char *format, ...)
{
	result->error = true;
	va_list args;
	va_start(args, format);
	result->error_string.format(format, args);
	va_end(args);
	result->error_line_number = loc->first_line;
	result->error_column_number = loc->first_column;
}

void parser_init()
{
    yydebug = 1;
}

