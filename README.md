# Adaptive

1. Install the package: `python setup.py develop`
2. Look at `examples/petstore` for a sample server/client and associated SDL.
   - `petstore.sdl` would be used to autogenerate `petstore_server.py` and `PetStore.py`, which are presently hand-written.
   - `petstore_impl.py` contains the hand-written implementation of the service's functionality.
   - `psserver.py` is a short script to launch the server using adaptive.sample_rpc
   - `psflask.py` is a longer script to launch the server using Flask. Requires Flask.
   - `psclient.py` has a function that uses the API and callers that run that function using the implementation directly and via RPC.
3. Run the server: `python psserver.py` or `python psflask.py`
4. Run the test client (in another terminal): `python psclient.py`
