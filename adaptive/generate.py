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
from adaptive.sdl import Operation


def process_declarations(declarations):
    res = []
    for declaration in declarations:
        if False and declaration.default:
            res.append("%s %s=%s" % (declaration.type, declaration.name, declaration.default))
        else:
            res.append("%s %s" % (declaration.type, declaration.name))
    return res


class Maker(object):

    def __init__(self):
        self.out = Emitter()
        self.ref = RefEmitter("// ", self.out)

        self.did_module_head = False
        self.did_module_body_lead_in = False
        self.module_name = None

    def dump(self, fd):
        return self.out.dump(fd)

    def module(self, m):
        self.ref.module_head(m)
        self.module_name = m.name
        self.mod = m

        for definition in m.definitions:
            if definition is None:
                continue
            kind = definition.__class__.__name__
            if kind == "Description":
                self.ref.description(definition)
                #self.out('"""')
                #self.out(str(definition.content)[1:-1])
                #self.out('"""')
            elif kind == "Defaults":
                self.ref("""defaults { %s };""" % "no content")
            elif kind == "Struct":
                self.struct(definition)
            elif kind == "Operation":
                self.operation(definition)
            else:
                raise ValueError("WTF? %s %s" % (kind, definition))

        self.ref.module_tail(m)
        self.module_tail()

    def module_head(self):
        raise NotImplementedError

    def module_tail(self):
        raise NotImplementedError

    def struct(self, st):
        self.module_head()
        assert not self.did_module_body_lead_in, "Must have all structs before any functions (to be fixed)"
        self.ref.struct(st)
        self.out("class %s {" % st.name)
        self.out("")
        with self.out.indentation():
            for field in st.fields:
                if field.default:
                    self.out("%s %s = %s;" % (field.type, field.name, field.default))
                else:
                    self.out("%s %s;" % (field.type, field.name))
            self.out("")
            self.out("%s(Map<String,Object> map) {" % st.name)
            with self.out.indentation():
                for field in st.fields:
                    self.out('self.%s = map.get("%s");' % (field.name, field.name))
            self.out("}")
            self.out("")
            self.out("Map<String,Object> toMap() {")
            with self.out.indentation():
                self.out("Map<String,Object> result = new Map<String,Object>();")
                for field in st.fields:
                    self.out('result.put("%s", %s);' % (field.name, field.name))
                self.out("return result;")
            self.out("}")
        self.out("}")
        self.out("")

    def operation(self, op):
        raise NotImplementedError


class ServerMaker(Maker):

    def module_body_lead_in(self):
        self.module_head()

        if self.did_module_body_lead_in:
            return

        self.out("class %s_server {" % self.module_name)
        self.out.indent()

        self.out("")
        self.out("%s impl;" % self.module_name)
        self.out("Map<String,Object> OK;")
        self.out("String name;")
        self.out("")

        self.out("%s_server(%s impl) {" % (self.module_name, self.module_name))
        with self.out.indentation():
            self.out("self.impl = impl;")
            self.out("self.OK = new Map<String,Object>();")
            self.out("""self.name = "%s";""" % self.module_name)
        self.out("}")

        self.out("")

        self.out("Map<String,Object> call(String name, Map<String,Object> args) {")
        self.out.indent()
        self.out('int idx;')
        self.out('Map<String,Object> map = new Map<String,Object>();')
        self.out('List<Map<String,Object>> list = new List<Map<String,Object>>();')
        self.did_module_body_lead_in = True

    def module_head(self):
        if self.did_module_head:
            return

        self.out("interface %s {" % self.module_name)

        with self.out.indentation():
            for op in self.mod.definitions:
                if isinstance(op, Operation):
                    if op.description:
                        pass
                        #self.out('"""' + op.description.content.text[1:-1] + '"""')
                    params = ["%s %s" % (p.type, p.name) for p in op.parameters]
                    self.out("%s %s(%s);" % (op.type, op.name, ", ".join(params)))

        self.out("}")
        self.out("")

        self.did_module_head = True

    def module_tail(self):
        self.out('map.put("$status", 500);')
        self.out('return map;')
        self.out.dedent()
        self.out("}")
        self.out.dedent()
        self.out("}")

    def operation(self, op):
        self.module_body_lead_in()
        self.ref.operation(op)
        self.out('if (name == "%s") {' % op.name)
        with self.out.indentation():
            for p in op.parameters:
                self.out('%s %s_%s = args.get("%s");' % (p.type, op.name, p.name, p.name))
            result = "%s_result" % op.name
            maybe_ret = "%s %s = " % (op.type, result) if op.type.name != "void" else ""
            self.out("%sself.impl.%s(%s);" % (maybe_ret, op.name,
                                             ", ".join(["%s_%s" % (op.name, p.name) for p in op.parameters])))
            self.out('map.put("$status", 200);')
            if maybe_ret:
                if op.type.name == "List":
                    self.out('idx = 0;')
                    self.out('while (idx < %s.size()) {' % result)
                    with self.out.indentation():
                        self.out('list.add(%s.get(idx).toMap());' % result)
                        self.out('idx = idx + 1;')
                    self.out('}')
                    self.out('map.put("$result", list);')
                else:
                    self.out('map.put("$result", %s.toMap());' % result)
            self.out("return map;")
        self.out("}")


class ClientMaker(Maker):

    def module_head(self):
        if self.did_module_head:
            return
        self.did_module_head = True

    def module_tail(self):
        self.out.dedent()
        self.out("}")

    def module_body_lead_in(self):
        self.module_head()

        if self.did_module_body_lead_in:
            return

        self.out("interface RPCClient {")
        with self.out.indentation():
            self.out("Map<String,Object> call(String name, Map<String,Object> args);")
        self.out("}")

        self.out("")

        self.out("class %s_client {" % self.module_name)
        self.out.indent()

        self.out("")
        self.out("RPCClient rpc;")
        self.out("String name;")
        self.out("")

        self.out("%s_client(RPCClient rpc) {" % self.module_name)
        with self.out.indentation():
            self.out("self.rpc = rpc;")
            self.out("""self.name = "%s";""" % self.module_name)
        self.out("}")
        self.out("")

        self.did_module_body_lead_in = True

    def operation(self, op):
        self.module_body_lead_in()
        self.ref.operation(op)

        if op.description:
            pass
            #self.out('"""' + op.description.content.text[1:-1] + '"""')
        self.out("%s %s(%s) {" % (op.type, op.name, ", ".join(process_declarations(op.parameters))))
        with self.out.indentation():
            self.out("Map<String,Object> args = new Map<String,Object>();")
            for param in op.parameters:
                self.out('args.put("%s", %s);' % (param.name, param.name))
            self.out('Map<String,Object> map = self.rpc.call("%s", args);' % op.name)
            if op.type.name != "void":
                if op.type.name == "List":
                    self.out('%s result = new %s();' % (op.type, op.type))
                    self.out('List<Map<String,Object>> list = map.get("$result");')
                    self.out('if (list != null) {')
                    with self.out.indentation():
                        self.out('int idx = 0;')
                        self.out('while (idx < list.size()) {')
                        with self.out.indentation():
                            self.out('result.add(new %s(list.get(idx)));' % op.type.parameters[0])
                            self.out('idx = idx + 1;')
                        self.out('}')
                    self.out('}')
                else:
                    self.out('%s result = new %s(map);' % (op.type, op.type))
                self.out("return result;")
        self.out("}")
