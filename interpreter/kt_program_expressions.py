from kt_program_tree import *

def compile_boolean_expression(si, expr):
	return expr.compile(si, ('boolean'))

def compile_void_expression(si, expr):
	return expr.compile(si, ('any'))

class node_expression(program_node):
	def analyze(self, semantic_info, valid_types):
		pass
	def analyze_lvalue(self, semantic_info, valid_types):
		raise compile_error, (self, "Expression is not an l-value.")
		pass
	def compile(self, si, valid_types):
		pass

class node_locator_expr(node_expression):
	def analyze(self, si, valid_types):
		locator_name = self.string
		if locator_name in si.symbols:
			self.location = si.symbols[locator_name]
		elif si.prev_scope and locator_name in si.prev_scope.symbols:
			self.location = ('prev_scope', si.prev_scope.symbols[locator_name])
			si.needs_prev_scope = True
			si.prev_scope.scope_needed = True
		elif si.compound_node and locator_name in si.compound_node.members:
			member = si.compound_node.members[locator_name]
			if member.is_variable():
				self.location = ('ivar', member.index)
			elif member.is_function():
				self.location = ('imethod', member.index)
			else:
				raise compile_error, (self, "member " + locator_name + " cannot be used here.")
		else:
			# search the global container
			node = si.facet.find_node(si.compound_node, locator_name)
			if not node:
				raise compile_error, (self, "locator " + locator_name + " not found.")
			self.location = ('global_node', node)
	def analyze_lvalue(self, si, valid_types):
		locator_name = self.string
		if locator_name in si.symbols:
			self.location = si.symbols[locator_name]
		elif si.prev_scope and locator_name in si.prev_scope.symbols:
			self.location = ('prev_scope', si.prev_scope.symbols[locator_name])
			si.needs_prev_scope = True
			si.prev_scope.scope_needed = True
		elif si.compound_node and locator_name in si.compound_node.members:
			member = si.compound_node.members[locator_name]
			if member.is_variable():
				self.location = ('ivar', member.index)
			else:
				raise compile_error, (self, "member " + locator_name + " cannot be used as an l-value.")
		else:
			raise compile_error, (self, "Symbol " + locator_name + " was not found or cannot be assigned a value.")
	def compile(self, si, valid_types):
		#print str(expr)
		return self.location

class selfmethod_global_expr(node_expression):
	# selfmethod_global evaluates to a declared global function, known to be a method callable
	# by the current self object.  This is used both for parent class constructor invocation
	# as well as [TBI] the special "super" object locator
	def compile(self, si, valid_types):
		return 'selfmethod_global', self.func_index

class node_int_constant_expr(node_expression):
	def compile(self, si, valid_types):
		return 'int_constant', self.value

class node_float_constant_expr(node_expression):
	def compile(self, si, valid_types):
		return 'float_constant', self.value

class node_string_constant(node_expression):
	def compile(self, si, valid_types):
		index = si.facet.add_string_constant(self.value)
		return 'string_constant', index

class node_strcat_expr(node_expression):
	def analyze(self, si, valid_types):
		self.left.analyze(si, ('string'))
		self.right.analyze(si, ('string'))
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
	def compile(self, si, valid_types):
		return ('strcat', self.get_cat_str(), self.left.compile(si, ('string')), self.right.compile(si, ('string')))

class node_array_index_expr(node_expression):
	def analyze(self, si, valid_types):
		self.array_expr.analyze(si, ('any'))
		self.index_expr.analyze(si, ('any'))
	def analyze_lvalue(self, si, valid_types):
		self.analyze(si, valid_types)
	def compile(self, si, valid_types):
		return ('array_index', self.array_expr.compile(si, ('any')),
				self.index_expr.compile(si, ('any')))

class node_func_call_expr(node_expression):
	def analyze(self, si, valid_types):
		self.func_expr.analyze(si, ('callable'))
		for arg in self.args:
			arg.analyze(si, ('any'))
	def compile(self, si, valid_types):
		arg_array = []
		for arg in self.args:
			arg_array.append(arg.compile(si, ('any')) )
		return ('func_call', self.func_expr.compile(si, ('callable')), arg_array)

class node_method_call(node_func_call_expr):
	def analyze(self, si, valid_types):
		args = [pair.expr for pair in self.selector_list]
		sel_str = self.primary_name + "".join(str(pair.string if pair.string is not None else "") + ":" for pair in self.selector_list )
		print "Got selector: " + sel_str
		self.func_expr = node_slot_expr()
		self.func_expr.object_expr = self.object_expr
		self.func_expr.slot_name = sel_str
		self.args = args
		node_func_call_expr.analyze(self, si, valid_types)

class node_slot_expr(node_expression):
	def analyze(self, si, valid_types):
		object_expr = self.object_expr
		if(object_expr.__class__ == node_locator_expr and object_expr.string == 'parent'):
			# parent references a function slot in the parent class
			parent_node = si.compound_node.parent_node
			if parent_node is None:
				raise compile_error, (self, "Compound " + si.compound_node.name + " has no declared parent.")
			if self.slot_name not in parent_node.members:
				raise compile_error, (self, "Parent of " + si.compound_node.name + " has no member named " + self.slot_name)
			slot = parent_record.members[expr.slot_name]
			if slot.type != 'function':
				raise compile_error, (self, "parent expression must reference a function.")
			self.parent_function_index = slot.global_function_index
		else:
			self.object_expr.analyze(si, ('any'))
	def analyze_lvalue(self, si, valid_types):
		if(object_expr.__class__ == node_locator_expr and object_expr.string == 'parent'):
			raise compile_error, (self, "Parent call slot reference cannot be used as an l-value")
		self.object_expr.analyze(si, ('any'))
	def compile(self, si, expr, valid_types, is_lvalue):
		if 'parent_function_index' in self.__dict__:
			return ('selfmethod_global', self.parent_function_index)
		else:
			return ('slot', self.object.expr.compile(si, ('any')), self.slot_name)

class node_unary_lvalue_op_expr(node_expression):
	def analyze(self, si, valid_types):
		self.expression.analyze_lvalue(si, ('number'))
	def compile(self, si, valid_types):
		return ('unary_lvalue_op', self.expression.compile(si, ('number')), self.op)

class node_unary_minus_expr(node_expression):
	def analyze(self, si, valid_types):
		self.expression.analyze(si, ('number'))
	def compile(self, si, valid_types):
		return ('unary_minus', self.expression.compile(si, ('number')))

class node_logical_not_expr(node_expression):
	def analyze(self, si, valid_types):
		self.expression.analyze(si, ('boolean'))
	def compile(self, si, valid_types):
		return ('logical_not', self.expression.compile(si, ('boolean')))

class node_bitwise_not_expr(node_expression):
	def analyze(self, si, valid_types):
		self.expression.analyze(si, ('integer'))
	def compile(self, si, valid_types):
		return ('bitwise_not', self.expression.compile(si, ('integer')))

class node_float_binary_expr(node_expression):
	def analyze(self, si, valid_types):
		self.left.analyze(si, ('number'))
		self.right.analyze(si, ('number'))
	def compile(self, si, valid_types):
		return ('float_binary', self.op,
			    self.left.compile(si, ('number')),
			    self.right.compile(si, ('number')))

class node_int_binary_expr(node_expression):
	def analyze(self, si, valid_types):
		self.left.analyze(si, ('integer'))
		self.right.analyze(si, ('integer'))
	def compile(self, si, valid_types):
		return ('int_binary', self.op,
				self.left.compile(si, ('integer')),
				self.right.compile(si, ('integer')))

class node_bool_binary_expr(node_expression):
	def analyze(self, si, valid_types):
		self.left.analyze(si, ('boolean'))
		self.right.analyze(si, ('boolean'))
	def compile(self, si, valid_types):
		return ('bool_binary', self.op,
				self.left.compile(si, ('boolean')),
				self.right.compile(si, ('boolean')))

class node_conditional_expr(node_expression):
	# test_expression, true_expression, false_expression
	def analyze(self, si, valid_types):
		self.test_expression.analyze(si, ('boolean'))
		self.true_expression.analyze(si, valid_types)
		self.false_expression.analyze(si, valid_types)
	def compile(self, si, valid_types):
		return ('conditional',
				self.test_expression.compile(si, ('boolean')),
				self.true_expression.compile(si, valid_types),
				self.false_expression.compile(si, valid_types))

class node_assign_expr(node_expression):
	def analyze(self, si, valid_types):
		self.left.analyze_lvalue(si, ('any'))
		self.right.analyze(si, ('any'))
	def compile(self, si, valid_types):
		return ('assign', self.left.compile(si, ('any')), self.right.compile(si, ('any')))

class node_float_assign_expr(node_expression):
	# left, right, op
	def analyze(self, si, valid_types):
		self.left.analyze_lvalue(si, ('number'))
		self.right.analyze(si, ('number'))
	def compile(self, si, valid_types):
		return ('float_assign', self.op, self.left.compile(si, ('number')), self.right.compile(si, ('number')))

class node_int_assign_expr(node_expression):
	# left, right, op
	def analyze(self, si, valid_types):
		self.left.analyze_lvalue(si, ('integer'))
		self.right.analyze(si, ('integer'))
	def compile(self, si, valid_types):
		return ('int_assign', expr.op, self.left.compile(si, ('integer')), self.right.compile(si, ('integer')))

class node_array_expr(node_expression):
	# array_values (list)
	def analyze(self, si, valid_types):
		for sub_expr in self.array_values:
			sub_expr.analyze(si, ('any'))
	def compile(self, si, valid_types):
		return ('array', [sub_expr.compile(si, ('any')) for sub_expr in self.array_values])

class node_map_expr(node_expression):
	# map_pairs (list)
	def analyze(self, si, valid_types):
		for pair in self.map_pairs:
			pair.key.analyze(si, ('any'))
			pair.value.analyze(si, ('any'))

	def map_expr_compile_(self, si, valid_types):
		return ('map', [(pair.key.compile(si, ('any'), False), pair.value.compile(si, ('any'), False)) for pair in self.map_pairs])

class node_map_pair(program_node):
	# key, value
	pass

