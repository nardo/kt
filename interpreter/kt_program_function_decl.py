from kt_program_tree import *
from kt_program_statements import node_return_stmt

class node_function (program_node):
	def __init__(self):
		program_node.__init__(self)
		self.analyzed = False
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
		self.compiled_statements = []
		self.child_functions = []
		self.branch_targets = {}
		self.next_branch_target = 0
		self.references_instance_variables = False
		self.ip = 0 # instruction pointer
		self.returns_value = False
		self.facet = None
		self.has_override = False
		self.parent_function_index = None
		self.is_class_function = False
		self.index = None

	def is_function(self):
		return True

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

	def analyze_function(self, the_facet):
		if self.analyzed:
			return
		self.analyzed = True
		if self.parent_function_index is not None:
			parent_func_record = the_facet.get_function_by_index(self.parent_function_index)
		else:
			parent_func_record = None
		print str(self)

		return_stmt_decl = None
		for arg in self.parameter_list:
			if arg in self.symbols:
				raise compile_error, (decl, "Argument " + arg + " is declared more than once.")
			self.symbols[arg] = ('arg', self.arg_count)
			self.arg_count += 1
			#print "Arg: " + arg
		if len(self.statements) == 0 or self.statements[-1].__class__ is not node_return_stmt:
			return_stmt_decl = node_return_stmt()
			return_stmt_decl.return_expression_list = []
			self.statements.append(return_stmt_decl)
		analyze_block(self, self.statements)
		print self.name + " - analysis complete"

	def compile_function(self):
		self.next_branch_target = self.facet.next_label_id
		compile_block(self, self.statements, 0, 0)
		print self.name + "function compiles to:\n" + str(self)
		self.facet.next_label_id = self.next_branch_target

class node_function_declaration_stmt(node_function):
	def analyze(self, func):
		func_name = self.name
		#print "func decl: " + func_name
		if func_name in func.symbols:
			raise compile_error, (self, "Symbol " + func_name + " is already declared in this scope.")

		func.facet.add_function(self)
		self.prev_scope = func
		func.symbols[func_name] = ('sub_function', self.function_index)
		func.child_functions.append(self.function_index)
	def compile(self, func, continue_ip, break_ip):
		pass

class node_function_expr(node_function):
	def analyze(self, func, valid_types):
		func.function_expr_count += 1
		self.name = "__func_expr_" + func.function_expr_count
		return_stmt = node_return_stmt()
		return_stmt.return_expression_list = (self.expr,)
		self.statements = [return_stmt]
		self.prev_scope = func
		func.facet.add_function(self)

		func.symbols[self.name] = ('sub_function', self.function_index)
		func.child_functions.append(self.function_index)

		self.result_register = si.add_register()
		return self.result_register

	def compile(self, func, valid_types):
		return 'load_sub_function', self.result_register, self.function_index

class node_selector_pair(program_node):
	pass

