from kt_program_tree import *
from kt_expressions import *
from kt_types import *

class node_continue_stmt(program_node):
	def analyze_stmt_structure(self, func):
		if func.loop_count == 0:
			raise compile_error, (self, "continue not allowed outside of a loop.")
	def analyze_stmt_linkage(self, func):
		pass
	def analyze_stmt_types(self, func):
		pass
	def compile(self, func, continue_label_id, break_label_id):
		func.append_code(goto_label(continue_label_id))

class node_break_stmt(program_node):
	def analyze_stmt_structure(self, func):
		if func.loop_count == 0 and func.switch_count == 0:
			raise compile_error, (self, "break not allowed outside of a loop or switch.")
	def analyze_stmt_linkage(self, func):
		pass
	def analyze_stmt_types(self, func):
		pass

	def compile(self, func, continue_label_id, break_label_id):
		func.append_code(goto_label(break_label_id))

class node_return_stmt(program_node):
	def __init__(self):
		program_node.__init__(self)
		self.return_expression = None
	def analyze_stmt_structure(self, func):
		if func.return_type is None:
			# if there is a return expression the return type is variable - else the return type is empty_type.
			if self.return_expression is not None:
				func.return_type = node_locator_type_specifier("variable")

	def analyze_stmt_linkage(self, func):
		if self.return_expression is not None:
			self.return_expression.analyze_expr_linkage(func)

	def analyze_stmt_types(self, func):
		if func.return_type_qualifier == func.facet.type_dictionary.builtin_type_qualifier_none and self.return_expression is not None:
			raise compile_error, (self, "Function returning none cannot return a value")
		if func.return_type_qualifier != func.facet.type_dictionary.builtin_type_qualifier_none and self.return_expression is None:
			raise compile_error, (self, "Function should return a value here")

		if self.return_expression is not None:
			self.return_expression.analyze_expr_types(func, func.return_type)

	def compile(self, func, continue_label_id, break_label_id):
		if self.return_expression is None:
			func.append_code("return;\n")
		else:
			returned_symbol = self.return_expression.compile(func, None, func.return_type_qualifier)
			func.append_code("return " + returned_symbol + ";\n")

class node_switch_stmt(program_node):
	def __init__(self):
		program_node.__init__(self)
		self.element_list = None
		self.default_block = None
		self.test_expression = None
		self.test_expression_type_qualifier = None

	# the basic form of the switch statement is to evaluate the switch expression into the temporary register (first instruction) then for each switch element there is either a branch test for the cases followed by a branch always to the default case or out of the switch if there's no default.

	def analyze_stmt_structure(self, func):
		func.switch_count += 1
		for element in self.element_list:
			func.analyze_block_structure(element.statement_list)
		if self.default_block is not None:
			func.analyze_block_structure(self.default_block)
		func.switch_count -= 1

	def analyze_stmt_linkage(self, func):
		self.test_expression.analyze_expr_linkage(func)
		for element in self.element_list:
			for label in element.label_list:
				label.test_constant.analyze_expr_linkage(func)
			func.analyze_block_linkage(element.statement_list)
		if self.default_block is not None:
			func.analyze_block_linkage(self.default_block)

	def analyze_stmt_types(self, func):
		# save the expression result in a register
		self.test_expression_type_qualifier = self.test_expression.get_preferred_type_qualifier()
		self.test_expression.analyze_expr_types(func, self.test_expression_type_qualifier)
		for element in self.element_list:
			for label in element.label_list:
				label.test_constant.analyze_expr_types(func, self.test_expression_type_qualifier)
			func.analyze_block_types(element.statement_list)
		if self.default_block is not None:
			func.analyze_block_types(self.default_block)

	def compile(self, func, continue_label_id, break_label_id):
		test_register = func.alloc_register(self.test_expression_type_qualifier)
		self.test_expression.compile(func, test_register, self.test_expression_type_qualifier)
		self.end_label_id = func.get_next_label_id()
		for element in self.element_list:
			element.label_id = func.get_next_label_id()
			for label in element.label_list:
				comparator = label.test_constant.compile(func, None, self.test_expression_type_qualifier)
				func.append_code("if(" + test_register + " == " + comparator + ") " + goto_label(element.label_id) + ";\n")
		if self.default_block is not None:
			func.compile_block(self.default_block, continue_label_id, self.end_label_id)
			func.append_code(goto_label(self.end_label_id))
		for element in self.element_list:
			func.append_code(label(element.label_id))
			func.compile_block(element.statement_list, continue_label_id, self.end_label_id)

class node_switch_element(program_node):
	pass

class node_switch_label(program_node):
	pass

class node_if_stmt(program_node):
	def __init__(self):
		program_node.__init__(self)
		self.test_expression = None
		self.if_block = None
		self.else_block = None

	def analyze_stmt_structure(self, func):
		func.analyze_block_structure(self.if_block)
		if self.else_block is not None:
			func.analyze_block_structure(self.else_block)

	def analyze_stmt_linkage(self, func):
		self.test_expression.analyze_expr_linkage(func)
		func.analyze_block_linkage(self.if_block)
		if self.else_block is not None:
			func.analyze_block_linkage(self.else_block)

	def analyze_stmt_types(self, func):
		self.test_expression.analyze_expr_types(func, func.facet.type_dictionary.builtin_type_qualifier_boolean)
		func.analyze_block_types(self.if_block)
		if self.else_block is not None:
			func.analyze_block_types(self.else_block)

	def compile(self, func, continue_label_id, break_label_id):
		else_block_label_id = func.get_next_label_id()
		symbol = self.test_expression.compile(func, None, func.facet.type_dictionary.builtin_type_qualifier_boolean)
		func.append_code("if(!" + symbol + ") " + goto_label(else_block_label_id))
		func.compile_block(self.if_block, continue_label_id, break_label_id)
		if(self.else_block is not None):
			end_if_label_id = func.get_next_label_id()
			func.append_code(goto_label(end_if_label_id) + label(else_block_label_id))
			func.compile_block(self.else_block, continue_label_id, break_label_id)
			func.append_code(label(end_if_label_id))
		else:
			func.append_code(label(else_block_label_id))

class node_while_stmt(program_node):
	def __init__(self):
		program_node.__init__(self)
		self.test_expression = None
		self.statement_list = None

	def analyze_stmt_structure(self, func):
		func.loop_count += 1
		func.analyze_block_structure(self.statement_list)
		func.loop_count -= 1

	def analyze_stmt_linkage(self, func):
		self.test_expression.analyze_expr_linkage(func)
		func.analyze_block_linkage(self.statement_list)

	def analyze_stmt_types(self, func):
		self.test_expression.analyze_expr_types(func, func.facet.builtin_type_qualifier_boolean)
		func.analyze_block_types(self.statement_list)

	def compile(self, func, continue_label_id, break_label_id):
		continue_label_id = func.get_next_label_id()
		break_label_id = func.get_next_label_id()
		func.append_code(label(continue_label_id))
		test_symbol = self.test_expression.compile(func, None, func.facet.builtin_type_qualifier_boolean)
		func.append_code("if(!" + test_symbol + ") " + goto_label(break_label_id))
		func.compile_block(self.statement_list, continue_label_id, break_label_id)
		func.append_code(label(break_label_id))

class node_do_while_stmt(program_node):
	def __init__(self):
		program_node.__init__(self)
		self.statement_list = None
		self.test_expression = None

	def analyze_stmt_structure(self, func):
		func.loop_count += 1
		func.analyze_block_structure(self.statement_list)
		func.loop_count -= 1

	def analyze_stmt_linkage(self, func):
		func.analyze_block_linkage(self.statement_list)
		self.test_expression.analyze_expr_linkage(func)

	def analyze_stmt_types(self, func):
		func.analyze_block_types(self.statement_list)
		self.test_expression.analyze_expr_types(func, func.facet.builtin_type_qualifier_boolean)

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
	def __init__(self):
		program_node.__init__(self)
		self.variable_initializer = None
		self.variable_type_spec = None
		self.init_expression = None
		self.test_expression = None
		self.end_loop_expression = None
		self.statement_list = None

	def analyze_stmt_structure(self, func):
		#print "for stmt" + str(stmt)
		func.loop_count += 1
		func.analyze_block_structure(self.statement_list)
		func.loop_count -= 1

	def analyze_stmt_linkage(self, func):
		#print "for stmt" + str(stmt)
		if self.variable_initializer is not None:
			func.add_local_variable(self, self.variable_initializer, self.variable_type_spec)
		if self.init_expression is not None:
			self.init_expression.analyze_expr_linkage(func)
		if self.end_loop_expression is not None:
			self.end_loop_expression.analyze_expr_linkage(func)
		self.test_expression.analyze_expr_linkage(func)
		func.analyze_block_linkage(self.statement_list)

	def analyze_stmt_types(self, func):
		#print "for stmt" + str(stmt)
		if self.init_expression is not None:
			self.init_expression.analyze_expr_types(func, func.facet.type_dictionary.builtin_type_qualifier_none)
		self.test_expression.analyze_expr_types(func, func.facet.type_dictionary.builtin_type_qualifier_boolean)
		func.analyze_block_types(self.statement_list)
		if self.end_loop_expression is not None:
			self.end_loop_expression.analyze_expr_types(func, func.facet.type_dictionary.builtin_type_qualifier_none)

	def compile(self, func, continue_label_id, break_label_id):
		if 'init_expression' in self.__dict__:
			self.init_expression.compile(func, None, func.facet.type_dictionary.builtin_type_qualifier_none)
		start_loop_label_id = func.get_next_label_id()
		break_label_id = func.get_next_label_id()
		if self.end_loop_expression is not None:
			continue_label_id = func.get_next_label_id()
		else:
			continue_label_id = start_loop_label_id
		func.append_code(label(start_loop_label_id))
		test_symbol = self.test_expression.compile(func, None, func.facet.type_dictionary.builtin_type_qualifier_boolean)
		func.append_code("if(!" + test_symbol + ") " + goto_label(break_label_id))
		func.compile_block(self.statement_list, continue_label_id, break_label_id)
		if self.end_loop_expression is not None:
			func.append_code(label(continue_label_id))
			self.end_loop_expression.compile(func, None, func.facet.type_dictionary.builtin_type_qualifier_none)
		func.append_code(goto_label(start_loop_label_id) + label(break_label_id))

class node_expression_stmt(program_node):
	def __init__(self):
		program_node.__init__(self)
		self.expr = None

	def analyze_stmt_structure(self, func):
		pass

	def analyze_stmt_linkage(self, func):
		self.expr.analyze_expr_linkage(func)

	def analyze_stmt_types(self, func):
		self.expr.analyze_expr_types(func, func.facet.type_dictionary.builtin_type_qualifier_none)

	def compile(self, func, continue_label_id, break_label_id):
		self.expr.compile(func, None, func.facet.type_dictionary.builtin_type_qualifier_none)

# initializer_stmt's are generated for constructors
class node_initializer_stmt(program_node):
	def __init__(self):
		program_node.__init__(self)
		self.slot_assignment = None
		self.slot = None

	def analyze_stmt_structure(self, func):
		pass

	def analyze_linkage(self, func):
		# verify that self.slot_assignment.name is in the current compound
		self.slot = None #FIXME
		self.slot_assignment.assign_expr.analyze_structure(func)

	def analyze_types(self, func):
		self.slot_assignment.assign_expr.analyze_types(func, self.slot.type_qualifier)

	def compile(self, func, continue_label_id, break_label_id):
		self.slot_assignment.assign_expr.compile(func, "this->" + self.slot.name, slot.type_spec)