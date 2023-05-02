import re
import sys
import os
import ast
from pathlib import Path
from ast_parsing import AstParser
from error_descr import error_descr


class Linter:
    """
    Linter class. Functionality:

    -- given a .py file or directory path, find style and naming errors
       for the file or all the .py files in the directory.

    How to invoke: create an instance and use analyze(path) method.
    """
    def __init__(self):
        """
        Initialize 2 dictionaries:
        all_errors -- dictionary with errors from all files. Structure:

        {<file_path_1>: {<line_no_1>: ['S001', 'S002', ..., ['S008', <class_name>],
                                                            ['S009', <func_name>],
                                                            ...
                                                            ['S011', <var_name>]],
                         <line_no_2>: [...],
                         ...}
         <file_path_2>: {<line_no_1>: ['S001', 'S002', ..., ['S008', <class_name>],
                                                            ['S009', <func_name>],
                                                            ...
                                                            ['S011', <var_name>]],
                         <line_no_2>: [...],
                         ...}
         ...}

        file_errors -- dictionary with local file errors. Structure:
                       same as ast_parsing.py 'errors' dictionary (see the docstring)

        files -- list with file path(s)
        """
        self.all_errors = {}
        self.file_errors = {}
        self.files = []

    def get_py_files(self, path):
        """
        Append .py file(s) to the 'files' instance variable.
        If path is a directory, find all .py files' paths in the subdirectories,
        if path is a file, append only it to the files list.

        :param: path -- relative or absolute directory or file path
        :return: None
        """
        if os.path.isfile(path):
            self.files.append(path)
            return

        if os.path.isabs(path):
            path = path[2:]

        for path in Path(path).rglob('*.py'):
            self.files.append(path)

    def sort_errors(self):
        for line_no, error_list in self.file_errors.items():
            # sort list of format:
            # [["S008", <class_name],...,["S011", <var_name>], "S001", ..., "S007"] =>
            # => ["S001", ..., "S007", ["S008", <class_name],...,["S011", <var_name>]]
            error_list.sort(key=lambda x: isinstance(x, list))

    def add_style_errors(self, file):
        """
        Given a file data, find style errors S001, S002, ...,
        S007 (full list is in error_descr.py) and append them to
        a list with the name errors.

        :param: file -- file data in string format
        :return: None
        """
        blank_lines = 0
        for i, line in enumerate(file.split('\n'), start=1):
            if len(line) > 79:
                self.file_errors.setdefault(i, []).append("S001")

            if (len(line) - len(line.lstrip(' '))) % 4 != 0:
                self.file_errors.setdefault(i, []).append("S002")

            if ('#' in line and line.split('#')[0].strip().endswith(';')) or \
                    ('#' not in line and line.strip().endswith(';')):
                self.file_errors.setdefault(i, []).append("S003")

            if not line.startswith('#') and '#' in line and \
                    not line.split('#')[0].endswith('  '):
                self.file_errors.setdefault(i, []).append("S004")
            if '#' in line and 'todo' in line.split('#')[1].lower():
                self.file_errors.setdefault(i, []).append("S005")

            if not line.strip():
                blank_lines += 1
            else:
                if blank_lines > 2:
                    self.file_errors.setdefault(i, []).append("S006")
                blank_lines = 0

            if ('def' in line or 'class' in line) and \
                    not re.match(r'\s*(def|class) \S', line):
                self.file_errors.setdefault(i, []).append("S007")

        self.sort_errors()

    def print_result(self):
        for file_path, file_errors in self.all_errors.items():
            for line_no, error_list in sorted(file_errors.items(), key=lambda x: x[0]):
                for error in error_list:
                    if isinstance(error, list):
                        error, entity_name = error[0], error[1]
                        message = error_descr[error].replace('-', entity_name)
                        print(f"{file_path}: Line {line_no}: {error} {message}")
                    else:
                        message = error_descr[error]
                        print(f"{file_path}: Line {line_no}: {error} {message}")

    def analyze(self, path):
        self.get_py_files(path)
        for file_path in self.files:
            self.analyze_file(file_path)
        self.print_result()

    def analyze_file(self, path):
        """
        Given a .py file path, find naming and style errors and
        record them in the 'all_errors' instance variable.

        :param: path: absolute or relative file path.
        :return: None
        """
        file = open(path, encoding="utf8").read()
        tree = ast.parse(file)
        ast_parser = AstParser()

        self.file_errors = ast_parser.name_errors(tree)
        self.add_style_errors(file)
        self.all_errors[path] = self.file_errors


def main():
    path = sys.argv[-1]
    linter = Linter()
    linter.analyze(path)


if __name__ == "__main__":
    main()
