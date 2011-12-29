#include "core/platform.h"
namespace core
{
#include "core/core.h"

struct kt_program
{
	context _context;
	type_database _type_database;
	struct object : public ref_object
	{
		string dummy_field;
		int32 dummy_int;
		
		int32 get_integer()
		{
			return dummy_int;
		}
		void set_field(string arg)
		{
			dummy_field = arg;
		}
	};
	
	struct directory : public object
	{
		
	};
	
	static void print(string the_string)
	{
		printf("%s\n", the_string.c_str());
	}
	kt_program() : _type_database(&_context)
	{
		_type_database.add_basic_type("string", get_global_type_record<string>());
		_type_database.add_basic_type("int32", get_global_type_record<int32>());
		_type_database.add_basic_type("float64", get_global_type_record<float64>());
		_type_database.add_basic_type("none", get_global_type_record<empty_type>());
		_type_database.add_function("print", print);
		core_type_begin_class(_type_database, object, ref_object, false)
		core_type_slot(_type_database, object, dummy_field, 0)
		core_type_slot(_type_database, object, dummy_int, 0)
		core_type_method(_type_database, object, get_integer);
		core_type_method(_type_database, object, set_field);
		core_type_end_class(_type_database)
		core_type_begin_class(_type_database, directory, object, false)
		core_type_end_class(_type_database)
	}
};

};

/*
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
*/