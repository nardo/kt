from kt_program_tree import *
from kt_functions import node_function
from kt_slot import *
from kt_compound import *

class node_object (compound_node):
	pass

class node_class (compound_node):
	pass

class node_builtin_class (compound_node):
	def get_c_classname(self):
		return self.name

class node_builtin_slot (program_node):
	pass

class node_record (compound_node):
	pass

class node_facet (node_object):
	pass

class node_connection (node_class):
	pass

class node_state (node_record):
	pass

class node_transmission_specifier (program_node):
	pass

