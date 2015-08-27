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

```
timonium:~ $ mktmpenv
New python executable in tmp-357ce91f6cf4e362/bin/python
Installing setuptools, pip, wheel...done.
This is a temporary environment. It will be deleted when you run 'deactivate'.

(tmp-357ce91f6cf4e362)timonium:tmp-357ce91f6cf4e362 $ pip -q install flask

(tmp-357ce91f6cf4e362)timonium:tmp-357ce91f6cf4e362 $ git clone -q https://github.com/datawire/adaptive.git

(tmp-357ce91f6cf4e362)timonium:tmp-357ce91f6cf4e362 $ cd adaptive/

(tmp-357ce91f6cf4e362)timonium:adaptive (master) $ py setup.py -q develop
zip_safe flag not set; analyzing archive contents...
zip_safe flag not set; analyzing archive contents...

(tmp-357ce91f6cf4e362)timonium:adaptive (master) $ cd examples/petstore/

(tmp-357ce91f6cf4e362)timonium:petstore (master) $ adaptive petstore.sdl python python:server
petstore.sdl python:client --> PetStore_client.py
petstore.sdl python:server --> PetStore_server.py

(tmp-357ce91f6cf4e362)timonium:petstore (master) $ py psflask.py > /dev/null 2>&1 &
[1] 18026

(tmp-357ce91f6cf4e362)timonium:petstore (master) $ py psclient.py 
All [<PetStore_server.Pet object at 0x10bafa638>, <PetStore_server.Pet object at 0x10bafa710>, <PetStore_server.Pet object at 0x10bafa680>, <PetStore_server.Pet object at 0x10bafa6c8>, <PetStore_server.Pet object at 0x10bafa4d0>, <PetStore_server.Pet object at 0x10bafa518>, <PetStore_server.Pet object at 0x10bafa830>, <PetStore_server.Pet object at 0x10bafa758>, <PetStore_server.Pet object at 0x10bafa560>, <PetStore_server.Pet object at 0x10bafa5a8>, <PetStore_server.Pet object at 0x10bafa7a0>, <PetStore_server.Pet object at 0x10bafa7e8>, <PetStore_server.Pet object at 0x10bafa5f0>]
Ten [<PetStore_server.Pet object at 0x10bafa638>, <PetStore_server.Pet object at 0x10bafa710>, <PetStore_server.Pet object at 0x10bafa680>, <PetStore_server.Pet object at 0x10bafa6c8>, <PetStore_server.Pet object at 0x10bafa4d0>, <PetStore_server.Pet object at 0x10bafa518>, <PetStore_server.Pet object at 0x10bafa830>, <PetStore_server.Pet object at 0x10bafa758>, <PetStore_server.Pet object at 0x10bafa560>, <PetStore_server.Pet object at 0x10bafa5a8>]
Cats [<PetStore_server.Pet object at 0x10bafa638>, <PetStore_server.Pet object at 0x10bafa680>, <PetStore_server.Pet object at 0x10bafa6c8>, <PetStore_server.Pet object at 0x10bafa5f0>]
Uncats [<PetStore_server.Pet object at 0x10bafa4d0>, <PetStore_server.Pet object at 0x10bafa518>, <PetStore_server.Pet object at 0x10bafa560>, <PetStore_server.Pet object at 0x10bafa5a8>]
Quads [<PetStore_server.Pet object at 0x10bafa638>, <PetStore_server.Pet object at 0x10bafa710>, <PetStore_server.Pet object at 0x10bafa680>, <PetStore_server.Pet object at 0x10bafa6c8>, <PetStore_server.Pet object at 0x10bafa758>, <PetStore_server.Pet object at 0x10bafa7a0>, <PetStore_server.Pet object at 0x10bafa7e8>, <PetStore_server.Pet object at 0x10bafa5f0>]
<PetStore_server.Pet object at 0x10bafa5a8>
Uncats [<PetStore_server.Pet object at 0x10bafa4d0>, <PetStore_server.Pet object at 0x10bafa518>, <PetStore_server.Pet object at 0x10bafa560>]
Got expected exception
==========================================================================================
All [<PetStore_client.Pet object at 0x10bdc75f0>, <PetStore_client.Pet object at 0x10bdc7638>, <PetStore_client.Pet object at 0x10bdc7680>, <PetStore_client.Pet object at 0x10bdc76c8>, <PetStore_client.Pet object at 0x10bdc7710>, <PetStore_client.Pet object at 0x10bdc7758>, <PetStore_client.Pet object at 0x10bdc77a0>, <PetStore_client.Pet object at 0x10bdc77e8>, <PetStore_client.Pet object at 0x10bdc7830>, <PetStore_client.Pet object at 0x10bdc7878>, <PetStore_client.Pet object at 0x10bdc78c0>, <PetStore_client.Pet object at 0x10bdc7908>, <PetStore_client.Pet object at 0x10bdc7950>]
Ten [<PetStore_client.Pet object at 0x10bdc77e8>, <PetStore_client.Pet object at 0x10bdc7830>, <PetStore_client.Pet object at 0x10bdc7878>, <PetStore_client.Pet object at 0x10bdc78c0>, <PetStore_client.Pet object at 0x10bdc7908>, <PetStore_client.Pet object at 0x10bdc7950>, <PetStore_client.Pet object at 0x10bdc75a8>, <PetStore_client.Pet object at 0x10bdc7998>, <PetStore_client.Pet object at 0x10bdc79e0>, <PetStore_client.Pet object at 0x10bdc7a28>]
Cats [<PetStore_client.Pet object at 0x10bdc79e0>, <PetStore_client.Pet object at 0x10bdc7a28>, <PetStore_client.Pet object at 0x10bdc7710>, <PetStore_client.Pet object at 0x10bdc7a70>]
Uncats [<PetStore_client.Pet object at 0x10bdc7b48>, <PetStore_client.Pet object at 0x10bdc7b90>, <PetStore_client.Pet object at 0x10bdc7bd8>, <PetStore_client.Pet object at 0x10bdc7c20>]
Quads [<PetStore_client.Pet object at 0x10bdc7cf8>, <PetStore_client.Pet object at 0x10bdc7d40>, <PetStore_client.Pet object at 0x10bdc7d88>, <PetStore_client.Pet object at 0x10bdc7dd0>, <PetStore_client.Pet object at 0x10bdc7e18>, <PetStore_client.Pet object at 0x10bdc7e60>, <PetStore_client.Pet object at 0x10bdc7ea8>, <PetStore_client.Pet object at 0x10bdc7ef0>]
<PetStore_client.Pet object at 0x10bdc7d40>
Uncats [<PetStore_client.Pet object at 0x10bdd0290>, <PetStore_client.Pet object at 0x10bdd02d8>, <PetStore_client.Pet object at 0x10bdd0320>]
Got expected exception
(tmp-357ce91f6cf4e362)timonium:petstore (master) $ 
```
