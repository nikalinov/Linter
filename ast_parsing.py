import ast
from re import match


def is_snake_case(name):
    return match(r'[a-z_][a-z0-9_()]*', name)


def is_camel_case(name):
    return match(r'[A-Z][A-Za-z0-9()^_]', name)


class AstParser:
    """
    AstParser class. Functionality:

    -- detecting naming errors S008, S009, S010, S011, S012

    How to invoke: create an instance and use name_errors(tree) method.
    """
    def __init__(self):
        """
        self.errors -- error dictionary in the following format:

        {<line_no_1>: [['S008', <class_name>], ['S009', <func_name>],
                       ['S010', <arg_name>], ['S011': <var_name>], 'S012'],
         <line_no_2>: [...],
         ...}
        """
        self.errors = {}

    # check if each argument of a function is in snake_case style
    def check_arguments(self, node: ast.FunctionDef):
        for arg in node.args.args:
            if not is_snake_case(arg.arg):
                self.errors.setdefault(node.lineno, []).append(["S010", arg.arg])

    # check all assignment variable names for snake_case style
    def check_variables(self, node: ast.FunctionDef):
        for body_node in node.body:
            if isinstance(body_node, ast.Assign):
                for var in body_node.targets:
                    if isinstance(var, ast.Name) and not is_snake_case(var.id):
                        self.errors.setdefault(var.lineno, []).append(["S011", var.id])

    # check if any default values of the arguments are mutable
    def check_mutable_args(self, node: ast.FunctionDef):
        for val in node.args.defaults:
            if isinstance(val, ast.List) or \
               isinstance(val, ast.Dict) or \
               isinstance(val, ast.Set):
                self.errors.setdefault(node.lineno, []).append("S012")
                break

    # check if a function or class name is in snake or camel case, respectively
    def check_name(self, node):
        if isinstance(node, ast.FunctionDef) and not is_snake_case(node.name):
            self.errors.setdefault(node.lineno, []).append(["S009", node.name])

        elif isinstance(node, ast.ClassDef) and not is_camel_case(node.name):
            self.errors.setdefault(node.lineno, []).append(["S008", node.name])

    def name_errors(self, tree: ast.AST):
        """
        Find naming errors in a code, if any.

        :param: tree -- code in the format of an AST tree root
        :return: dictionary of errors for each line
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.check_arguments(node)
                self.check_variables(node)
                self.check_mutable_args(node)
                self.check_name(node)
            elif isinstance(node, ast.ClassDef):
                self.check_name(node)
        return self.errors
