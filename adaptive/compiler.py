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

"""
Adaptive Code Generation by datawire.io

Usage: adaptive <sdl_filename> <target> ...
       adaptive -h | --help
       adaptive -V | --version

Targets are of the form language:intent.

Languages: python
           java (not implemented)

Intents: client (default)
         async-client (not implemented)
         server
"""

import sys

from docopt import docopt

import _metadata, python, genpyserver, genpyclient
from sdl import SDL

supported_languages = "python",
supported_intents = "client", "server"


def main(args):
    if args["-V"] or args["--version"]:
        sys.stderr.write("Adaptive Codegen %s\n" % _metadata.__version__)
        return
    sdl_filename = args["<sdl_filename>"]
    targets_in = args["<target>"]

    targets = set()
    problems = False
    for target_in in targets_in:
        if ":" not in target_in:
            target = target_in + ":client"
        else:
            target = target_in
        language, intent = target.split(":", 1)
        language = language.strip().lower()
        intent = intent.strip().lower()
        if language not in supported_languages:
            sys.stderr.write("Language %r not supported for target %r\n" % (language, target_in))
            problems = True
        if intent not in supported_intents:
            sys.stderr.write("Intent %r not supported for target %r\n" % (intent, target_in))
            problems = True
        if not problems:
            targets.add((language, intent))
    if problems:
        return "Failed to parse some targets. See also: adaptive --help"

    try:
        sdl_text = open(sdl_filename).read()
    except IOError as exc:
        sys.stderr.write(str(exc) + "\n")
        return "Failed to open SDL file %r" % sdl_filename

    try:
        module = SDL().parse(sdl_text)
    except Exception:
        # FIXME: Do something smart here
        raise

    for language, intent in targets:
        assert language == "python", (language, intent)
        module.traverse(python.Pythonize())
        if intent == "client":
            out_name = module.name + "_client.py"
            sys.stderr.write("%s python:client --> %s\n" % (sdl_filename, out_name))
            cm = genpyclient.ClientMaker()
            cm.module(module)
            with open(out_name, "wb") as fd:
                cm.dump(fd)
        elif intent == "server":
            out_name = module.name + "_server.py"
            sys.stderr.write("%s python:server --> %s\n" % (sdl_filename, out_name))
            sm = genpyserver.ServerMaker()
            sm.module(module)
            with open(out_name, "wb") as fd:
                sm.dump(fd)
        else:
            raise ValueError("WTF? %s %s" % (language, intent))


def call_main():
    exit(main(docopt(__doc__)))

if __name__ == "__main__":
    call_main()
