class slot:
	variable_slot = 0
	function_slot = 1
	reference_slot = 2

	def __init__(self, initial_node, type, name, index, type_spec = None, function_decl = None):
		self.name = name
		self.type = type
		self.index = index
		self.initial_node = initial_node
		self.function_decl = function_decl
		self.type_spec = type_spec
		self.assignment = None
		if self.type == slot.function_slot:
			self.type_spec = self.function_decl.get_type_signature()
		elif self.type == slot.reference_slot:
			self.type_spec = self.initial_node.get_reference_type_spec()
	def is_variable(self):
		return self.type == slot.variable_slot
	def is_function(self):
		return self.type == slot.function_slot
	def __str__(self):
		return "(" + str(self.type) + " " + self.name + ": " + str((self.index, self.function_decl, self.type_spec)) + ")"

