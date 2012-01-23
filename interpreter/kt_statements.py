from kt_program_tree import *
from kt_expressions import *
from kt_types import *

def goto_label(label_id):
	return "goto @l" + str(label_id) + ";\n"
def label(label_id):
	return "@l" + str(label_id) + ":\n"
class node_variable_declaration_stmt(program_node):
	def analyze(self, func):
		if self.type_spec is None:
			self.type_spec = node_locator_type_specifier("variable")
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
	def compile(self, func, continue_label_id, break_label_id):
		if self.assign_stmt is not None:
			func.append_code(self.type_spec.emit_declaration(self.name) + ";\n")
			self.assign_stmt.compile(func, continue_label_id, break_label_id)
class node_continue_stmt(program_node):
	def analyze(self, func):
		if func.loop_count == 0:
			raise compile_error, (self, "continue not allowed outside of a loop.")
	def compile(self, func, continue_label_id, break_label_id):
		func.append_code(goto_label(continue_label_id))
class node_break_stmt(program_node):
	def analyze(self, func):
		if func.loop_count == 0 and func.switch_count == 0:
			raise compile_error, (self, "break not allowed outside of a loop or switch.")
	def compile(self, func, continue_label_id, break_label_id):
		func.append_code(goto_label(break_label_id))
class node_return_stmt(program_node):
	def analyze(self, func):
		if len(self.return_expression_list) != len(func.return_type_list):
			raise compile_error, (self, "Returned element count does not match prior return statements and/or the function signature.")
		for expr, type in zip(self.return_expression_list, func.return_type_list):
			expr.analyze(func, type)
	def compile(self, func, continue_label_id, break_label_id):
		return_count = len(self.return_expression_list)
		if return_count == 0:
			func.append_code("return;\n")
		elif return_count == 1:
			#in this case, let the expression return the symbol for the returned value
			returned_symbol = self.return_expression_list[0].compile(func, None, func.return_type_list[0])
			func.append_code("return " + returned_symbol + ";\n")
		else:
			for index, pair in enumerate(zip(self.return_expression_list, func.return_type_list)):
				pair[0].compile(func, "__rv.rv_" + str(index), pair[1])
				func.append_code("return __rv;\n")

class node_switch_stmt(program_node):
	def analyze(self, func):
		# save the expression result in a register
		self.test_expression_type = self.test_expression.get_preferred_type()
		func.switch_count += 1
		# the basic form of the switch statement is to evaluate the switch expression into the temporary register (first instruction) then for each switch element there is either a branch test for the cases followed by a branch always to the default case or out of the switch if there's no default.
		self.test_expression.analyze(func, self.test_expression_type)
		for element in self.element_list:
			for label in element.label_list:
				label.test_constant.analyze(func, self.test_expression_type)
			func.analyze_block(element.statement_list)
		if self.default_block is not None:
			func.analyze_block(default_block)
		func.switch_count -= 1

	def compile(self, func, continue_label_id, break_label_id):
		test_register = func.alloc_register(self.test_expression_type)
		self.test_expression.compile(func, test_register, self.test_expression_type)
		self.end_label_id = func.get_next_label_id()
		for element in self.element_list:
			element.label_id = func.get_next_label_id()
			for label in label_list:
				comparator = label.test_constant.compile(func, None, self.test_expression_type)
				func.append_code("if(" + test_register + " == " + comparator + ") " + goto_label(element.label_id) + ";\n")
		if self.default_block is not None:
			func.compile_block(default_block, continue_label_id, self.end_label_id)
			func.append_code(goto_label(self.end_label_id))
		for element in self.element_list:
			func.append_code(label(element.label_id))
			func.compile_block(element.statement_list, continue_label_id, self.end_label_id)

class node_switch_element(program_node):
	pass

class node_switch_label(program_node):
	pass

class node_if_stmt(program_node):
	def analyze(self, func):
		self.test_expression.analyze(func, func.facet.builtin_type_spec_boolean)
		analyze_block(func, self.if_block)
		if 'else_block' in self.__dict__:
			analyze_block(func.ip, stmt.else_block)

	def compile(self, func, continue_label_id, break_label_id):
		else_block_label_id = func.get_next_label_id()
		symbol = self.test_expression.compile(None, func.facet.builtin_type_spec_boolean)
		func.append_code("if(!" + symbol + ") " + goto_label(else_block_label_id))
		func.compile_block(self.if_block, continue_label_id, break_label_id)
		if('else_block' in self.__dict__):
			end_if_label_id = func.get_next_label_id()
			func.append_code(goto_label(end_if_label_id) + label(else_block_label_id))
			func.compile_block(self.else_block, continue_label_id, break_label_id)
			func.append_code(label(end_if_label_id))
		else:
			func.append_code(label(else_block_label_id))

class node_while_stmt(program_node):
	def analyze(self, func):
		func.loop_count += 1
		self.test_expression.analyze(func, func.facet.builtin_type_spec_boolean)
		func.analyze_block(self.statement_list)
		func.loop_count -= 1
	def compile(self, func, continue_label_id, break_label_id):
		continue_label_id = func.get_next_label_id()
		break_label_id = func.get_next_label_id()
		func.append_code(label(continue_label_id))
		test_symbol = self.test_expression.compile(func, None, func.facet.builtin_type_spec_boolean)
		func.append_code("if(!" + test_symbol + ") " + goto_label(break_label_id))
		func.compile_block(self.statement_list, continue_label_id, break_label_id)
		func.append_code(label(break_label_id))

class node_do_while_stmt(program_node):
	def analyze(self, func):
		func.loop_count += 1
		analyze_block(func, self.statement_list)
		self.test_expression.analyze(func, func.facet.builtin_type_spec_boolean)
		func.loop_count -= 1
	def compile(self, func, continue_label_id, break_label_id):
		start_label_id = func.get_next_label_id()
		continue_label_id = func.get_next_label_id()
		break_label_id = func.get_next_label_id()
		func.append_code(label(start_label_id))
		func.compile_block(self.statement_list, continue_label_id, break_label_id)
		func.append_code(label(continue_label_id))
		test_symbol = self.test_expression.compile(func, None, func.facet.builtin_type_spec_boolean)
		func.append_code("if(" + test_symbol + ") " + goto_label(start_label_id) + label(break_label_id))

class node_for_stmt(program_node):
	def analyze(self, func):
		#print "for stmt" + str(stmt)
		func.loop_count += 1
		if 'variable_initializer' in self.__dict__:
			func.add_local_variable(self, self.variable_initializer, self.variable_type_spec)
		if 'init_expression' in self.__dict__:
			self.init_expression.analyze(func, func.facet.builtin_type_spec_none)
		self.test_expression.analyze(func, func.facet.builtin_type_spec_boolean)
		func.analyze_block(self.statement_list)
		if self.end_loop_expression is not None:
			self.end_loop_expression.analyze(func, func.facet.builtin_type_spec_none)
		func.loop_count -= 1
	def compile(self, func, continue_label_id, break_label_id):
		if 'init_expression' in self.__dict__:
			self.init_expression.compile(func, None, func.facet.builtin_type_spec_none)
		start_loop_label_id = func.get_next_label_id()
		break_label_id = func.get_next_label_id()
		if self.end_loop_expression is not None:
			continue_label_id = func.get_next_label_id()
		else:
			continue_label_id = start_loop_label_id
		func.append_code(label(start_loop_label_id))
		test_symbol = self.test_expression.compile(func, None, func.facet.builtin_type_spec_boolean)
		func.append_code("if(!" + test_symbol + ") " + goto_label(break_label_id))
		func.compile_block(self.statement_list, continue_label_id, break_label_id)
		if self.end_loop_expression is not None:
			func.append_code(label(continue_label_id))
			self.end_loop_expression.compile(func, None, func.facet.builtin_type_spec_none)
		func.append_code(goto_label(start_loop_label_id) + label(break_label_id))

class node_expression_stmt(program_node):
	# expr
	def analyze(self, func):
		self.expr.analyze(func, func.facet.builtin_type_spec_none)

	def compile(self, func, continue_label_id, break_label_id):
		self.expr.compile(func, None, func.facet.builtin_type_spec_none)

# initializer_stmt's are generated for constructors
class node_initializer_stmt(program_node):
	#slot
	def analyze(self, func):
		self.slot.assignment.analyze(func, slot.type_spec)

	def compile(self, func, continue_label_id, break_label_id):
		self.slot.assignment.compile(func, "this->" + self.slot.name, slot.type_spec)