__author__ = 'markf'

# general error exception thrown by the compiler if given incorrect input
class compile_error:
	def __init__(self, node_where, error_string):
		self.fail = self.foo
		self.node_where = node_where
		self.error_string = error_string

# output a warning message during the compile process
def compiler_warning(node_where, warning_string):
	print "Warning!: " + warning_string

class program_node(object):
	def __init__(self):
		object.__init__(self)
		self.compound = None
	def is_compound(self):
		return False
	def is_variable(self):
		return False
	def is_function(self):
		return False
	def get_compound_list(self):
		if self.compound is None:
			return [self]
		else:
			return self.compound.get_compound_list() + [self]

	def dump_tree(self):
		def dump_node(node, level, visited_set):
			if node in visited_set:
				if 'name' in node.__dict__:
					return "\n" + " " * (level * 2) + "'" + node.name + "'"
				else:
					return "\n" + " " * (level * 2) + str(node.__class__)
			visited_set.add(node)
			return "\n" + " " * (level * 2) + str(node.__class__) + "".join ( "\n" + " " * (level * 2 + 2) + str (field_name) + " = " + dump_element(node.__dict__[field_name], level + 1, visited_set) for field_name in node.__dict__.keys() )
		def dump_element(node, level, visited_set):
			if node is None:
				return "<null>"
			elif node.__class__ == list:
				return "( " + ", ".join( (dump_element(x, level + 1, visited_set) for x in node) ) + " )"
			elif node.__class__ == dict:
				return "{" + "".join("\n" + " " * (level * 2 + 2) + str (key) + dump_element(value, level + 2, visited_set) for key, value in node.iteritems())+ "\n" + " " * (level * 2) + "}"
			elif issubclass(node.__class__, program_node):
				return dump_node(node, level, visited_set)
			elif node.__class__ == str:
				return "\"" + node + "\""
			else:
				return str(node)
		dump_node(self, 0, set())


def find_in_tree(start, filter_func):
	def find_in_node(node, filter_func, visited_set):
		if node not in visited_set:
			visited_set.add(node)
			for field_value in node.__dict__.values():
				for element in find_in_element(field_value, filter_func, visited_set):
					yield element
	def find_in_element(element, filter_func, visited_set):
		if element is not None:
			if element.__class__ == list:
				for entry in element:
					for found_item in find_in_element(entry, filter_func, visited_set):
						yield found_item
			elif element.__class__ == dict:
				for entry in element.values():
					for found_item in find_in_element(entry, filter_func, visited_set):
						yield found_item
			elif issubclass(element.__class__, program_node):
				if element not in visited_set:
					visited_set.add(element)
					if filter_func(element):
						yield element
					for found_item in find_in_node(element, filter_func, visited_set):
						yield found_item
	for result in find_in_element(start, filter_func, set()):
		yield result

from kt_types import *
from kt_declarations import *
from kt_functions import *
from kt_statements import *
from kt_expressions import *

ast_node_lookup_table = {}

def build_node_lookup_table():
	prefix = "node_"
	for pair in globals().iteritems():
		if pair[0].startswith(prefix):
			split_string = pair[0].partition(prefix)
			# print "Node: " + split_string[2] + " = " + str(pair[1])
			ast_node_lookup_table[split_string[2]] = pair[1]

def construct_node(node_name):
	#print "Constructing node of type: " + node_name
	return ast_node_lookup_table[node_name]()

from kt_file_tree import ast_node

def build_facet_program_tree(the_facet, file_tree):
	def decl_in_facet(decl):
		if decl.__dict__.has_key('facet_list') and decl.facet_list is not None:
			if (len(decl.facet_list) != 0) and (the_facet.facet_name not in decl.facet_list):
				return False
		if decl.__dict__.has_key('transmission_list') and decl.transmission_list is not None:
			# see if it's in the from_facet or to_facet of any transmission specifiers
			if len(decl.transmission_list) and len(filter(decl.transmission_list, lambda x: x.from_facet == self.facet_name or x.to_facet == the_facet.facet_name)) == 0:
				return False
		return True

	def build_accept_reject_list(accept_list, reject_name_list, decl):
		if decl.type == 'facet':
			if decl.name != the_facet.facet_name:
				for sub_decl in decl.body:
					reject_name_list.append(sub_decl.name)
			else:
				accept_list += decl.body
		else:
			if decl_in_facet(decl):
				print "decl in facet"
				accept_list.append(decl)
			else:
				reject_name_list.append(decl.name)

	def build_tree_recurse(facet_node, file_node, indent_level):
		print "|  " * indent_level + facet_node.name + ":"
		files_and_dirs = [d for d in file_node.contents.values() if d.type == 'directory' or d.type == 'resource']
		print files_and_dirs
		reject_list = []
		decls_list = []

		if 'body' in facet_node.__dict__ and facet_node.body != None:
			for decl in facet_node.body:
				build_accept_reject_list(decls_list, reject_list, decl)
		for file in (k for k in file_node.contents.values() if k.type == 'kt'):
			for decl in file.parse_result:
				print decl
				build_accept_reject_list(decls_list, reject_list, decl)
		# now add all the files and directories to the tree and recurse them:
		for file in (f for f in files_and_dirs if f.name not in reject_list):
			parent = 'resource' if file.type == 'resource' else 'directory'
			decl = node_object()
			decl.name = file.name
			decl.parent_decl = [parent]
			decl.body = []
			decl.compound = facet_node
			decl.file_node = file
			facet_node.contents[file.name] = decl

		for decl in decls_list:
			if decl.name in facet_node.contents:
				# this is only allowed if the item in contents is a resource or directory;
				# also it must have an empty body
				existing_node = facet_node.contents[decl.name]
				if existing_node.type != 'object' or decl.type != 'object' or 'file_node' not in existing_node.decl:
					print "Redefinition of " + decl.name + " in " + facet_node.name + " not allowed."
				elif decl.body is not None:
					print "Resources and directories cannot contain other nodes."
				else:
					if decl.parent_decl != None and decl.parent_decl != existing_node.decl.parent_decl:
						print "Parent type mismatch for object " + decl.name
					else:
						# copy all the fields over
						for pair in decl.iteritems():
							existing_node.setattr(pair[0], pair[1])
						#existing_node.decl.update(decl)
			else:
				new_node = construct_node(decl.type)
				new_node.name = decl.name;
				new_node.compound = facet_node
				new_node.syntax_tree = decl
				facet_node.contents[decl.name] = new_node

		# now go back through the contents and recurse the children:
		for node in facet_node.contents.values():
			print "|  " * (indent_level + 1) + node.name + ":"
			# everything declared at the top level is added to the globals; otherwise, only compounds are added
			the_facet.add_global(node)
			if 'file_node' in node.__dict__:
				build_tree_recurse(node, node.file_node, indent_level + 2)
			if 'syntax_tree' in node.__dict__:
				print "|  " * (indent_level + 1) + " ** recursing syntax tree ** "
				build_tree_recurse_decl(node, node.syntax_tree, indent_level + 1)

	def syntax_to_program_tree(syntax_tree_node, indent_level):
		if syntax_tree_node is None:
			return None
		elif syntax_tree_node.__class__ == list:
			print "|  " * indent_level + "[]:"
			return [syntax_to_program_tree(x, indent_level + 1) for x in syntax_tree_node]
		elif syntax_tree_node.__class__ == ast_node:
			new_node = construct_node(syntax_tree_node.type)
			print "|  " * indent_level + str(new_node.__class__)
			indent_level += 1
			for field, value in syntax_tree_node.__dict__.iteritems():
				print "|  " * indent_level + field + " = "
				setattr(new_node, field, syntax_to_program_tree(value, indent_level + 1))
			return new_node
		else:
			print "|  " * indent_level + str(syntax_tree_node)
			return syntax_tree_node

	def build_tree_recurse_decl(facet_node, syntax_tree_node, indent_level):
		for field, value in syntax_tree_node.__dict__.iteritems():
			#print "Field " + field + " - value: " + str(value)
			if field == 'body':
				if 'contents' not in facet_node.__dict__:
					facet_node.contents = {}
				# if it has a body, it's a compound, so continue building the compound tree
				for sub_decl in value:
					# if it's a method, it has a primary name.  Here's where the full name is computed:
					if 'primary_name' in sub_decl.__dict__:
						sub_decl.name = sub_decl.primary_name + "".join(str(pair.string if pair.string is not None
						else "") + ":" for pair in sub_decl.selector_decl_list )
						sub_decl.parameter_list = [pair.name for pair in sub_decl.selector_decl_list]
					if 'name' in sub_decl.__dict__ and decl_in_facet(sub_decl):
						if sub_decl.name in facet_node.contents:
							raise compile_error, (syntax_tree_node, "Redefinition of " + sub_decl.name + " in " +
							                                    facet_node.name+ " not allowed.")
						# create the new node:
						new_node = construct_node(sub_decl.type)
						new_node.name = sub_decl.name
						new_node.compound = facet_node
						facet_node.contents[new_node.name] = new_node
						print "|  " * indent_level + new_node.name + ":"
						build_tree_recurse_decl(new_node, sub_decl, indent_level + 1)
						if new_node.is_compound():
							the_facet.add_global(new_node)
			else:
				print "|  " * indent_level + field + " = "
				setattr(facet_node, field, syntax_to_program_tree(value, indent_level + 1))

	build_tree_recurse(the_facet.root, file_tree, 0)
	print("Dumping program tree:")
	print(the_facet.root.dump_tree())
	print("-- Done")

