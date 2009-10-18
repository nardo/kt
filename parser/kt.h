// (C) 2009 Mark Frohnmayer.  The use of this code is governed by its license.  See /license/info.txt in the source distribution for the full license agreement.
typedef unsigned int uint;
#include <stdlib.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#ifndef assert
#define assert(x)
#endif

#include "memory_functions.h"
#include "formatted_string_buffer.h"
#include "page_allocator.h"
#include "parser_interface.h"

extern void kt_parse(const char *parse_string, uint parse_string_len, parse_result &result);
