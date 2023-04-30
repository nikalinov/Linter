import re
import sys
import os
import ast
from copy import deepcopy


def is_snake_case(name):
    return re.match(r'[a-z_][a-z0-9_()]*', name)


def is_camel_case(name):
    return re.match(r'[A-Z][A-Za-z0-9()^_]', name)


# dictionary with S008, S009, S010, S011, S012 errors for each line
dic = {}


def check_functions(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # check if each argument of a function is in snake_case style
            for arg in node.args.args:
                if not is_snake_case(arg.arg):
                    dic[node.lineno]["S010"].append(arg.arg)
            # check all assignment variable names for snake_case style
            for body_node in node.body:
                if isinstance(body_node, ast.Assign):
                    for var in body_node.targets:
                        if isinstance(var, ast.Name) and not is_snake_case(var.id):
                            dic[var.lineno]["S011"].append(var.id)
            # check if any default values of the arguments are mutable
            for val in node.args.defaults:
                if isinstance(val, ast.List) or \
                   isinstance(val, ast.Dict) or \
                   isinstance(val, ast.Set):
                    dic[node.lineno]["S012"] = True
                    break
            # check if function names are in snake_case
            if not is_snake_case(node.name):
                dic[node.lineno]["S009"] = node.name
        elif isinstance(node, ast.ClassDef):
            # check if class names are in snake_case
            if not is_camel_case(node.name):
                dic[node.lineno]["S008"] = node.name


def analyze(file_name):
    if not os.access(file_name, os.R_OK):
        return

    file = open(file_name, encoding="utf8").read()

    global dic
    subdict = {"S008": "", "S009": "", "S010": [], "S011": [], "S012": False}
    dic = {line_num: deepcopy(subdict) for line_num in range(1, file.count('\n') + 2)}

    tree = ast.parse(file)
    #print(ast.dump(tree, indent=2))
    check_functions(tree)

    blank_line = 0
    for i, line in enumerate(file.split('\n'), start=1):
        if len(line) > 79:
            print(f'{file_name}: Line {i}: S001 Too Long')

        if (len(line) - len(line.lstrip(' '))) % 4 != 0:
            print(f'{file_name}: Line {i}: S002 Indentation is not a multiple of four')

        if '#' in line and line.split('#')[0].strip().endswith(';'):
            print(f'{file_name}: Line {i}: S003 Unnecessary semicolon')

        if '#' not in line and line.strip().endswith(';'):
            print(f'{file_name}: Line {i}: S003 Unnecessary semicolon')

        if not line.startswith('#') and '#' in line and not line.split('#')[0].endswith('  '):
            print(f'{file_name}: Line {i}: S004 At least two spaces before inline comment required')

        if '#' in line and 'todo' in line.split('#')[1].lower():
            print(f'{file_name}: Line {i}: S005 TODO found')

        if not line.strip():
            blank_line += 1
        else:
            if blank_line > 2:
                print(f'{file_name}: Line {i}: S006 More than two blank lines used before this line')
            blank_line = 0

        if ('def' in line or 'class' in line) and not re.match(r'\s*(def|class) \S', line):
            print(f"{file_name}: Line {i}: S007 Too many spaces after {'def' if 'def' in line else 'class'}")

        for error, val in dic[i].items():
            if error == "S008" and val:
                print(f"{file_name}: Line {i}: S008 Class name '{val}' should be written in CamelCase")
            elif error == "S009" and val:
                print(f"{file_name}: Line {i}: S009 Function name {val} should be written in snake_case")
            elif error == "S010":
                for arg in val:
                    print(f"{file_name}: Line {i}: S010 Argument name {arg} should be written in snake_case")
            elif error == "S011":
                for var in val:
                    print(f"{file_name}: Line {i}: S011 Variable {var} should be written in snake_case")
            elif val:
                print(f"{file_name}: Line {i}: S012 The default argument value is mutable")


def analyze_directory(dir_path):
    if not os.access(dir_path, os.R_OK):
        return
    for file_or_dir in os.listdir(dir_path):
        abs_path = os.path.join(dir_path, file_or_dir)
        if os.path.isfile(abs_path) and file_or_dir != "tests.py":
            analyze(abs_path)


def main():
    inp = sys.argv[-1]
    if os.path.isfile(inp):
        analyze(inp)
    else:
        analyze_directory(inp)


if __name__ == "__main__":
    main()
