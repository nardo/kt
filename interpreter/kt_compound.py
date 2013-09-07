from kt_program_tree import *
from kt_variable import *
from kt_functions import *
from kt_declarations import *
from kt_facet import *
from kt_type_qualifier import *
import sys
import kt_globals

class node_slot_assignment(program_node):
	pass

class compound_node (program_node):
	kind_class = 0
	kind_object = 1
	kind_record = 2
	kind_facet = 3
	kind_connection = 4
	kind_state = 5

	def __init__(self):
		program_node.__init__(self)
		self.parentage_process = 0
		self.compound_id = -1

		self.contents = {}
		self.assignments = []
		self.constructor_decl = None

		self.members_origin_node = self
		self.members = {} # symbols holds all the slots (named variables and functions) for a compound
		self.vtable = [] # vtable is a fast method lookup table.  Each method slot is assigned a vtable entry for
		# fast method dispatch
		self.slot_count = 0
		self.vtable_count = 0
		self.compound_type_spec = None
		self.instance_type_spec = None

		self.compound_kind = None
		self.reference_kind = None
		self.qualified_type = None

	def is_compound(self):
		return True

	def set_member_info_from(self, parent):
		self.members_origin_node = parent
		self.members = parent.members
		self.vtable = parent.vtable
		self.slot_count = parent.slot_count
		self.vtable_count = parent.vtable_count

	def copy_member_info(self):
		self.members_origin_node = self
		self.members = self.members.copy()
		old_vtable = self.vtable
		self.vtable = [x for x in old_vtable]

	def find_slot(self, slot_name):
		return self.members[slot_name] if slot_name in self.members else None

	def add_member_variable(self, element):
		if self.members_origin_node != self:
			self.copy_member_info()
		if self.find_slot(element.name) is not None:
			raise compile_error, (element, "Variable " + element.name + " already declared.")
		self.members[element.name] = compound_member(self, compound_member_types.slot, element.name, self.slot_count, element.type_spec, None)
		self.slot_count += 1
		if element.assign_expr is not None:
			self.add_constructor_assignment(element)

	def add_member_function(self, function_node):
		if self.members_origin_node != self:
			self.copy_member_info()
		name = function_node.name
		parent_func = self.find_slot(name)
		if parent_func:
			#todo: check that the parent_func is not actually declared in this node (multiple definition)
			if parent_func.type != 'function':
				raise compile_error, (function_node, "Function " + name + " of " + function_node.name + " is already declared as a nonfunction")
			vtable_index = parent_func.vtable_index
			parent_func.has_override = True
		else:
			parent_func = None
			vtable_index = self.vtable_count
			self.vtable_count += 1
		self.members[function_node.name] = compound_member(initial_node = self, member_type = compound_member_types.function, name = function_node.name, index = vtable_index, function_decl = function_node)
		if vtable_index == len(self.vtable):
			self.vtable.append(function_node)
		else:
			self.vtable[vtable_index] = function_node
		kt_globals.current_facet.add_function(function_node)

	def add_constructor_assignment(self, slot):
		self.assignments.append(slot)

	def build_constructor(self):
		# if is is a compound with a body, check for slot assignments
		if 'body' in self.__dict__:
			for assignment in (v for v in self.body if v.__class__ == node_slot_assignment):
				if assignment.name not in self.members:
					raise compile_error, (self, "Compound " + self.name + " does not have a slot named " + assignment.name)
				else:
					the_slot = self.members[assignment.name]
					if the_slot.type != slot.variable_slot:
						raise compile_error, (self, "Member " + assignment.name + " of " + self.name + " is not an assignable slot.")
					self.add_constructor_assignment(the_slot.index, assignment.assign_expr)
		print "Compound " + self.name + ":"
		for slot_name, the_slot in self.members.iteritems():
			print the_slot
		#for assignment in node.assignments:
		#	print "  Assigns variable slot: " + str(assignment.slot_index) + " assign: " + str(assignment.assign_expr)
		if len(self.assignments):
			constructor_decl = node_function()
			constructor_decl.name = '__construct__' + self.name
			constructor_decl.statements = []
			parent = self.parent_node
			if parent is not None and parent.constructor_decl is not None:
				parent_stmt = node_expression_stmt()
				parent_stmt.expr = node_func_call_expr()
				parent_stmt.expr.func_expr = node_locator_expr()
				parent_stmt.expr.func_expr.string = parent.constructor_decl.name
				parent_stmt.expr.args = node.parent_decl[1]
				constructor_decl.statements.append(parent_stmt)
			for e in node.assignments:
				initializer_stmt = node_initializer_stmt()
				initializer_stmt.slot_assignment = e
				constructor_decl.statements.append(initializer_stmt)
			constructor_decl.parameter_list = node.parameter_list if 'parameter_list' in self.__dict__ else []
			self.constructor_decl = constructor_decl
			kt_globals.current_facet.add_function(constructor_decl)
		else:
			self.constructor_decl = None

	def connect_parentage_and_sort_compounds(self, the_facet):
		if self.parentage_process == 1:
			raise compile_error, (self, "Error - compound " + self.name + " cannot be its own ancestor")
		elif self.parentage_process == 2:
			return
		self.parentage_process = 1
		if 'parent_decl' in self.__dict__ and self.parent_decl.name is not None:
			print "node: " + self.name + " has parent: " + self.parent_decl.name
			parent_node = the_facet.find_node(self, self.parent_decl.name)
			if parent_node is None:
				raise compile_error, (self, "Could not find parent " + parent + " for compound " + self.name)
			else:
				parent_node.connect_parentage_and_sort_compounds(the_facet)
			self.parent_node = parent_node
		else:
			self.parent_node = None
		self.parentage_process = 2
		self.compound_id = len(the_facet.sorted_compounds)
		the_facet.sorted_compounds.append(self)

	def analyze_compound_structure(self, the_facet):
		# compounds get analyzed in order of sorted_compounds

		if self.parent_node is not None:
			self.set_member_info_from(self.parent_node)

		# first add any new functions and variable declarations
		for element in self.contents.values():
			if element.__class__ == node_slot_declaration:
				self.add_member_variable(element)
			elif element.__class__ == node_function:
				self.add_member_function(element)

		self.build_constructor()
		print "node " + self.name + " processed - booyaka"

	def assign_qualified_type(self, the_facet):
		# assign type_qualifiers for this compound
		if self.members_origin_node == self:
			# compounds get their own type_qualifier iff they introduce new members.  Otherwise they are functionally the same as their parent type.
			self.qualified_type = the_facet.type_dictionary.get_type_compound(self.compound_kind, self)
		else:
			self.qualified_type = self.members_origin_node.qualified_type

	def analyze_compound_types(self, the_facet):
		if self.members_origin_node == self:
			for member in self.members.values():
				member.assign_qualified_type(self)

	def get_c_classname(self):
		compound_list = self.get_compound_list();
		return "_".join(x.name for x in compound_list)

	def get_c_name(self):
		compound_list = self.get_compound_list()

	def emit_classdef(self):
		parent_string = " : " + self.parent_node.get_c_classname() if self.parent_node is not None else ""
		emit_string = "struct " + self.get_c_classname() + parent_string + " {\n"
		for member in self.members.values():
			print(member.name)
			if member.initial_node == self:
				if member.type == slot.variable_slot:
					emit_string += member.type_decl.get_c_type_string() + " " + member.name + ";\n"
				elif member.type == slot.function_slot:
					emit_string += member.function_decl.compile_function()
		if self.constructor_decl is not None:
			emit_string += self.constructor_decl.compile_function()

		emit_string += "};\n"
		return emit_string

