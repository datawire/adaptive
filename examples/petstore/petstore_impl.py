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
