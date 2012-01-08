from kt_program_tree import *
from kt_program_function_decl import node_function
#from kt_facet import *

class slot:
	variable_slot = 0
	function_slot = 1

	def __init__(self, initial_node, type, name, index, type_spec = None, function_decl = None):
		self.name = name
		self.type = type
		self.index = index
		self.initial_node = initial_node
		self.function_decl = function_decl
		self.type_spec = type_spec
	def is_variable(self):
		return self.type == slot.variable_slot
	def is_function(self):
		return self.type == slot.function_slot
	def __str__(self):
		return "(" + str(self.type) + " " + self.name + ": " + str((self.index, self.function_decl, self.type_spec)) + ")"

class container_node (program_node):
	def __init__(self):
		program_node.__init__(self)
		self.contents = {}
		self.assignments = []
		self.constructor_index = None
		self.members = {} # members holds all the slots for a compound
		self.vtable = [] # vtable is a fast method lookup table.  Each method slot is assigned a vtable entry for
		# fast method dispatch
		self.members_origin_node = self
		self.slot_count = 0
		self.vtable_count = 0
		self.process_pass = 0
		
	def is_container(self):
		return True

	def get_c_classname(self):
		container_list = self.get_ancestry_list();
		return "_".join(x.name for x in container_list)

	def emit_classdef(self):
		parent_string = " : " + self.parent_node.get_c_classname() if self.parent_node is not None else ""
		emit_string = "struct " + self.get_c_classname() + parent_string + " {\n"
		for member in self.members.values():
			if member.initial_node == self:
				if member.type == slot.variable_slot:
					emit_string += member.type_decl.get_c_type_string() + " " + member.name + ";\n"
				elif member.type == slot.function_slot:
					emit_string += member.function_decl.emit_function()
		if self.constructor_decl is not None:
			emit_string += self.constructor_decl.emit_function()

		emit_string += "};\n"
		return emit_string

	def set_member_info_from(self, parent):
		self.members = parent.members
		self.vtable = parent.vtable
		self.slot_count = parent.slot_count
		self.vtable_count = parent.vtable_count
		
	def copy_member_info(self):
		self.members = self.members.copy()
		old_vtable = self.vtable
		self.vtable = [x for x in old_vtable]
		self.members_origin_node = self

	def find_slot(self, slot_name):
		return self.members[slot_name] if slot_name in self.members else None

	def add_member_variable(self, element):
		if self.members_origin_node != self:
			self.copy_member_info()
		the_slot = self.find_slot(element.name)
		if the_slot:
			raise compile_error, (element, "Variable " + element.name + " already declared.")
		slot_index = self.slot_count
		the_slot = slot(initial_node = self, type= slot.variable_slot, name = element.name, index=slot_index, type_spec=element.type_spec)
		self.members[the_slot.name] = the_slot
		self.slot_count += 1

		if element.assign_expr is not None:
			self.add_constructor_assignment(the_slot.index, element.assign_expr)

	def add_member_function(self, function_node, the_facet):
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
		self.members[function_node.name] = slot(initial_node = self, type=slot.function_slot,
		                                        name=function_node.name,index=vtable_index,
		                                        function_decl=function_node)
		if vtable_index == len(self.vtable):
			self.vtable.append(function_node)
		else:
			self.vtable[vtable_index] = function_node
		the_facet.add_function(function_node)

	def add_constructor_assignment(self, slot_index, assignment_expression):
		self.assignments.append((slot_index, assignment_expression))

	def build_constructor(self, the_facet):
		if len(self.assignments):
			constructor_decl = node_function()
			constructor_decl.name = '__constructor'
			constructor_decl.statements = []
			parent = self.parent_node
			if parent is not None and parent.constructor_index is not None:
				parent_stmt = node_expression_stmt()
				parent_stmt.expr = node_func_call_expr()
				parent_stmt.expr.func_expr = node_selfmethod_global_expr()
				parent_stmt.expr.func_expr.func_index = parent.constructor_index
				parent_stmt.expr.args = node.parent_decl[1]
				constructor_decl.statements.append(parent_stmt)
			for e in node.assignments:
				assign_stmt = node_initializer_stmt()
				assign_stmt.slot = e[0]
				assign_stmt.value = e[1]
			constructor_decl.parameter_list = node.parameter_list if 'parameter_list' in self.__dict__ else []
			self.constructor_decl = constructor_decl
			the_facet.add_function(constructor_decl)
		else:
			self.constructor_decl = None

	def analyze_container(self, the_facet):
		if self.process_pass == 1:
			raise compile_error, (self, "Error - compound " + self.name + " cannot be its own ancestor")
		elif self.process_pass == 0:
			self.process_pass = 1
			# check if it has a parent class, and process that one first.
			print "Processing compound: " + self.name
			parent = self.parent_decl[0] if 'parent_decl' in self.__dict__ and len(self.parent_decl) > 0 \
			else None
			if parent is not None:
				print "node: " + self.name + " has parent: " + parent
				parent_node = the_facet.find_node(self, parent)
				if parent_node is None:
					raise compile_error, (self, "Could not find parent " + parent + " for compound " + self.name)
				else:
					print "processing parent: " + parent_node.name
					parent_node.analyze_container(the_facet)
				self.parent_node = parent_node
			else:
				self.parent_node = None
			self.process_pass = 2
			the_facet.sorted_containers.append(self)
			# now that the parent node is processed, we can process this node
			self.assignments = []

			if self.parent_node is not None:
				self.set_member_info_from(self.parent_node)
				
			# first add any new functions and variable declarations
			for element in self.contents.values():
				if element.__class__ == node_variable:
					self.add_member_variable(element)
				elif element.__class__ == node_function:
					self.add_member_function(element, the_facet)

			# if is is a compound with a body, check for slot assignments
			if 'body' in self.__dict__:
				for assignment in (v for v in self.body if v.__class__ == node_slot_assignment):
					if assignment.name not in self.members:
						raise compile_error, (self, "Compound " + self.name + " does not have a slot named " +
						                         assignment.name)
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
			self.build_constructor(the_facet)
			print "node " + self.name + " processed - booyaka"


class node_object (container_node):
	pass

class node_class (container_node):
	pass

class node_builtin_class (container_node):
	def get_c_classname(self):
		return self.name

class node_builtin_slot (program_node):
	pass

class node_record (container_node):
	pass

class node_facet (node_object):
	pass

class node_connection (node_class):
	pass

class node_state (node_record):
	pass

class node_variable (program_node):
	def is_variable(self):
		return True

class node_transmission_specifier (program_node):
	pass

class node_slot_assignment(program_node):
	pass

