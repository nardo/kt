from kt_expressions import *
from kt_locator import *

class node_locator_expr(node_expression):
	def __init__(self):
		node_expression.__init__(self)
		self.resolved_location = None
		#self.locator_type = locator_types.unknown_type
		#self.slot = None
		#self.resolved = False
		self.string = None
		self.c_name = None

	def resolve(self, func):
		if self.resolved_location:
			return
		self.resolved_location = resolve_locator(func, self.string, self)

	def get_preferred_type_spec(self, func):
		self.resolve(func)
		return self.resolved_location.slot.type_spec

	def analyze(self, func, type_spec):
		self.resolve(func)
		self.resolved_location.slot.type_spec.check_conversion(type_spec)

	def analyze_lvalue(self, func, type_spec):
		self.resolve(func)
		if self.resolved_location.locator_type > locator_types.last_lvalue_type:
			raise compile_error, (self, "Symbol " + self.string + " was not found or cannot be assigned a value.")

	def compile(self, func, result_symbol, type_spec):
		if self.resolved_location.slot.type_spec.is_equivalent(type_spec):
			if result_symbol is not None:
				func.append_code(result_symbol + " = " + self.resolved_location.c_name + ";\n")
				return result_symbol
			else:
				return self.resolved_location.c_name
		else:
			if result_symbol is None:
				result_symbol = func.add_register(self.resolved_location.type_spec)
			func.append_type_conversion(self.resolved_location.c_name, self.resolved_location.locator_type, result_symbol, type_spec)
			return result_symbol

	def compile_lvalue(self, func):
		return self.resolved_location.c_name, self.resolved_location.locator_type
