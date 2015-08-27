# Copyright 2015 datawire. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Helpers for generating Python code

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
def py_typename(name):
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

    def visit_Null(self, node):
        node.py_name = "None"

    def visit_StringLiteral(self, node):
        # XXX: this depends on SDL literals matching python literals
        node.py_name = node.text

    def visit_Operation(self, node):
        node.py_name = py_name(node.name)

    def visit_Type(self, node):
        node.py_name = py_typename(node.name)


def process_declarations(declarations):
    res = []
    for declaration in declarations:
        if declaration.default:
            res.append("%s=%s" % (declaration.py_name, declaration.default.py_name))
        else:
            res.append(declaration.py_name)
    return res


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

    def ref_struct(self, st):
        self.ref("struct %s {" % st.name)
        self.ref_indent()
        for field in st.fields:
            self.ref(str(field))
        self.ref_dedent()
        self.ref("};")

    def ref_operation(self, op):
        self.ref("%s %s(%s) {" % (op.type, op.name, ", ".join(str(p) for p in op.parameters)))
        self.ref_indent()
        # FIXME: Loop over contents of operation here, once they are parsed and available.
        self.ref_dedent()
        self.ref("};")

    def dump(self, fd=sys.stdout):
        # Fancy print...
        was_pass_thru = True
        for line in self.lines:
            is_pass_thru = line.startswith("## ")
            if is_pass_thru != was_pass_thru:
                fd.write("\n")
            fd.write(line.rstrip())
            fd.write("\n")
            was_pass_thru = is_pass_thru


def assert_list_of(lst, typ, or_none=True):
    assert isinstance(lst, list), lst
    if or_none:
        for idx, value in enumerate(lst):
            assert value is None or isinstance(value, typ), (idx, value)
    else:
        for idx, value in enumerate(lst):
            assert isinstance(value, typ), (idx, value)
    return True


def emit_type_check(out, name, typ, or_none=True):
    d = dict(name=name, typ=typ.py_name)
    if typ.name == "void":
        out("assert %(name)s is None, %(name)s" % d)
    elif typ.parameters:
        assert len(typ.parameters) == 1, "Unimplemented: %s" % typ
        assert typ.name == "List",  "Unimplemented: %s" % typ
        d["param"] = typ.parameters[0].py_name
        if or_none:
            out("assert %(name)s is None or _assert_list_of(%(name)s, %(param)s), %(name)s" % d)
        else:
            out("_assert_list_of(%(name)s, %(param)s), %(name)s" % d)
    else:
        if or_none:
            out("assert %(name)s is None or isinstance(%(name)s, %(typ)s), %(name)s" % d)
        else:
            out("assert isinstance(%(name)s, %(typ)s), %(name)s" % d)
