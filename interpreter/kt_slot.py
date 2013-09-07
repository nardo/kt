#import kt_locator

import kt_globals

class compound_member_types:
	slot = 0
	function = 1

class compound_member:
	def __init__(self, initial_node, member_type, name, index, type_spec = None, function_decl = None):
		self.name = name
		self.member_type = member_type
		self.index = index
		self.initial_node = initial_node
		self.function_decl = function_decl
		self.type_spec = type_spec
		self.assignment = None
		self.qualified_type = None

	def assign_qualified_type(self, the_scope):
		if self.member_type == compound_member_types.slot:
			if self.type_spec == None:
				self.qualified_type = kt_globals.current_facet.type_dictionary.builtin_type_qualifier_variable
			else:
				self.type_spec.resolve(the_scope)
				self.qualified_type = self.type_spec.qualified_type
		else:
			self.qualified_type = self.function_decl.qualified_type

	def is_variable(self):
		return self.member_type == compound_member_types.slot_member_type
	def is_function(self):
		return self.member_type == compound_member_types.function_member_type
	def __str__(self):
		return "(" + str(self.member_type) + " " + self.name + ": " + str((self.index, self.function_decl, self.type_spec)) + ")"