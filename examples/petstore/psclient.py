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

# Use the pet store

def psclient(store):
    for name in "Alvin Bob Carly Diana".split():
        store.addPet(name)
    for name in "Spot Crookshanks Mrs.Norris Jinx".split():
        store.addPet(name, "cat")
    for name in "Fido Rover Astro Scooby".split():
        store.addPet(name, "dog")
    store.addPet("Hedwig", "bird")

    print "All", store.findPets()
    print "Ten", store.findPets(limit=10)
    print "Cats", store.findPets(tags=["cat"])
    print "Uncats", store.findPets(tags=[None])
    print "Quads", store.findPets(tags="cat dog".split())

    print store.findPetById(3)
    store.deletePet(3)
    print "Uncats", store.findPets(tags=[None])
    try:
        print store.findPetById(3)
    except LookupError:
        print "Got expected exception"


def main():
    from petstore_impl import PetStore
    store = PetStore()
    psclient(store)

def main2():
    import PetStore_client as PetStore
    psclient(PetStore)

if __name__ == "__main__":
    main()
    print "===" * 30
    main2()
