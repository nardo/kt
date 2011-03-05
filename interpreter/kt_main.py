# kt_main.py
# main module for the kt interpreter
# (C) 2009 Mark Frohnmayer.  The use of this code is governed by its license.  See /License/info.txt in the source distribution for the full license agreement.

from kt_compiler import *
from kt_vm import *
from kt_builtin_functions import *
from kt_builtin_classes import *
from kt_file_tree import *
from kt_codegen import *

import sys
import traceback

def test():
	root_tree = sys.argv[1]
	try:
		file_tree = build_file_tree(root_tree)
		images = get_image_set(file_tree)
		print "Images in test program: " + str(images)
		image_trees = {}
		for img in images:
			print "Processing image: " + img
			the_image = image(file_tree, img)
			add_builtin_functions(the_image)
			add_builtin_classes(the_image)
	
			the_image.build_tree(file_tree)
			the_image.tree.dump()
			
			print "Globals: " + str((g.name for g in the_image.globals_list))
			print "Analyzing Compounds"
			
			for c in (c for c in the_image.globals_list if c.type in ('class', 'object', 'struct')):
				the_image.analyze_compound(c)
				
			print "Analyzing Functions"
			the_image.analyze_functions()
			
			the_vm = vm(the_image)
			the_vm.exec_function("main", ())
			
			the_code_generator = code_generator(the_image)
			the_code_generator.go()

	except compile_error, err:
		traceback.print_exc()
		print "Compile ERROR DUDE!!: " + err.error_string
	except fatal_error, err:
		traceback.print_exc()
		print "Fatal: " + err.error_string
		
test()
print ast_node
