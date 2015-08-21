import pickle

from flask import Flask, abort
app = Flask(__name__)

import petstore_impl
import petstore_server

store = petstore_impl.PetStore()
server = petstore_server.PetStore_server(store)

@app.route("/" + petstore_server.service_name + "/<args>")
def run_service(args):
    try:
        command, args, kwargs = pickle.loads(args.decode("base64"))
    except Exception:
        abort(400)

    try:
        method = getattr(server, command)
    except AttributeError:
        abort(404)

    try:
        output = True, method(*args, **kwargs)
    except Exception as exc:
        output = False, exc

    return pickle.dumps(output)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
