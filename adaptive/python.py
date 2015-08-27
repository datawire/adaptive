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

import json, sys

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
    """Add py_name node attributes"""

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
    """Generate decent-looking Python code"""

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
        self.ref("desc %s;" % op.description.content)
        # FIXME: Loop over contents of operation here, once they are parsed and available.
        self.ref_dedent()
        self.ref("};")

    def def_struct(self, st):
        self.out("@AdaptiveValue")
        self.out("class %s(AdaptiveValueType):" % st.py_name)
        self.indent()
        self.out("__slots__ = " + ", ".join('"%s"' % field.name for field in st.fields))
        self.out("")

        self.out("def __init__(self, %s):" % ", ".join(process_declarations(st.fields)))
        self.indent()
        self.out("AdaptiveValueType.__init__(self)")
        for field in st.fields:
            self.out("self.%s = %s" % (field.name, field.py_name))  # FIXME is this okay?
        self.dedent()

        self.dedent()
        self.out("")

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


class AdaptiveValueType(object):
    __slots__ = ()
    __known_subclasses__ = {}  # name -> class

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        for slot_name in self.__slots__:
            if getattr(self, slot_name) != getattr(other, slot_name):
                return False
        return True

    def __to_jsonable__(self):
        # FIXME: Detect object cycles to avoid infinite recursion
        res = {"__adaptive_class_name__": self.__class__.__name__}
        for slot_name in self.__slots__:
            value = getattr(self, slot_name)
            if isinstance(value, AdaptiveValueType):
                res[slot_name] = value.__to_jsonable__()
            else:
                res[slot_name] = value
        return res

    @staticmethod
    def __from_jsonable__(value):
        class_name = value["__adaptive_class_name__"]
        class_ = AdaptiveValueType.__known_subclasses__[class_name]
        args = [value[slot_name] for slot_name in class_.__slots__]
        return class_(*args)


def AdaptiveValue(cls):
    AdaptiveValueType.__known_subclasses__[cls.__name__] = cls
    return cls


class AdaptiveJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, AdaptiveValueType):
            return obj.__to_jsonable__()
        return json.JSONEncoder.default(self, obj)


def adaptive_object_hook(obj_dict):
    try:
        return AdaptiveValueType.__from_jsonable__(obj_dict)
    except KeyError:
        return obj_dict


def serialize(obj):
    return json.dumps(obj, cls=AdaptiveJSONEncoder, separators=(',', ':'))


def deserialize(data):
    return json.loads(data, object_hook=adaptive_object_hook)


@AdaptiveValue
class AdaptiveException(AdaptiveValueType, Exception):
    __slots__ = "name", "value"

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return "%s: %s" % (self.name, self.value)


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
            out("assert %(name)s is None or assert_list_of(%(name)s, %(param)s), %(name)s" % d)
        else:
            out("assert_list_of(%(name)s, %(param)s), %(name)s" % d)
    else:
        if or_none:
            out("assert %(name)s is None or isinstance(%(name)s, %(typ)s), %(name)s" % d)
        else:
            out("assert isinstance(%(name)s, %(typ)s), %(name)s" % d)
