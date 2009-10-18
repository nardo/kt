// (C) 2009 Mark Frohnmayer.  The use of this code is governed by its license.  See /license/info.txt in the source distribution for the full license agreement.

struct parse_node;
struct parse_result;

struct parse_node_property
{
	const char *name;
	parse_node *value;
	parse_node_property *next;
};

// the parser class takes as input a string to parse.
struct parse_node
{
	enum parse_node_type
	{
		type_node,
		type_integer,
		type_float,
		type_string,
		type_list,
	};
	const char *name;
	parse_node *next;
	parse_node_property *property_list_head;
	parse_node_property *property_list_tail;
	parse_node_type type;
	
	char *string_data;
	uint string_data_len;
	int int_data;
	double float_data;
	
	void append(parse_node *node)
	{
		parse_node *walk;
		for(walk = this; walk->next; walk = walk->next)
			;
		walk->next = node;
	}

	inline void set_property(parse_result *result, const char *property_name, parse_node *property_value);
};

typedef parse_node *parse_node_ptr;

struct parse_result
{
	parse_node *root;
	uint line_count;
	bool error;
	uint error_line_number;
	uint error_column_number;
	formatted_string_buffer error_string;
	
	parse_result()
	{
		root = 0;
		error = false;
		error_line_number = 0;
		error_column_number = 0;
		line_count = 0;
	}
	
	parse_node *add_list(parse_node *first_element)
	{
		parse_node *ret = _alloc_node();
		ret->type = parse_node::type_list;
		ret->next = first_element;
		return ret;
	}
	
	parse_node *add_node(const char *node_name)
	{
		parse_node *ret = _alloc_node();
		ret->type = parse_node::type_node;
		ret->name = node_name;
		return ret;
	}
	
	parse_node *add_int(int integer_value)
	{
		parse_node *ret = _alloc_node();
		ret->type = parse_node::type_integer;
		ret->int_data = integer_value;
		return ret;
	}
	
	parse_node *add_float(double float_value)
	{
		parse_node *ret = _alloc_node();
		ret->type = parse_node::type_float;
		ret->float_data = float_value;
		return ret;
	}
	
	parse_node *add_string(const char *string, uint string_len)
	{
		parse_node *ret = _alloc_node();
		ret->type = parse_node::type_string;
		ret->string_data = (char *) allocate(string_len + 1);
		ret->string_data_len = string_len;
		memcpy(ret->string_data, string, string_len);
		ret->string_data[string_len] = 0;
		return ret;
	}

	void dump_as_text()
	{
		if(error)
		{
			printf("Error (%d:%d): %s\n", error_line_number, 
					error_column_number, error_string.c_str());
			return;
		}
		_dump_node(root, 0);
		printf("\n");
	}
	void *allocate(uint byte_size)
	{
		return _allocator.allocate(byte_size);
	}

private:
	page_allocator _allocator;
	
	void _dump_node(parse_node *node, uint depth)
	{
		if(!node)
		{
			printf("<null>");
			return;
		}
		switch(node->type)
		{
			case parse_node::type_node:
			{
				printf("\n%*c%s (node)", depth * 2, ' ', node->name);
				for(parse_node_property * walk = node->property_list_head; 
						walk; walk = walk->next)
				{
					printf("\n%*c%s = ", depth * 2 + 2, ' ', walk->name);
					_dump_node(walk->value, depth + 2);
				}
				break;
			}
			case parse_node::type_integer:
				printf("%d", node->int_data);
				break;
			case parse_node::type_float:
				printf("%gf", node->float_data);
				break;
			case parse_node::type_string:
				printf("\"%s\"", node->string_data);
				break;
			case parse_node::type_list:
				printf("( ");
				for(parse_node *walk = node->next; walk; walk = walk->next)
				{
					_dump_node(walk, depth + 2);
					printf(", ");
				}
				printf(" )");
				break;
					
		}
	}

	parse_node *_alloc_node()
	{
		parse_node *ret = (parse_node *) allocate(sizeof(parse_node));
		ret->name = 0;
		ret->next = 0;
		ret->property_list_head = ret->property_list_tail = 0;
		ret->string_data = 0;
		ret->string_data_len = 0;
		ret->int_data = 0;
		ret->float_data = 0;
		return ret;
	}
	
};

inline void parse_node::set_property(parse_result *result, const char *property_name, parse_node *property_value)
{
	parse_node_property *prop = (parse_node_property *) 
		result->allocate(sizeof(parse_node_property));
	prop->next = 0;
	prop->name = property_name;
	prop->value = property_value;
	
	if(property_list_head)
	{
		property_list_tail->next = prop;
		property_list_tail = prop;
	}
	else
		property_list_head = property_list_tail = prop;
}


// the parse function takes as input a string to parse and a parse_result structure to return the
// parse tree in.  The parse function returns true if the parse was successful, and false if there
// was an error.

static void parse(const char *parse_string, uint parse_string_len, parse_result &result);
