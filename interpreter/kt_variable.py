from kt_program_tree import *
from kt_statements import *
from kt_locator_expr import *

# node_variable can be contained in parameter lists, compounds and in functions as declaration statements
class node_variable(program_node):
	def __init__(self):
		program_node.__init__(self)
		self.slot_index = None
	def is_variable(self):
		return True
	def resolve_type(self, scope):
		if self.type_spec is None:
			self.type_spec = kt_globals.current_facet.builtin_type_spec_variable
		self.type_spec.resolve(scope)

	def analyze(self, func):
		self.resolve_type(func)
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
