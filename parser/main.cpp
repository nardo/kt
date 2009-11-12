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

PyObject *kt_build_pyobject_tree(parse_node *tree)
{
	PyObject *ret;
	if(!tree)
	{
		Py_INCREF(Py_None);
		return Py_None;
	}
	
	switch(tree->type)
	{
		case parse_node::type_node:
			// parse nodes become dictionaries:
			ret = PyDict_New();
			PyDict_SetItemString(ret, "type", PyString_FromString(tree->name));
			for(parse_node_property *walk = tree->property_list_head; walk; walk = walk->next)
				PyDict_SetItemString(ret, walk->name, kt_build_pyobject_tree(walk->value));
			return ret;
		case parse_node::type_integer:
			return PyInt_FromLong(tree->int_data);
		case parse_node::type_float:
			return PyFloat_FromDouble(tree->float_data);
		case parse_node::type_string:
			return PyString_FromString(tree->string_data);
		case parse_node::type_list:
			ret = PyList_New(0);
			for(parse_node *walk = tree->first; walk; walk = walk->next)
				PyList_Append(ret, kt_build_pyobject_tree(walk));
			return ret;
	}
	return NULL;
}

static PyObject *kt_parse_py(PyObject *self, PyObject *args)
{
	const char *script_data;
	if(!PyArg_ParseTuple(args, "s", &script_data))
		return NULL;
		
	uint len = strlen(script_data);
	parse_result result;
	kt_parse(script_data, len, result);
	result.dump_as_text();

	if(result.error)
		return NULL;
		
	PyObject *tree = kt_build_pyobject_tree(result.root);	
    Py_INCREF(tree);
	
    return tree;
}

static PyMethodDef kt_Methods[] = {
    {"parse",  kt_parse_py, METH_VARARGS,
     "Parse a single kt script."},
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
