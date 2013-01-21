
class locator_types:
	# different types of locators.  The first set (up to last_lvalue_type) can be lvalues in expressions
	unknown_type = 0
	local_variable_type = 1
	prev_scope_variable_type = 2
	instance_variable_type = 3
	global_variable_type = 4
	last_lvalue_type = 4 #------------
	method_type = 5
	reference_type = 6
	global_function_type = 7
	child_function_type = 8
	prev_scope_child_function_type = 9
	builtin_class_type = 10
	builtin_function_type = 11
	builtin_type_type = 12

	def is_variable(locator_type):
		return locator_type == locator_types.local_variable_type or locator_type == locator_types.prev_scope_variable_type or locator_type == locator_types.instance_variable_type or locator_type == locator_types.global_variable_type

	def is_function(locator_type):
		return locator_type == locator_types.global_function_type or locator_type == locator_types.child_function_type or locator_type == locator_types.prev_scope_function_type or locator_type == locator_types.builtin_function_type
