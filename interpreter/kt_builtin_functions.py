# kt_builtin_functions.py
# built in functions for kt
# (C) 2009 Mark Frohnmayer.  The use of this code is governed by its license.  See /license/info.txt in the source distribution for the full license agreement.

def add_builtin_functions(the_facet):
	the_facet.add_python_function("builtins/print", builtin_print)

def builtin_print(the_string):
	print the_string

