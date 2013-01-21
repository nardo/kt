#import kt_locator

class slot_types:
	variable_slot_type = 0
	function_slot_type = 1

class slot:

	def __init__(self, initial_node, slot_type, name, index, type_spec = None, function_decl = None):
		self.name = name
		self.slot_type = slot_type
		self.index = index
		self.initial_node = initial_node
		self.function_decl = function_decl
		self.type_spec = type_spec
		self.assignment = None
		if self.is_function():
			self.type_spec = self.function_decl.get_type_signature()
	def is_variable(self):
		return self.slot_type == slot_types.variable_slot_type
	def is_function(self):
		return self.slot_type == slot_types.function_slot_type
	def __str__(self):
		return "(" + str(self.slot_type) + " " + self.name + ": " + str((self.index, self.function_decl, self.type_spec)) + ")"

