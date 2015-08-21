# Pet Store as a service

import petstore_impl
import petstore_server

store = petstore_impl.PetStore()
petstore_server.serve_forever(store)
