__author__ = 'markf'

from kt_construct_node import *
#from kt_builtin_functions import *
#from kt_builtin_classes import *
#from kt_program_declarations import *
from kt_locator import *
import kt_globals
import kt
from kt_type_qualifier import *
from kt_file_tree import ast_node

# returns the number of elements that are the same in two lists starting from
# the beginning of the list
def common_list_length(list1, list2):
	i = 0
	while i < len(list1) and i < len(list2) and list1[i] == list2[i]:
		i += 1
	return i

# types in kt:
# Every variable in kt has a type - by default a variable has the generic
# "variable" type, which can be assigned any value of any type.
# Variables can also be declared with specific types that fall into
# several categories.
#
# generic type: variable
# basic types: integer (32 bit), float (64 bit), string
# object references: soft and hard references.  Soft references are specified with
# the '&' operator, hard references without.  Soft references are set to nil
# when all hard references go out of scope
# arrays, maps and strings are all hard reference types
# arrays and maps: declared with [] and {}
# arrays may also be specified with a constant size
# compound types: structs
# function and method signatures:
#
# how this breaks down

class node_basic_type (type_qualifier):
	def __init__(self, type_id):
		self.type_id = type_id
		self.type = kt_type.kind.basic_type

# a facet in kt defines a full program execution space.
class facet:
	def __init__(self, facet_name, output_file):
		self.string_constants = []
		self.string_constant_lookup = {}
		self.facet_name = facet_name
		self.sorted_compounds = []
		self.globals = {}
		self.globals_list = []
		self.functions = []
		self.globals_by_id = []
		self.type_dictionary = type_dictionary()
		self.next_label_id = 1
		self.output_file = output_file

		self.root = node_object()
		self.root.name = 'Root'
		self.add_global(self.root)

	def process(self, file_tree):
		kt_globals.current_facet = self

		# create the root node of the program tree
		self.root.body = [kt.query_builtins(ast_node)]

		# build the full program tree from the file tree and its parsed syntax trees
		# all compounds are added as globals
		# all declarations (functions, variables) at the top level of each file are added as globals
		build_facet_program_tree(self, file_tree)

		# all nodes in builtins are added as globals
		builtins_node = self.root.contents['builtins']
		for node in builtins_node.contents.values():
			if not node.is_compound():
				self.add_global(node)

		# set qualifiers for the builtin types
		self.find_node(None, "/builtins/none").qualified_type = self.type_dictionary.builtin_type_qualifier_none
		self.type_dictionary.builtin_type_qualifier_none.c_name = "kt_program::none"

		self.find_node(None, "/builtins/boolean").qualified_type = self.type_dictionary.builtin_type_qualifier_boolean
		self.type_dictionary.builtin_type_qualifier_boolean.c_name = "bool"

		self.find_node(None, "/builtins/int32").qualified_type = self.type_dictionary.builtin_type_qualifier_integer
		self.type_dictionary.builtin_type_qualifier_integer.c_name = "int32"

		self.find_node(None, "/builtins/float64").qualified_type = self.type_dictionary.builtin_type_qualifier_float
		self.type_dictionary.builtin_type_qualifier_float.c_name = "float64"

		self.find_node(None, "/builtins/string").qualified_type = self.type_dictionary.builtin_type_qualifier_string
		self.type_dictionary.builtin_type_qualifier_string.c_name = "string"

		self.find_node(None, "/builtins/variable").qualified_type = self.type_dictionary.builtin_type_qualifier_variable
		self.type_dictionary.builtin_type_qualifier_variable.c_name = "kt_program::variable"

		print "Globals: " + str(" ".join(g.name for g in self.globals_list))

		# the program tree is processed as follows:
		# 1. Process all compound definitions - build the derivation hierarchy and membership of all compounds
		# 2. Process all function definitions - build local variable lists, and translate statement structure into linear operation instruction lists
		# 3. Qualify the types of all program variables and structures. type id and type_qualifier for

		print "Analyzing Compound Structures"
		for c in (x for x in self.globals_list if x.is_compound()):
			c.connect_parentage_and_sort_compounds(self)
		for c in self.sorted_compounds:
			c.analyze_compound_structure(self)
		sys.stdout.flush()

		print "Assigning Compound Types"
		for c in self.sorted_compounds:
			c.assign_qualified_type(self)

		print "Analyzing Function Structure"
		for func in self.functions:
			func.analyze_function_structure()

		for func in self.functions:
			func.resolve_c_name()
		for f in (x for x in self.globals_list if x.__class__ == node_builtin_function):
			f.resolve_c_name()

		print "Analyzing Function Linkage"
		for func in self.functions:
			func.analyze_function_linkage()

		print "Analyzing Function Signatures"
		for func in self.functions:
			func.analyze_signature_types()
		for f in (x for x in self.globals_list if x.__class__ == node_builtin_function):
			f.analyze_signature_types()

		print "Analyzing Compound Member Types"
		for c in self.sorted_compounds:
			c.analyze_compound_types(self)

		sys.stdout.flush()
		sys.stderr.flush()

		print "Analyzing Function Types"
		for func in self.functions:
			func.analyze_types()
		sys.stdout.flush()

		print "Facet compiles to:\n"
		self.emit_standard_includes()
		self.emit_code("namespace core {\n")
		#self.emit_code("static kt_program kt;\n")
		self.emit_string_table()
		self.emit_code("struct program {\n")
		self.emit_classdefs()
		self.emit_functions()
		self.emit_code("};\n}\n")

		self.emit_code("int main(int argc, const char **argv) { core::__init_string_constants(); core::program::main(); return 0; } ")

		kt_globals.current_facet = None

	def emit_code(self, the_code):
		self.output_file.write(the_code)
		sys.stdout.write(the_code)
		sys.stdout.flush()

	def emit_standard_includes(self):
		self.emit_code( "#include \"standard_library.h\"\n")

	def emit_string_table(self):
		self.emit_code("string __string_constants[" + str(len(self.string_constants)) + "];\nstatic void __init_string_constants(void)\n{\n")
		for const_index in range(len(self.string_constants)):
			const_str = self.string_constants[const_index]
			self.emit_code("__string_constants[" + str(const_index) + "] = \"" + const_str + "\";\n")
		self.emit_code("}\n")

	def emit_classdefs(self):
		builtins_node = self.find_node(None, "/builtins")
		self.emit_code("//found builtins_node: " + str(builtins_node) + "\n")

		# output a classdef for each compound that is not a builtin
		for c in self.sorted_compounds:
			if c.compound != builtins_node:
				c.emit_classdef(self)

	def emit_functions(self):
		self.emit_code("// Compiling Functions\n")
		for func in self.functions:
			func.compile_function()

	def add_function(self, the_function):
		self.functions.append(the_function)
		the_function.facet = self

	def add_string_constant(self, string_value):
		if string_value in self.string_constant_lookup:
			return self.string_constant_lookup[string_value]
		index = len(self.string_constants)
		self.string_constants.append(string_value)
		self.string_constant_lookup[string_value] = index
		return index

	def add_global(self, item):
		if item.name in self.globals:
			self.globals[item.name].append(item)
		else:
			self.globals[item.name] = [item]

		item.global_index = len(self.globals_list)
		self.globals_list.append(item)

	def add_builtin_node(self, node_path, the_node):
		node = self.root
		path = node_path.partition('/')
		while path[2] != "":
			if node.contents.has_key(path[0]):
				node = node.contents[path[0]]
			else:
				new_node = node_object()
				new_node.name = path[0]
				new_node.body = []
				new_node.parent_decl = node_parent_specifier()
				new_node.parent_decl.parent = 'directory'
				new_node.parent_decl.args = []
				node.contents[path[0]] = new_node
				new_node.compound = node
				node = new_node
			path = path[2].partition('/')
		if node.contents.has_key(path[0]):
			raise compile_error, (None, "duplicate addition of builtin node: " + path[0])
		the_node.name = path[0]
		the_node.compound = node
		node.contents[path[0]] = the_node
		self.add_global(the_node)

	def add_python_function(self, node_path, the_function):
		self.add_builtin_node(node_path, node_python_function(the_function))

	def add_python_class(self, node_path, the_class):
		self.add_builtin_node(node_path, node_python_class(the_class))

	def find_node(self, search_node, parent_name, filter_func = lambda x: True ):
		parent_part = parent_name.partition('/')
		if len(parent_part[0]) > 0 and not self.globals.has_key(parent_part[0]):
			print "Error, node named " + parent_part[0] + " is not in facet " + self.facet_name
			return None
		else:
			if len(parent_part[0]) == 0:
				search_list = [self.root]
			else:
				search_list = self.globals[parent_part[0]]
			node_list = []
			# construct a list of nodes that can be reached from the specified parent_name path
			for node in search_list:
				remainder_path = parent_part[2]
				leaf_node = node
				while remainder_path != "":
					sub_path = remainder_path.partition('/')
					if leaf_node.contents.has_key(sub_path[0]):
						leaf_node = leaf_node.contents[sub_path[0]]
						remainder_path = sub_path[2]
					else:
						leaf_node = None
						break
				if leaf_node is not None and filter_func(leaf_node):
					node_list.append(leaf_node)
			if not len(node_list):
				return None
			elif len(node_list) == 1 or search_node is None:
				return node_list[0]
			else:
				# figure out which is the closest relative to search_node
				search_ancestry = search_node.get_ancestry_list()
				node_ancestry = node_list[0].get_ancestry_list()
				closest_ancestry_depth = common_list_length(search_ancestry, node_ancestry)
				closest_node = node_list[0]
				for n in node_list[1:]:
					node_ancestry = n.get_ancestry_list()
					depth = common_list_length(search_ancestry, node_ancestry)
					if depth > closest_ancestry_depth:
						closest_node = n
						closest_ancestry_depth = depth
					elif depth == closest_ancestry_depth:
						compiler_warning(None, "Node " + parent_name + " ambiguously resolves to multiple objects at same depth.")
				return closest_node