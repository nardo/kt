from kt_program_tree import *
from kt_functions import node_function
from kt_slot import *
from kt_compound import *
from kt_type_qualifier import *

class node_object (compound_node):
	def __init__(self):
		compound_node.__init__(self)
		self.compound_kind = compound_node.kind_object
		self.reference_kind = type_qualifier.kind.class_instance_type

class node_class (compound_node):
	def __init__(self):
		compound_node.__init__(self)
		self.compound_kind = compound_node.kind_class
		self.reference_kind = type_qualifier.kind.class_type

class node_builtin_class (compound_node):
	def __init__(self):
		compound_node.__init__(self)
		self.compound_kind = compound_node.kind_class
		self.reference_kind = type_qualifier.kind.class_type
	def get_c_classname(self):
		return self.name

class node_builtin_slot (program_node):
	pass

class node_record (compound_node):
	def __init__(self):
		compound_node.__init__(self)
		self.compound_kind = compound_node.kind_record
		self.reference_kind = type_qualifier.kind.record_type

class node_facet (node_object):
	def __init__(self):
		compound_node.__init__(self)
		self.compound_kind = compound_node.kind_facet
		self.reference_kind = type_qualifier.kind.class_instance_type

class node_connection (node_class):
	def __init__(self):
		compound_node.__init__(self)
		self.compound_kind = compound_node.kind_connection
		self.reference_kind = type_qualifier.kind.class_type

class node_state (node_record):
	def __init__(self):
		compound_node.__init__(self)
		self.compound_kind = compound_node.kind_state
		self.reference_kind = type_qualifier.kind.record_type

class node_parent_specifier (program_node):
	def __init__(self):
		program_node.__init__(self)
		self.name = None
		self.args = None

class node_transmission_specifier (program_node):
	pass

