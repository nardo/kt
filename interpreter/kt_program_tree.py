__author__ = 'markf'

# general error exception thrown by the compiler if given incorrect input
class compile_error:
	def __init__(self, node_where, error_string):
		print error_string
		self.fail = self.foo
		self.node_where = node_where
		self.error_string = error_string

# output a warning message during the compile process
def compiler_warning(node_where, warning_string):
	print "Warning!: " + warning_string

def goto_label(label_id):
	return "goto _gt_l" + str(label_id) + ";\n"

def label(label_id):
	return "_gt_l" + str(label_id) + ":\n"

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
	def is_type(self):
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

