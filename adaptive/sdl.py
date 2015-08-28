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

from grammar import Grammar

class AST:

    def origin(self, node):
        if not hasattr(self, "node"):
            self.node = node

    def traverse(self, visitor):
        visit = getattr(visitor, "visit_%s" % self.__class__.__name__,
                        getattr(visitor, "visit_DEFAULT", lambda s: None))
        leave = getattr(visitor, "leave_%s" % self.__class__.__name__,
                        getattr(visitor, "leave_DEFAULT", lambda s: None))
        visit(self)
        if self.children:
            for c in self.children:
                if c is not None:
                    c.traverse(visitor)
        leave(self)

def joindent(items):
    st = "\n".join(map(str, items))
    if st:
        st = ("\n" + st).replace("\n", "\n    ")
        st += "\n"
    return st

class Module(AST):

    def __init__(self, name, definitions):
        self.name = name
        self.definitions = definitions

    @property
    def children(self):
        return self.definitions

    def __str__(self):
        return "module %s {%s};" % (self.name, joindent(self.definitions))

class Struct(AST):

    def __init__(self, name, fields):
        self.name = name
        self.fields = fields

    @property
    def children(self):
        return self.fields

    def __str__(self):
        return "struct %s {%s};" % (self.name, joindent(self.fields))

class Description(AST):

    def __init__(self, content):
        self.content = content

    @property
    def children(self):
        return []

    def __str__(self):
        return "desc %s;" % self.content

class StringLiteral(AST):

    def __init__(self, text):
        self.text = text

    @property
    def children(self):
        if False: yield

    def __str__(self):
        return self.text

class Null(AST):

    @property
    def children(self):
        if False: yield

    def __str__(self):
        return "null"

class _Declaration(AST):

    def __init__(self, name, type, default):
        self.name = name
        self.type = type
        self.default = default

    @property
    def children(self):
        yield self.type
        yield self.default

    def __str__(self):
        if self.default:
            return "%s %s = %s" % (self.type, self.name, self.default)
        else:
            return "%s %s" % (self.type, self.name)

class Field(_Declaration):

    def __str__(self):
        return _Declaration.__str__(self) + ";"

class Parameter(_Declaration):
    pass

class Operation(AST):

    def __init__(self, name, parameters, type, description):
        self.name = name
        self.parameters = parameters
        self.type = type
        self.description = description

    @property
    def children(self):
        yield self.type
        for p in self.parameters:
            yield p

    def __str__(self):
        if self.description:
            return "%s %s(%s) {\n    %s\n};" % (self.type, self.name, ", ".join(map(str, self.parameters)),
                                              self.description)
        else:
            return "%s %s(%s);" % (self.type, self.name, ", ".join(map(str, self.parameters)))

class Type(AST):

    def __init__(self, name, parameters=None):
        self.name = name
        self.parameters = parameters

    @property
    def children(self):
        return self.parameters

    def __str__(self):
        if self.parameters:
            return "%s<%s>" % (self.name, ", ".join([str(s) for s in self.parameters]))
        else:
            return self.name

g = Grammar()

@g.parser
class SDL:

    keywords = ["module", "struct", "desc", "defaults"]
    symbols = {"EQ": "=",
               "SEMI": ";",
               "COMMA": ",",
               "LA": "<",
               "RA": ">",
               "LBR": "{",
               "RBR": "}",
               "LPR": "(",
               "RPR": ")",
               "NULL": "null"}

    @g.rule('module = MODULE name LBR definition* RBR SEMI ~"$"')
    def visit_module(self, node, (m, name, l, definitions, r, s, eof)):
        return Module(name, definitions)

    @g.rule('definition = struct / operation / desc / defaults')
    def visit_definition(self, node, (dfn,)):
        return dfn

    @g.rule('desc = DESC STRING SEMI')
    def visit_desc(self, node, (d, content, sc)):
        return Description(content)

    @g.rule('defaults = DEFAULTS LBR ~"[^}]*" RBR SEMI')
    def visit_defaults(self, node, children): pass

    @g.rule('struct = STRUCT name LBR field* RBR SEMI')
    def visit_struct(self, node, (s, name, l, fields, r, sc)):
        return Struct(name, fields)

    # should think about queries and/or idempotency
    @g.rule('operation = type name LPR parameters? RPR (LBR desc? ~"[^}]*" RBR)? SEMI')
    def visit_operation(self, node, (type, name, l, params, r, body, s)):
        if params:
            params = params[0]
        else:
            params = []
        if body:
            desc = body[0][1]
            if desc:
                desc = desc[0]
        else:
            desc = None
        return Operation(name, params, type, desc)

    @g.rule('parameters = param (COMMA param)*')
    def visit_parameters(self, node, (first, rest)):
        return [first] + [n[-1] for n in rest]

    @g.rule('param = type name (EQ literal)?')
    def visit_param(self, node, (type, name, default)):
        if default:
            literal = default[0][-1]
        else:
            literal = None
        return Parameter(name, type, literal)

    @g.rule('field = type name (EQ literal)? SEMI')
    def visit_field(self, node, (type, name, default, _)):
        if default:
            literal = default[0][-1]
        else:
            literal = None
        return Field(name, type, literal)

    @g.rule('literal = STRING / NULL')
    def visit_literal(self, node, (literal,)):
        if isinstance(literal, StringLiteral):
            return literal
        else:
            return Null()

    @g.rule('type = name (LA types RA)?')
    def visit_type(self, node, (name, params)):
        if params:
            _, types, _ = params[0]
            return Type(name, types)
        else:
            return Type(name)

    @g.rule('types = type (COMMA type)*')
    def visit_types(self, node, (first, rest)):
        return [first] + [n[-1] for n in rest]

    @g.rule('name = _ name_re _')
    def visit_name(self, node, (pre, name, post)):
        return name

    @g.rule('name_re = ~"[a-zA-Z][a-zA-Z0-9]*"')
    def visit_name_re(self, node, children):
        return node.text

    # lame string literals here
    @g.rule(r'STRING = _ STRING_RE _')
    def visit_STRING(self, node, (pre, string, post)):
        return StringLiteral(string)

    @g.rule(r'STRING_RE = ~"\"[^\"]*\""')
    def visit_STRING_RE(self, node, children):
        return node.text

    @g.rule('_ = __?')
    def visit__(self, node, children):
        return None

    @g.rule(r'__ = ~"[ \t\n\r]*//[^\n]*[ \t\n\r]+" / ~"[ \t\n\r]+"')
    def visit___(self, node, children):
        return None

    def visit_(self, node, children):
        return children

if __name__ == "__main__":
    m = SDL().parse("""
    // this is a test, hey this works
    module asdf {};
    """)
    print m
    m = SDL().parse("""
    module asdf {
      struct A {
        a b = null;
        c d = "asdf"; //asdf
        x y;
      };

      List<A, B, C> funge(List<int> a, int b, int c);
      List<A, B> funge(int a, int b);
      List<A> funge(int a);
      void funge();
      List<A<B, C>> funge(int a = null);
    };
    """)
    print m
    m = SDL().parse(open("examples/petstore/petstore.sdl").read())
    print m

    class Visitor:

        def visit_Module(self, m):
            print "## module %s {" % m.name
        def leave_Module(self, m):
            print "## };"

        def visit_Struct(self, s):
            print "##   struct %s {" % s.name
        def visit_Field(self, f):
            print "##     %s %s;" % (f.type, f.name)
        def leave_Struct(self, m):
            print "##   };"

        def visit_Operation(self, o):
            print "##   %s %s(%s);" % (o.type, o.name, ", ".join(str(p) for p in o.parameters))

    m.traverse(Visitor())
