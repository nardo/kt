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


#include "core/platform.h"
namespace core
{
#include "core/core.h"
};


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
			PyObject_SetAttrString(ret, "type", PyString_FromString(tree->name));
			for(parse_node_property *walk = tree->property_list_head; walk; walk = walk->next)
				PyObject_SetAttrString(ret, walk->name, kt_build_pyobject_tree(walk->value, script_object_class));
			return ret;
			//// parse nodes become dictionaries:
			//ret = PyDict_New();
			//PyDict_SetItemString(ret, "type", PyString_FromString(tree->name));
			//for(parse_node_property *walk = tree->property_list_head; walk; walk = walk->next)
			//	PyDict_SetItemString(ret, walk->name, kt_build_pyobject_tree(walk->value));
			//return ret;
		case parse_node::type_integer:
			return PyInt_FromLong(tree->int_data);
		case parse_node::type_float:
			return PyFloat_FromDouble(tree->float_data);
		case parse_node::type_string:
			return PyString_FromString(tree->string_data);
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
	if(!PyArg_ParseTuple(args, "sO", &script_data, &script_object_class))
		return NULL;
	printf("** test 2 ** \n");
		
	uint len = strlen(script_data);
	parse_result result;
	kt_parse(script_data, len, result);
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

static PyMethodDef kt_Methods[] = {
    {"parse",  kt_parse_py, METH_VARARGS, "Parse a single kt script."},
	{"objc_test", kt_objc_test_py, METH_VARARGS, "Test some objective C action!."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

int main (int argc, char *  argv[])
{
	 /* Pass argv[0] to the Python interpreter */
    Py_SetProgramName(argv[0]);

    /* Initialize the Python interpreter.  Required. */
    Py_Initialize();
    Py_InitModule("kt", kt_Methods);
	Py_Main(argc, argv);
    return 0;
}
