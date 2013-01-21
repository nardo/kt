from kt_slot import *
import kt_globals
#from kt_variable import *
#from kt_functions import *
from kt_types import *
from kt_locator_types import *

class resolved_location:
	def __init__(self):
		self.locator_type = None
		self.c_name = None
		self.type_spec = None
		self.slot = None
		self.node = None
		#elif self.locator_type == locator_types.reference_type:
		#self.type_spec = self.initial_node.get_reference_type_spec()

def resolve_locator(enclosing_scope, locator_name, program_node):
	location = resolved_location()
	if enclosing_scope.is_function():
		enclosing_compound = enclosing_scope.compound
		if locator_name in enclosing_scope.symbols:
			location.slot = enclosing_scope.symbols[locator_name]
			if location.slot.slot_type == slot_types.variable_slot_type:
				location.locator_type = locator_types.local_variable_type
				location.c_name = locator_name
			else:
				location.locator_type = locator_types.child_function_type
				location.c_name = location.slot.function_decl.get_c_name()
			return location
		elif enclosing_scope.prev_scope and locator_name in enclosing_scope.prev_scope.symbols:
			location.slot = enclosing_scope.prev_scope.symbols[locator_name]
			if location.slot.slot_type == slot_types.variable_slot_type:
				enclosing_scope.needs_prev_scope = True
				enclosing_scope.prev_scope.scope_needed = True
				location.locator_type = locator_types.prev_scope_variable_type
				location.c_name = "__prev_scope__->" + locator_name
			else:
				location.locator_type = locator_types.prev_scope_child_function_type
				location.c_name = location.slot.function_decl.get_c_name()
			return location
		elif enclosing_scope.compound and locator_name in enclosing_scope.compound.members:
			location.slot = enclosing_scope.compound.members[locator_name]
			if location.slot.is_variable():
				location.locator_type = locator_types.instance_variable_type
				location.c_name = "__self_object__->" + locator_name
			elif location.slot.is_function():
				location.locator_type = locator_types.method_type
				location.c_name = location.slot.function_decl.get_c_name()
			else:
				raise compile_error, (enclosing_scope, "member " + locator_name + " cannot be used here.")
			return location
	else:
		enclosing_compound = enclosing_scope
	# search the global compound
	node = kt_globals.current_facet.find_node(enclosing_compound, locator_name)
	if not node:
		raise compile_error, (program_node, "locator " + locator_name + " not found.")
	if node.is_compound():
		location.locator_type = locator_types.reference_type
		location.node = node
		location.c_name = node.get_c_name()
	elif node.type == "variable":
		location.locator_type = locator_types.global_variable_type
		location.node = node
		location.type_spec = node.type_spec
		location.c_name = node.get_c_name() + "." + locator_name
	elif node.type == "function":
		location.locator_type = locator_types.global_function_type
		location.node = node
		location.c_name = node.get_c_name()
	elif node.type == "builtin_type":
		location.locator_type = locator_types.builtin_type_type
		location.node = node
		location.c_name = node.get_c_name()
	else:
		raise compile_error, (program_node, "global node " + locator_name + " cannot be used as a locator.")
	return location

class node_locator_type_specifier(type_specifier):
	def __init__(self, locator = None):
		type_specifier.__init__(self)
		self.locator = locator
		self.resolved_locator = None
	def resolve(self, scope):
		if not self.resolved_locator:
			self.resolved_locator = resolve_locator(scope, self.locator, self)

		#	return
		#self.resolved = True
		#self.locator_slot, self.locator_type, self.locator_name = resolve_locator(scope, self.locator)
