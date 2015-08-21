# Pet Store as a service

from adaptive import sample_rpc

import petstore

if __name__ == '__main__':
    sample_rpc.add_instance("PetStore", petstore.PetStore())
    sample_rpc.serve_forever()
