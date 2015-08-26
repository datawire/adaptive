import sdl
from python import Pythonize, PyOutput, emitTypeCheck

class ClientMaker(PyOutput):

    def __init__(self):
        PyOutput.__init__(self)

    def module(self, m):
        self.ref("module %s {" % m.name)
        self.ref_indent()

        self.out("from adaptive import assertListOf as _assertListOf, sample_rpc as _sample_rpc")
        self.out("")
        self.out("""_remote_url = "http://127.0.0.1:8080/%s" """ % m.name)  # FIXME
        self.out("_service = _sample_rpc.Client(_remote_url)")

        for definition in m.definitions:
            if definition is None: continue
            kind = definition.__class__.__name__
            if kind == "Desc":
                self.ref("""desc "%s";""" % "no content")
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

    def struct(self, s):
        self.ref("struct %s {" % s.name)
        self.ref_indent()
        for field in s.fields:
            self.ref(str(field))
        self.ref_dedent()
        self.ref("};")

        self.out("""%s = _service._getClass("%s")""" % (s.py_name, s.name))

    def operation(self, o):
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
        self.out("def %s(%s):" % (o.py_name, ", ".join(params)))
        self.indent()
        for parameter in o.parameters:
            has_null_default = parameter.default and parameter.default.py_name == "None"  # FIXME for non-string, non-null
            emitTypeCheck(self.out, parameter.py_name, parameter.type, orNone=has_null_default)
        self.out("res = _service.%s(%s)" % (o.py_name, ", ".join(p.py_name for p in o.parameters)))
        emitTypeCheck(self.out, "res", o.type, orNone=False)
        self.out("return res")
        self.dedent()


m = sdl.SDL().parse(open("../examples/petstore/petstore.sdl").read())
m.traverse(Pythonize())  # Add py_name attributes to the AST
#print m

cm = ClientMaker()
cm.module(m)
cm.dump()
