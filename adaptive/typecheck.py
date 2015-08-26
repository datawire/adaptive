# Tools for type checking

def assertListOf(lst, typ, orNone=True):
    assert isinstance(lst, list), lst
    if orNone:
        for idx, value in enumerate(lst):
            assert value is None or isinstance(value, typ), (idx, value)
    else:
        for idx, value in enumerate(lst):
            assert isinstance(value, typ), (idx, value)
    return True

def emitTypeCheck(out, name, typ, orNone=True):
    d = dict(name=name, typ=typ.py_name)
    if typ.name == "void":
        out("assert %(name)s is None, %(name)s" % d)
    elif typ.parameters:
        assert len(typ.parameters) == 1, "Unimplemented: %s" % typ
        assert typ.name == "List",  "Unimplemented: %s" % typ
        d["param"] = typ.parameters[0].py_name
        if orNone:
            out("assert %(name)s is None or _assertListOf(%(name)s, %(param)s), %(name)s" % d)
        else:
            out("_assertListOf(%(name)s, %(param)s), %(name)s" % d)
    else:
        if orNone:
            out("assert %(name)s is None or isinstance(%(name)s, %(typ)s), %(name)s" % d)
        else:
            out("assert isinstance(%(name)s, %(typ)s), %(name)s" % d)
