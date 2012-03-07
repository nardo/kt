from kt_program_tree import *
from kt_statements import node_return_stmt
from kt_slot import *

class function_base (program_node):
	def __init__(self):
		program_node.__init__(self)
		self.return_type = None
		self.arg_count = 0

	def is_function(self):
		return True

class node_builtin_function(function_base):
	pass

class node_builtin_method(function_base):
	pass

class node_function (function_base):
	class register:
		def __init__(self):
			self.allocated_count = 0
			self.in_use = 0

	def __init__(self):
		function_base.__init__(self)
		self.analyzed = False
		self.function_expr_count = 0
		self.loop_count = 0
		self.switch_count = 0
		self.register_count = 0
		self.local_variable_count = 0
		self.needs_prev_scope = False
		self.scope_needed = False
		self.prev_scope = None
		self.symbols = {}
		self.registers_by_type_id = {}
		self.child_functions = []
		self.references_instance_variables = False
		self.facet = None
		self.has_override = False
		self.parent_function = None
		self.is_class_function = False
		self.vtable_index = None
		self.return_type = None

	def get_type_signature(self):
		return None

	def get_c_name(self):
		if self.prev_scope is None:
			return self.name
		else:
			return self.prev_scope.get_c_name() + "__X__" + self.name

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

	def get_next_label_id(self):
		label_id = self.facet.next_label_id
		self.facet.next_label_id += 1
		return label_id

	def add_local_variable(self, ref_node, var_name, var_type_spec):
		if var_name in self.symbols:
			raise compile_error, (ref_node, "Variable " + var_name + " is declared more than once.")
		self.symbols[var_name] = slot(ref_node, slot.variable_slot, var_name, self.local_variable_count, var_type_spec)
		self.local_variable_count += 1
		print "Var decl: " + var_name

	def add_child_function(self, func):
		func.prev_scope = self
		self.facet.add_function(func)

		if func.name in self.symbols:
			raise compile_error, (func, "Symbol " + func.name + " is already declared in this scope.")

		self.symbols[func.name] = slot(self, slot.function_slot, func.name, len(self.child_functions), self, None, func)
		self.child_functions.append(func)

	def add_register(self, register_type_spec):
		type_id = register_type_spec.get_type_id()
		if type_id not in registers_by_type_id:
			registers_by_type_id[type_id] = node_function.register()
		register = registers_by_type_id[type_id]
		register.in_use += 1
		register_symbol = "register_" + type_id + "_" + register.in_use
		if register.in_use <= register.allocated_count:
			return register_symbol
		register.allocated_count += 1
		self.append_code(register_type_spec.emit_declaration(register_symbol) + ";\n")
		return register_symbol

	def analyze_function(self, the_facet):
		if self.analyzed:
			return
		self.analyzed = True

		print "..analyzing function " + self.name
		return_stmt_decl = None
		for arg in self.parameter_list:
			if arg.name in self.symbols:
				raise compile_error, (self, "Argument " + arg.name + " is declared more than once.")
			self.symbols[arg.name] = ('arg', self.arg_count)
			if arg.type_spec == None:
				arg.type_spec = node_locator_type_specifier()
				arg.type_spec.locator = "variable"
			self.arg_count += 1
			#print "Arg: " + arg
		if len(self.statements) == 0 or self.statements[-1].__class__ is not node_return_stmt:
			return_stmt_decl = node_return_stmt()
			return_stmt_decl.return_expression_list = []
			self.statements.append(return_stmt_decl)

		self.analyze_block(self.statements)
		print self.name + " - analysis complete"

	def analyze_block(self, statement_list):
		for stmt in statement_list:
			stmt.analyze(self)

	def append_code(self, the_string):
		self.code += the_string
	def append_type_conversion(self, source_symbol, source_type, destination_symbol, destination_type):
		# TODO: put in actual type conversion code
		self.append_code(destination_symbol + " = " + source_symbol + ";\n")

	def compile_function(self):
		self.code = ""
		return_type_name = self.return_type.get_c_typename()
		append_code(return_type_name + " " + self.name + "(" + ", ".join(arg.type_spec.emit_declaration(arg.name) for arg in self.parameter_list) + ")\n{\n")
		self.compile_block(self.statements, 0, 0)
		append_code("}\n")

		# now emit the child functions
		for child in self.child_functions:
			append_code(child.function_decl.compile_function())

		return self.code

	def compile_block(self, statement_list, continue_label_id, break_label_id):
		for stmt in statement_list:
			stmt.compile(self, continue_label_id, break_label_id)

class node_function_declaration_stmt(node_function):
	def analyze(self, func):
		func_name = self.name
		func.add_child_function(self)

class node_function_expr(node_function):
	def analyze(self, func, valid_types):
		func.function_expr_count += 1
		self.name = "__func_expr_" + func.function_expr_count
		return_stmt = node_return_stmt()
		return_stmt.return_expression_list = (self.expr,)
		self.statements = [return_stmt]
		func.add_child_function(self)

	def compile(self, func, valid_types):
		return 'load_sub_function', self.result_register, self

class node_selector_pair(program_node):
	pass

class node_parameter(program_node):
	pass
