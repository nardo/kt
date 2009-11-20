object the_object
	var x = 10
	var y = 20
	function do_print()
		print("X = $x, Y = $y")

function main()
	the_object.do_print()
	var value = 10
	print(value == 10 ? "yes, it's 10" : "no, it's not!")
	var array
	array = [10, 20, 30]
	print("This should be 30: " @ array[2])

	array = { "foo" : "bar", "slash" : "dot", 100 : 5000 }
	print("This should be dot: " @ array["slash"])