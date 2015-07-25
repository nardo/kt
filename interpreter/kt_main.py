# kt_main.py
# main module for the kt interpreter
# (C) 2013 Mark Frohnmayer.  The use of this code is governed by its license.  See /License/info.txt in the source distribution for the full license agreement.

#from kt_compiler import *
from kt_file_tree import *
from kt_program_tree import *
from kt_facet import *
import kt
import sys
import subprocess

import traceback

def kt():
	build_node_lookup_table()
	root_tree = sys.argv[1]
	#try:
	file_tree = build_file_tree(root_tree)
	facets = get_facet_set(file_tree)
	print "Facets in test program: " + str(facets)
	sys.stdout.flush()
	output_file = open(root_tree + "_output.cpp", "w")

	facet_trees = {}
	for facet_name in facets:
		print "Processing facet: " + facet_name
		new_facet = facet(facet_name, output_file)
		new_facet.process(file_tree)
	output_file.close()
	subprocess.call(["gcc", "-g", "-o", root_tree + "_output.o", "-c", root_tree + "_output.cpp", "-I", "../..", "-I", "../standard_library"], stdout=sys.stdout, stderr=sys.stderr)
	subprocess.call(["gcc", "-g", "-o", root_tree + "_out", root_tree + "_output.o", "-lstdc++"], stdout=sys.stdout, stderr=sys.stderr)
	#except compile_error, err:
	#	traceback.print_exc()
	#	print "Compile ERROR DUDE!!: " + err.error_string
	#except fatal_error, err:
	#	traceback.print_exc()
	#	print "Fatal: " + err.error_string
		
kt()
