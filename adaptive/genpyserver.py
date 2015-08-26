import sdl
from python import Pythonize, PyOutput, emitTypeCheck

class ServerMaker(PyOutput):

    def __init__(self):
        PyOutput.__init__(self)
        self.did_module_head = False
        self.did_module_body = False
        self.module_name = None
        self.module_py_name = None
        self.known_classes = {}  # name -> py_name

    def module(self, m):
        self.ref("module %s {" % m.name)
        self.ref_indent()
        self.module_name = m.name
        self.module_py_name = m.py_name

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

        self.out("from adaptive import assertListOf as _assertListOf")
        self.out("")
        self.out("""service_name = "%s" """ % self.module_name)

        self.did_module_head = True

    def struct(self, s):
        self.module_head()
        assert not self.did_module_body, "Must have all structs before any functions (to be fixed)"

        self.ref("struct %s {" % s.name)
        self.ref_indent()
        for field in s.fields:
            self.ref(str(field))
        self.ref_dedent()
        self.ref("};")

        self.out("class %s(object):" % s.py_name)
        self.out("")
        self.indent()
        fields = []
        for field in s.fields:
            if field.default:
                fields.append("%s=%s" % (field.py_name, field.default.py_name))
            else:
                fields.append(field.py_name)

        self.out("def __init__(self, %s):" % ", ".join(fields))
        self.indent()
        for field in s.fields:
            self.out("self.%s = %s" % (field.name, field.py_name))  # FIXME is this okay?
        self.dedent()

        self.dedent()
        self.out("")
        self.known_classes[s.name] = s.py_name

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

        self.out("def _getClass(self, classname):")
        self.indent()
        for name, py_name in self.known_classes.items():
            self.out("""if classname == "%s":""" % name)
            self.indent()
            self.out("return %s" % py_name)
            self.dedent()
        self.out("""raise ValueError("Don't know about class %r" % classname)""")
        self.dedent()

        self.did_module_body = True

    def operation(self, o):
        self.module_body()
        self.ref("%s %s(%s) {" % (o.type, o.name, ", ".join(str(p) for p in o.parameters)))
        self.ref_indent()
        # FIXME: Loop over contents of operation here, once they are parsed and available.
        self.ref_dedent()
        self.ref("};")

        params = []
        for parameter in o.parameters:
            if parameter.default:
                params.append("%s=%s" % (parameter.py_name, parameter.default.py_name))
            else:
                params.append(parameter.py_name)
        self.out("def %s(self, %s):" % (o.py_name, ", ".join(params)))
        self.indent()
        for parameter in o.parameters:
            has_null_default = parameter.default and parameter.default.py_name == "None"  # FIXME for non-string, non-null
            emitTypeCheck(self.out, parameter.py_name, parameter.type, orNone=has_null_default)
        self.out("res = self.impl.%s(%s)" % (o.py_name, ", ".join(p.py_name for p in o.parameters)))
        emitTypeCheck(self.out, "res", o.type, orNone=False)
        self.out("return res")
        self.dedent()


m = sdl.SDL().parse(open("../examples/petstore/petstore.sdl").read())
m.traverse(Pythonize())  # Add py_name attributes to the AST
#print m

sm = ServerMaker()
sm.module(m)
sm.dump()
