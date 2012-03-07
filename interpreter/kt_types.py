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
	def resolve(self, func):
		pass
	def emit_declaration(self, var_name_str):
		return "variable " + var_name_str
	def get_c_typename(self):
		return "variable"
	def check_conversion(self, type_spec):
		# raises a compile error if self cannot be converted to the specified type
		return None
	def is_equivalent(self, type_spec):
		# returns True if the types are fundamentally the same
		return False
	def is_callable(self):
		return False
	def get_callable_return_type(self):
		return None
	def callable_has_signature(self):
		return False
	def get_callable_parameter_types(self):
		return None
	def is_numeric(self):
		return False
	def is_string(self):
		return False
	def is_compound(self):
		return False
	def is_compound_pointer(self):
		return False
	def get_compound_members(self):
		return None
	def is_container(self):
		return False
	def is_container_sequential(self):
		return False
	def get_container_size(self):
		return "Variable"
	def get_container_key_type(self):
		return None
	def get_container_value_type(self):
		return None


class node_locator_type_specifier(type_specifier):
	def __init__(self, locator = None):
		type_specifier.__init__(self)
		self.locator = locator
	pass

class node_reference_type_specifier(type_specifier):
	pass

class node_array_type_specifier(type_specifier):
	pass

class node_builtin_type(type_specifier):
	pass

