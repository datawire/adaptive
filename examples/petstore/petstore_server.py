## module PetStore {
##     desc "A sample API that uses a petstore as an example to demonstrate features in the Adaptive specification";

"""
A sample API that uses a petstore as an example to demonstrate features in the Adaptive specification
"""

##     defaults {
##         extbase "http://127.0.0.1:8080/PetStore";
##     };

from adaptive import assert_list_of as _assert_list_of

service_name = "PetStore"

##     struct Pet {
##         int64 id;
##         string name;
##         string tag = null;
##     };

class Pet(object):

    def __init__(self, id_, name, tag=None):
        self.id = id_
        self.name = name
        self.tag = tag


class PetStore_server(object):

    def __init__(self, impl):
        self.impl = impl

    def _getClass(self, classname):
        if classname == "Pet":
            return Pet
        raise ValueError("Don't know about class %r" % classname)

##     List<Pet> findPets(List<string> tags = null, int32 limit = null) {
##         desc "Returns all pets from the system that the user has access to";
##         ext "http://example.com/PetStore/findPets";  // Override default
##     };

    def findPets(self, tags=None, limit=None):
        """Returns all pets from the system that the user has access to"""
        assert tags is None or _assert_list_of(tags, basestring), tags
        assert limit is None or isinstance(limit, int), limit
        res = self.impl.findPets(tags, limit)
        _assert_list_of(res, Pet), res
        return res

##     Pet addPet(string name, string tag = null) {
##         desc "Creates a new pet in the store. Duplicates are allowed";
##     };

    def addPet(self, name, tag=None):
        """Creates a new pet in the store. Duplicates are allowed"""
        assert isinstance(name, basestring), name
        assert tag is None or isinstance(tag, basestring), tag
        res = self.impl.addPet(name, tag)
        assert isinstance(res, Pet), res
        return res

##     Pet findPetById(int64 id) {
##         desc "Returns a pet based on the ID supplied";
##     };

    def findPetById(self, id_):
        """Returns a pet based on the ID supplied"""
        assert isinstance(id_, int), id_
        res = self.impl.findPetById(id_)
        assert isinstance(res, Pet), res
        return res

##     void deletePet(int64 id) {
##         desc "deletes a single pet based on the ID supplied";
##     };

    def deletePet(self, id_):
        """deletes a single pet based on the ID supplied"""
        assert isinstance(id_, int), id_
        res = self.impl.deletePet(id_)
        assert res is None, res
        return res

## };
