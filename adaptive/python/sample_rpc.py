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

from runtime import serialize, deserialize, AdaptiveException


def call_to_url_path(name, args):
    return "/" + serialize((name, args)).encode("base64").replace("\n", "")


def url_path_to_call(path):
    name, args = deserialize(path.decode("base64"))
    return name, args


def pack_exception(exc):
    return AdaptiveException(exc.__class__.__name__, str(exc))


# Client side

class RPCClient(object):
    def __init__(self, url):
        self.url = url

    def call(self, name, args):
        url = self.url + call_to_url_path(name, args)
        u = urllib2.urlopen(url)
        okay, res = deserialize(u.read())
        if okay:
            return res
        try:
            exc = getattr(exceptions, res.name)
            raise exc(res.value)
        except AttributeError:  # One of res.name, res.value, or the getattr
            raise res


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
            call_path = "/".join(components[1:])

            try:
                instance = ServiceRequestHandler.services[name]
            except KeyError:
                error = "Not found: %r" % name
                break

            try:
                command, args = url_path_to_call(call_path)
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
                output = True, method(*args)
            except Exception as exc:
                output = False, pack_exception(exc)

            res = 200
            try:
                body = serialize(output)
                error = None
            except Exception as exc:
                print "Returning", output
                print "Failed because:", exc
                raise

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
