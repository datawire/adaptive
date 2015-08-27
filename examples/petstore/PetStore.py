## module PetStore {
##     desc "A sample API that uses a petstore as an example to demonstrate features in the Adaptive specification";

"""
A sample API that uses a petstore as an example to demonstrate features in the Adaptive specification
"""

##     defaults {
##         extbase "http://127.0.0.1:8080/PetStore";
##     };

from adaptive import assert_list_of as _assertListOf, sample_rpc as _sample_rpc

_remote_url = "http://127.0.0.1:8080/PetStore"
_service = _sample_rpc.Client(_remote_url)

##     struct Pet {
##         int64 id;
##         string name;
##         string tag = null;
##     };

Pet = _service._getClass("Pet")

##     List<Pet> findPets(List<string> tags = null, int32 limit = null) {
##         desc "Returns all pets from the system that the user has access to";
##         ext "http://example.com/PetStore/findPets";  // Override default
##     };

def findPets(tags=None, limit=None):
    """Returns all pets from the system that the user has access to"""
    assert tags is None or _assertListOf(tags, basestring), tags
    assert limit is None or isinstance(limit, int), limit
    res = _service.findPets(tags, limit)
    _assertListOf(res, Pet), res
    return res

##     Pet addPet(string name, string tag = null) {
##         desc "Creates a new pet in the store. Duplicates are allowed";
##     };

def addPet(name, tag=None):
    """Creates a new pet in the store. Duplicates are allowed"""
    assert isinstance(name, basestring), name
    assert tag is None or isinstance(tag, basestring), tag
    res = _service.addPet(name, tag)
    assert isinstance(res, Pet), res
    return res

##     Pet findPetById(int64 id) {
##         desc "Returns a pet based on the ID supplied";
##     };

def findPetById(id_):
    """Returns a pet based on the ID supplied"""
    assert isinstance(id_, int), id_
    res = _service.findPetById(id_)
    assert isinstance(res, Pet), res
    return res

##     void deletePet(int64 id) {
##         desc "deletes a single pet based on the ID supplied";
##     };

def deletePet(id_):
    """deletes a single pet based on the ID supplied"""
    assert isinstance(id_, int), id_
    res = _service.deletePet(id_)
    assert res is None, res
    return res

## };
