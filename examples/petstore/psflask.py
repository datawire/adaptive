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

from flask import Flask, abort
app = Flask(__name__)

from adaptive import serialize, deserialize, AdaptiveException

import petstore_impl
import PetStore_server

store = petstore_impl.PetStore()
server = PetStore_server.PetStore_server(store)


@app.route("/" + PetStore_server.service_name + "/<args>")
def run_service(args):
    try:
        command, args = deserialize(args.decode("base64"))
    except Exception:
        abort(400)

    try:
        method = getattr(server, command)
    except AttributeError:
        abort(404)

    try:
        output = True, method(*args)
    except Exception as exc:
        output = False, AdaptiveException(exc.__class__.__name__, str(exc))

    try:
        res = serialize(output)
    except Exception as exc:
        print "Returning:", output
        print "Failed because:", exc
        raise

    return res


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
