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

# Python-to-Python RPC using pickle and HTTP

import os, urllib2, exceptions
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from python import serialize, deserialize, AdaptiveException


# Server side

class ServiceRequestHandler(BaseHTTPRequestHandler):

    services = {}  # name -> instance

    def do_GET(self):
        res = 404
        error = "Not found"
        body = None

        components = self.path.split("/")
        while components and not components[0].strip():
            components = components[1:]

        while components:
            name = components[0].strip()
            args = "/".join(components[1:])

            try:
                instance = ServiceRequestHandler.services[name]
            except KeyError:
                error = "Not found: %r" % name
                break

            try:
                command, args, kwargs = pickle.loads(args.decode("base64"))
            except Exception:
                res = 400
                error = "Bad Request: Failed to parse operation"
                break

            try:
                method = getattr(instance, command)
            except AttributeError:
                error = "Not found: %s :: %r" % (name, command)
                break

            try:
                output = True, method(*args, **kwargs)
            except Exception as exc:
                output = False, exc

            res = 200
            body = pickle.dumps(output)
            error = None
            break

        if error:
            self.send_error(res, error)
            return

        self.send_response(res)
        self.end_headers()
        if body:
            self.wfile.write(body)


def add_instance(name, instance):
    ServiceRequestHandler.services[name] = instance


def serve_forever(host="0.0.0.0", port=8080):
    port = int(os.environ.get("SERVER_PORT", port))
    server = HTTPServer((host, port), ServiceRequestHandler)
    server.serve_forever()


# Client side

class Client(object):
    def __init__(self, url):
        self.url = url

    def call(self, name, args):
        url = self.url + "/" + serialize((name, args)).encode("base64").replace("\n", "")
        u = urllib2.urlopen(url)
        okay, res = deserialize(u.read())
        if okay:
            return res
        try:
            exc = getattr(exceptions, res.name)
            raise exc(res.value)
        except AttributeError:  # One of res.name, res.value, or the getattr
            raise res


# Sample

if __name__ == '__main__':
    class Greeting(object):
        def __init__(self):
            self.counter = 0

        def greet(self):
            self.counter += 1
            return '''{"id":%s,"content":"Hello, World!"}''' % self.counter

    add_instance("Greeting", Greeting())
    serve_forever()
