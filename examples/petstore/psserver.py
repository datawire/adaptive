# Pet Store as a service

from adaptive import sample_rpc

import petstore_impl
import petstore_server

store = petstore_impl.PetStore()
server = petstore_server.PetStore_server(store)
sample_rpc.add_instance(petstore_server.service_name, server)
sample_rpc.serve_forever()
