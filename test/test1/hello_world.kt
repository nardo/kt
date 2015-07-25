function test_function(foo)
	var part1: string = "hello"
	var part2: string = ", world!"

	function get_letter(index: int32) -> int32
		foo = 10
		return part2[index]
	
	var result = part1
	var i: int32

	for i = 0; part2[i]; i += 1
		print(i)
		result = result @ get_letter(i)
		if i > 20
			break
	print(foo)
	return result

function main()
	var the_string = test_function(11)
	print(the_string)
