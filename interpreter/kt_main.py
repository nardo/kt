# kt_main.py
# main module for the kt interpreter
# (C) 2009 Mark Frohnmayer.  The use of this code is governed by its license.  See /License/info.txt in the source distribution for the full license agreement.

#from kt_compiler import *
from kt_file_tree import *
from kt_program_tree import *
from kt_types import *
from kt_facet import *
import kt
import sys
import traceback

def test():
	#builtins_tree = kt.query_builtins(ast_node)
	#print str(builtins_tree)
	#print dump_ast(builtins_tree, 0)
	#return
	build_node_lookup_table()
	root_tree = sys.argv[1]
	#try:
	file_tree = build_file_tree(root_tree)
	facets = get_facet_set(file_tree)
	print "Facets in test program: " + str(facets)
	facet_trees = {}
	for facet_name in facets:
		print "Processing facet: " + facet_name
		new_facet = facet(facet_name)
		new_facet.process(file_tree)

		# the_vm = vm(new_facet)
		# the_vm.exec_function("main", ())
			
			#the_code_generator = code_generator(new_facet)
			#the_code_generator.go()

	#except compile_error, err:
	#	traceback.print_exc()
	#	print "Compile ERROR DUDE!!: " + err.error_string
	#except fatal_error, err:
	#	traceback.print_exc()
	#	print "Fatal: " + err.error_string
		
test()
