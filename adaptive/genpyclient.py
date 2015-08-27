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

import sdl
from python import Pythonize, PyOutput, emit_type_check, process_declarations


class ClientMaker(PyOutput):

    def __init__(self):
        PyOutput.__init__(self)
        self.did_module_head = False
        self.module_name = None

    def module(self, m):
        self.ref("module %s {" % m.name)
        self.ref_indent()
        self.module_name = m.name

        for definition in m.definitions:
            if definition is None: continue
            kind = definition.__class__.__name__
            if kind == "Description":
                self.ref("""desc %s;""" % definition.content)
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

        self.ref_dedent()
        self.ref("};")

    def module_head(self):
        if self.did_module_head:
            return

        self.out("from adaptive import assert_list_of as _assert_list_of, sample_rpc as _sample_rpc")
        self.out("")
        self.out("""_remote_url = "http://127.0.0.1:8080/%s" """ % self.module_name)  # FIXME
        self.out("_service = _sample_rpc.Client(_remote_url)")

        self.did_module_head = True

    def struct(self, s):
        self.module_head()
        self.ref_struct(s)
        self.out("""%s = _service._getClass("%s")""" % (s.py_name, s.name))

    def operation(self, o):
        self.module_head()
        self.ref_operation(o)
        self.out("def %s(%s):" % (o.py_name, ", ".join(process_declarations(o.parameters))))
        self.indent()
        for parameter in o.parameters:
            has_null_default = parameter.default and parameter.default.py_name == "None"  # FIXME for non-string, non-null
            emit_type_check(self.out, parameter.py_name, parameter.type, or_none=has_null_default)
        self.out("res = _service.%s(%s)" % (o.py_name, ", ".join(p.py_name for p in o.parameters)))
        emit_type_check(self.out, "res", o.type, or_none=False)
        self.out("return res")
        self.dedent()


m = sdl.SDL().parse(open("../examples/petstore/petstore.sdl").read())
m.traverse(Pythonize())  # Add py_name attributes to the AST
#print m

cm = ClientMaker()
cm.module(m)
cm.dump()
