// Pet Store

@doc("A sample API that uses a petstore as an example to demonstrate features in the Adaptive specification")
@url("http://127.0.0.1:8080/")
package petstore {

    @doc("Essential information about a pet.")
    class Pet {
        int id;
        String name;
        String tag = null;
    }

    @service interface PetStore {

        @doc("Returns all pets from the system that the user has access to")
        @url("http://example.com/PetStore/findPets") // Override default
        @query List<Pet> findPets(List<String> tags /*= null*/, int limit /*= null*/);

        @doc("Creates a new pet in the store. Duplicates are allowed")
        @operation Pet addPet(String name, String tag /*= null*/);

        @doc("Returns a pet based on the ID supplied")
        @query Pet findPetById(int id);

        @doc("deletes a single pet based on the ID supplied")
        @operation void deletePet(int id);

    }

}
