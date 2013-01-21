function test_function()
	var part1: string = "hello"
	var part2: string = ", world!"

	function get_letter(index)
		return part2[index]
	
	var result = part1
	var i: integer

	for i = 0; part2[i]; i += 1
		print(i)
		result = result @ get_letter(i)
		if i > 20
			break
	return result

function multi_return_type()
	return "hello, world - sorry, the multiple return expressions feature has been removed."

function main()
	var string = test_function()
	print(string)
