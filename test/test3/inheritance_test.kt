class test_class(_x)
	var x = _x
	function do_print(foo)
		print("X = $x, foo = $foo")

class test_subclass(_x, _y) : test_class(_x)
	var y = _y
	function do_print(foo)
		parent.do_print(foo)
		print("X = $x, Y = $y")

object the_object : test_subclass(10, 20)
	var z = 30
	function do_print(foo)
		parent.do_print(foo)
		print("X = $x, Y = $y, Z = $z")

object container
	object sub_object1
		var x = 10
		var y = 10
	object sub_object2
		function do_print()
			print("X = " @ sub_object1.x @ " Y = " @ sub_object1.y)

object container2
	object sub_object1
		var x = 20
		var y = 20
	object sub_object2
		function do_print()
			print("X = " @ sub_object1.x @ " Y = " @ sub_object1.y)


function main()
	the_object.do_print(100)
	'container/sub_object2'.do_print()
	sub_object2.do_print()
	'container2/sub_object2'.do_print()
	//var object3 = new test_subclass(100, 200)
	//object3.do_print()
	var object4 = test_subclass("foo", "bar")
	object4.do_print(200)