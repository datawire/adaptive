# Tools for type checking

def assertListOf(lst, typ):
    assert isinstance(lst, list), lst
    for idx, value in enumerate(lst):
        #assert isinstance(value, typ), (idx, value)
        assert value is None or isinstance(value, typ), (idx, value)
    return True
