# Pet Store

from petstore_server import Pet

class PetStore(object):
    """
    A sample API that uses a petstore as an example to demonstrate features in project x
    """

    def __init__(self):
        self.pets = set()
        self.next_id = 0

    def findPets(self, tags=None, limit=None):
        "Returns all pets from the system that the user has access to"
        if tags is not None:
            tags = set(tags)
        res = []
        for pet in self.pets:
            if tags is None or pet.tag in tags:
                res.append(pet)
                if limit is not None and len(res) >= limit:
                    break
        return res

    def addPet(self, name, tag=None):
        "Creates a new pet in the store. Duplicates are allowed"
        pet = Pet(self.next_id, name, tag)
        self.next_id += 1
        self.pets.add(pet)
        return pet

    def _findPet(self, id_):
        for pet in self.pets:
            if pet.id == id_:
                return pet
        return None

    def findPetById(self, id_):
        "Returns a pet based on the ID supplied"
        pet = self._findPet(id_)
        if pet is None:
            raise LookupError("findPetById: No Pet with id=%r in this pet store" % id_)
        return pet

    def deletePet(self, id_):
        "deletes a single pet based on the ID supplied"
        pet = self._findPet(id_)
        if pet is None:
            raise LookupError("deletePet: No Pet with id=%r in this pet store" % id_)
        self.pets.remove(pet)
