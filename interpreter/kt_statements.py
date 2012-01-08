from kt_program_tree import *
from kt_expressions import *

class node_variable_declaration_stmt(program_node):
	def analyze(self, func):
		func.add_local_variable(self, self.name, self.type_spec)
		# if the statement has an assignment expression, generate an assignment statement for the assignment
		if self.assign_expr is not None:
			self.assign_stmt = node_expression_stmt()
			self.assign_stmt.expr = node_assign_expr()
			self.assign_stmt.expr.left = node_locator_expr()
			self.assign_stmt.expr.left.string = self.name
			self.assign_stmt.expr.right = self.assign_expr
			#print "  Adding assignment statement: " + str(assign_stmt)
			self.assign_stmt.analyze(func)
	def compile(self, func, continue_ip, break_ip):
		if self.assign_expr is not None:
			self.assign_stmt.compile(func, continue_ip, break_ip)

class node_continue_stmt(program_node):
	def analyze(self, func):
		if func.loop_count == 0:
			raise compile_error, (self, "continue not allowed outside of a loop.")
		func.ip += 1
	def compile(self, func, continue_ip, break_ip):
		func.compiled_statements.append(('branch_always', continue_ip))
		func.add_branch_target(continue_ip)


class node_break_stmt(program_node):
	def analyze(self, func):
		if func.loop_count == 0 and func.switch_count == 0:
			raise compile_error, (self, "break not allowed outside of a loop or switch.")
		func.ip += 1
	def compile(self, func, continue_ip, break_ip):
		func.compiled_statements.append(('branch_always', break_ip))
		func.add_branch_target(break_ip)


class node_return_stmt(program_node):
	def analyze(self, func):
		if func.return_type_list is None:
			func.return_type_list = [node_locator_type_specifier() for x in self.return_expression_list]
			for type_spec in func.return_type_list:
				type_spec.locator = 'variable'
				type_spec.analyze(func)
		if len(func.return_type_list) != len(self.return_expression_list):
			raise compile_error, (self, "all return points from a function must return the same number of arguments " \
			                            "and must match the number of return types if specified in the function " \
			                            "declaration.")
		for expr, type in zip(self.return_expression_list, func.return_type_list):
			expr.analyze(func, type)
			func.returns_value = True
		func.ip += 1
	def compile(self, func, continue_ip, break_ip):
		func.compiled_statements.append(('return', [x.compile(func, ('any')) for x in self.return_expression_list]))

class node_switch_stmt(program_node):
	def analyze(self, func):
		# save the expression result in a register

		self.expr_register = func.add_register()
		func.switch_count += 1
		# the basic form of the switch statement is to evaluate
		# the switch expression into the temporary register (first instruction)
		# then for each switch element there is either a branch test for the cases
		# followed by a branch always to the default case or out of the switch if there's
		# no default.
		func.ip += 2 + len(self.element_list)
		self.test_expression.analyze(func, ('any'))
		for element in self.element_list:
			for label in element.label_list:
				label.test_constant.analyze(func, ('any'))
			analyze_block(func, element.statement_list)
		if self.default_block is not None:
			self.default_block.analyze(func)
		self.break_ip = func.ip
		func.switch_count -= 1

	def compile(self, func, continue_ip, break_ip):
		switch_start = len(func.statements)
		test_register = self.expr_register
		func.compiled_statements.append( ('eval', ('assign', ('local', test_register), self.test_expression.compile(func, ('any')))))
		# reserve cascading statement list for the test expressions and final branch
		func.compiled_statements = func.compiled_statements + [None] * (len(self.element_list) + 1)
		index = 1

		def build_compare(expr):
			return ('bool_binary', 'compare_equal', ('local', test_register ), expr.compile(func, ('any')))

		for element in self.element_list:
			ip = len(func.compiled_statements)
			compile_block(func, element.statement_list, continue_ip, self.break_ip)
			label_list = element.label_list
			compare_expr = build_compare(label_list[0].test_constant)
			for label in label_list[1:]:
				compare_expr = ('bool_binary', 'logical_or', compare_expr, build_compare(label.test_constant))
			func.compiled_statements[switch_start + index] = ('branch_if_nonzero', ip, compare_expr)
			func.add_branch_target(ip)
			index += 1
		switch_end = len(func.compiled_statements)
		func.compiled_statements[switch_start + index] = ('branch_always', switch_end)
		func.add_branch_target(switch_end)
		if self.default_block is not None:
			compile_block(func, self.default_block, continue_ip, self.break_ip)

class node_switch_element(program_node):
	pass

class node_switch_label(program_node):
	pass

class node_if_stmt(program_node):
	def analyze(self, func):
		self.test_expression.analyze(func, ('bool'))
		func.ip += 1
		analyze_block(func, self.if_block)
		if 'else_block' in self.__dict__:
			func.ip += 1
			self.if_false_jump = func.ip
			analyze_block(func.ip, stmt.else_block)
			self.if_true_jump = func.ip
		else:
			self.if_false_jump = func.ip
	def compile(self, func, continue_ip, break_ip):
		func.compiled_statements.append(('branch_if_zero', self.if_false_jump, compile_boolean_expression(func, self.test_expression)))
		func.add_branch_target(self.if_false_jump)
		compile_block(func, self.if_block, continue_ip, break_ip)
		if 'else_block' in self.__dict__:
			func.compiled_statements.append(('branch_always', self.if_true_jump))
			func.add_branch_target(self.if_true_jump)
			compile_block(func, self.else_block, continue_ip, break_ip)

class node_while_stmt(program_node):
	def analyze(self, func):
		func.loop_count += 1
		self.test_expression.analyze(func, ('bool'))
		self.continue_ip = func.ip
		func.ip += 1
		analyze_block(func, self.statement_list)
		func.ip += 1
		self.break_ip = func.ip
		func.loop_count -= 1
	def compile(self, func, continue_ip, break_ip):
		func.compiled_statements.append(('branch_if_zero', self.break_ip, compile_boolean_expression(func, self.test_expression)))
		func.add_branch_target(self.break_ip)
		compile_block(func, self.statement_list, self.continue_ip, self.break_ip)

class node_do_while_stmt(program_node):
	def analyze(self, func):
		func.loop_count += 1
		self.start_ip = func.ip
		analyze_block(func, self.statement_list)
		self.continue_ip = func.ip
		func.ip += 1
		self.break_ip = func.ip
		self.test_expression.analyze(func, ('bool'))
		func.loop_count -= 1
	def compile(self, func, continue_ip, break_ip):
		compile_block(func, self.statement_list, self.continue_ip, self.break_ip)
		func.compiled_statements.append(('branch_if_nonzero', self.start_ip, compile_boolean_expression(func, self.test_expression)))
		func.add_branch_target(self.start_ip)

class node_for_stmt(program_node):
	def analyze(self, func):
		#print "for stmt" + str(stmt)
		func.loop_count += 1
		if 'variable_initializer' in self.__dict__:
			func.add_local_variable(self, self.variable_initializer, self.variable_type_spec)
		if 'init_expression' in self.__dict__:
			self.init_expression.analyze(func, ('any'))
			func.ip += 1
		loop_start_ip = func.ip
		self.test_expression.analyze(func, ('bool'))
		func.ip += 1
		analyze_block(func, self.statement_list)
		if 'end_loop_expression' in self.__dict__ and self.end_loop_expression is not None:
			self.continue_ip = func.ip
			self.end_loop_expression.analyze(func, ('any'))
			func.ip += 2
		else:
			self.continue_ip = loop_start_ip
		self.loop_start_ip = loop_start_ip
		self.break_ip = func.ip
		func.loop_count -= 1
	def compile(self, func, continue_ip, break_ip):
		if 'init_expression' in self.__dict__:
			func.compiled_statements.append(('eval', compile_void_expression(func, self.init_expression)))
		func.compiled_statements.append(('branch_if_zero', self.break_ip, self.test_expression.compile(func, ('boolean'))))
		func.add_branch_target(self.break_ip)
		compile_block(func, self.statement_list, self.continue_ip, self.break_ip)
		if 'end_loop_expression' in self.__dict__ and self.end_loop_expression is not None:
			func.compiled_statements.append(('eval', compile_void_expression(func, self.end_loop_expression)))
		func.compiled_statements.append(('branch_always', self.loop_start_ip))
		func.add_branch_target(self.loop_start_ip)

class node_expression_stmt(program_node):
	# expr
	def analyze(self, func):
		self.expr.analyze(func, ('any'))
		func.ip += 1

	def compile(self, func, continue_ip, break_ip):
		func.compiled_statements.append(('eval', compile_void_expression(func, self.expr)))

# initializer_stmt's are generated for constructors
class node_initializer_stmt(program_node):
	#slot
	##value
	def analyze(self, func):
		self.value.analyze(func, ('any'))
		func.ip += 1

	def compile(self, func, continue_ip, break_ip):
		func.compiled_statements.append(('eval', ('assign', ('ivar', self.slot),
									   self.value.compile(func, ('any')) )))

