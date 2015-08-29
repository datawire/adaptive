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

from adaptive.emit import Emitter, RefEmitter


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


class PythonMaker(object):

    def __init__(self):
        self.out = Emitter()
        self.ref = RefEmitter("## ", self.out)

        self.did_module_head = False
        self.did_module_body_lead_in = False
        self.module_name = None
        self.module_py_name = None

    def dump(self, fd):
        return self.out.dump(fd)

    def module(self, m):
        self.ref.module_head(m)
        self.module_name = m.name
        self.module_py_name = m.py_name

        for definition in m.definitions:
            if definition is None:
                continue
            kind = definition.__class__.__name__
            if kind == "Description":
                self.ref.description(definition)
                self.out('"""')
                self.out(str(definition.content)[1:-1])
                self.out('"""')
            elif kind == "Defaults":
                self.ref("""defaults { %s };""" % "no content")
            elif kind == "Struct":
                self.struct(definition)
            elif kind == "Operation":
                self.operation(definition)
            else:
                raise ValueError("WTF? %s %s" % (kind, definition))

        self.ref.module_tail(m)

    def module_head(self):
        raise NotImplementedError

    def struct(self, st):
        self.module_head()
        assert not self.did_module_body_lead_in, "Must have all structs before any functions (to be fixed)"
        self.ref.struct(st)
        self.out("@AdaptiveValue")
        self.out("class %s(AdaptiveValueType):" % st.py_name)
        with self.out.indentation():
            self.out("__slots__ = " + ", ".join('"%s"' % field.name for field in st.fields))
            self.out("")
            self.out("def __init__(self, %s):" % ", ".join(process_declarations(st.fields)))
            with self.out.indentation():
                self.out("AdaptiveValueType.__init__(self)")
                for field in st.fields:
                    self.out("self.%s = %s" % (field.name, field.py_name))  # FIXME is this okay?
        self.out("")

    def operation(self, op):
        raise NotImplementedError


class ServerMaker(PythonMaker):

    def module_body_lead_in(self):
        self.module_head()

        if self.did_module_body_lead_in:
            return

        self.out("class %s_server(object):" % self.module_py_name)
        self.out("")
        self.out.indent()

        self.out("def __init__(self, impl):")
        with self.out.indentation():
            self.out("self.impl = impl")
            self.out("""self.name = "%s" """ % self.module_name)

        self.did_module_body_lead_in = True

    def module_head(self):
        if self.did_module_head:
            return

        self.out("")
        self.out("from adaptive.python.runtime import AdaptiveValue, AdaptiveValueType, assert_list_of")
        self.out("")

        self.did_module_head = True

    def operation(self, op):
        self.module_body_lead_in()
        self.ref.operation(op)

        self.out("def %s(self, %s):" % (op.py_name, ", ".join(process_declarations(op.parameters))))
        with self.out.indentation():
            if op.description:
                self.out('"""' + op.description.content.text[1:-1] + '"""')
            for parameter in op.parameters:
                has_null_default = parameter.default and str(parameter.default) == "null"
                emit_type_check(self.out, parameter.py_name, parameter.type, or_none=has_null_default)
            self.out("res = self.impl.%s(%s)" % (op.py_name, ", ".join(p.py_name for p in op.parameters)))
            emit_type_check(self.out, "res", op.type, or_none=False)
            self.out("return res")


class ClientMaker(PythonMaker):

    def module_head(self):
        if self.did_module_head:
            return

        self.out("")
        self.out("from adaptive.python.runtime import AdaptiveValue, AdaptiveValueType, assert_list_of")
        self.out("from adaptive.python.sample_rpc import RPCClient")
        self.out("")

        self.did_module_head = True

    def module_body_lead_in(self):
        self.module_head()

        if self.did_module_body_lead_in:
            return

        self.out("class %s_client(object):" % self.module_py_name)
        self.out("")
        self.out.indent()

        self.out("def __init__(self, url):")
        with self.out.indentation():
            self.out("self.rpc = RPCClient(url)")
            self.out("""self.name = "%s" """ % self.module_name)
        self.out("")

        self.did_module_body_lead_in = True

    def operation(self, op):
        self.module_body_lead_in()
        self.ref.operation(op)

        self.out("def %s(self, %s):" % (op.py_name, ", ".join(process_declarations(op.parameters))))
        with self.out.indentation():
            if op.description:
                self.out('"""' + op.description.content.text[1:-1] + '"""')
            for parameter in op.parameters:
                has_null_default = parameter.default and str(parameter.default) == "null"
                emit_type_check(self.out, parameter.py_name, parameter.type, or_none=has_null_default)
            self.out("""res = self.rpc.call("%s", (%s,))""" % (op.py_name, ", ".join(p.py_name for p in op.parameters)))
            emit_type_check(self.out, "res", op.type, or_none=False)
            self.out("return res")
