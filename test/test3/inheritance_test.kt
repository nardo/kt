class test_class(_x)
	var x = _x
	function do_print()
		print("X = $x")

class test_subclass(_x, _y) : test_class(_x)
	var y = _y
	function do_print()
		parent.do_print()
		print("X = $x, Y = $y")

object the_object : test_subclass(10, 20)
	var z = 30
	function do_print()
		parent.do_print()
		print("X = $x, Y = $y, Z = $z")

function main()
	the_object.do_print()