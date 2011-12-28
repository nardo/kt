from kt_program_tree import *

def compile_boolean_expression(func, expr):
	return expr.compile(func, ('boolean'))

def compile_void_expression(func, expr):
	return expr.compile(func, ('any'))

class node_expression(program_node):
	def analyze(self, func, valid_types):
		pass
	def analyze_lvalue(self, func, valid_types):
		raise compile_error, (self, "Expression is not an l-value.")
		pass
	def compile(self, func, valid_types):
		pass

class node_locator_expr(node_expression):
	def analyze(self, func, valid_types):
		locator_name = self.string
		if locator_name in func.symbols:
			self.location = func.symbols[locator_name]
		elif func.prev_scope and locator_name in func.prev_scope.symbols:
			self.location = ('prev_scope', func.prev_scope.symbols[locator_name])
			func.needs_prev_scope = True
			func.prev_scope.scope_needed = True
		elif func.container and locator_name in func.container.members:
			member = func.container.members[locator_name]
			if member.is_variable():
				self.location = ('ivar', member.index)
			elif member.is_function():
				self.location = ('imethod', member.index)
			else:
				raise compile_error, (self, "member " + locator_name + " cannot be used here.")
		else:
			# search the global container
			node = func.facet.find_node(func.container, locator_name)
			if not node:
				raise compile_error, (self, "locator " + locator_name + " not found.")
			self.location = ('global_node', node)
	def analyze_lvalue(self, func, valid_types):
		locator_name = self.string
		if locator_name in func.symbols:
			self.location = func.symbols[locator_name]
		elif func.prev_scope and locator_name in func.prev_scope.symbols:
			self.location = ('prev_scope', func.prev_scope.symbols[locator_name])
			func.needs_prev_scope = True
			func.prev_scope.scope_needed = True
		elif func.container and locator_name in func.container.members:
			member = func.container.members[locator_name]
			if member.is_variable():
				self.location = ('ivar', member.index)
			else:
				raise compile_error, (self, "member " + locator_name + " cannot be used as an l-value.")
		else:
			raise compile_error, (self, "Symbol " + locator_name + " was not found or cannot be assigned a value.")
	def compile(self, func, valid_types):
		#print str(expr)
		return self.location

class selfmethod_global_expr(node_expression):
	# selfmethod_global evaluates to a declared global function, known to be a method callable
	# by the current self object.  This is used both for parent class constructor invocation
	# as well as [TBI] the special "super" object locator
	def compile(self, func, valid_types):
		return 'selfmethod_global', self.func_index

class node_int_constant_expr(node_expression):
	def compile(self, func, valid_types):
		return 'int_constant', self.value

class node_float_constant_expr(node_expression):
	def compile(self, func, valid_types):
		return 'float_constant', self.value

class node_string_constant(node_expression):
	def analyze(self, func, valid_types):
		self.string_index = func.facet.add_string_constant(self.value)

	def compile(self, func, valid_types):
		return 'string_constant', string_index

class node_strcat_expr(node_expression):
	def analyze(self, func, valid_types):
		self.left.analyze(func, ('string'))
		self.right.analyze(func, ('string'))
	def get_cat_str(self):
		str_op = self.op
		if str_op == 'cat_none':
			return ""
		elif str_op == 'cat_newline':
			return "\n"
		elif str_op == 'cat_space':
			return " "
		elif str_op == 'cat_tab':
			return "\t"
		else:
			raise compile_error, (self, "Unknown string cat operator" + str(str_op))
	def compile(self, func, valid_types):
		return ('strcat', self.get_cat_str(), self.left.compile(func, ('string')), self.right.compile(func, ('string')))

class node_array_index_expr(node_expression):
	def analyze(self, func, valid_types):
		self.array_expr.analyze(func, ('any'))
		self.index_expr.analyze(func, ('any'))
	def analyze_lvalue(self, func, valid_types):
		self.analyze(func, valid_types)
	def compile(self, func, valid_types):
		return ('array_index', self.array_expr.compile(func, ('any')),
				self.index_expr.compile(func, ('any')))

class node_func_call_expr(node_expression):
	def analyze(self, func, valid_types):
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
			if not func.container:
				raise compile_error, (self, "Function has no container.")
			parent_node = func.container.parent_node
			if parent_node is None:
				raise compile_error, (self, "Container " + func.container.name + " has no declared parent.")
			if self.slot_name not in parent_node.members:
				raise compile_error, (self, "Parent of " + func.container.name + " has no member named " + self.slot_name)
			slot = parent_record.members[expr.slot_name]
			if slot.type != 'function':
				raise compile_error, (self, "parent expression must reference a function.")
			self.parent_function_index = slot.global_function_index
		else:
			self.object_expr.analyze(func, ('any'))
	def analyze_lvalue(self, func, valid_types):
		if(object_expr.__class__ == node_locator_expr and object_expr.string == 'parent'):
			raise compile_error, (self, "Parent call slot reference cannot be used as an l-value")
		self.object_expr.analyze(si, ('any'))
	def compile(self, func, expr, valid_types):
		if 'parent_function_index' in self.__dict__:
			return ('selfmethod_global', self.parent_function_index)
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

