from kt_program_tree import *
from kt_statements import node_return_stmt
from kt_slot import *
from kt_type_qualifier import *
import kt_globals

class node_parameter(program_node):
	def __init__(self):
		program_node.__init__(self)
		self.name = None
		self.type_spec = None
		self.member = None

class function_base (program_node):
	def __init__(self):
		program_node.__init__(self)
		self.return_type = None
		self.arg_count = 0
		self.parameter_list = None
		self.qualified_type = None
		self.return_type_qualifier = None
		self.prev_scope = None
		self.name = None
		self.c_name = None
		self.needs_closure = False

	def is_function(self):
		return True

	def resolve_c_name(self):
		if self.prev_scope is None:
			self.c_name = self.name
		else:
			self.c_name = self.prev_scope.c_name + "__X__" + self.name

	def get_closure_struct_name(self):
		return "__closure__" + self.c_name

	def analyze_signature_types(self):
		print("Analyzing signature of " + self.name)
		enclosing_scope = self.compound if self.compound is not None else self.prev_scope

		for arg in self.parameter_list:
			if arg.type_spec == None:
				arg.qualified_type = kt_globals.current_facet.type_dictionary.builtin_type_qualifier_variable
			else:
				arg.type_spec.resolve(enclosing_scope)
				arg.qualified_type = arg.type_spec.qualified_type
		if self.return_type is None:
			self.return_type_qualifier = kt_globals.current_facet.type_dictionary.builtin_type_qualifier_none
		else:
			self.return_type.resolve(enclosing_scope)
			self.return_type_qualifier = self.return_type.qualified_type

		arg_type_qualifier_list = [arg.qualified_type for arg in self.parameter_list]
		self.qualified_type = kt_globals.current_facet.type_dictionary.get_type_function(arg_type_qualifier_list, self.return_type_qualifier, self.needs_closure)


class node_builtin_function(function_base):
	pass

class node_builtin_method(function_base):
	pass

class node_function (function_base):
	class register:
		def __init__(self, type_qual):
			self.allocated_count = 0
			self.in_use = 0
			self.type_qual = type_qual

	def __init__(self):
		function_base.__init__(self)
		self.statements = None

		self.compiled_statements = ""
		self.structure_analyzed = False
		self.types_analyzed = False

		self.function_expr_count = 0
		self.loop_count = 0
		self.switch_count = 0
		self.register_count = 0
		self.local_variable_count = 0
		self.has_closure = False
		self.symbols = {}
		self.registers_by_type_id = {}
		self.child_functions = []
		self.instruction_list = [] # when function is evaluated, body statement tree becomes a linear instruction list
		self.branch_target_list = []
		self.references_instance_variables = False
		self.facet = None
		self.has_override = False
		self.parent_function = None
		self.is_class_function = False
		self.vtable_index = None

		self.registers_by_type_id = {}

	def get_type_signature(self):
		return None

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
			raise compile_error(ref_node, "Variable " + var_name + " is declared more than once.")
		self.symbols[var_name] = compound_member(ref_node, compound_member_types.slot, var_name, self.local_variable_count, var_type_spec)
		self.local_variable_count += 1
		print("Var decl: " + var_name)

	def add_child_function(self, func):
		func.prev_scope = self
		self.facet.add_function(func)

		if func.name in self.symbols:
			raise compile_error(func, "Symbol " + func.name + " is already declared in this scope.")

		self.symbols[func.name] = compound_member(self, compound_member_types.function, func.name, len(self.child_functions), None, func)
		self.child_functions.append(func)

	def add_register(self, register_type_qualifier):
		type_id = register_type_qualifier.id
		if type_id not in self.registers_by_type_id:
			self.registers_by_type_id[type_id] = node_function.register(register_type_qualifier)
		register = self.registers_by_type_id[type_id]
		register_symbol = "register_" + str(type_id) + "_" + str(register.in_use)
		register.in_use += 1
		if register.in_use <= register.allocated_count:
			return register_symbol
		register.allocated_count += 1
		return register_symbol

	# registers are allocated during the compile step, but must be declared sequentially before the function's code.

	def analyze_function_structure(self):
		print("..analyzing function structure of " + self.name)
		if len(self.statements) == 0 or self.statements[-1].__class__ is not node_return_stmt:
			return_stmt_decl = node_return_stmt()
			return_stmt_decl.return_expression_list = []
			self.statements.append(return_stmt_decl)
		self.analyze_block_structure(self.statements)
		print(self.name + " - structure analysis complete")

	def analyze_function_linkage(self):
		print("..analyzing function linkage of " + self.name)
		return_stmt_decl = None
		for arg in self.parameter_list:
			if arg.name in self.symbols:
				raise compile_error(self, "Argument " + arg.name + " is declared more than once.")
			arg.member = compound_member(self, compound_member_types.parameter, arg.name, self.arg_count, arg.type_spec)
			self.symbols[arg.name] = arg.member
			self.arg_count += 1
			#print "Arg: " + arg

		self.analyze_block_linkage(self.statements)
		print(self.name + " - linkage analysis complete")

	def analyze_types(self):
		if self.types_analyzed:
			return
		self.types_analyzed = True
		for member in self.symbols.values():
			member.assign_qualified_type(self)

		print("..analyzing types of function " + self.name)
		self.analyze_block_types(self.statements)
		print(self.name + " - types analysis complete")

	def analyze_block_linkage(self, statement_list):
		for stmt in statement_list:
			stmt.analyze_stmt_linkage(self)

	def analyze_block_structure(self, statement_list):
		for stmt in statement_list:
			stmt.analyze_stmt_structure(self)

	def analyze_block_types(self, statement_list):
		for stmt in statement_list:
			stmt.analyze_stmt_types(self)

	def append_code(self, the_string):
		self.code += the_string

	def append_type_conversion(self, source_symbol, source_type, destination_symbol, destination_type):
		# TODO: put in actual type conversion code
		self.append_code("type_convert(" + destination_symbol + ", " + source_symbol + ");\n")

	def compile_function(self):
		self.code = ""
		if self.has_closure:
			self.append_code("struct " + self.get_closure_struct_name() + " {\n")
			for member in self.symbols.values():
				if member.in_closure:
					self.append_code(member.qualified_type.emit_declaration(member.name) + ";\n")
			self.append_code("};\n")
		return_type_name = self.return_type_qualifier.c_name
		if self.return_type_qualifier.type_kind == type_qualifier.kind.none_type:
			return_type_name = "void"
		self.append_code("static " + return_type_name + " " + self.c_name + "(")
		if self.needs_closure:
			self.append_code(self.prev_scope.get_closure_struct_name() + " *__closure__" + ("," if len(self.parameter_list) > 0 else ""))
		self.append_code(",".join(arg.qualified_type.emit_declaration(arg.name) for arg in self.parameter_list) + ")\n{\n")
		if self.has_closure:
			self.append_code(self.get_closure_struct_name() + " __self_closure__;\n")
		for member in self.symbols.values():
			if member.member_type == compound_member_types.slot and not member.in_closure:
				self.append_code(member.qualified_type.emit_declaration(member.name) + ";\n")

		for member in self.symbols.values():
			if member.member_type == compound_member_types.parameter and member.in_closure:
				self.append_code("__self_closure__." + member.name + " = " + member.name + ";\n")

		#for member in self.symbols.values():
		#	self.append_code(member.qualified_type.emit_declaration(member.name) + ";\n")
		self.facet.emit_code(self.code)
		self.code = ""
		self.compile_block(self.statements, 0, 0)
		self.append_code("}\n")

		func_code = self.code
		self.code = ""

		for id, reg in self.registers_by_type_id.items():
			for i in range(0, reg.allocated_count):
				register_symbol = "register_" + str(id) + "_" + str(i)
				self.append_code(reg.type_qual.emit_declaration(register_symbol) + ";\n")

		self.facet.emit_code(self.code)
		self.facet.emit_code(func_code)

	def compile_block(self, statement_list, continue_label_id, break_label_id):
		for stmt in statement_list:
			stmt.compile(self, continue_label_id, break_label_id)

class node_function_declaration_stmt(node_function):
	def analyze_stmt_structure(self, func):
		func_name = self.name
		func.add_child_function(self)
	def analyze_stmt_linkage(self, func):
		pass
	def analyze_stmt_types(self, func): pass
	def compile(self, func, continue_label_id, break_label_id): pass

class node_function_expr(node_function):
	def __init__(self):
		node_function.__init__(self)
		self.expr = None

	def analyze_expr_structure(self, func):
		func.function_expr_count += 1
		self.name = "__func_expr_" + func.function_expr_count
		return_stmt = node_return_stmt()
		return_stmt.return_expression_list = (self.expr,)
		self.statements = [return_stmt]
		func.add_child_function(self)
	def analyze_expr_linkage(self, func):
		pass

	def analyze_expr_types(self, func, type_qual):
		self.signature_type_qualifier.check_conversion(type_qual)

	def compile(self, func, valid_types):
		return 'load_sub_function', self.result_register, self

class node_selector_pair(program_node):
	pass
