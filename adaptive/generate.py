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
from quark.ast import code

def value(node):
    out = Emitter()
    with out.block('package %s' % code(node.package.name)):
        node.traverse(EncodeGenerator(out))
        node.traverse(DecodeGenerator(out))
    return out.dumps()

def service_client(node):
    out = Emitter()
    with out.block('package %s' % code(node.package.name)):
        node.traverse(ClientGenerator(out))
    return out.dumps()

def service_server(node):
    out = Emitter()
    with out.block('package %s' % code(node.package.name)):
        node.traverse(ServerGenerator(out))
    return out.dumps()

class Generator(object):

    def __init__(self, emitter):
        self.out = emitter

    def get_annotation(self, node, name):
        for ann in node.annotations:
            if code(ann.name) == name:
                return ann

class EncodeGenerator(Generator):

    def visit_Class(self, cls):
        name = code(cls.name)
        self.out('Map<String,Object> %s_toMap(%s object) {' % (name, name))
        self.out.indent()
        self.out('Map<String,Object> result = new Map<String,Object>();')

    def visit_Field(self, f):
        return self.out('result["%s"] = object.%s;' % (code(f.name), code(f.name)))

    def leave_Class(self, cls):
        self.out('return result;')
        self.out.dedent()
        self.out('}')

class DecodeGenerator(Generator):

    def visit_Class(self, cls):
        name = code(cls.name)
        self.out('%s %s_fromMap(Map<String,Object> map) {' % (name, name))
        self.out.indent()
        self.out('%s result = new %s();' % (name, name))

    def visit_Field(self, f):
        self.out('result.%s = map["%s"];' % (code(f.name), code(f.name)))

    def leave_Class(self, cls):
        self.out('return result;')
        self.out.dedent()
        self.out('}')

class ClientGenerator(Generator):

    def visit_Interface(self, i):
        with self.out.block("interface RPCClient"):
            self.out("Map<String,Object> call(String name, Map<String,Object> args);")

        with self.out.block("class CacheEntry"):
            self.out("Map<String,Object> result;")
            self.out("long timestamp = 0;")

        self.out("class %sClient {" % i.name.text)
        self.out.indent()
        self.out("RPCClient rpc;")
        self.out("""

        Map<Object,Map<String,Object>> index_entries = new Map<Object,Map<String,Object>>();

        Map<String,Object> index(String name, Map<String,Object> args) {
            // XXX: nothing updates the index right now!!!
            return index_entries[args];
        }

        Map<Object,CacheEntry> cache_entries = new Map<Object,CacheEntry>();

        Map<String,Object> cache(String name, Map<String,Object> args, long threshold) {
            CacheEntry entry;
            if (cache_entries.contains(args)) {
                entry = cache_entries[args];
            } else {
                entry = new CacheEntry();
                cache_entries[args] = entry;
            }
            if ((now() - entry.timestamp) > threshold) {
                entry.result = self.rpc.call(name, args);
                entry.timestamp = now();
            }
            return entry.result;
        }
        """)

    def leave_Interface(self, i):
        self.out.dedent()
        self.out("}")

    def visit_Method(self, m):
        self.out("%s %s(%s) {" % (m.type.code(), m.name.code(), code(m.params)))
        self.out.indent()
        self.out("Map<String,Object> args = new Map<String,Object>();")

    def visit_Param(self, p):
        self.out('args["%s"] = %s;' % (code(p.name), code(p.name)))

    def leave_Method(self, m):
        if self.get_annotation(m, "index"):
            meth = "index"
            extra = ""
        elif self.get_annotation(m, "cache"):
            ann = self.get_annotation(m, "cache")
            meth = "cache"
            extra = ", %s" % code(ann.arguments, ", ")
        else:
            meth = "rpc.call"
            extra = ""

        self.out('Map<String,Object> map = self.%s("%s", args%s);' % (meth, code(m.name), extra))
        tname = code(m.type.path[0])
        if tname != "void":
            if tname == "List":
                self.out('%s result = new %s();' % (code(m.type), code(m.type)))
                self.out('List<Map<String,Object>> list = map["$result"];')
                with self.out.block('if (list != null)'):
                    self.out('int idx = 0;')
                    with self.out.block('while (idx < list.size())'):
                        self.out('result.add(%s_fromMap(list[idx]));' % code(m.type.parameters[0]))
                        self.out('idx = idx + 1;')
            else:
                self.out('%s result = %s_fromMap(map);' % (code(m.type), code(m.type)))
            self.out('return result;')
        self.out.dedent()
        self.out('}')

class ServerGenerator(Generator):

    def visit_Interface(self, i):
        name = code(i.name)
        self.out('class %sServer {' % name)
        self.out.indent()
        self.out('%s impl;' % name)
        with self.out.block('%sServer(%s impl)' % (name, name)):
            self.out('self.impl = impl;')
        self.out('Map<String,Object> call(String name, Map<String,Object> args) {')
        self.out.indent()
        self.out('int idx;')
        self.out('Map<String,Object> map = new Map<String,Object>();')
        self.out('List<Map<String,Object>> list = new List<Map<String,Object>>();')

    def visit_Method(self, m):
        self.out('if (name == "%s") {' % code(m.name))
        self.out.indent()

    def visit_Param(self, p):
        self.out('%s %s_%s = args["%s"];' % (code(p.type),
                                                  code(p.callable.name),
                                                  code(p.name),
                                                  code(p.name)))

    def leave_Method(self, m):
        name = code(m.name)
        params = ", ".join(["%s_%s" % (name, code(p.name)) for p in m.params])
        call = 'self.impl.%s(%s);' % (name, params)
        rettype = code(m.type.path[0])
        if rettype == "void":
            self.out(call)
        else:
            self.out('%s %s_result = %s' % (code(m.type), name, call))
            if rettype == "List":
                eltype = code(m.type.parameters[0])
                self.out('idx  = 0;')
                with self.out.block('while (idx < %s_result.size())' % name):
                    self.out('list.add(%s_toMap(%s_result[idx]));' % (eltype, name))
                    self.out('idx = idx + 1;')
                self.out('map["$result"] = list;')
            else:
                self.out('map = %s_toMap(%s_result);' % (rettype, name))
        self.out('map["$status"] = 200;')
        self.out('return map;')
        self.out.dedent()
        self.out('}')

    def leave_Interface(self, i):
        self.out('map["$status"] = 500;')
        self.out('return map;')
        self.out.dedent()
        self.out('}')
        self.out.dedent()
        self.out('}')
