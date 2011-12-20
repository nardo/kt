# kt_builtin_classes.py
# builtin python class for kt
# (C) 2009 Mark Frohnmayer.  The use of this code is governed by its license.  See /license/info.txt in the source distribution for the full license agreement.

def add_builtin_classes(the_facet):
	the_facet.add_python_class("builtins/object", builtin_object)
	the_facet.add_python_class("builtins/directory", builtin_directory)
	
class builtin_object(object):
	def __init__(self):
		pass
	
class builtin_directory(object):
	def __init__(self):
		pass

