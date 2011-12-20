# kt_file_tree.py
# functionality for converting a directory tree into an internal representation the compiler can understand
# (C) 2009 Mark Frohnmayer.  The use of this code is governed by its license.  See /license/info.txt in the source distribution for the full license agreement.

import os
import stat
import kt

class ast_node:
	def dump(self, level):
		pass

def dump_ast(node, level):
	if node is None:
		return "<null>"
	elif node.__class__ == list:
		return "( " + ", ".join( (dump_ast(x, level + 2) for x in node) ) + " )"
	elif node.__class__ == ast_node:
		return "\n" + " " * (level * 2) + "node" + "".join ( "\n" + " " * (level * 2 + 2) + str(field_name) + " = " + dump_ast(node.__dict__[field_name], level + 2) for field_name in node.__dict__.keys() )
	elif node.__class__ == str:
		return "\"" + node + "\""
	else:
		return str(node)

class file_tree_node:
    def __init__(self, name, type, parse_result):
        self.name = name
        self.type = type
        self.contents = {}
        self.parse_result = parse_result
        
def build_file_tree(root_path):
    def recurse_directory(node, node_path):
        dir_contents = os.listdir(node_path)
        for file in dir_contents:
            #ignore hidden files
            if file[0] == '.':
                continue
            file_path = node_path + '/' + file
            file_stat = os.stat(file_path)
            if stat.S_ISDIR(file_stat.st_mode):
                file_node = file_tree_node(file, 'directory', None)
                node.contents[file] = file_node
                recurse_directory(file_node, file_path)
            elif file.endswith('.kt'):
                print "Compiling ... " + file_path
                kt_file = open(file_path, "rb")
                text = kt_file.read()
                print text
                kt_file.close()
                parse_result = kt.parse(text, ast_node)
                print parse_result
                print dump_ast(parse_result, 0)
                node.contents[file] = file_tree_node(file, 'kt', parse_result)
            else:
                node.contents[file] = file_tree_node(file, 'resource', None)
    root = file_tree_node('', 'directory', None)
    recurse_directory(root, root_path)
    return root

def get_facet_set(file_tree):
    def recurse_decl(decl, facet_set):
        if type(decl) is dict:
            if decl['type'] == 'facet':
                facet_set.add(decl['name'])
            if 'facet_list' in decl and decl['facet_list'] is not None:
                facet_set.update(decl['facet_list'])
            if 'transmission_list' in decl and decl['transmission_list'] is not None:
                for trans_spec in decl['transmission_list']:
                    facet_set.add(trans_spec['from_facet'])
                    facet_set.add(trans_spec['to_facet'])
            for v in decl.values():
                recurse_decl(v, facet_set)
        elif type(decl) is list:
            for i in decl:
                recurse_decl(i, facet_set)
    def recurse_file_tree(node, facet_set):
        for child in node.contents.values():
            if child.type == 'directory':
                recurse_file_tree(child, facet_set)
            elif child.type == 'kt':
                recurse_decl(child.parse_result, facet_set)
    facet_set = set()
    recurse_file_tree(file_tree, facet_set)
    if len(facet_set) == 0:
        facet_set.add('Default')
    return facet_set

