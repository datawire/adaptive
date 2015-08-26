import sys

py_reserved = set("id is class def".split())  # FIXME
def py_name(name):
    if name in py_reserved:
        return name + "_"
    return name

sdl_to_python = {
    "int32": "int",
    "int64": "int",
    "double": "float",
    "string": "basestring"
}
def py_Typename(name):
    return sdl_to_python.get(name, name)

class Pythonize(object):
    "Add py_name node attributes"

    def visit_DEFAULT(self, node):
        print "DEFAULT", repr(node)

    def visit_Module(self, node):
        node.py_name = py_name(node.name)

    def visit_Struct(self, node):
        node.py_name = py_name(node.name)

    def visit_Field(self, node):
        node.py_name = py_name(node.name)

    def visit_Parameter(self, node):
        node.py_name = py_name(node.name)
        if node.default:
            if node.default.name == "null":
                node.default.py_name = "None"
            else:
                node.default.py_name = repr(node.default.name)

    def visit_Operation(self, node):
        node.py_name = py_name(node.name)

    def visit_Type(self, node):
        node.py_name = py_Typename(node.name)

class PyOutput(object):
    "Generate decent-looking Python code"

    def __init__(self):
        self.lines = []
        self.main_indent_level = 0
        self.ref_indent_level = 0

    def out(self, line):
        self.lines.append(self.main_indent_level * "    " + line.strip())

    def ref(self, line):
        self.lines.append("## " + self.ref_indent_level * "    " + line.strip())

    def indent(self):
        self.main_indent_level += 1

    def dedent(self):
        assert self.main_indent_level > 0, (self.main_indent_level, "\n".join(self.lines))
        self.main_indent_level -= 1

    def ref_indent(self):
        self.ref_indent_level += 1

    def ref_dedent(self):
        assert self.ref_indent_level > 0, (self.ref_indent_level, "\n".join(self.lines))
        self.ref_indent_level -= 1

    def dump(self, fd=sys.stdout):
        # Fancy print...
        wasPassThru = True
        for line in self.lines:
            isPassThru = line.startswith("## ")
            if isPassThru != wasPassThru:
                fd.write("\n")
            fd.write(line)
            fd.write("\n")
            wasPassThru = isPassThru
