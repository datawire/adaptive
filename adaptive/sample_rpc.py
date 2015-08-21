# Python-to-Python RPC using pickle and HTTP

import os, urllib2, pickle
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

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

class Proxy(object):
    def __init__(self, client, name):
        self.client = client
        self.name = name

    def __call__(self, *args, **kwargs):
        url = self.client.url + "/" + pickle.dumps((self.name, args, kwargs)).encode("base64").replace("\n", "")
        u = urllib2.urlopen(url)
        okay, res = pickle.loads(u.read())
        if okay:
            return res
        raise res


class Client(object):
    def __init__(self, url):
        self.url = url

    def __getattr__(self, attr):
        return Proxy(self, attr)


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
