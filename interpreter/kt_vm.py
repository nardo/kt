# kt_vm.py
# virtual machine for the kt interpreter - evaluates the program facet generated by kt_compiler.py
# (C) 2009 Mark Frohnmayer.  The use of this code is governed by its license.  See /license/info.txt in the source distribution for the full license agreement.

from kt_program_tree import *

def build_jump_table(the_object, prefix):
	the_map = {}
	for pair in the_object.__dict__.iteritems():
		if pair[0].startswith(prefix):
			split_string = pair[0].partition(prefix)
			the_map[split_string[2]] = pair[1]
	return the_map

import types

should_spew = False

Exec_Normal = 0
Exec_Return = 1
Exec_Exception = 2

def spew(str):
	if should_spew:
		print str
	
class fatal_error:
	def __init__(self, vm, error_string):
		self.foo = self.bar
		self.vm = vm
		self.error_string = error_string
		
class vm:
	class function_record_instance:
		def __init__(self, function):
			self.function = function
		def call(self, vm, reference_object, parameters):
			vm.invoke_function(self.function, reference_object, parameters)
	class object_instance:
		def __init__(self, node):
			self.id = node
			self.slots = [None for x in range(0, node.slot_count)]
		def eval(self, vm):
			return self
	class class_instance:
		def __init__(self, node):
			self.node = node
			self.compound_record = node.compound_record
		def eval(self, vm):
			return (self, None)
		def call(self, vm, reference_object, params):
			result = vm.object_instance(self.node)
			if self.node.constructor_index is not None:
				vm.invoke_function_record(vm.facet.functions[self.node.constructor_index], result, params)
			vm.return_value = result
			
	class function_instance:
		def __init__(self, node):
			self.function = node
			self.container_index = node.container.global_index
		def eval(self, vm):
			return (self, vm.globals[self.container_index])
		def call(self, vm, reference_object, params):
			return vm.invoke_function(self.function, reference_object, params)
	class python_function_instance:
		def __init__(self, node):
			self.python_function = node.python_function
		def eval(self, vm):
			return (self, None)
		def call(self, vm, reference_object, params):
			self.python_function(*params)
	class python_class_instance:
		def __init__(self, node):
			self.python_class = node.python_class
	class frame:
		def __init__(self, function, arguments, prev_frame, reference_object):
			self.function = function
			self.registers = list((None for i in range(0,function.register_count)))
			self.locals = list((None for i in range(0, function.local_variable_count)))
			self.arguments = arguments
			self.ip = 0
			self.prev_frame = prev_frame
			self.reference_object = reference_object
			
	def __init__(self, compiled_facet):
		self.depth = 0
		self.exec_table = build_jump_table(vm, "_exec_")
		self.eval_table = build_jump_table(vm, "_eval_")
		self.evallvalue_table = build_jump_table(vm, "_evallvalue_")
		self.globals = []
		for o in compiled_facet.globals_list:
			if o.__class__ == node_object:
				the_global_object = vm.object_instance(o)
			elif o.__class__ == node_class:
				the_global_object = vm.class_instance(o)
			elif o.__class__ == node_function:
				the_global_object = vm.function_instance(o)
			elif o.__class__ == node_python_function:
				the_global_object = vm.python_function_instance(o)
			elif o.__class__ == node_python_class:
				the_global_object = vm.python_class_instance(o)
			else:
				the_global_object = None
				#raise fatal_error, (self, "unknown global object type " + str(o.__class__) )
			self.globals.append(the_global_object)
		self.facet = compiled_facet
		self.tos = None
		self.return_value = None
		for o in (o for o in compiled_facet.globals_list if o is not None and o.__class__ == node_object):
			if o.constructor_index is not None:
				callable = (vm.function_record_instance(compiled_facet.functions[o.constructor_index]), self.globals[o.global_index])
				self.call_function(callable, ())
				
	def exec_function(self, func_name, args):
		func_node = self.facet.find_node(None, func_name, lambda x: x.type =='function' )
		self.call_function(self.globals[func_node.global_index].eval(self), ())
	
	def invoke_function(self, function, reference_object, arguments):
		new_frame = vm.frame(function, arguments, self.tos, reference_object)
		self.tos = new_frame
		result = self.exec_current_instruction()
		while result == Exec_Normal:
			result = self.exec_current_instruction()
		self.tos = self.tos.prev_frame
		return result
	
	def call_function(self, callable, arguments):
		callable[0].call(self, callable[1], arguments)

	def exec_current_instruction(self):
		instruction = self.tos.function.compiled_statements[self.tos.ip]
		spew("Executing instruction: " + str(instruction))
		return self.exec_table[instruction[0]](self, *instruction[1:])
		
	def _exec_eval(self, expression):
		self.eval(expression)
		self.tos.ip += 1
		return Exec_Normal
	
	def _exec_branch_if_zero(self, branch_target, test_expression):
		test_result = self.eval(test_expression)
		if(test_result == 0 or test_result == '\0'):
			self.tos.ip = branch_target
		else:
			self.tos.ip += 1
		return Exec_Normal
	
	def _exec_branch_if_nonzero(self, branch_target, test_expression):
		if(self.eval(test_expression) != 0):
			self.tos.ip = branch_target
		else:
			self.tos.ip += 1
		return Exec_Normal
	
	def _exec_branch_always(self, branch_target):
		self.tos.ip = branch_target
		return Exec_Normal
	
	def _exec_return(self, expression_list):
		list_len = len(expression_list)
		if list_len == 0:
			self.return_value = None
		elif list_len == 1:
			self.return_value = self.eval(expression_list[0])
		else:
			self.return_value = [self.eval(x) for x in expression_list]
		return Exec_Return

	def _exec_load_sub_function(self, register_index, sub_function_index):
		self.registers[register_index] = vm.function_record_instance(self.facet.functions[sub_function_index], self.tos)

	def eval(self, node):
		spew("  " * self.depth + "evaluating node: " + str(node))
		self.depth = self.depth + 1
		return_value = self.eval_table[node[0]](self, *node[1:])
		self.depth = self.depth - 1
		spew("  " * self.depth + "returned " + str(return_value))
		return return_value
	def eval_lvalue(self, node):
		return self.evallvalue_table[node[0]](self, *node[1:])
	def store(self, location, value):
		location[0][location[1]] = value

	def _eval_assign(self, left, right):
		self.store(self.eval_lvalue(left), self.eval(right))
	def _eval_float_assign(self, op, left, right):
		loc = self.eval_lvalue(left)
		
		index = loc[1]
		address = loc[0]
		if op == 'add':
			address[index] = address[index] + self.eval(right)
		elif op == 'subtract':
			address[index] = address[index] - self.eval(right)
		elif op == 'multiply':
			address[index] = address[index] * self.eval(right)
		elif op == 'divide':
			address[index] = address[index] / self.eval(right)
		elif op == 'modulus':
			address[index] = address[index] % self.eval(right)

	#bool_binary
	#   op
	#	   "compare_less"
	#	   "compare_greater"
	#	   "compare_less_or_equal"
	#	   "compare_greater_or_equal"
	#	   "compare_equal"
	#	   "compare_not_equal"
	#	   "logical_and"
	#	   "logical_or"
	#   left
	#   right
	def _eval_bool_binary(self, op, left, right):
		left_value = self.eval(left)
		right_value = self.eval(right)
		if op == "compare_less":
			return left_value < right_value
		elif op == "compare_greater":
			return left_value > right_value
		elif op == "compare_less_or_equal":
			return left_value <= right_value
		elif op == "compare_greater_or_equal":
			return left_value >= right_value
		elif op == "compare_equal":
			return left_value == right_value
		elif op == "compare_not_equal":
			return left_value != right_value
		elif op == "logical_and":
			return left_value and right_value
		elif op == "logical_or":
			return left_value or right_value
		raise fatal_error(self, "invalid bool_binary comparison op")

	def _eval_float_binary(self, op, left, right):
		if op == "add":
			spew("left: " + str(left))
			spew("right: " + str(right))
			return self.eval(left) + self.eval(right)
		elif op == "subtract":
			return self.eval(left) - self.eval(right)
		elif op == "multiply":
			return self.eval(left) * self.eval(right)
		elif op == "divide":
			return self.eval(left) / self.eval(right)
		elif op == "modulus":
			return self.eval(left) % self.eval(right)
	def _eval_local(self, local_index, type_spec):
		return self.tos.locals[local_index]
	def _eval_arg(self, arg_index):
		return self.tos.arguments[arg_index]
	def _evallvalue_local(self, local_index, type_record):
		return (self.tos.locals, local_index)
	def _evallvalue_ivar(self, ivar_index):
		return (self.tos.reference_object.slots, ivar_index)
	def _eval_prev_scope(self, prev_scope_node):
		save_top = self.tos
		self.tos = self.tos.reference_object
		result = self.eval(prev_scope_node)
		self.tos = save_top
		return result
	def _eval_global_node(self, node):
		return self.globals[node.global_index].eval(self)
	def _eval_sub_function(self, sub_function_index):
		# callables are (function_record, reference_object) pairs
		return (vm.function_record_instance(self.facet.functions[sub_function_index]), self.tos)
	def _eval_string_constant(self, value):
		return self.facet.string_constants[value]
	def _eval_int_constant(self, value):
		return value
	def _eval_strcat(self, op_str, left, right):
		spew("strcat " + str(left) + " " + str(right))
		return str(self.eval(left)) + op_str + str(self.eval(right))
	def _eval_func_call(self, func_expr, args):
		callable = self.eval(func_expr)
		evaluated_args = [self.eval(arg) for arg in args]
		self.call_function(callable, evaluated_args)
		return self.return_value
	def _eval_array_index(self, array_expr, index_expr):
		the_array = self.eval(array_expr)
		the_index = self.eval(index_expr)
		
		spew("  " * (self.depth + 1) + str(the_array) + " [ " + str(the_index) + " ] ")
		array_type = type(the_array)
		if array_type == types.ListType or array_type == types.DictType:
			return the_array[the_index]
		if array_type == types.StringType:
			if the_index >= len(the_array):
				return '\0'
			return the_array[the_index]
		pass
	def _eval_imethod(self, imethod_index):
		reference_object = self.tos.reference_object
		method = reference_object.id.vtable[imethod_index]
		spew("imethod: " + str(reference_object))
		return (vm.function_record_instance(method), reference_object) 
	def _eval_selfmethod_global(self, global_index):
		reference_object = self.tos.reference_object
		method = self.facet.functions[global_index]
		return (vm.function_record_instance(method), reference_object)
	def _eval_ivar(self, ivar_index):
 		return self.tos.reference_object.slots[ivar_index]

	#slot_expr
	#   object_expr
	#   slot_name
	def _eval_slot(self, object_expr, slot_name):
		the_object = self.eval(object_expr)
		the_slot = the_object.id.members[slot_name]
 		if the_slot.type == 'variable':
 			return the_object.slots[the_slot.index]
  		elif the_slot.type == 'function':
  			return (vm.function_record_instance(the_object.id.vtable[the_slot.index]), the_object)
	
   	#conditional_expr
   	#   test_expression
   	#   true_expression
   	#   false_expression
   	# ('conditional', test_expr, true_expr, false_expr)
   	def _eval_conditional(self, test_expr, true_expr, false_expr):
		value = self.eval(test_expr)
		if value != 0:
			return self.eval(true_expr)
		else:
			return self.eval(false_expr)
 
 	#array_expr
 	#   array_values
 	# ('array', [array_values])
 	def _eval_array(self, array_values_list):
 		result = []
 		for expr in array_values_list:
 			sub_result = self.eval(expr)
 			result.append(sub_result)
 		return result

	#map_expr
	#   map_pairs
	#	   map_pair
	#		   key
	#		   value
	def _eval_map(self, map_pairs_list):
		result = {}
		for pair in map_pairs_list:
			key = self.eval(pair[0])
			value = self.eval(pair[1])
			result[key] = value
		return result

	#('prev_scope', ()) - a reference to a variable in a previous scope
	#('local', local_index) - local variable
	#('arg', arg_index) - local argument
	#('sub_function', sub_function index)
	#('ivar', slot_index)
	#('imethod', vtable_index)
	#('global_node', global_node_index)
	#('int_constant', value)
	#('float_constant', value)
	#('string_constant', value)
	#('array_index', array_expr, index_expr)
	#('func_call_expr', func_expr, arg_1_expr, ... arg_n_expr)
	#('slot_expr', object_expr, slot_name)
	#locator_expr
	#   string
	#int_constant_expr
	#   value
	#float_constant_expr
	#   value
	#string_constant
	#   value
	#array_index_expr
	#   array_expr
	#   index_expr
	#func_call_expr
	#   func_expr
	#   args
	#unary_lvalue_op_expr
	#   expression
	#   op
	#	   "post_increment"
	#	   "post_decrement"
	#	   "pre_increment"
	#	   "pre_decrement"
	#unary_minus_expr
	#   expression
	#logical_not_expr
	#   expression
	#bitwise_not_expr
	#   expression
	#float_binary_expr
	#   left
	#   right
	#   op
	#	   "multiply"
	#	   "divide"
	#	   "modulus"
	#	   "add"
	#	   "subtract"
	#int_binary_expr
	#   left
	#   right
	#   op
	#	   "shift_left"
	#	   "shift_right"
	#	   "bitwise_and"
	#	   "bitwise_xor"
	#	   "bitwise_or"
	#bool_binary_expr
	#   left
	#   right
	#   op
	#	   "compare_less"
	#	   "compare_greater"
	#	   "compare_less_or_equal"
	#	   "compare_greater_or_equal"
	#	   "compare_equal"
	#	   "compare_not_equal"
	#	   "logical_and"
	#	   "logical_or"
	#strcat_expr
	#   left
	#   right
	#   op
	#	   "cat_none"
	#	   "cat_newline"
	#	   "cat_space"
	#	   "cat_tab"
	#assign_expr
	#   left
	#   right
	#float_assign_expr
	#   left
	#   right
	#   op
	#int_assign_expr
	#   left
	#   right
	#   op
	#function_expr
	#   parameter_list
	#   expr
