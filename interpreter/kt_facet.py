__author__ = 'markf'

from kt_program_tree import *
#from kt_builtin_functions import *
#from kt_builtin_classes import *
#from kt_program_declarations import *
import kt
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

class node_basic_type (type_specifier):
	def __init__(self, type_id):
		self.type_id = type_id
		self.type = kt_type.kind.basic_type

# a facet in kt defines a full program execution space.
class facet:
	def __init__(self, facet_name):
		self.string_constants = []
		self.string_constant_lookup = {}
		self.facet_name = facet_name
		self.sorted_containers = []
		self.globals = {}
		self.globals_list = []
		self.functions = []
		self.globals_by_id = []
		self.next_label_id = 1
		self.next_type_id = 0
		self.type_list = []

		self.root = construct_node('object')
		self.root.name = 'Root'
		self.add_global(self.root)

	def process(self, file_tree):
		self.root.body = [kt.query_builtins(ast_node)]
		build_facet_program_tree(self, file_tree)
		builtins_node = self.root.contents['builtins']
		for node in builtins_node.contents.values():
			if not node.is_container():
				self.add_global(node)

		print "Globals: " + str(" ".join(g.name for g in self.globals_list))

		print "Analyzing Containers"
		for c in (x for x in self.globals_list if x.is_container()):
			c.analyze_container(self)

		print "Analyzing Functions"
		for func in self.functions:
			func.analyze_function(self)

		# output the compiled code
		emit_string = self.emit_standard_includes() +\
					self.emit_string_table() +\
					"struct program {\n" +\
					self.emit_classdefs() +\
					self.emit_functions() +\
					"};\n"
		print "Facet compiles to:\n"
		print emit_string

	def emit_standard_includes(self):
		return "#include \"standard_library.h\"\n"

	def emit_string_table(self):
		emit_string = "kt_string_constant __string_constants[" + str(len(self.string_constants)) + "] = {\n"
		for const_index in range(len(self.string_constants)):
			const_str = self.string_constants[const_index]
			emit_string += "{ " + str(len(const_str)) + ", \"" + const_str + "\"},\n"
		emit_string += "};\n"
		return emit_string

	def emit_classdefs(self):
		result = ""
		for c in self.sorted_containers:
			result += c.emit_classdef()
		return result

	def emit_functions(self):
		return ""
		#print "Compiling Functions"
		#for func in self.functions:
		#	func.compile_function()

	def add_function(self, the_function):
		func_index = len(self.functions)
		self.functions.append(the_function)
		the_function.function_index = func_index
		the_function.facet = self
		return func_index

	def get_function_by_index(self, index):
		return self.functions[index]

	# add_type takes a parsed type_spec and returns an integer type id
	# type_spec => [locator, is_array, is_reference, size_expr]
	# if the array_expr is a non-constant expression,
	def add_basic_type(self, type_name):
		new_node = node_basic_type(self.next_type_id)
		self.type_list.append(new_node)
		self.next_type_id += 1
		self.add_builtin_node("builtins/types/" + type_name, new_node)

	def add_type(self, type_spec):
		if type_spec.type == 'locator_type_specifier':
			node = self.find_node(type_spec, type_spec.locator)
			if type_id in node:
				return type_id
			else:
				# build a type
				pass
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
				new_node = construct_node('object')
				new_node.name = path[0]
				new_node.body = []
				new_node.parent_decl = ['directory' ]
				node.contents[path[0]] = new_node
				new_node.container = node
				node = new_node
			path = path[2].partition('/')
		if node.contents.has_key(path[0]):
			raise compile_error, (None, "duplicate addition of builtin node: " + path[0])
		the_node.name = path[0]
		the_node.container = node
		node.contents[path[0]] = the_node
		self.add_global(the_node)

	def add_python_function(self, node_path, the_function):
		self.add_builtin_node(node_path, node_python_function(the_function))

	def add_python_class(self, node_path, the_class):
		self.add_builtin_node(node_path, node_python_class(the_class))

	def find_node(self, search_node, parent_name, filter_func = lambda x: True ):
		parent_part = parent_name.partition('/')
		if not self.globals.has_key(parent_part[0]):
			print "Error, node named " + parent_part[0] + " is not in facet " + self.facet_name
			return None
		else:
			node_list = []
			# construct a list of nodes that can be reached from the specified parent_name path
			for node in self.globals[parent_part[0]]:
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
			elif len(node_list) == 1:
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