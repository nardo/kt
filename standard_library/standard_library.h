#include <stdlib.h>

struct kt_string_constant
{
	int len;
	const char *data;
};

struct kt_string
{
	int ref_count;
	int len;
	char data[1];
};

class kt_object
{

};

class kt_variable
{
	public:
	enum type {
		type_nil,
		type_int,
		type_double,
		type_string,
		type_string_constant,
		type_object_ptr,
		num_types,
	};
	type variable_type;
	typedef void (*dtor)(kt_variable *var);
	static dtor destructors[num_types];
	
	union
	{
		int int_value;
		double double_value;
		kt_string *string_value;
		kt_string_constant *string_constant_value;
	};
	kt_variable()
	{
		variable_type = type_nil;
	}
	~kt_variable()
	{
		destructors[variable_type](this);
	}
	void operator=(kt_string_constant &constant)
	{
		destructors[variable_type](this);
		variable_type = type_string_constant;
		string_constant_value = &constant;
	}
	void operator=(int value)
	{
		destructors[variable_type](this);
		variable_type = type_int;
		int_value = value;
	}
	void operator=(double value)
	{
		destructors[variable_type](this);
		variable_type = type_double;
		double_value = value;
	}
	void operator=(kt_string &str)
	{
	
	}
};

void destruct_nil(kt_variable *var)
{
}

void destruct_string(kt_variable *string)
{
	if(!--string->string_value->ref_count)
		free(string->string_value);
}

void destruct_object(kt_variable *object)
{
}

kt_variable::dtor kt_variable::destructors[kt_variable::num_types] = {
	destruct_nil,
	destruct_nil,
	destruct_nil,
	destruct_string,
	destruct_nil,
	destruct_object,
};
