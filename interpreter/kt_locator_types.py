
class locator_types:
	# different types of locators.  The first set (up to last_lvalue_type) can be lvalues in expressions
	unknown = 0
	local_variable = 1
	prev_scope_variable = 2
	instance_variable = 3
	last_lvalue = 3 #------------
	method = 4
	child_function = 5
	prev_scope_child_function = 6
	builtin_function = 7
	reference = 8
	builtin_type = 9

	def is_variable(locator_type):
		return locator_type == locator_types.local_variable or locator_type == locator_types.prev_scope_variable or locator_type == locator_types.instance_variable or locator_type == locator_types.global_variable

	def is_function(locator_type):
		return locator_type == locator_types.global_function or locator_type == locator_types.child_function or locator_type == locator_types.prev_scope_function or locator_type == locator_types.builtin_function
