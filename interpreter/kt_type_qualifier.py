import kt_globals

class type_qualifier:
	class kind:
		none_type = -1
		variable_type = 0
		basic_type = 1
		class_type = 2
		class_instance_type = 3
		record_type = 4
		record_instance_type = 5
		function_type = 6
		array_type = 7
		map_type = 8
	def __init__(self, kind_id):
		self.id = -1
		self.type_kind = kind_id
		self.return_type = None
		self.is_callable = False
		self.parameter_type_list = None
		self.is_builtin = False
		self.needs_closure = False
		self.compound = None
		self.is_numeric = False
		self.is_integer = False
		self.bit_width = 0
		self.is_string = False
		self.is_container = False # is this type a container type
		self.is_sequential = False # True if the container is accessed sequentially (i.e. an array)
		self.container_key_type = None # the type specifier of keys that index this container
		self.container_value_type = None # the type specifier of values in this container
		self.container_size = -1
		self.c_name = "<invalid type>"

	def get_type_string(self):
		if self.type_kind == type_qualifier.kind.none_type:
			return "N"
		elif self.type_kind == type_qualifier.kind.variable_type:
			return "V"
		elif self.type_kind == type_qualifier.kind.basic_type:
			return "B" + "S" if self.is_string else ("I" if self.is_integer else "F" + str(self.bit_width))
		elif self.type_kind >= type_qualifier.kind.class_type and self.type_kind <= type_qualifier.kind.record_instance_type:
			return "R" + str(self.kind) + "_" + str(self.compound.compound_id)
		elif self.type_kind == type_qualifier.kind.function_type:
			return "F(" + ("C" if self.needs_closure else "N") + "," + "," + ",".join(x.get_type_string() for x in self.parameter_type_list) + ")->(" + self.return_type.get_type_string() + ")"
		elif self.type_kind == type_qualifier.kind.array_type:
			return "A[" + self.container_key_type.get_type_string() + "," + self.container_value_type.get_type_string() + "," + self.container_size + "]"
		elif self.type_kind == type_qualifier.kind.map_type:
			return "M{" + self.container_key_type.get_type_string() + "," + self.container_value_type.get_type_string() + "}"
	def type_kind(self):
		return self.type_kind
	def resolve(self, scope):
		pass
	def emit_declaration(self, name):
		return self.c_name + " " + name
	def check_conversion(self, type_qualifier):
		# raises a compile error if self cannot be converted to the specified type
		return None
	def is_equivalent(self, type_spec):
		# returns True if the types are fundamentally the same
		return self.id == type_spec.id
	def is_none(self):
		return self.type_kind == type_qualifier.kind.none_type
	def get_callable_return_type(self):
		return self.return_type
	def callable_has_signature(self):
		return self.type_kind == type_qualifier.kind.class_type or self.type_kind == type_qualifier.kind.function_type
	def get_callable_parameter_types(self):
		return self.parameter_type_list
	def is_compound_pointer(self):
		return False
	def get_compound_members(self):
		return None

class type_dictionary:
	def __init__(self):
		self.next_type_id = 0
		self.type_list = []
		self.type_dictionary = {}
		self.builtin_type_qualifier_none = self.get_type_none()
		self.builtin_type_qualifier_boolean = self.get_type_integer(32)
		self.builtin_type_qualifier_integer = self.get_type_integer(32)
		self.builtin_type_qualifier_float = self.get_type_float(64)

		string_type = type_qualifier(type_qualifier.kind.basic_type)
		string_type.is_string = True
		string_type.is_sequential = True
		string_type.is_container = True
		string_type.container_key_type = self.builtin_type_qualifier_integer
		string_type.container_value_type = self.builtin_type_qualifier_integer
		self.builtin_type_qualifier_string = self.add_type(string_type)

		var_type = type_qualifier(type_qualifier.kind.variable_type)
		self.builtin_type_qualifier_variable = self.add_type(var_type)
		var_type.is_string = True
		var_type.is_numeric = True
		var_type.is_container = True
		var_type.is_callable = True
		var_type.container_key_type = var_type
		var_type.container_value_type = var_type
		var_type.return_type = var_type

	def get_type_none(self):
		q = type_qualifier(type_qualifier.kind.none_type)
		return self.add_type(q)

	def get_type_integer(self, bit_width):
		q = type_qualifier(type_qualifier.kind.basic_type)
		q.is_integer = True
		q.is_numeric = True
		q.bit_width = bit_width
		return self.add_type(q)

	def get_type_float(self, bit_width):
		q = type_qualifier(type_qualifier.kind.basic_type)
		q.is_numeric = True
		q.bit_width = bit_width
		return self.add_type(q)

	def get_type_compound(self, qualifier_kind, the_compound):
		q = type_qualifier(qualifier_kind)
		q.compound = the_compound
		return self.add_type(q)

	def get_type_function(self, arg_list, return_type, needs_closure):
		q = type_qualifier(type_qualifier.kind.function_type)
		q.parameter_type_list = arg_list
		q.return_type = return_type
		q.is_callable = True
		#q.is_builtin = is_builtin
		q.needs_closure = needs_closure
		return self.add_type(q)

	def add_type(self, q):
		type_string = q.get_type_string()
		if type_string in self.type_dictionary:
			return self.type_dictionary[type_string]
		else:
			q.id = self.next_type_id
			self.next_type_id += 1
			self.type_list.append(q)
			self.type_dictionary[type_string] = q
			return q
