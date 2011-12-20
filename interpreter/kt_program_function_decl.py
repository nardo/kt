from kt_program_tree import *
from kt_program_statements import node_return_stmt

class semantic_info:
	def __init__(self, next_branch_target):
		self.function_expr_count = 0
		self.loop_count = 0
		self.switch_count = 0
		self.arg_count = 0
		self.register_count = 0
		self.local_variable_count = 0
		self.needs_prev_scope = False
		self.scope_needed = False
		self.prev_scope = None
		self.symbols = {}
		self.register_types = []
		self.statements = []
		self.child_functions = []
		self.branch_targets = {}
		self.next_branch_target = next_branch_target
		self.references_instance_variables = False
		self.ip = 0 # instruction pointer
		self.returns_value = False
		self.facet = None
	def add_branch_target(self, ip):
		self.branch_targets[ip] = self.next_branch_target
		self.next_branch_target += 1
	def add_local_variable(self, ref_node, var_name, var_type_spec):
		if var_name in self.symbols:
			raise compile_error, (ref_node, "Variable " + var_name + " is declared more than once.")
		self.symbols[var_name] = ('local', self.local_variable_count, var_type_spec)
		self.local_variable_count += 1
		print "Var decl: " + var_name
	def add_register(self, register_type_spec):
		register_index = self.register_count
		self.register_count += 1
		return register_index

class node_function (program_node):
	def __init__(self):
		program_node.__init__(self)
		self.arg_count = 0
		self.register_count = 0
		self.local_variable_count = 0
		self.compiled_statements = None
		self.has_override = False
		self.parent_function_index = None
		self.is_class_function = False
		self.index = None
		self.branch_targets = {}
		self.analyzed = False

	def set_from_semantic_info(self, si):
		self.arg_count = si.arg_count
		self.compiled_statements = si.statements
		self.branch_targets = si.branch_targets
		self.is_class_function = not si.references_instance_variables
		self.register_count = si.register_count
		self.local_variable_count = si.local_variable_count
		self.returns_value = si.returns_value

	def is_function(self):
		return True

	def set_parent_function_index(self, parent_index):
		self.parent_function_index = parent_index

	def __str__(self):
		ret = "Arg Count " + str(self.arg_count) + " Local Count " + str(self.local_variable_count) + " Register Count " + str(self.register_count) + "\n"
		i = 0
		if self.compiled_statements is not None:
			for s in self.compiled_statements:
				ret += str(i) + ": " + str(s) + "\n"
				i += 1
		for bt in self.branch_targets.keys():
			ret += "tg: " + str(bt) + "\n"
		return ret

	def analyze_function(self, enclosing_scope, the_facet):
		if self.analyzed:
			return
		self.analyzed = True
		si = semantic_info(the_facet.next_label_id)
		si.prev_scope = enclosing_scope
		si.compound_node = self.container
		si.facet = the_facet
		if self.parent_function_index is not None:
			parent_func_record = the_facet.get_function_by_index(self.parent_function_index)
		else:
			parent_func_record = None
		print str(self)
		for arg in self.parameter_list:
			if arg in si.symbols:
				raise compile_error, (decl, "Argument " + arg + " is declared more than once.")
			si.symbols[arg] = ('arg', si.arg_count)
			si.arg_count += 1
			#print "Arg: " + arg
		analyze_block(si, self.statements)
		compile_block(si, self.statements, 0, 0)
		if len(self.statements) == 0 or self.statements[-1].__class__ is not node_return_stmt:
			return_stmt_decl = node_return_stmt()
			return_stmt_decl.return_expression_list = []
			return_stmt_decl.analyze(si)
			return_stmt_decl.compile(si, 0, 0)

		self.set_from_semantic_info(si)
		the_facet.next_label_id = si.next_branch_target
		#analyze any sub functions
		print self.name + " - function compiles to:\n" + str(self)

		for func_index in si.child_functions:
			the_facet.get_function_by_index(func_index).analyze_function(si, the_facet)


class node_function_declaration_stmt(node_function):
	def analyze(self, si):
		func_name = self.name
		#print "func decl: " + func_name
		if func_name in si.symbols:
			raise compile_error, (self, "Symbol " + func_name + " is already declared in this scope.")

		function_index = si.facet.add_function(self)
		si.symbols[func_name] = ('sub_function', function_index)
		si.child_functions.append(function_index)
	def compile(self, si, continue_ip, break_ip):
		pass

class node_function_expr(program_node):
	def analyze(self, si, valid_types, is_lvalue):
		si.function_expr_count += 1
		decl = node_function()
		decl.name = "__func_expr_" + str(si.function_expr_count)
		decl.parameter_list = self.parameter_list
		return_stmt = node_return_stmt()
		return_stmt.return_expression_list = (self.expr,)
		decl.statements = [return_stmt]
		self.function_index = si.facet.add_function(decl)

		si.symbols[func_name] = ('sub_function', self.function_index)
		si.child_functions.append(self.function_index)

		self.result_register = si.add_register()
		return self.result_register

	def compile(self, si, valid_types, is_lvalue):
		return 'load_sub_function', self.result_register, self.function_index

class node_selector_pair(program_node):
    pass

