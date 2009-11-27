function test_function()
	var part1 = "hello"
	var part2 = ", world!"

	function get_letter(index)
		return part2[index]
	
	var result = part1
	var i

	for i = 0; part2[i]; i += 1
		print(i)
		result = result @ get_letter(i)
		if i > 20
			break
	return result

function main()
	var string = test_function()
	print(string)
