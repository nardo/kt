class test_class(_x, _y)
	var x = _x
	var y = _y

object the_object : test_class(10, 20)
	var z = 30
	function do_print()
		print("X = $x, Y = $y, Z = $z")

function main()
	the_object.do_print()