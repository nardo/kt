from kt_program_tree import *
from kt_program_expressions import *

class node_variable_declaration_stmt(program_node):
	def analyze(self, si):
		si.add_local_variable(self, self.name, self.type_spec)
		# if the statement has an assignment expression, generate an assignment statement for the assignment
		if self.assign_expr is not None:
			self.assign_stmt = node_expression_stmt()
			self.assign_stmt.expr = node_assign_expr()
			self.assign_stmt.expr.left = node_locator_expr()
			self.assign_stmt.expr.left.string = self.name
			self.assign_stmt.expr.right = self.assign_expr
			#print "  Adding assignment statement: " + str(assign_stmt)
			self.assign_stmt.analyze(si)
	def compile(self, si, continue_ip, break_ip):
		if self.assign_expr is not None:
			self.assign_stmt.compile(si, continue_ip, break_ip)

class node_continue_stmt(program_node):
	def analyze(self, si):
		if si.loop_count == 0:
			raise compile_error, (self, "continue not allowed outside of a loop.")
		si.ip += 1
	def compile(self, si, continue_ip, break_ip):
		si.statements.append(('branch_always', continue_ip))
		si.add_branch_target(continue_ip)


class node_break_stmt(program_node):
	def analyze(self, si):
		if si.loop_count == 0 and si.switch_count == 0:
			raise compile_error, (self, "break not allowed outside of a loop or switch.")
		si.ip += 1
	def compile(self, si, continue_ip, break_ip):
		si.statements.append(('branch_always', break_ip))
		si.add_branch_target(break_ip)


class node_return_stmt(program_node):
	def analyze(self, si):
        # todo: typecheck the return expressions against the function signature
		for expr in self.return_expression_list:
			expr.analyze(si, ('any'))
			si.returns_value = True
		si.ip += 1
	def compile(self, si, continue_ip, break_ip):
		si.statements.append(('return', [x.compile(si, ('any')) for x in self.return_expression_list]))

class node_switch_stmt(program_node):
	def analyze(self, si):
		# save the expression result in a register

		self.expr_register = si.add_register()
		si.switch_count += 1
		# the basic form of the switch statement is to evaluate
		# the switch expression into the temporary register (first instruction)
		# then for each switch element there is either a branch test for the cases
		# followed by a branch always to the default case or out of the switch if there's
		# no default.
		si.ip += 2 + len(self.element_list)
		self.test_expression.analyze(si, ('any'))
		for element in self.element_list:
			for label in element.label_list:
				label.test_constant.analyze(si, ('any'))
			analyze_block(si, element.statement_list)
		if self.default_block is not None:
			self.default_block.analyze(si)
		self.break_ip = si.ip
		si.switch_count -= 1

	def compile(self, si, continue_ip, break_ip):
		switch_start = len(si.statements)
		test_register = self.expr_register
		si.statements.append( ('eval', ('assign', ('local', test_register), self.test_expression.compile(si, ('any')))))
		# reserve cascading statement list for the test expressions and final branch
		si.statements = si.statements + [None] * (len(self.element_list) + 1)
		index = 1

		def build_compare(expr):
			return ('bool_binary', 'compare_equal', ('local', test_register ), expr.compile(si, ('any')))

		for element in self.element_list:
			ip = len(si.statements)
			compile_block(si, element.statement_list, continue_ip, self.break_ip)
			label_list = element.label_list
			compare_expr = build_compare(label_list[0].test_constant)
			for label in label_list[1:]:
				compare_expr = ('bool_binary', 'logical_or', compare_expr, build_compare(label.test_constant))
			si.statements[switch_start + index] = ('branch_if_nonzero', ip, compare_expr)
			si.add_branch_target(ip)
			index += 1
		switch_end = len(si.statements)
		si.statements[switch_start + index] = ('branch_always', switch_end)
		si.add_branch_target(switch_end)
		if self.default_block is not None:
			compile_block(si, self.default_block, continue_ip, self.break_ip)

class node_switch_element(program_node):
	pass

class node_switch_label(program_node):
	pass

class node_if_stmt(program_node):
	def analyze(self, si):
		self.test_expression.analyze(si, ('bool'))
		si.ip += 1
		analyze_block(si, self.if_block)
		if 'else_block' in self.__dict__:
			si.ip += 1
			self.if_false_jump = si.ip
			analyze_block(si, stmt.else_block)
			self.if_true_jump = si.ip
		else:
			self.if_false_jump = si.ip
	def compile(self, si, continue_ip, break_ip):
		si.statements.append(('branch_if_zero', self.if_false_jump, compile_boolean_expression(si, self.test_expression)))
		si.add_branch_target(self.if_false_jump)
		compile_block(si, self.if_block, continue_ip, break_ip)
		if 'else_block' in self.__dict__:
			si.statments.append(('branch_always', self.if_true_jump))
			si.add_branch_target(self.if_true_jump)
			compile_block(si, self.else_block, continue_ip, break_ip)

class node_while_stmt(program_node):
	def analyze(self, si):
		si.loop_count += 1
		self.test_expression.analyze(si, ('bool'))
		self.continue_ip = si.ip
		si.ip += 1
		analyze_block(si, self.statement_list)
		si.ip += 1
		self.break_ip = si.ip
		si.loop_count -= 1
	def compile(self, si, continue_ip, break_ip):
		si.statements.append(('branch_if_zero', self.break_ip, compile_boolean_expression(si, self.test_expression)))
		si.add_branch_target(self.break_ip)
		compile_block(si, self.statement_list, self.continue_ip, self.break_ip)

class node_do_while_stmt(program_node):
	def analyze(self, si):
		si.loop_count += 1
		self.start_ip = si.ip
		analyze_block(si, self.statement_list)
		self.continue_ip = si.ip
		si.ip += 1
		self.break_ip = si.ip
		self.test_expression.analyze(si, ('bool'))
		si.loop_count -= 1
	def compile(self, si, continue_ip, break_ip):
		compile_block(si, self.statement_list, self.continue_ip, self.break_ip)
		si.statements.append(('branch_if_nonzero', self.start_ip, compile_boolean_expression(si, self.test_expression)))
		si.add_branch_target(self.start_ip)

class node_for_stmt(program_node):
	def analyze(self, si):
		#print "for stmt" + str(stmt)
		si.loop_count += 1
		if 'variable_initializer' in self.__dict__:
			si.add_local_variable(self, self.variable_initializer, self.variable_type_spec)
		if 'init_expression' in self.__dict__:
			self.init_expression.analyze(si, ('any'))
			si.ip += 1
		loop_start_ip = si.ip
		self.test_expression.analyze(si, ('bool'))
		si.ip += 1
		analyze_block(si, self.statement_list)
		if 'end_loop_expression' in self.__dict__ and self.end_loop_expression is not None:
			self.continue_ip = si.ip
			self.end_loop_expression.analyze(si, ('any'))
			si.ip += 2
		else:
			self.continue_ip = loop_start_ip
		self.loop_start_ip = loop_start_ip
		self.break_ip = si.ip
		si.loop_count -= 1
	def compile(self, si, continue_ip, break_ip):
		if 'init_expression' in self.__dict__:
			si.statements.append(('eval', compile_void_expression(si, self.init_expression)))
		si.statements.append(('branch_if_zero', self.break_ip, self.test_expression.compile(si, ('boolean'))))
		si.add_branch_target(self.break_ip)
		compile_block(si, self.statement_list, self.continue_ip, self.break_ip)
		if 'end_loop_expression' in self.__dict__ and self.end_loop_expression is not None:
			si.statements.append(('eval', compile_void_expression(si, self.end_loop_expression)))
		si.statements.append(('branch_always', self.loop_start_ip))
		si.add_branch_target(self.loop_start_ip)

class node_expression_stmt(program_node):
	# expr
	def analyze(self, si):
		self.expr.analyze(si, ('any'))
		si.ip += 1

	def compile(self, si, continue_ip, break_ip):
		si.statements.append(('eval', compile_void_expression(si, self.expr)))

# initializer_stmt's are generated for constructors
class node_initializer_stmt(program_node):
    #slot
    #value
	def analyze(self, si):
		self.value.analyze(si, ('any'))
		si.ip += 1

	def compile(self, si, continue_ip, break_ip):
		si.statements.append(('eval', ('assign', ('ivar', self.slot),
									   self.value.compile(si, ('any')) )))

