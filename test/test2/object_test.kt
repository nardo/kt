the_object
	var x = 10
	var y = 20
	function do_print()
		print("X = $x, Y = $y")
	method do_print: string1 with_arg: string2
		print("X = $x string1 = $string1 Y = $y arg = $string2")

function main()
	the_object.do_print()
	[the_object do_print]
	[the_object do_print:"hello" with_arg:"world"]
	
	var value = 10
	print(value == 10 ? "yes, it's 10" : "no, it's not!")
	var array = [10, 20, 30]
	print("This should be 30: " @ array[2])

	var map = { "foo" : "bar", "slash" : "dot", 100 : 5000 }
	print("This should be dot: " @ map["slash"])

	function test_function(func)
		print("Sub function result = " @ func(20))

	test_function(function(val) ( "sweetness! val = $val, value = $value" ) )

