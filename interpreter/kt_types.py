from kt_program_tree import *

class node_type(program_node):
	pass

class type_specifier(program_node):
	class kind:
		invalid_type = -1
		basic_type = 0
		reference_type = 1
		object_type = 2
		class_type = 3
		record_type = 4
		function_type = 5
		array_type = 6
		map_type = 7
	def type_kind(self):
		return invalid_type
	def analyze(self, func):
		pass

class node_locator_type_specifier(type_specifier):
	pass

class node_reference_type_specifier(type_specifier):
	pass

class node_array_type_specifier(type_specifier):
	pass

class node_builtin_type(type_specifier):
	pass

