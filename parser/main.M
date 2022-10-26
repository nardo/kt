// (C) 2009 Mark Frohnmayer.  The use of this code is governed by its license.  See /license/info.txt in the source distribution for the full license agreement.

#include <iostream>
#include "kt.h"

#include <sys/types.h>
#include <sys/uio.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include "file.h"
#include "Python.h"
#include <objc/runtime.h>
#include <Foundation/NSBundle.h>
#include "standard_library.h"

void objc_test()
{
	NSBundle *bundle = [[NSBundle alloc] initWithPath: @"/System/Library/Frameworks/AppKit.framework"];
	printf("AppKit Bundle load success = %d\n", [bundle load]);
	
	Class *classes = NULL;
	int numClasses = objc_getClassList(NULL, 0);
	printf("Classes!\n");
	if (numClasses > 0)
	{
		classes = (Class *) malloc(sizeof(Class) * numClasses);
		numClasses = objc_getClassList(classes, numClasses);
		for(int i = 0; i < numClasses; i++)
		{
			const char *cname = class_getName(classes[i]);
			printf("ObjC class: %s\n", cname);
			unsigned count = 0;
			Method *method_list = (Method *) class_copyMethodList(classes[i], &count);
			for(int j = 0; j < count; j++)
			{
				Method the_method = method_list[j];
				SEL selector = method_getName(the_method);
				const char *sel_name = sel_getName(selector);
				unsigned arg_count = method_getNumberOfArguments(the_method);
				printf("  %s (%d) - encoding: %s\n", sel_name, arg_count, method_getTypeEncoding(the_method));
				char type_name_buffer[255];
				method_getReturnType(the_method, type_name_buffer, sizeof(type_name_buffer));
				printf("   returns %s\n", type_name_buffer);
				for(int k = 0; k < arg_count; k++)
				{
					method_getArgumentType(the_method, k, type_name_buffer, sizeof(type_name_buffer));
					printf("   arg %d: %s\n", k, type_name_buffer);
				}
			}
			free(method_list);
		}
		fflush(stdout);
		free(classes);
	}
}

PyObject *kt_build_pyobject_tree(parse_node *tree, PyObject *script_object_class)
{
	PyObject *ret;
	if(!tree)
	{
		return Py_None;
	}
	
	switch(tree->type)
	{
		case parse_node::type_node:
			ret = PyObject_CallObject(script_object_class, NULL);
			PyObject_SetAttrString(ret, "type", PyUnicode_FromString(tree->name));
			for(parse_node_property *walk = tree->property_list_head; walk; walk = walk->next)
				PyObject_SetAttrString(ret, walk->name, kt_build_pyobject_tree(walk->value, script_object_class));
			return ret;
			//// parse nodes become dictionaries:
			//ret = PyDict_New();
			//PyDict_SetItemString(ret, "type", PyUnicode_FromString(tree->name));
			//for(parse_node_property *walk = tree->property_list_head; walk; walk = walk->next)
			//	PyDict_SetItemString(ret, walk->name, kt_build_pyobject_tree(walk->value));
			//return ret;
		case parse_node::type_integer:
			return PyLong_FromLong(tree->int_data);
		case parse_node::type_float:
			return PyFloat_FromDouble(tree->float_data);
		case parse_node::type_string:
			return PyUnicode_FromString(tree->string_data);
		case parse_node::type_list:
			ret = PyList_New(0);
			for(parse_node *walk = tree->first; walk; walk = walk->next)
				PyList_Append(ret, kt_build_pyobject_tree(walk, script_object_class));
			return ret;
	}
	return NULL;
}

static PyObject *kt_parse_py(PyObject *self, PyObject *args)
{
	const char *script_data;
	PyObject *script_object_class;
	printf("** test 1 ** \n");
	if(!PyArg_ParseTuple(args, "yO", &script_data, &script_object_class))
		return NULL;
	printf("** test 2 ** %s\n", script_data);
		
	uint len = strlen(script_data);
	parse_result result;
	parse_buffer(script_data, len, result);
	result.dump_as_text();

	if(result.error)
		return NULL;
		
	PyObject *tree = kt_build_pyobject_tree(result.root, script_object_class);
    Py_INCREF(tree);
	
    return tree;
}

static PyObject *kt_objc_test_py(PyObject *self, PyObject *args)
{
	objc_test();
	return 0;
}

static PyObject *kt_query_builtins(PyObject *self, PyObject *args)
{
	const char *script_data;
	PyObject *script_object_class;
	if(!PyArg_ParseTuple(args, "O", &script_object_class))
		return NULL;
	parse_result result;
	parse_node_ptr builtins_node = result.add_node("object");
	parse_node_ptr parent_decl = result.add_node("parent_specifier");
	parent_decl->set_property(&result, "parent", result.add_c_string("directory"));
	parent_decl->set_property(&result, "args", result.add_list(NULL));

	builtins_node->set_property(&result, "parent_decl", parent_decl);
	builtins_node->set_property(&result, "is_public", result.add_int(0));
	builtins_node->set_property(&result, "name", result.add_c_string("builtins"));
	builtins_node->set_property(&result, "parameter_list", NULL);
	builtins_node->set_property(&result, "facet_list", NULL);
	parse_node_ptr body = result.add_list(NULL);
	builtins_node->set_property(&result, "body", body);
	
	core::dictionary<core::type_database::type_rep *>::pointer p = core::kt._type_database._class_table.first();
	while(p)
	{
		core::type_database::type_rep *val = *(p.value());
		if(val->kind == core::type_database::type_basic)
		{
			parse_node_ptr type_node = result.add_node("builtin_type");
			type_node->set_property(&result, "name", result.add_c_string(val->name.c_str()));
			type_node->set_property(&result, "is_numeric", result.add_int(val->type->is_numeric));
			body->append(type_node);
		}
		else
		{
			parse_node_ptr compound_node = result.add_node("builtin_class");
			compound_node->set_property(&result, "name", result.add_c_string(val->name.c_str()));
			parse_node_ptr compound_body = result.add_list(NULL);
			parse_node_ptr parent_specifier = result.add_node("parent_specifier");
			compound_node->set_property(&result, "parent_decl", parent_specifier);
			parent_specifier->set_property(&result, "args", result.add_list(NULL));
			if(val->parent_class)
				parent_specifier->set_property(&result, "name", result.add_c_string(val->parent_class->name.c_str()));
			else
				parent_specifier->set_property(&result, "name", NULL);

			compound_node->set_property(&result, "body", compound_body);
			for(core::dictionary<core::type_database::field_rep>::pointer fp = val->fields.first(); fp; fp = fp.next())
			{
				parse_node_ptr compound_field = result.add_node("builtin_slot");
				compound_field->set_property(&result, "name", result.add_c_string(fp.value()->name.c_str()));
				core::type_database::type_rep *field_type = core::kt._type_database.find_type(fp.value()->type);
				if(field_type)
				{
					parse_node_ptr type_spec = result.add_node("locator_type_specifier");
					type_spec->set_property(&result, "locator", result.add_c_string(field_type->name.c_str()));
					compound_field->set_property(&result, "type_spec", type_spec);
				}
				compound_body->append(compound_field);
			}
			for(core::hash_table_flat<core::indexed_string, core::function_record *>::pointer mp = val->method_table.first(); mp; ++mp)
			{
				const core::indexed_string *name = mp.key();
				core::function_record *func = *(mp.value());
				parse_node_ptr method_node = result.add_node("builtin_method");
				method_node->set_property(&result, "name", result.add_c_string(name->c_str()));

				printf("Adding method %s\n", name->c_str());

				parse_node_ptr parameters = result.add_list(NULL);
				method_node->set_property(&result, "parameter_list", parameters);
				core::function_type_signature *sig = func->get_signature();
				for(uint32 i = 0; i < sig->argument_count; i++)
				{
					core::type_record *param_type = sig->argument_types[i];
					core::type_database::type_rep *param_rep = core::kt._type_database.find_type(param_type);
					printf("Param - type %x\n", sig->argument_types[i]);
					parse_node_ptr parameter = result.add_node("parameter");
					parameter->set_property(&result, "name", NULL);
					if(param_rep)
					{
						parse_node_ptr type_spec = result.add_node("locator_type_specifier");
						type_spec->set_property(&result, "locator", result.add_c_string(param_rep->name.c_str()));
						parameter->set_property(&result, "type_spec", type_spec);
					}
					else
						parameter->set_property(&result, "type_spec", NULL);
					parameters->append(parameter);
				}
				core::type_database::type_rep *return_rep = core::kt._type_database.find_type(sig->return_type);
				if(return_rep)
				{
					parse_node_ptr type_spec = result.add_node("locator_type_specifier");
					type_spec->set_property(&result, "locator", result.add_c_string(return_rep->name.c_str()));
					method_node->set_property(&result, "return_type", result.add_list(type_spec));
				}
				else
					method_node->set_property(&result, "return_type", NULL);
				compound_body->append(method_node);
			}
			body->append(compound_node);
		}
		p = p.next();
	}
	for(core::hash_table_flat<core::indexed_string, core::function_record *>::pointer fp = core::kt._type_database._function_table.first(); fp; ++fp)
	{
		const core::indexed_string *name = fp.key();
		core::function_record *func = *(fp.value());
		parse_node_ptr function_node = result.add_node("builtin_function");
		function_node->set_property(&result, "name", result.add_c_string(name->c_str()));
		printf("Adding function %s\n", name->c_str());
		parse_node_ptr parameters = result.add_list(NULL);
		function_node->set_property(&result, "parameter_list", parameters);
		core::function_type_signature *sig = func->get_signature();
		for(uint32 i = 0; i < sig->argument_count; i++)
		{
			core::type_record *param_type = sig->argument_types[i];
					printf("Param - type %x\n", sig->argument_types[i]);
			core::type_database::type_rep *param_rep = core::kt._type_database.find_type(param_type);
			
			parse_node_ptr parameter = result.add_node("parameter");
			parameter->set_property(&result, "name", NULL);
			if(param_rep)
			{
				parse_node_ptr type_spec = result.add_node("locator_type_specifier");
				type_spec->set_property(&result, "locator", result.add_c_string(param_rep->name.c_str()));
				parameter->set_property(&result, "type_spec", type_spec);						
			}
			else
				parameter->set_property(&result, "type_spec", NULL);
			parameters->append(parameter);
		}
		core::type_database::type_rep *return_rep = core::kt._type_database.find_type(sig->return_type);
		if(return_rep)
		{
			parse_node_ptr type_spec = result.add_node("locator_type_specifier");
			type_spec->set_property(&result, "locator", result.add_c_string(return_rep->name.c_str()));
			function_node->set_property(&result, "return_type", type_spec);
		}
		else
			function_node->set_property(&result, "return_type", NULL);
		body->append(function_node);
	}
	PyObject *return_tree = kt_build_pyobject_tree(builtins_node, script_object_class);
	Py_INCREF(return_tree);
	return return_tree;
}

static PyMethodDef kt_methods[] = {
    {"parse",  kt_parse_py, METH_VARARGS, "Parse a single kt script."},
    {"query_builtins",  kt_query_builtins, METH_VARARGS, "Returns a python object tree of builtin objects."},
	{"objc_test", kt_objc_test_py, METH_VARARGS, "Test some objective C action!."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static struct PyModuleDef kt_module =
{
    PyModuleDef_HEAD_INIT,
    "kt", /* name of module */
    "",          /* module documentation, may be NULL */
    -1,          /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */
    kt_methods
};

PyMODINIT_FUNC
PyInit_kt(void)
{
    return PyModule_Create(&kt_module);
}

extern void parser_init();

int main (int argc, char *  argv[])
{
    parser_init();
	 /* Pass argv[0] to the Python interpreter */
    std::wstring app_name(argv[0], argv[0] + strlen(argv[0]));
    Py_SetProgramName(app_name.data());

    if (PyImport_AppendInittab("kt", PyInit_kt) == -1) {
        fprintf(stderr, "Error: could not extend in-built modules table\n");
        exit(1);
        
    }    /* Initialize the Python interpreter.  Required. */
    Py_Initialize();
    
    std::vector<std::wstring> args;
    for(int i = 0; i < argc; i++)
        args.push_back(std::wstring(argv[i], argv[i] + strlen(argv[i])));
    std::vector<const wchar_t *> arg_array;
    for(int i = 0; i < argc; i++)
        arg_array.push_back(args[i].data());
	Py_Main(argc, (wchar_t **) arg_array.data());
    return 0;
}
