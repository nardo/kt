
class locator_types:
	# different types of locators.  The first set (up to last_lvalue_type) can be lvalues in expressions
	unknown = 0
	local_variable = 1
	local_parameter = 2
	prev_scope_variable = 3
	prev_scope_parameter = 4
	instance_variable = 5
	last_lvalue = 5 #------------
	method = 6
	child_function = 7
	prev_scope_child_function = 8
	builtin_function = 9
	reference = 10
	builtin_type = 11

	def is_variable(locator_type):
		return locator_type == locator_types.local_variable or locator_type == locator_types.prev_scope_variable or locator_type == locator_types.instance_variable or locator_type == locator_types.global_variable

	def is_function(locator_type):
		return locator_type == locator_types.global_function or locator_type == locator_types.child_function or locator_type == locator_types.prev_scope_function or locator_type == locator_types.builtin_function
