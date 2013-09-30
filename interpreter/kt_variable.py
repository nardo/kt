from kt_program_tree import *
from kt_statements import *
from kt_locator_expr import *

# node_slot_declaration declares a slot on a compound
class node_slot_declaration(program_node):
	def __init__(self):
		program_node.__init__(self)
		self.is_public = False
		self.is_shared = False
		self.name = None
		self.assign_expr = None
		self.type_spec = None
		self.slot_index = None

class node_variable_declaration_stmt(program_node):
	def __init__(self):
		program_node.__init__(self)
		self.is_shared = False
		self.name = None
		self.assign_expr = None
		self.type_spec = None
		self.assign_stmt = None

	def analyze_stmt_structure(self, func):
		func.add_local_variable(self, self.name, self.type_spec)
		# if the statement has an assignment expression, generate an assignment statement for the assignment
		if self.assign_expr is not None:
			self.assign_stmt = node_expression_stmt()
			self.assign_stmt.expr = node_assign_expr()
			self.assign_stmt.expr.left = node_locator_expr()
			self.assign_stmt.expr.left.string = self.name
			self.assign_stmt.expr.right = self.assign_expr
			#print "  Adding assignment statement: " + str(assign_stmt)
			self.assign_stmt.analyze_stmt_structure(func)

	def analyze_stmt_types(self, func):
		if self.assign_stmt is not None:
			self.assign_stmt.analyze_stmt_types(func)

	def compile(self, func, continue_label_id, break_label_id):
		if self.assign_stmt is not None:
			#func.append_code(self.type_spec.emit_declaration(self.name) + ";\n")
			self.assign_stmt.compile(func, continue_label_id, break_label_id)
