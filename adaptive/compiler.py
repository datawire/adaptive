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

Targets: client (default)
         async-client (not implemented)
         server
"""

import sys

from docopt import docopt

import _metadata, generate
from sdl import SDL

supported_targets = "client", "server"


def main(args):
    if args["-V"] or args["--version"]:
        sys.stderr.write("Adaptive Codegen %s\n" % _metadata.__version__)
        return
    sdl_filename = args["<sdl_filename>"]
    targets_in = args["<target>"]

    targets = set(["client"])
    problems = False
    for target in targets_in:
        if target not in supported_targets:
            sys.stderr.write("Intent %r not supported for target %r\n" % (intent, target_in))
            problems = True
        if not problems:
            targets.add(target)
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

    for target in targets:
        if target == "client":
            out_name = module.name + "_client.q"
            sys.stderr.write("%s client --> %s\n" % (sdl_filename, out_name))
            cm = generate.ClientMaker()
            cm.module(module)
            with open(out_name, "wb") as fd:
                cm.dump(fd)
        elif target == "server":
            out_name = module.name + "_server.q"
            sys.stderr.write("%s server --> %s\n" % (sdl_filename, out_name))
            sm = generate.ServerMaker()
            sm.module(module)
            with open(out_name, "wb") as fd:
                sm.dump(fd)
        else:
            raise ValueError("WTF? %s" % target)


def call_main():
    exit(main(docopt(__doc__)))

if __name__ == "__main__":
    call_main()
