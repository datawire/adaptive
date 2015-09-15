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
from quark.ast import quark

def value(node):
    code = Emitter()
    with code.block('package %s' % quark(node.package.name)):
        node.traverse(EncodeGenerator(code))
        node.traverse(DecodeGenerator(code))
    return code.dumps()

def service_client(node):
    code = Emitter()
    with code.block('package %s' % quark(node.package.name)):
        node.traverse(ClientGenerator(code))
    return code.dumps()

def service_server(node):
    code = Emitter()
    with code.block('package %s' % quark(node.package.name)):
        node.traverse(ServerGenerator(code))
    return code.dumps()

class Generator(object):

    def __init__(self, emitter):
        self.code = emitter

class EncodeGenerator(Generator):

    def visit_Class(self, cls):
        name = quark(cls.name)
        self.code('Map<String,Object> %s_toMap(%s object) {' % (name, name))
        self.code.indent()
        self.code('Map<String,Object> result = new Map<String,Object>();')

    def visit_Field(self, f):
        return self.code('result.put("%s", object.%s);' % (quark(f.name), quark(f.name)))

    def leave_Class(self, cls):
        self.code('return result;')
        self.code.dedent()
        self.code('}')

class DecodeGenerator(Generator):

    def visit_Class(self, cls):
        name = quark(cls.name)
        self.code('%s %s_fromMap(Map<String,Object> map) {' % (name, name))
        self.code.indent()
        self.code('%s result = new %s();' % (name, name))

    def visit_Field(self, f):
        self.code('result.%s = map.get("%s");' % (quark(f.name), quark(f.name)))

    def leave_Class(self, cls):
        self.code('return result;')
        self.code.dedent()
        self.code('}')

class ClientGenerator(Generator):

    def visit_Interface(self, i):
        with self.code.block("interface RPCClient"):
            self.code("Map<String,Object> call(String name, Map<String,Object> args);")

        self.code("class %sClient {" % i.name.text)
        self.code.indent()
        self.code("RPCClient rpc;")

    def leave_Interface(self, i):
        self.code.dedent()
        self.code("}")

    def visit_Method(self, m):
        self.code("%s %s(%s) {" % (m.type.quark(), m.name.quark(), quark(m.params)))
        self.code.indent()
        self.code("Map<String,Object> args = new Map<String,Object>();")

    def visit_Param(self, p):
        self.code('args.put("%s", %s);' % (quark(p.name), quark(p.name)))

    def leave_Method(self, m):
        self.code('Map<String,Object> map = self.rpc.call("%s", args);' % quark(m.name))
        tname = quark(m.type.path[0])
        if tname != "void":
            if tname == "List":
                self.code('%s result = new %s();' % (quark(m.type), quark(m.type)))
                self.code('List<Map<String,Object>> list = map.get("$result");')
                with self.code.block('if (list != null)'):
                    self.code('int idx = 0;')
                    with self.code.block('while (idx < list.size())'):
                        self.code('result.add(%s_fromMap(list.get(idx)));' % quark(m.type.parameters[0]))
                        self.code('idx = idx + 1;')
            else:
                self.code('%s result = %s_fromMap(map);' % (quark(m.type), quark(m.type)))
            self.code('return result;')
        self.code.dedent()
        self.code('}')

class ServerGenerator(Generator):

    def visit_Interface(self, i):
        name = quark(i.name)
        self.code('class %sServer {' % name)
        self.code.indent()
        self.code('%s impl;' % name)
        with self.code.block('%sServer(%s impl)' % (name, name)):
            self.code('self.impl = impl;')
        self.code('Map<String,Object> call(String name, Map<String,Object> args) {')
        self.code.indent()
        self.code('int idx;')
        self.code('Map<String,Object> map = new Map<String,Object>();')
        self.code('List<Map<String,Object>> list = new List<Map<String,Object>>();')

    def visit_Method(self, m):
        self.code('if (name == "%s") {' % quark(m.name))
        self.code.indent()

    def visit_Param(self, p):
        self.code('%s %s_%s = args.get("%s");' % (quark(p.type),
                                                  quark(p.callable.name),
                                                  quark(p.name),
                                                  quark(p.name)))

    def leave_Method(self, m):
        name = quark(m.name)
        params = ", ".join(["%s_%s" % (name, quark(p.name)) for p in m.params])
        call = 'self.impl.%s(%s);' % (name, params)
        rettype = quark(m.type.path[0])
        if rettype == "void":
            self.code(call)
        else:
            self.code('%s %s_result = %s' % (quark(m.type), name, call))
            if rettype == "List":
                eltype = quark(m.type.parameters[0])
                self.code('idx  = 0;')
                with self.code.block('while (idx < %s_result.size())' % name):
                    self.code('list.add(%s_toMap(%s_result.get(idx)));' % (eltype, name))
                    self.code('idx = idx + 1;')
                self.code('map.put("$result", list);')
            else:
                self.code('map = %s_toMap(%s_result);' % (rettype, name))
        self.code('map.put("$status", 200);')
        self.code('return map;')
        self.code.dedent()
        self.code('}')

    def leave_Interface(self, i):
        self.code('map.put("$status", 500);')
        self.code('return map;')
        self.code.dedent()
        self.code('}')
        self.code.dedent()
        self.code('}')
