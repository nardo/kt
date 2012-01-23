from kt_program_tree import *

def compile_boolean_expression(func, expr):
	return expr.compile(func, ('boolean'))

def compile_void_expression(func, expr):
	return expr.compile(func, ('any'))

class node_expression(program_node):
	def analyze(self, func, result_type_specifier):
		pass
	def analyze_lvalue(self, func, result_type_specifier):
		raise compile_error, (self, "Expression is not an l-value.")
		pass
	def compile(self, func, result_symbol, result_type_specifier):
		pass
	def compile_lvalue(self, func):
		# the compile_lvalue method returns a touple containing first a compiled expression string representing the lvalue location and the type specifier for that lvalue.
		return "symbol_name", None
		pass
	def get_preferred_type_spec(self, func):
		return func.facet.builtin_type_spec_variable

class node_locator_expr(node_expression):

	# different types of locators.  The first set (up to last_lvalue_type) can be lvalues in expressions
	unknown_type = 0
	local_variable_type = 1
	prev_scope_variable_type = 2
	instance_variable_type = 3
	global_variable_type = 4
	last_lvalue_type = 4 #------------
	method_type = 5
	reference_type = 6
	global_function_type = 7
	child_function_type = 8
	prev_scope_child_function_type = 9
	builtin_class_type = 10
	builtin_function_type = 11

	def __init__(self):
		node_expression.__init__(self)
		self.locator_type = node_locator_expr.unknown_type
		self.slot = None
		self.resolved = False

	def resolve(self, func):
		if self.resolved:
			return
		self.resolved = True
		locator_name = self.string
		if locator_name in func.symbols:
			self.slot = func.symbols[locator_name]
			if self.slot.type == slot.variable_slot:
				self.locator_type = node_locator_expr.local_variable_type
				self.c_name = locator_name
			else:
				self.locator_type = node_locator_expr.child_function_type
				self.c_name = self.slot.function_decl.get_c_name()
		elif func.prev_scope and locator_name in func.prev_scope.symbols:
			self.slot = func.prev_scope.symbols[locator_name]
			if self.slot.type == slot.variable_slot:
				self.c_name = "__prev_scope__->" + locator_name
				self.locator_type = node_locator_expr.prev_scope_variable_type
				func.needs_prev_scope = True
				func.prev_scope.scope_needed = True
			else:
				self.c_name = self.slot.function_decl.get_c_name()
				self.locator_type = node_locator_expr.prev_scope_child_function_type
		elif func.compound and locator_name in func.compound.members:
			self.slot = func.compound.members[locator_name]
			if self.slot.is_variable():
				self.c_name = "__self_object__->" + locator_name
				self.locator_type = node_locator_expr.instance_variable_type
			elif self.slot.is_function():
				self.locator_type = node_locator_expr.method_type
				self.c_name = self.slot.function_decl.get_c_name()
			else:
				raise compile_error, (self, "member " + locator_name + " cannot be used here.")
		else:
			# search the global compound
			node = func.facet.find_node(func.compound, locator_name)
			if not node:
				raise compile_error, (self, "locator " + locator_name + " not found.")
			if node.is_compound():
				self.slot = slot(node, slot.reference_slot, locator_name, 0)
				self.locator_type = node_locator_expr.reference_type
				self.c_name = node.get_c_name()
			elif node.__class__ == node_variable:
				self.slot = slot(node, slot.variable_slot, locator_name, 0, node.type_spec)
				self.locator_type = node_locator_expr.global_variable_type
				self.c_name = node.get_c_name() + "." + locator_name
			elif node.__class__ == node_function:
				self.slot = slot(node, slot.function_slot, locator_name, 0, function_decl = node)
				self.locator_type = node_locator_expr.global_function_type
				self.c_name = node.get_c_name()
			else:
				raise compile_error, (self, "global node " + locator_name + " cannot be used as a locator.")

	def get_preferred_type_spec(self, func):
		self.resolve(func)
		return self.slot.type_spec

	def analyze(self, func, type_spec):
		self.resolve(func)
		self.slot.type_spec.check_conversion(type_spec)

	def analyze_lvalue(self, func, type_spec):
		self.resolve(func)
		if self.locator_type > node_locator_expr.last_lvalue_type:
			raise compile_error, (self, "Symbol " + self.string + " was not found or cannot be assigned a value.")

	def compile(self, func, result_symbol, type_spec):
		if self.slot.type_spec.is_equivalent(type_spec):
			if result_symbol is not None:
				func.append_code(result_symbol + " = " + self.c_name ";\n")
				return result_symbol
			else:
				return self.c_name
		else:
			if result_symbol is None:
				result_symbol = func.add_register(type_spec)
			func.append_type_conversion(self.c_name, self.locator_type, result_symbol, type_spec)
			return result_symbol

	def compile_lvalue(self, func):
		return self.c_name, self.locator_type


class selfmethod_global_expr(node_expression):
	# selfmethod_global evaluates to a declared global function, known to be a method callable
	# by the current self object.  This is used both for parent class constructor invocation
	# as well as [TBI] the special "super" object locator
	def compile(self, func, valid_types):
		return 'selfmethod_global', self.func_index

class node_int_constant_expr(node_expression):
	def analyze(self, func, result_type_specifier):
		if not result_type_specifier.is_numeric():
			raise compile_error, (self, "integer constant expression is not valid here.")
	def compile(self, func, result_symbol, type_spec):
		if result_symbol is None:
			result_symbol = func.add_register(type_spec)
		func.append_code(result_symbol + " = " + self.value + ";\n")
		return result_symbol

	def get_preferred_type_spec(self, func):
		return func.facet.builtin_type_spec_integer

class node_float_constant_expr(node_expression):
	def analyze(self, func, result_type_specifier):
		if not result_type_specifier.is_numeric():
			raise compile_error, (self, "floating point constant expression is not valid here.")
	def compile(self, func, result_symbol, type_spec):
		if result_symbol is None:
			result_symbol = func.add_register(type_spec)
		func.append_code(result_symbol + " = " + self.value + ";\n")
		return result_symbol
	def get_preferred_type_spec(self, func):
		return func.facet.builtin_type_spec_float

class node_string_constant(node_expression):
	def analyze(self, func, result_type_specifier):
		if not result_type_specifier.is_string():
			raise compile_error, (self, "string constant expression is not valid here.")
		self.string_index = func.facet.add_string_constant(self.value)
	def compile(self, func, result_symbol, type_spec):
		if result_symbol is None:
			result_symbol = func.add_register(type_spec)
		func.append_code(result_symbol + " = __string_constants[" + self.string_index + "];\n")
		return result_symbol
	def get_preferred_type_spec(self, func):
		return func.facet.builtin_type_spec_string

class node_strcat_expr(node_expression):
	op_table = { 'cat_none' : "", 'cat_newline' : "\n", 'cat_space' : " ", 'cat_tab' : "\t" }
	def get_cat_str(self):
		if self.op not in node_strcat_expr.op_table:
			raise compile_error, (self, "Unknown string cat operator" + str(self.op))
		return node_strcat_expr.op_table[self.op]

	def analyze(self, func, type_spec):
		func.facet.builtin_type_spec_string.check_conversion(type_spec)
		self.left.analyze(func, func.facet.builtin_type_spec_string)
		self.right.analyze(func, func.facet.builtin_type_spec_string)

	def compile(self, func, result_symbol, type_spec):
		if result_symbol is None:
			result_symbol = func.add_register(type_spec)
		left_symbol = self.left.compile(func, None, func.facet.builtin_type_spec_string)
		right_symbol = self.right.compile(func, None, func.facet.builtin_type_spec_string)
		func.append_code(result_symbol + " = format_string(\"%s%s%s\", " + left_symbol + ", " + self.get_cat_str() + ", " + right_symbol + ");\n")
		return result_symbol

	def get_preferred_type_spec(self, func):
		return func.facet.builtin_type_spec_string

class node_array_index_expr(node_expression):
	def __init__(self):
		node_expression.__init__(self)
		self.resolved = False
		self.container_type = None
		self.container_value_type = None
		self.container_key_type = None

	def resolve(self, func):
		if self.resolved:
			return
		self.resolved = 1
		self.container_type = self.array_expr.get_preferred_type()
		if not array_type.is_container():
			raise compile_error, (self, "this type is not a container.")
		self.container_value_type = array_type.get_container_value_type()
		self.container_key_type = array_type.get_container_key_type()

	def get_preferred_type_spec(self, func):
		self.resolve(func)
		return self.container_value_type

	def analyze(self, func, type_spec):
		self.resolve(func)
		self.array_expr.analyze(func, self.container_type)
		self.index_expr.analyze(func, self.container_key_type)
		self.container_value_type.check_conversion(type_spec)

	def analyze_lvalue(self, func, type_spec):
		self.analyze(func, type_spec)
		type_spec.check_conversion(self.container_value_type)

	def compile(self, func, result_symbol, type_spec):
		index_symbol = self.index_expr.compile(func, None, self.container_key_type)
		container_symbol = self.array_expr.compile(func, None, self.container_type)
		if result_symbol is None:
			result_symbol = func.add_register(type_spec)
		if self.container_value_type.is_equivalent(type_spec):
			func.append_code(result_symbol + " = " + container_symbol + "[" + index_symbol + "];\n")
		else:
			func.append_type_conversion(container_symbol + "[" + index_symbol + "]", self.container_value_type, result_symbol, type_spec)
		return result_symbol
	def compile_lvalue(self, func):
		index_symbol = self.index_expr.compile(func, None, self.container_key_type)
		container_symbol = self.array_expr.compile(func, None, self.container_type)
		return container_symbol + "[" + index_symbol + "]", self.container_value_type

class node_func_call_expr(node_expression):
	def analyze(self, func, type_spec):


		self.func_expr.analyze(func, ('callable'))
		for arg in self.args:
			arg.analyze(func, ('any'))
	def compile(self, func, valid_types):
		arg_array = []
		for arg in self.args:
			arg_array.append(arg.compile(func, ('any')) )
		return ('func_call', self.func_expr.compile(func, ('callable')), arg_array)

class node_method_call(node_func_call_expr):
	def analyze(self, func, valid_types):
		args = [pair.expr for pair in self.selector_list]
		sel_str = self.primary_name + "".join(str(pair.string if pair.string is not None else "") + ":" for pair in self.selector_list )
		print "Got selector: " + sel_str
		self.func_expr = node_slot_expr()
		self.func_expr.object_expr = self.object_expr
		self.func_expr.slot_name = sel_str
		self.args = args
		node_func_call_expr.analyze(self, func, valid_types)

class node_slot_expr(node_expression):
	def analyze(self, func, valid_types):
		object_expr = self.object_expr
		if(object_expr.__class__ == node_locator_expr and object_expr.string == 'parent'):
			# parent references a function slot in the parent class
			if not func.compound:
				raise compile_error, (self, "Function has no compound.")
			parent_node = func.compound.parent_node
			if parent_node is None:
				raise compile_error, (self, "compound " + func.compound.name + " has no declared parent.")
			if self.slot_name not in parent_node.members:
				raise compile_error, (self, "Parent of " + func.compound.name + " has no member named " + self.slot_name)
			slot = parent_record.members[expr.slot_name]
			if slot.type != 'function':
				raise compile_error, (self, "parent expression must reference a function.")
			self.parent_function = slot.function_decl
		else:
			self.object_expr.analyze(func, ('any'))
	def analyze_lvalue(self, func, valid_types):
		if(object_expr.__class__ == node_locator_expr and object_expr.string == 'parent'):
			raise compile_error, (self, "Parent call slot reference cannot be used as an l-value")
		self.object_expr.analyze(si, ('any'))
	def compile(self, func, expr, valid_types):
		if 'parent_function' in self.__dict__:
			return ('selfmethod_global', self.parent_function)
		else:
			return ('slot', self.object.expr.compile(func, ('any')), self.slot_name)

class node_unary_lvalue_op_expr(node_expression):
	def analyze(self, func, valid_types):
		self.expression.analyze_lvalue(func, ('number'))
	def compile(self, func, valid_types):
		return ('unary_lvalue_op', self.expression.compile(func, ('number')), self.op)

class node_unary_minus_expr(node_expression):
	def analyze(self, func, valid_types):
		self.expression.analyze(func, ('number'))
	def compile(self, func, valid_types):
		return ('unary_minus', self.expression.compile(func, ('number')))

class node_logical_not_expr(node_expression):
	def analyze(self, func, valid_types):
		self.expression.analyze(func, ('boolean'))
	def compile(self, func, valid_types):
		return ('logical_not', self.expression.compile(func, ('boolean')))

class node_bitwise_not_expr(node_expression):
	def analyze(self, func, valid_types):
		self.expression.analyze(func, ('integer'))
	def compile(self, func, valid_types):
		return ('bitwise_not', self.expression.compile(func, ('integer')))

class node_float_binary_expr(node_expression):
	def analyze(self, func, valid_types):
		self.left.analyze(func, ('number'))
		self.right.analyze(func, ('number'))
	def compile(self, func, valid_types):
		return ('float_binary', self.op,
			    self.left.compile(func, ('number')),
			    self.right.compile(func, ('number')))

class node_int_binary_expr(node_expression):
	def analyze(self, func, valid_types):
		self.left.analyze(func, ('integer'))
		self.right.analyze(func, ('integer'))
	def compile(self, si, valid_types):
		return ('int_binary', self.op,
				self.left.compile(si, ('integer')),
				self.right.compile(si, ('integer')))

class node_bool_binary_expr(node_expression):
	def analyze(self, si, valid_types):
		self.left.analyze(si, ('boolean'))
		self.right.analyze(si, ('boolean'))
	def compile(self, func, valid_types):
		return ('bool_binary', self.op,
				self.left.compile(func, ('boolean')),
				self.right.compile(func, ('boolean')))

class node_conditional_expr(node_expression):
	# test_expression, true_expression, false_expression
	def analyze(self, func, valid_types):
		self.test_expression.analyze(func, ('boolean'))
		self.true_expression.analyze(func, valid_types)
		self.false_expression.analyze(func, valid_types)
	def compile(self, func, valid_types):
		return ('conditional',
				self.test_expression.compile(func, ('boolean')),
				self.true_expression.compile(func, valid_types),
				self.false_expression.compile(func, valid_types))

class node_assign_expr(node_expression):
	def analyze(self, func, valid_types):
		self.left.analyze_lvalue(func, ('any'))
		self.right.analyze(func, ('any'))
	def compile(self, func, valid_types):
		return ('assign', self.left.compile(func, ('any')), self.right.compile(func, ('any')))

class node_float_assign_expr(node_expression):
	# left, right, op
	def analyze(self, func, valid_types):
		self.left.analyze_lvalue(func, ('number'))
		self.right.analyze(func, ('number'))
	def compile(self, func, valid_types):
		return ('float_assign', self.op, self.left.compile(func, ('number')), self.right.compile(func, ('number')))

class node_int_assign_expr(node_expression):
	# left, right, op
	def analyze(self, func, valid_types):
		self.left.analyze_lvalue(func, ('integer'))
		self.right.analyze(func, ('integer'))
	def compile(self, func, valid_types):
		return ('int_assign', expr.op, self.left.compile(func, ('integer')), self.right.compile(func, ('integer')))

class node_array_expr(node_expression):
	# array_values (list)
	def analyze(self, func, valid_types):
		for sub_expr in self.array_values:
			sub_expr.analyze(func, ('any'))
	def compile(self, func, valid_types):
		return ('array', [sub_expr.compile(func, ('any')) for sub_expr in self.array_values])

class node_map_expr(node_expression):
	# map_pairs (list)
	def analyze(self, func, valid_types):
		for pair in self.map_pairs:
			pair.key.analyze(func, ('any'))
			pair.value.analyze(func, ('any'))

	def map_expr_compile_(self, func, valid_types):
		return ('map', [(pair.key.compile(func, ('any'), False), pair.value.compile(func, ('any'), False)) for pair in self.map_pairs])

class node_map_pair(program_node):
	# key, value
	pass

