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

# Pet Store as a service

from adaptive import sample_rpc

import petstore_impl
import petstore_server

store = petstore_impl.PetStore()
server = petstore_server.PetStore_server(store)
sample_rpc.add_instance(petstore_server.service_name, server)
sample_rpc.serve_forever()
