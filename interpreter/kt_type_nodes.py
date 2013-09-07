from kt_program_tree import *
from kt_type_qualifier import *
class node_type(program_node):
	pass

class node_reference_type_specifier(program_node):
	pass

class node_array_type_specifier(program_node):
	def resolve_type_specifier(self, container_node):
		pass

class node_builtin_type(program_node):
	def __init__(self):
		self.type_specifier = None
	def get_c_name(self):
		return self.name
	def get_type_specifier(self, scope):
		if self.type_specifier is None:
			self.type_specifier = type_qualifier(type_qualifier.kind.basic_type)
			self.type_specifier.is_numeric = self.is_numeric
		return self.type_specifier
	pass
