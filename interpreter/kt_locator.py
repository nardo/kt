from kt_slot import *
import kt_globals
#from kt_variable import *
#from kt_functions import *
from kt_locator_types import *
from kt_program_tree import *

class resolved_location:
	def __init__(self):
		self.locator_type = None
		self.compound_member = None
		self.node = None

	def get_type_qualifier(self):
		if self.locator_type <= locator_types.prev_scope_child_function:
			return self.compound_member.qualified_type
		else:
			return self.node.qualified_type

	def get_c_name(self):
		if self.locator_type == locator_types.local_variable or self.locator_type == locator_types.local_parameter:
			if self.compound_member.in_closure:
				return "__self_closure__." + self.compound_member.name
			else:
				return self.compound_member.name
		elif self.locator_type == locator_types.child_function or self.locator_type == locator_types.prev_scope_child_function or self.locator_type == locator_types.method:
			if self.node is not None:
				return self.node.get_c_name()
			else:
				return self.compound_member.function_decl.c_name
		elif self.locator_type == locator_types.prev_scope_variable or self.locator_type == locator_types.prev_scope_parameter:
			return "__closure__->" + self.compound_member.name
		elif self.locator_type == locator_types.instance_variable:
			if self.node is not None:
				return self.node.get_c_name() + "." + self.compound_member.name
			else:
				return "__self_object__->" + self.compound_member.name
		elif self.locator_type == locator_types.builtin_type:
			return self.node.get_c_name()
		elif self.locator_type == locator_types.builtin_function:
			return self.node.c_name




def resolve_locator(enclosing_scope, locator_name, program_node):
	location = resolved_location()
	enclosing_compound = enclosing_scope.compound

	if enclosing_scope.is_function():
		if locator_name in enclosing_scope.symbols:
			location.compound_member = enclosing_scope.symbols[locator_name]
			if location.compound_member.member_type == compound_member_types.slot:
				location.locator_type = locator_types.local_variable
			elif location.compound_member.member_type == compound_member_types.parameter:
				location.locator_type = locator_types.local_parameter
			else:
				location.locator_type = locator_types.child_function
			return location
		elif enclosing_scope.prev_scope and locator_name in enclosing_scope.prev_scope.symbols:
			location.compound_member = enclosing_scope.prev_scope.symbols[locator_name]
			if location.compound_member.member_type == compound_member_types.slot:
				enclosing_scope.needs_closure = True
				enclosing_scope.prev_scope.has_closure = True
				location.compound_member.in_closure = True
				location.locator_type = locator_types.prev_scope_variable
			elif location.compound_member.member_type == compound_member_types.parameter:
				enclosing_scope.needs_closure = True
				enclosing_scope.prev_scope.has_closure = True
				location.compound_member.in_closure = True
				location.locator_type = locator_types.prev_scope_parameter
			else:
				location.locator_type = locator_types.prev_scope_child_function
			return location
		elif enclosing_compound and locator_name in enclosing_compound.members:
			location.compound_member = enclosing_compound.members[locator_name]
			if location.compound_member.member_type == compound_member_types.slot:
				location.locator_type = locator_types.instance_variable
			else:
				location.locator_type = locator_types.method
			#@else:
			#	raise compile_error, (enclosing_scope, "member " + locator_name + " cannot be used here.")
			return location
	else:
		enclosing_compound = enclosing_scope
	# search the global compound
	node = kt_globals.current_facet.find_node(enclosing_compound, locator_name)
	if not node:
		raise compile_error, (program_node, "locator " + locator_name + " not found.")
	locator_name_part = locator_name.rpartition('/')[2]
	if node.is_compound():
		location.locator_type = locator_types.reference
		location.node = node
	elif node.type == "variable":
		location.locator_type = locator_types.instance_variable
		location.node = node.compound
		location.compound_member = location.node.members.find(node.name)
	elif node.type == "function":
		location.locator_type = locator_types.method
		location.node = node.compound
		location.compound_member = location.node.members.find(node.name)
	elif node.type == "builtin_type":
		location.locator_type = locator_types.builtin_type
		location.node = node
		# location.type_specifier = node.get_type_specifier()
	elif node.type == "builtin_function":
		location.locator_type = locator_types.builtin_function
		location.node = node
	else:
		raise compile_error, (program_node, "global node " + locator_name + " cannot be used as a locator.")
	return location

class node_locator_type_specifier(program_node):
	def __init__(self, locator = None):
		program_node.__init__(self)
		self.locator = locator
		self.resolved_location = None
		self.qualified_type = None
	def resolve(self, scope):
		self.resolved_location = resolve_locator(scope, self.locator, self)
		# verify that this location is a valid type
		if self.resolved_location.locator_type < locator_types.reference:
			raise compile_error, (self, "locator \"" + self.locator + "\" is not a valid type name.")
		self.qualified_type = self.resolved_location.node.qualified_type

	def get_qualified_type(self):
		if self.resolved_location.locator_type <= locator_types.prev_scope_child_function:
			self.qualified_type = self.resolved_location.compound_member.qualified_type
		elif self.resolved_location == locator_types.reference:
			self.qualified_type = self.resolved_location.node.qualified_type
		elif self.resolved_location.locator_type == locator_types.builtin_type:
			self.qualified_type = self.resolved_location.node.qualified_type

		#	return
		#self.resolved = True
		#self.locator_slot, self.locator_type, self.locator_name = resolve_locator(scope, self.locator)
