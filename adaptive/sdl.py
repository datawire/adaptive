from parsimonious.nodes import RegexNode
from grammar import Grammar

class AST:

    def origin(self, node):
        if not hasattr(self, "node"):
            self.node = node

def joindent(items):
    st = "\n".join(map(str, items))
    if st:
        st = ("\n" + st).replace("\n", "\n  ")
        st += "\n"
    return st

class Module(AST):

    def __init__(self, name, definitions):
        self.name = name
        self.definitions = definitions

    def __str__(self):
        return "module %s {%s}" % (self.name, joindent(self.definitions))

class Struct(AST):

    def __init__(self, name, fields):
        self.name = name
        self.fields = fields

    def __str__(self):
        return "struct %s {%s}" % (self.name, joindent(self.fields))

class Fieldish(AST):

    def __init__(self, name, type, default):
        self.name = name
        self.type = type
        self.default = default

    def __str__(self):
        if self.default:
            return "%s %s = %s" % (self.type, self.name, self.default)
        else:
            return "%s %s" % (self.type, self.name)

class Field(Fieldish):

    def __str__(self):
        return Fieldish.__str__(self) + ";"

class Parameter(Fieldish):
    pass

class Operation(AST):

    def __init__(self, name, parameters, type):
        self.name = name
        self.parameters = parameters
        self.type = type

    def __str__(self):
        return "%s %s(%s);" % (self.type, self.name, ", ".join(map(str, self.parameters)))

class Type(AST):

    def __init__(self, name, parameters=None):
        self.name = name
        self.parameters = parameters

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
    def visit_desc(self, node, children): pass

    @g.rule('defaults = DEFAULTS LBR ~"[^}]*" RBR SEMI')
    def visit_defaults(self, node, children): pass

    @g.rule('struct = STRUCT name LBR field* RBR SEMI')
    def visit_struct(self, node, (s, name, l, fields, r, sc)):
        return Struct(name, fields)

    # should think about queries and/or idempotency
    @g.rule('operation = type name LPR parameters? RPR (LBR ~"[^}]*" RBR)? SEMI')
    def visit_operation(self, node, (type, name, l, params, r, _, s)):
        if params:
            params = params[0]
        else:
            params = []
        return Operation(name, params, type)

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
        return literal

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

    @g.rule('name = _ ~"[a-zA-Z][a-zA-Z0-9]*" _')
    def visit_name(self, node, (pre, name, post)):
        return name.text

    # lame string literals here
    @g.rule(r'STRING = _ ~"\"[^\"]*\"" _')
    def visit_STRING(self, node, (pre, string, post)):
        return string.text

    @g.rule('_ = __?')
    def visit__(self, node, children):
        return None

    @g.rule(r'__ = ~"[ \t\n\r]*//[^\n]*[ \t\n\r]+" / ~"[ \t\n\r]+"')
    def visit___(self, node, children):
        return None

    def visit_(self, node, children):
        if isinstance(node, RegexNode):
            return node
        else:
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
    };
    """)
    print m
    m = SDL().parse(open("examples/petstore/petstore.sdl").read())
    print m
