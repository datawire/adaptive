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
from quark.parser import Parser
from quark.ast import *

def parse(rule, text):
    p = Parser()
    return p.visit(p.grammar[rule].parse(text))

def statement(text):
    return parse("statement", text)

class MapConstructor(object):

    def Class(self, cls):
        return Constructor(cls.name.copy(), parse("parameters", "Map<String,Object> map"),
                           Block([d.apply(self) for d in cls.definitions if isinstance(d, Field)]))

    def Field(self, f):
        return parse("statement", 'self.%s = map.get("%s");' % (f.name.text, f.name.text))

class MapRenderer(object):

    def Class(self, cls):
        return Method(parse("type", "Map<String,Object>"), Name("toMap"), [],
                      Block([statement("Map<String,Object> map = new Map<String,Object>();")] +
                            [d.apply(self) for d in cls.definitions if isinstance(d, Field)] +
                            [statement("return map;")]))

    def Field(self, f):
        return parse("statement", 'map.put("%s", self.%s);' % (f.name.text, f.name.text))

class Generator(object):

    def __init__(self, transform):
        self.classes = []
        self.transform = transform

    def leave_Class(self, cls):
        cls.definitions.append(cls.apply(MapConstructor()))
        cls.definitions.append(cls.apply(MapRenderer()))

    def get_annotation(self, node, name):
        for a in node.annotations:
            if a.name.text == name:
                return a
        return None

    def leave_Interface(self, i):
        if self.get_annotation(i, "service"):
            cls = i.apply(self.transform)
            self.classes.append(cls)

    def leave_Primitive(self, p):
        pass

    def leave_Package(self, p):
        p.definitions.append(parse("class", """
        interface RPCClient {
            Map<String,Object> call(String name, Map<String,Object> args);
        }
        """))
        p.definitions.extend(self.classes)

class ClientTransform(object):

    def Interface(self, i):
        return Class(parse("name", "%sClient" % i.name.text), (), None,
                     [parse("field", "RPCClient rpc;")] +
                     [d.apply(self) for d in i.definitions])

    def Method(self, m):
        result = m.copy()
        body = [statement("Map<String,Object> args = new Map<String,Object>();")]
        body.extend([p.apply(self) for p in m.params])
        body.append(statement('Map<String,Object> map = self.rpc.call("%s", args);' % m.name.text))
        tname = m.type.path[0].text
        if tname != "void":
            new = Call(m.type.copy(), [])
            body.append(Local(Declaration(m.type.copy(), Name("result"), new)))
            if tname == "List":
                body.append(statement('List<Map<String,Object>> list = map.get("$result");'))
                if_ = statement("if (list != null) {}")
                body.append(if_)
                cons = if_.consequence.statements
                cons.append(statement('int idx = 0;'))
                while_ = statement('while (idx < list.size()) {}')
                cons.append(while_)
                loop = while_.body.statements
                loop.append(ExprStmt(Call(Attr(parse("var", "result"),
                                               Name("add")),
                                          [Call(m.type.parameters[0].copy(),
                                                parse("exprs", "list.get(idx)"))])))
                loop.append(statement('idx = idx + 1;'))
            else:
                new.args.append(parse("var", "map"))
            body.append(statement("return result;"))
        result.body = Block(body)
        return result

    def Param(self, p):
        return statement('args.put("%s", %s);' % (p.name.text, p.name.text))

class ServerTransform(object):

    def Interface(self, i):
        cls = parse("class", """class %(name)sServer {
            %(name)s impl;

            %(name)sServer(%(name)s impl) {
                self.impl = impl;
            }
        }""" % {"name": i.name.text})
        call = parse("method", """Map<String,Object> call(String name, Map<String,Object> args) {
            int idx;
            Map<String,Object> map = new Map<String,Object>();
            List<Map<String,Object>> list = new List<Map<String,Object>>();
        }""")
        cls.definitions.append(call)
        body = call.body.statements
        body.extend([d.apply(self) for d in i.definitions])
        body.append(statement('map.put("$status", 500);'))
        body.append(statement('return map;'))
        return cls

    def Method(self, m):
        result = statement('if (name == "%s") {}' % m.name.text)
        cons = result.consequence.statements
        cons.extend([p.apply(self, m.name.text) for p in m.params])
        call = parse("expr", "self.impl.%s(%s)" % (m.name.text,
                                                   ", ".join(["%s_%s" % (m.name.text, p.name.text)
                                                              for p in m.params])))
        rettype = m.type.path[0].text
        if rettype == "void":
            cons.append(ExprStmt(call))
        else:
            var = parse("name", "%s_result" % m.name.text)
            cons.append(Local(Declaration(m.type.copy(), var, call)))

            if rettype == "List":
                cons.append(statement('idx  = 0;'))
                while_ = statement('while (idx < %s.size()) {}' % var.text)
                body = while_.body.statements
                body.append(statement('list.add(%s.get(idx).toMap());' % var.text))
                body.append(statement('idx = idx + 1;'))
                cons.append(statement('map.put("$result", list);'))
            else:
                cons.append(statement('map = %s.toMap();' % var.text))
        cons.append(statement('map.put("$status", 200);'))
        cons.append(statement("return map;"))
        return result

    def Param(self, p, prefix):
        decl = Declaration(p.type.copy(), parse("name", "%s_%s" % (prefix, p.name.text)),
                           parse("expr", 'args.get("%s")' % p.name.text))
        return Local(decl)
