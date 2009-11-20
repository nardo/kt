# kt_compiler.py
# functionality for converting a kt program tree into an analyzed, executable form
# (C) 2009 Mark Frohnmayer.  The use of this code is governed by its license.  See /license/info.txt in the source distribution for the full license agreement.

import os
import stat
import kt
from kt_file_tree import *

# general error exception thrown by the compiler if given incorrect input
class compile_error:
	def __init__(self, node_where, error_string):
		self.node_where = node_where
		self.error_string = error_string

def compiler_warning(node_where, warning_string):
	print "Warning!: " + warning_string

compound_node_types = ('object', 'class', 'struct')

def iterate_tree(t):
		for sub_object in t.contents.values():
			for x in iterate_tree(sub_object):
				yield x
		yield t

def build_jump_table(the_object, prefix):
    the_map = {}
    for pair in the_object.__dict__.iteritems():
        if pair[0].startswith(prefix):
            split_string = pair[0].partition(prefix)
            the_map[split_string[2]] = pair[1]
    return the_map

def common_list_length(list1, list2):
	i = 0
	while i < len(list1) and i < len(list2) and list1[i] == list2[i]:
		i += 1
	return i


class image:
	def __init__(self, file_tree, image_name):
		self.image_name = image_name
		self.globals = {}
		self.globals_list = []
		self.functions = []
		self.globals_by_id = []
		root = image.tree_node(None, "root", 'object', { 'name': '', 'type' : 'object' } )
		self.add_global(root)
		self.tree = root
		self.analyze_stmt_jump_table = build_jump_table(image, '_analyze_stmt_')
		self.compile_stmt_jump_table = build_jump_table(image, '_compile_stmt_')
		self.analyze_expr_jump_table = build_jump_table(image, '_analyze_expr_')
		self.compile_expr_jump_table = build_jump_table(image, '_compile_expr_')

	class tree_node:
		def __init__(self, container, name, type, decl):
			self.parent_node = None
			self.container = container
			self.contents = {}
			self.assignments = []
			self.constructor_index = None
			self.name = name
			self.type = type
			self.decl = decl
			self.index = None
			self.func_record = None
			self.compound_record = None
			self.process_pass = 0
		def dump(self, level = 0):
			container = self.container.name if self.container is not None else "tree root"
			print "  " * level + self.name + " is " + self.type + " contained by " + container
			print "  " * level + " " + str(self.decl)
			for v in self.contents.values():
				v.dump(level + 1)
		def is_compound(self):
			return self.type in compound_node_types
		def is_function(self):
			return self.type == 'function'
		def get_ancestry_list(self):
			if self.container is None:
				return [self]
			else:
				return self.container.get_ancestry_list() + [self]
	
	class compound_record:
		def __init__(self, origin_node):
			self.members = {}
			self.vtable = []
			self.slot_count = 0
			self.vtable_count = 0
			self.origin_node = origin_node
		
		def copy_from(self, the_info):
			self.members = the_info.members.copy()
			self.vtable = [x for x in the_info.vtable]
			self.slot_count = the_info.slot_count
			self.vtable_count = the_info.vtable_count

	class slot:
		def __init__(self, type, name, index, global_function_index=0,type_index=0):
			self.name = name
			self.type = type
			self.index = index
			self.global_function_index = global_function_index
			self.type_index = type_index	
		def __str__(self):
			return "(" + self.type + " " + self.name + ": " + str((self.index, self.global_function_index, self.type_index)) + ")"
		
	class func_record:
		def __init__(self, decl, node, node_vtable_index):
			self.decl = decl
			self.node = node
			self.node_vtable_index = node_vtable_index
			self.arg_count = 0
			self.register_count = 0
			self.statements = None
			self.parent_function_index = None
			self.is_class_function = False
		def set(self, si):
			self.arg_count = si.arg_count
			self.statements = si.statements
			self.is_class_function = not si.references_instance_variables
			self.register_count = si.register_count
		def set_parent_function_index(self, parent_index):
			self.parent_function_index = parent_index
		def __str__(self):
			ret = "Arg Count " + str(self.arg_count) + " Register Count " + str(self.register_count) + "\n"
			i = 0
			for s in self.statements:
				ret += str(i) + ": " + str(s) + "\n"
				i += 1
			return ret

	def check_compound_record_unique(self, node):
		# each compound 
		if node.compound_record.origin_node != node:
			new_info = image.compound_record(node)
			new_info.copy_from(node.compound_record)
			node.compound_record = new_info

	def add_slot(self, node, element):
		self.check_compound_record_unique(node)
		info = node.compound_record
		the_slot = self.find_slot(node, element.name)
		if the_slot:
			raise compile_error, (element.decl, "Variable " + element.name + " already declared.")
		slot_index = info.slot_count
		the_slot = image.slot(type='variable',name = element.name, index=slot_index, type_index=self.get_type_spec(element.decl))
		info.members[the_slot.name] = the_slot
		info.slot_count += 1
		
		if(element.decl['assign_expr'] != None):
			self.add_constructor_assignment(node, the_slot.index, element.decl['assign_expr'])

	def find_slot(self, node, slot_name):
		return node.compound_record.members[slot_name] if slot_name in node.compound_record.members else None

	def add_sub_function_record(self, decl):
		function_index = len(self.functions)
		record = image.func_record(decl, None, None)
		self.functions.append(record)
		return function_index
	
	def add_constructor_assignment(self, node, slot_index, assignment_expression):
		node.assignments.append((slot_index, assignment_expression))
	def build_constructor(self, node):
		if len(node.assignments) != 0:
			node.constructor_index = len(self.functions)
			parent = node.parent_node
			if parent != None and parent.constructor_index != None:
				parent_call = node.decl['parent_decl']
				parent_constructor_stmt = [{'type': 'expression_stmt', 'expr': { 'type': 'func_call_expr', 'func_expr': { 'type': 'selfmethod_global_expr', 'func_index': parent.constructor_index }, 'args': parent_call[1] }} ]
			else:
				parent_constructor_stmt = []
			statements = parent_constructor_stmt + [{'type' : 'initializer_stmt', 'slot':e[0], 'value':e[1]} for e in node.assignments]
			param_list = node.decl['parameter_list'] if 'parameter_list' in node.decl else ()
			decl = {'type': 'function', 'name' : '__constructor', 'parameter_list': param_list, 'statements' : statements }
			the_func_record = image.func_record(decl, node, None)
			self.functions.append(the_func_record)
			self.analyze_function(the_func_record, None)
	
	def add_function_decl(self, node, func_node):
		if func_node.func_record is not None:
			return
		decl = func_node.decl
		name = func_node.name
		self.check_compound_record_unique(node)
		parent_func = self.find_slot(node, name)
		if parent_func:
			#todo: check that the parent_func is not actually declared in this node (multiple definition)
			if parent_func.type != 'function':
				raise compile_error, (decl, "Function " + name + " of " + node.name + " is already declared as a nonfunction")
			vtable_index = parent_func.index
		else:
		   parent_func = None
		   vtable_index = node.compound_record.vtable_count
		   node.compound_record.vtable_count += 1
		if func_node.index is not None:
			function_index = func_node.index
			func_node.func_record = self.functions[function_index]
		else:
			function_index = len(self.functions)
			func_node.func_record = image.func_record(decl, node, vtable_index)
			self.functions.append(func_node.func_record)

		node.compound_record.members[decl['name']] = image.slot(type='function', name=decl['name'],index=vtable_index,global_function_index=function_index)
		if vtable_index == len(node.compound_record.vtable):
			node.compound_record.vtable.append(self.functions[function_index])
		else:
			node.compound_record.vtable[vtable_index] = self.functions[function_index]

	def build_tree_recurse_decl(self, image_node):
		if 'body' in image_node.decl and image_node.decl['body'] != None:
			for sub_decl in image_node.decl['body']:
				if 'name' in sub_decl and self.decl_in_image(sub_decl):
					if sub_decl['name'] in image_node.contents:
						raise compile_error, (image_node, "Redefinition of " + sub_decl['name'] + " in " + image_node.name + " not allowed.")
					else:
						new_node = image.tree_node(image_node, sub_decl['name'], sub_decl['type'], sub_decl)
						image_node.contents[sub_decl['name']] = new_node
						if new_node.is_compound():
							self.add_global(new_node)
						self.build_tree_recurse_decl(new_node)
	def decl_in_image(self, decl):
		if decl.has_key('image_list') and decl['image_list'] is not None:
			if (len(decl['image_list']) != 0) and (self.image_name not in decl['image_list']):
				return False
		if decl.has_key('transmission_list') and decl['transmission_list'] is not None:
			# see if it's in the from_image or to_image of any transmission specifiers
			if len(decl['transmission_list']) and len(filter(decl['transmission_list'], lambda x: x['from_image'] == self.image_name or x['to_image'] == self.image_name)) == 0:
				return False
		return True
	def build_accept_reject_list(self, accept_list, reject_name_list, decl):
		if decl['type'] == 'image':
			if decl['name'] != self.image_name:
				for sub_decl in decl['body']:
					reject_name_list.append(sub_decl['name'])
			else:
				accept_list += decl['body']
		else:
			if self.decl_in_image(decl):
				accept_list.append(decl)
			else:
				reject_name_list.append(decl['name'])
	def build_tree(self, file_tree):
		self.build_tree_recurse(self.tree, file_tree)
	def build_tree_recurse(self, image_node, file_node):
		print "Recursing node: " + image_node.name
		files_and_dirs = [d for d in file_node.contents.values() if d.type == 'directory' or d.type == 'resource']
		reject_list = []
		decls_list = [] 
		if 'body' in image_node.decl and image_node.decl['body'] != None:
			for decl in image_node.decl['body']:
				self.build_accept_reject_list(decls_list, reject_list, decl)
		for file in (k for k in file_node.contents.values() if k.type == 'kt'):
			for decl in file.parse_result:
				self.build_accept_reject_list(decls_list, reject_list, decl)
		# now add all the files and directories to the tree and recurse them:
		for file in (f for f in files_and_dirs if f.name not in reject_list):
			parent = 'resource' if file.type == 'resource' else 'directory'
			decl = { 'name' : file.name, 'type' : 'object', 'body' : [], 'parent_decl' : [parent], 'file_node' : file }
			image_node.contents[file.name] = image.tree_node(image_node, file.name, 'object', decl)		
		for decl in decls_list:
			if decl['name'] in image_node.contents:
				# this is only allowed if the item in contents is a resource or directory;
				# also it must have an empty body
				existing_node = image_node.contents[decl['name']]
				if existing_node.type != 'object' or decl['type'] != 'object' or 'file_node' not in existing_node.decl:
					print "Redefinition of " + decl['name'] + " in " + image_node.name + " not allowed."
				else:
					if decl['parent_decl'] != None and decl['parent_decl'] != existing_node.decl['parent_decl']:
						print "Parent type mismatch for object " + decl['name']
					else:
						existing_node.decl.update(decl)
			else:
				image_node.contents[decl['name']] = image.tree_node(image_node, decl['name'], decl['type'], decl)
		# now go back through the contents and recurse the children:
		for node in image_node.contents.values():
			# everything declared at the top level is added to the globals; otherwise, only compounds are added
			self.add_global(node)
			if 'file_node' in node.decl:
				self.build_tree_recurse(node, node.decl['file_node'])
			else:
				self.build_tree_recurse_decl(node)
	def add_global(self, item):
		if item.name in self.globals:
			self.globals[item.name].append(item)
		else:
			self.globals[item.name] = [item]

		item.global_index = len(self.globals_list)
		self.globals_list.append(item)
	
	def add_builtin_node(self, node_path, node_type):
		node = self.tree
		path = node_path.partition('/')
		while path[2] != "":
			if node.contents.has_key(path[0]):
				node = node.contents[path[0]]
			else:
				decl = { 'name' : path[0], 'type' : 'object', 'body' : [], 'parent_decl' : ['directory'] }
				new_node = image.tree_node(node, path[0], 'object', decl)
				node.contents[path[0]] = new_node
				node = new_node
			path = path[2].partition('/')
		if node.contents.has_key(path[0]):
			raise compile_error, (None, "duplicate addition of builtin node: " + path[0])
		symbol_node = image.tree_node(node, path[0], node_type, { 'name' : path[0], 'type' : node_type })
		node.contents[path[0]] = symbol_node
		self.add_global(symbol_node)
		return symbol_node
	def add_python_function(self, node_path, the_function):
		new_node = self.add_builtin_node(node_path, 'python_function')
		new_node.python_function = the_function
	def add_python_class(self, node_path, the_class):
		new_node = self.add_builtin_node(node_path, 'python_class')
		new_node.python_class = the_class
	def find_node(self, search_node, parent_name, filter_func = lambda x: True ):		
		parent_part = parent_name.partition('/')			
		if not self.globals.has_key(parent_part[0]):
			print "Error, node named " + parent_part[0] + " is not in image " + self.image_name
			return None
		else:
			node_list = []
			# construct a list of nodes that can be reached from the specified parent_name path
			for node in self.globals[parent_part[0]]:
				remainder_path = parent_part[2]
				leaf_node = node
				while remainder_path != "":
					sub_path = remainder_path.partition('/')
					if leaf_node.contents.has_key(sub_path[0]):
						leaf_node = leaf_node.contents[sub_path[0]]
						remainder_path = sub_path[2]
					else:
						leaf_node = None
						break
				if leaf_node != None and filter_func(leaf_node):
				   node_list.append(leaf_node)
			if len(node_list) == 0:
				return None
			elif len(node_list) == 1:
			    return node_list[0]
			else:
				# figure out which is the closest relative to search_node
				search_ancestry = search_node.get_ancestry_list()
				node_ancestry = node_list[0].get_ancestry_list()
				closest_ancestry_depth = common_list_length(search_ancestry, node_ancestry)
				closest_node = node_list[0]
				for n in node_list[1:]:
					node_ancestry = n.get_ancestry_list()
					depth = common_list_length(search_ancestry, node_ancestry)
					if depth > closest_ancestry_depth:
						closest_node = n
						closest_ancestry_depth = depth
					elif depth == closest_ancestry_depth:
						compiler_warning(None, "Node " + parent_name + " ambiguously resolves to multiple objects at same depth.")
				return closest_node				

	def get_type_spec(self, var_decl):
		return 0
	
	def analyze_compound(self, node):
		if node.process_pass == 1:
			raise compile_error, (node.decl, "Error - compound " + node.name + " is part of a class definition cycle")
		elif node.process_pass == 0:
			node.process_pass = 1
			# check if it has a parent class, and process that one first.
			print "Processing compound: " + node.name + " with decl: " + str(node.decl)
			parent = node.decl['parent_decl'][0] if 'parent_decl' in node.decl and len(node.decl['parent_decl']) > 0 else None
			if parent != None:
				print "node: " + node.name + " has parent: " + parent
				parent_node = self.find_node(node, parent)
				if parent_node == None:
					raise compile_error, (node.decl, "Could not find parent " + parent + " for compound " + node.name)
				else:
					print "processing parent: " + parent_node.name
					self.analyze_compound(parent_node)
				node.parent_node = parent_node
			node.process_pass = 2
			# now that the parent node is processed, we can process this node
			node.assignments = []
			
			if node.parent_node == None:
				node.compound_record = image.compound_record(node)
			else:
				node.compound_record = parent_node.compound_record
			# first add any new functions and variable declarations 
			for element in node.contents.values():
				if element.type == 'variable':
					self.add_slot(node, element)
				elif element.type == 'function':
					self.add_function_decl(node, element)
					
			# if is is a compound with a body, check for slot assignments
			if 'body' in node.decl:
				for assignment in (v for v in node.decl['body'] if v['type'] == 'slot_assignment'):
					if assignment['name'] not in node.members:
						raise compile_error, (node.decl, "Compound " + node.name + " does not have a slot named " + assignment['name'])
					else:
						the_slot = node.members[assignment['name']]
						if the_slot.type != 'variable':
							raise compile_error, (node.decl, "Member " + assignment['name'] + " of " + node.name + " is not an assignable slot.")
						self.add_constructor_assignment(node, the_slot.index, assignment['assign_expr'])
			print "Compound " + node.name + ":"
			for slot_name, the_slot in node.compound_record.members.iteritems():
				print the_slot
			#for assignment in node.assignments:
			#	print "  Assigns variable slot: " + str(assignment.slot_index) + " assign: " + str(assignment.assign_expr)
			self.build_constructor(node)
			print "node " + node.name + " processed - booyaka"


	def analyze_functions(self):
		for func in self.functions:
			print str(func.decl)
			if func.node:
				print "analyzing method " + func.node.name + "." + func.decl['name']
				self.analyze_function(func, None)
			
	class semantic_info:
		def __init__(self):
			self.loop_count = 0
			self.switch_count = 0
			self.arg_count = 0
			self.register_count = 0
			self.needs_prev_scope = False
			self.scope_needed = False
			self.prev_scope = None
			self.symbols = {}
			self.statements = []
			self.child_functions = []
			self.references_instance_variables = False
			self.ip = 0 # instruction pointer
	
	def analyze_function(self, func, enclosing_scope):
		si = image.semantic_info()
		si.prev_scope = enclosing_scope
		si.compound_node = func.node
		decl = func.decl
		if func.parent_function_index is not None:
			parent_func_record = self.functions[func.parent_function_index]
		else:
			parent_func_record = None
		print str(decl)
		for arg in decl['parameter_list']:
			if arg in si.symbols:
				raise compile_error, (decl, "Argument " + arg + " is declared more than once.")
			si.symbols[arg] = ('arg', si.arg_count)
			si.arg_count += 1
			#print "Arg: " + arg
		self.analyze_block(si, decl['statements'])
		self.compile_block(si, decl['statements'], 0, 0)
		if len(decl['statements']) == 0 or decl['statements'][-1]['type'] is not 'return_stmt':
			self._analyze_stmt_return_stmt(si, {'type':'return_stmt','return_expression_list':()})
			self._compile_stmt_return_stmt(si, {'type':'return_stmt','return_expression_list':()}, 0, 0)
		
		func.set(si)
		#analyze any sub functions
		print decl['name'] + " - function compiles to:\n" + str(func)

		for func_index in si.child_functions:
			self.analyze_function(self.functions[func_index], si)
	
	def analyze_block(self, si, statement_list):
		for stmt in statement_list:
			self.analyze_statement(si, stmt)
	def compile_block(self, si, statement_list, continue_ip, break_ip):
		for stmt in statement_list:
			self.compile_statement(si, stmt, continue_ip, break_ip)
	
	def analyze_statement(self, si, stmt):
		if stmt['type'] in self.analyze_stmt_jump_table:
			self.analyze_stmt_jump_table[stmt['type']](self, si, stmt)
			
	def compile_statement(self, si, stmt, continue_ip, break_ip):
		if stmt['type'] in self.compile_stmt_jump_table:
			self.compile_stmt_jump_table[stmt['type']](self, si, stmt, continue_ip, break_ip)

	def _analyze_stmt_variable_declaration_stmt(self, si, stmt):
		var_name = stmt['name']
		if var_name in si.symbols:
			raise compile_error, (stmt, "Variable " + var_name + " is declared more than once.")
		si.symbols[var_name] = ('local', si.register_count)
		si.register_count += 1
		print "Var decl: " + stmt['name']
		
		# if the statement has an assignment expression, generate an assignment statement for the assignment
		if stmt['assign_expr'] is not None:
			assign_stmt = { 'type': 'expression_stmt', 'expr': { 'type': 'assign_expr', 'left': { 'type': 'locator_expr', 'string' : stmt['name'] }, 'right': stmt['assign_expr'] } }
			#print "  Adding assignment statement: " + str(assign_stmt)
			stmt['assign_stmt'] = assign_stmt
			self.analyze_statement(si, assign_stmt)
	def _compile_stmt_variable_declaration_stmt(self, si, stmt, continue_ip, break_ip):
		if 'assign_stmt' in stmt:
			self.compile_statement(si, stmt['assign_stmt'], continue_ip, break_ip)
	
	def _analyze_stmt_function_declaration(self, si, stmt):
		func_name = stmt['name']
		#print "func decl: " + func_name
		if func_name in si.symbols:
			raise compile_error, (stmt, "Symbol " + func_name + " is already declared in this scope.")
		
		function_index = self.add_sub_function_record(stmt)
		si.symbols[func_name] = ('sub_function', function_index)
		si.child_functions.append(function_index)
	def _compile_stmt_function_declaration(self, si, stmt, continue_ip, break_ip):
		pass

	def _analyze_stmt_continue_stmt(self, si, stmt):
		if si.loop_count == 0:
			raise compile_error, (stmt, "continue not allowed outside of a loop.")
		si.ip += 1
		#print "continue stmt"
	def _compile_stmt_continue_stmt(self, si, stmt, continue_ip, break_ip):
		si.statements.append(('branch_always', continue_ip))
		
	def _analyze_stmt_break_stmt(self, si, stmt):
		if si.loop_count == 0 and si.switch_count == 0:
			raise compile_error, (stmt, "break not allowed outside of a loop or switch.")
		si.ip += 1
		#print "break stmt"
	def _compile_stmt_break_stmt(self, si, stmt, continue_ip, break_ip):
		si.statements.append(('branch_always', break_ip))
		
	def _analyze_stmt_switch_stmt(self, si, stmt):
		# save the expression result in a register
		stmt['expr_register'] = si.register_count
		si.register_count += 1
		si.switch_count += 1
		# the basic form of the switch statement is to evaluate
		# the switch expression into the temporary register (first instruction)
		# then for each switch element there is either a branch test for the cases
		# followed by a branch always to the default case or out of the switch if there's
		# no default.
		si.ip += 2 + len(stmt['element_list'])
		self.analyze_expression(si, stmt['test_expression'], ('any'), False)
		for element in stmt['element_list']:
			for label in element['label_list']:
				self.analyze_expression(si, label['test_constant'], ('any'), False)
			self.analyze_block(si, element['statement_list'])
		if stmt['default_block'] is not None:
			self.analyze_block(si, stmt['default_block'])
		stmt['break_ip'] = si.ip
		si.switch_count -= 1
		
	def _compile_stmt_switch_stmt(self, si, stmt, continue_ip, break_ip):
		switch_start = len(si.statements)
		test_register = stmt['expr_register']
		si.statements.append( ('eval', ('assign', ('local', test_register), self.compile_expression(si, stmt['test_expression'], ('any'), False))))
		# reserve cascading statement list for the test expressions and final branch
		si.statements = si.statements + [None] * (len(stmt['element_list']) + 1)
		index = 1
		def build_compare(expr):
			return ('bool_binary', 'compare_equal', ('local', test_register ), self.compile_expression(si, expr, ('any'), False))
			
		for element in stmt['element_list']:
			ip = len(si.statements)
			self.compile_block(si, element['statement_list'], continue_ip, stmt['break_ip'])
			label_list = element['label_list']
			compare_expr = build_compare(label_list[0]['test_constant'])
			for label in label_list[1:]:
				compare_expr = ('bool_binary', 'logical_or', compare_expr, build_compare(label['test_constant']))
			si.statements[switch_start + index] = ('branch_if_nonzero', ip, compare_expr)
			index += 1
		si.statements[switch_start + index] = ('branch_always', len(si.statements))
		if stmt['default_block'] is not None:
			self.compile_block(si, stmt['default_block'], continue_ip, stmt['break_ip'])
		
	def _analyze_stmt_if_stmt(self, si, stmt):
		#print "if stmt" + str(stmt)
		self.analyze_expression(si, stmt['test_expression'], ('bool'), False)
		si.ip += 1
		self.analyze_block(si, stmt['if_block'])
		if 'else_block' in stmt:
			si.ip += 1
			stmt['if_false_jump'] = si.ip
			self.analyze_block(si, stmt['else_block'])
			stmt['if_true_jump'] = si.ip
		else:
			stmt['if_false_jump'] = si.ip
	def _compile_stmt_if_stmt(self, si, stmt, continue_ip, break_ip):
		si.statements.append(('branch_if_zero', stmt['if_false_jump'], self.compile_boolean_expression(si, stmt['test_expression'])))
		self.compile_block(si, stmt['if_block'], continue_ip, break_ip)
		if 'else_block' in stmt:
			si.statments.append(('branch_always', stmt['if_true_jump']))
			self.compile_block(si, stmt['else_block'], continue_ip, break_ip)
	
	def _analyze_stmt_while_stmt(self, si, stmt):
		si.loop_count += 1
		self.analyze_expression(si, stmt['test_expression'], ('bool'), False)
		stmt['continue_ip'] = si.ip
		si.ip += 1
		self.analyze_block(si, stmt['statement_list'])
		si.ip += 1
		stmt['break_ip'] = si.ip
		si.loop_count -= 1
	def _compile_stmt_while_stmt(self, si, stmt, continue_ip, break_ip):
		si.statements.append(('branch_if_zero', stmt['break_ip'], self.compile_boolean_expression(si, stmt['test_expression'])))
		self.compile_block(si, stmt['statement_list'], stmt['continue_ip'], stmt['break_ip'])

	def _analyze_stmt_do_while_stmt(self, si, stmt):
		si.loop_count += 1
		stmt['start_ip'] = si.ip
		self.analyze_block(si, stmt['statement_list'])
		stmt['continue_ip'] = si.ip
		si.ip += 1
		stmt['break_ip'] = si.ip
		self.analyze_expression(si, stmt['test_expression'], ('bool'), False)
		si.loop_count -= 1
	def _compile_stmt_do_while_stmt(self, si, stmt, continue_ip, break_ip):
		self.compile_block(si, stmt['statement_list'], stmt['continue_ip'], stmt['break_ip'])
		si.statements.append(('branch_if_nonzero', stmt['start_ip'], self.compile_boolean_expression(si, stmt['test_expression'])))
		
	def _analyze_stmt_for_stmt(self, si, stmt):
		#print "for stmt" + str(stmt)
		si.loop_count += 1
		if 'variable_initializer' in stmt:			
			var_name = stmt['variable_initializer']
			if var_name in si.symbols:
				raise compile_error, (stmt, "Variable " + var_name + " is declared more than once.")
			si.symbols[var_name] = ('local', si.variable_register_count, stmt['variable_type_spec'])
			si.variable_register_count += 1
			print "Var decl: " + stmt['name']
		if 'init_expression' in stmt:
			self.analyze_expression(si, stmt['init_expression'], ('any'), False)
			si.ip += 1
		loop_start_ip = si.ip
		self.analyze_expression(si, stmt['test_expression'], ('bool'), False)
		si.ip += 1
		self.analyze_block(si, stmt['statement_list'])
		if 'end_loop_expression' in stmt and stmt['end_loop_expression'] is not None:
			stmt['continue_ip'] = si.ip
			self.analyze_expression(si, stmt['end_loop_expression'], ('any'), False)
			si.ip += 2
		else:
			stmt['continue_ip'] = loop_start_ip
		stmt['loop_start_ip'] = loop_start_ip
		stmt['break_ip'] = si.ip
		si.loop_count -= 1
	def _compile_stmt_for_stmt(self, si, stmt, continue_ip, break_ip):
		if 'init_expression' in stmt:
			si.statements.append(('eval', self.compile_void_expression(si, stmt['init_expression'])))
		si.statements.append(('branch_if_zero', stmt['break_ip'], self.compile_boolean_expression(si, stmt['test_expression'])))
		self.compile_block(si, stmt['statement_list'], stmt['continue_ip'], stmt['break_ip'])
		if 'end_loop_expression' in stmt and stmt['end_loop_expression'] is not None:
			si.statements.append(('eval', self.compile_void_expression(si, stmt['end_loop_expression'])))
		si.statements.append(('branch_always', stmt['loop_start_ip']))
		
	def _analyze_stmt_return_stmt(self, si, stmt):
		#print "return stmt" + str(stmt)
		for expr in stmt['return_expression_list']:
			self.analyze_expression(si, expr, ('any'), False)
		si.ip += 1
	def _compile_stmt_return_stmt(self, si, stmt, continue_ip, break_ip):
		si.statements.append(('return', self.compile_expression_list(si, stmt['return_expression_list'])))

	def _analyze_stmt_expression_stmt(self, si, stmt):
		#print "expression stmt" + str(stmt)
		self.analyze_expression(si, stmt['expr'], ('any'), False)
		si.ip += 1
	def _compile_stmt_expression_stmt(self, si, stmt, continue_ip, break_ip):
		si.statements.append(('eval', self.compile_void_expression(si, stmt['expr'])))
	
	def _analyze_stmt_initializer_stmt(self, si, stmt):
		self.analyze_expression(si, stmt['value'], ('any'), False)
		si.ip += 1
	def _compile_stmt_initializer_stmt(self, si, stmt, continue_ip, break_ip):
		si.statements.append(('eval', ('assign', ('ivar', stmt['slot']),
									   self.compile_expression(si, stmt['value'], ('any'), False) )))

	def compile_boolean_expression(self, si, expr):
		return self.compile_expression(si, expr, ('boolean'), False)

	def compile_void_expression(self, si, expr):
		return self.compile_expression(si, expr, ('any'), False)
	
	def compile_expression_list(self, si, expr_list):
		return [self.compile_void_expression(si, x) for x in expr_list]
	
	def analyze_expression(self, si, expr, valid_types, is_lvalue):
		#print "Analyzing expression: " + str(expr)
		if is_lvalue and expr['type'] not in ('locator_expr', 'array_index_expr', 'slot_expr'):
			raise compile_error, (expr, "Expression is not an l-value.")
		print str(expr)
		if expr['type'] in self.analyze_expr_jump_table:
			self.analyze_expr_jump_table[expr['type']](self, si, expr, valid_types, is_lvalue)
		
	def compile_expression(self, si, expr, valid_types, is_lvalue):
		if expr['type'] in self.compile_expr_jump_table:
			return self.compile_expr_jump_table[expr['type']](self, si, expr, valid_types, is_lvalue)
		else:
			return expr
		
	def _compile_expr_selfmethod_global_expr(self, si, expr, valid_types, is_lvalue):
		return ('selfmethod_global', expr['func_index'])
	
	def _analyze_expr_locator_expr(self, si, expr, valid_types, is_lvalue):
		locator_name = expr['string']
		if locator_name in si.symbols:
			expr['location'] = si.symbols[locator_name]
		elif si.prev_scope and locator_name in si.prev_scope.symbols:
			expr['location'] = ('prev_scope', si.prev_scope.symbols[locator_name])
			si.needs_prev_scope = True
			si.prev_scope.scope_needed = True
		elif si.compound_node and locator_name in si.compound_node.compound_record.members:
			member = si.compound_node.compound_record.members[locator_name]
			if member.type == 'variable':
				expr['location'] = ('ivar', member.index)
			elif member.type == 'function':
				expr['location'] = ('imethod', member.index)
			else:
				raise compile_error, (expr, "member " + locator_name + " cannot be used here.")
		else:
			# search the global container
			node = self.find_node(si.compound_node, locator_name)
			if not node:
				raise compile_error, (expr, "locator " + locator_name + " not found.")
			expr['location'] = ('global_node', node)
			if is_lvalue:
				raise compile_error, (expr, "Global object " + locator_name + " cannot be assigned a value.")
	def _compile_expr_locator_expr(self, si, expr, valid_types, is_lvalue):
		#print str(expr)
		return expr['location']

	def _compile_expr_int_constant_expr(self, si, expr, valid_types, is_lvalue):
		return ('int_constant', expr['value'])
	
	def _compile_expr_float_constant_expr(self, si, expr, valid_types, is_lvalue):
		return ('float_constant', expr['value'])
	
	def _compile_expr_string_constant(self, si, expr, valid_types, is_lvalue):
		return ('string_constant', expr['value'])
	
	def _analyze_expr_array_index_expr(self, si, expr, valid_types, is_lvalue):
		self.analyze_expression(si, expr['array_expr'], ('any'), False)
		self.analyze_expression(si, expr['index_expr'], ('any'), False)
	
	def _compile_expr_array_index_expr(self, si, expr, valid_types, is_lvalue):
		return ('array_index', self.compile_expression(si, expr['array_expr'], ('any'), False), 
			    self.compile_expression(si, expr['index_expr'], ('any'), False))
	
	def _analyze_expr_func_call_expr(self, si, expr, valid_types, is_lvalue):
		self.analyze_expression(si, expr['func_expr'], ('callable'), False)
		for arg in expr['args']:
			self.analyze_expression(si, arg, ('any'), False)
	def _compile_expr_func_call_expr(self, si, expr, valid_types, is_lvalue):
		arg_array = []
		for arg in expr['args']:
			arg_array.append(self.compile_expression(si, arg, ('any'), False) )
		return ('func_call', self.compile_expression(si, expr['func_expr'], ('callable'), False), arg_array)
		
	def _analyze_expr_slot_expr(self, si, expr, valid_types, is_lvalue):
		object_expr = expr['object_expr']
		if(object_expr['type'] == 'locator_expr' and object_expr['string'] == 'parent'):
			# parent references a function slot in the parent class
			parent_node = si.compound_node.parent_node
			if parent_node == None:
				raise compile_error, (expr, "Compound " + si.compound_node.name + " has no declared parent.")
			parent_record = parent_node.compound_record
			if expr['slot_name'] not in parent_record.members:
				raise compile_error, (expr, "Parent of " + si.compound_node.name + " has no member named " + expr['slot_name'])
			slot = parent_record.members[expr['slot_name']]
			if slot.type != 'function':
				raise compile_error, (expr, "parent expression must reference a function.")				
			expr['parent_function_index'] = slot.global_function_index
 		else:
 			self.analyze_expression(si, expr['object_expr'], ('any'), False)
	def _compile_expr_slot_expr(self, si, expr, valid_types, is_lvalue):
		if 'parent_function_index' in expr:
			return ('selfmethod_global', expr['parent_function_index'])
		else:
			return ('slot', self.compile_expression(si, expr['object_expr'], ('any'), False), expr['slot_name'])
	
	def _analyze_expr_unary_lvalue_op_expr(self, si, expr, valid_types, is_lvalue):
		self.analyze_expression(si, expr['expression'], ('number'), True)
	def _compile_expr_unary_lvalue_op_expr(self, si, expr, valid_types, is_lvalue):
		return ('unary_lvalue_op', self.compile_expression(si, expr['expression'], ('number'), True), expr['op'])
	
	def _analyze_expr_unary_minus_expr(self, si, expr, valid_types, is_lvalue):
		self.analyze_expression(si, expr['expression'], ('number'), False)		
	def _compile_expr_unary_minus_expr(self, si, expr, valid_types, is_lvalue):
		return ('unary_minus', self.compile_expression(si, expr, ('number'), False))
	
	def _analyze_expr_logical_not_expr(self, si, expr, valid_types, is_lvalue):
		self.analyze_expression(si, expr['expression'], ('boolean'), False)	
	def _compile_expr_logical_not_expr(self, si, expr, valid_types, is_lvalue):
		return ('logical_not', self.compile_expression(si, expr, ('boolean'), False))
		
	def _analyze_expr_bitwise_not_expr(self, si, expr, valid_types, is_lvalue):
		self.analyze_expression(si, expr['expression'], ('integer'), False)	
	def _compile_expr_bitwise_not_expr(self, si, expr, valid_types, is_lvalue):
		return ('bitwise_not', self.compile_expression(si, expr, ('integer'), False))

	def _analyze_expr_float_binary_expr(self, si, expr, valid_types, is_lvalue):
		self.analyze_expression(si, expr['left'], ('number'), False)
		self.analyze_expression(si, expr['right'], ('number'), False)
	def _compile_expr_float_binary_expr(self, si, expr, valid_types, is_lvalue):
		return ('float_binary', expr['op'], 
			    self.compile_expression(si, expr['left'], ('number'), False),
			    self.compile_expression(si, expr['right'], ('number'), False))

	def _analyze_expr_int_binary_expr(self, si, expr, valid_types, is_lvalue):
		self.analyze_expression(si, expr['left'], ('integer'), False)
		self.analyze_expression(si, expr['right'], ('integer'), False)
	def _compile_expr_int_binary_expr(self, si, expr, valid_types, is_lvalue):
		return ('int_binary', expr['op'], 
			    self.compile_expression(si, expr['left'], ('integer'), False),
			    self.compile_expression(si, expr['right'], ('integer'), False))

	def _analyze_expr_bool_binary_expr(self, si, expr, valid_types, is_lvalue):
		self.analyze_expression(si, expr['left'], ('boolean'), False)
		self.analyze_expression(si, expr['right'], ('boolean'), False)
	def _compile_expr_bool_binary_expr(self, si, expr, valid_types, is_lvalue):
		return ('bool_binary', expr['op'], 
			    self.compile_expression(si, expr['left'], ('boolean'), False),
			    self.compile_expression(si, expr['right'], ('boolean'), False))

	def _analyze_expr_strcat_expr(self, si, expr, valid_types, is_lvalue):
		self.analyze_expression(si, expr['left'], ('string'), False)
		self.analyze_expression(si, expr['right'], ('string'), False)
	def get_cat_str(self, expr):
		str_op = expr['op']
		if str_op == 'cat_none':
			return ""
		elif str_op == 'cat_newline':
			return "\n"
		elif str_op == 'cat_space':
			return " "
		elif str_op == 'cat_tab':
			return "\t"
		else:
			raise compile_error, (expr, "Unknown string cat operator" + str(str_op))
	def _compile_expr_strcat_expr(self, si, expr, valid_types, is_lvalue):
		return ('strcat', self.get_cat_str(expr), 
			    self.compile_expression(si, expr['left'], ('string'), False),
			    self.compile_expression(si, expr['right'], ('string'), False))

	def _analyze_expr_conditional_expr(self, si, expr, valid_types, is_lvalue):
		self.analyze_expression(si, expr['test_expression'], ('boolean'), False)
		self.analyze_expression(si, expr['true_expression'], valid_types, False)
		self.analyze_expression(si, expr['false_expression'], valid_types, False)
	def _compile_expr_conditional_expr(self, si, expr, valid_types, is_lvalue):
		return ('conditional',
				self.compile_expression(si, expr['test_expression'], ('boolean'), False),
				self.compile_expression(si, expr['true_expression'], valid_types, False),
				self.compile_expression(si, expr['false_expression'], valid_types, False))
		
	def _analyze_expr_assign_expr(self, si, expr, valid_types, is_lvalue):
		self.analyze_expression(si, expr['left'], ('any'), True)
		self.analyze_expression(si, expr['right'], ('any'), False)
	def _compile_expr_assign_expr(self, si, expr, valid_types, is_lvalue):
		return ('assign',
			    self.compile_expression(si, expr['left'], ('any'), True),
			    self.compile_expression(si, expr['right'], ('any'), False))
	
	def _analyze_expr_float_assign_expr(self, si, expr, valid_types, is_lvalue):
		self.analyze_expression(si, expr['left'], ('number'), True)
		self.analyze_expression(si, expr['right'], ('number'), False)
	def _compile_expr_float_assign_expr(self, si, expr, valid_types, is_lvalue):
		return ('float_assign', expr['op'], 
			    self.compile_expression(si, expr['left'], ('number'), True),
			    self.compile_expression(si, expr['right'], ('number'), False))

	def _analyze_expr_int_assign_expr(self, si, expr, valid_types, is_lvalue):
		self.analyze_expression(si, expr['left'], ('integer'), True)
		self.analyze_expression(si, expr['right'], ('integer'), False)
	def _compile_expr_int_assign_expr(self, si, expr, valid_types, is_lvalue):
		return ('int_assign', expr['op'], 
			    self.compile_expression(si, expr['left'], ('integer'), True),
			    self.compile_expression(si, expr['right'], ('integer'), False))
	
	def _analyze_expr_array_expr(self, si, expr, valid_types, is_lvalue):
		if is_lvalue:
			raise compile_error, (expr, "Array initializer cannot be an lvalue.")
		for sub_expr in expr['array_values']:
			self.analyze_expression(si, sub_expr, ('any'), False)
			
	def _compile_expr_array_expr(self, si, expr, valid_types, is_lvalue):
		return ('array', [self.compile_expression(si, sub_expr, ('any'), False) for sub_expr in expr['array_values']])
	
	def _analyze_expr_map_expr(self, si, expr, valid_types, is_lvalue):
		if is_lvalue:
			raise compile_error, (expr, "Map initializer cannot be an lvalue.")
		for pair in expr['map_pairs']:
			self.analyze_expression(si, pair['key'], ('any'), False)
			self.analyze_expression(si, pair['value'], ('any'), False)
	
	def _compile_expr_map_expr(self, si, expr, valid_types, is_lvalue):
		return ('map', [(self.compile_expression(si, pair['key'], ('any'), False), self.compile_expression(si, pair['value'], ('any'), False)) for pair in expr['map_pairs']])
		
