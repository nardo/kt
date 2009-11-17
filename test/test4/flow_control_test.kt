function test_switch(value)
	switch value
		case "hello"
			print("Got hello")
			break
		case "world"
			print("Got world")
			break
		case 10
			print("Got 10, falling through")
		case 20
			print("Got 20, falling through")
		default
			print("default case")
	print("done with switch")

function main()
	test_switch("hello")
	test_switch("world")
	test_switch(10)
	test_switch(20)
	test_switch(30)
