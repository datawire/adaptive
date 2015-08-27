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

from python import PyOutput, emit_type_check, process_declarations


class ServerMaker(PyOutput):

    def __init__(self):
        PyOutput.__init__(self)
        self.did_module_head = False
        self.did_module_body = False
        self.module_name = None
        self.module_py_name = None

    def module(self, m):
        self.ref("module %s {" % m.name)
        self.ref_indent()
        self.module_name = m.name
        self.module_py_name = m.py_name

        for definition in m.definitions:
            if definition is None:
                continue
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

        self.out("from adaptive import AdaptiveValue, AdaptiveValueType, AdaptiveException, assert_list_of")
        self.out("")
        self.out("""service_name = "%s" """ % self.module_name)

        self.did_module_head = True

    def struct(self, s):
        self.module_head()
        assert not self.did_module_body, "Must have all structs before any functions (to be fixed)"

        self.ref_struct(s)
        self.def_struct(s)

    def module_body(self):
        self.module_head()

        if self.did_module_body:
            return

        self.out("")
        self.out("class %s_server(object):" % self.module_py_name)
        self.out("")
        self.indent()

        self.out("def __init__(self, impl):")
        self.indent()
        self.out("self.impl = impl")
        self.dedent()
        self.out("")

        self.did_module_body = True

    def operation(self, o):
        self.module_body()
        self.ref_operation(o)

        self.out("def %s(self, %s):" % (o.py_name, ", ".join(process_declarations(o.parameters))))
        self.indent()
        if o.description:
            self.out('"""' + o.description.content.text[1:-1] + '"""')
        for parameter in o.parameters:
            has_null_default = parameter.default and str(parameter.default) == "null"  # FIXME for non-string, non-null
            emit_type_check(self.out, parameter.py_name, parameter.type, or_none=has_null_default)
        self.out("res = self.impl.%s(%s)" % (o.py_name, ", ".join(p.py_name for p in o.parameters)))
        emit_type_check(self.out, "res", o.type, or_none=False)
        self.out("return res")
        self.dedent()
