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
Adaptive

Usage:
  adaptive client [--java=<dir>] [--python=<dir>] [--ruby=<dir>] <file> ...
  adaptive server [--java=<dir>] [--python=<dir>] [--ruby=<dir>] <file> ...
  adaptive -h | --help
  adaptive --version

Options:
  -h --help       Show this screen.
  --version       Show version.
  --java=<dir>    Emit java code to specified directory.
  --python=<dir>  Emit python code to specified directory.
  --ruby=<dir>    Emit ruby code to specified directory.
"""

import sys

from docopt import docopt

import _metadata, generate
from quark.compiler import Compiler, ParseError, CompileError
from quark.backend import Java

def main(args):
    if args["--version"]:
        sys.stderr.write("Adaptive %s\n" % _metadata.__version__)
        return
    filenames = args["<file>"]

    java = args["--java"]
    python = args["--python"]
    ruby = args["--ruby"]
    if python: return "python is not yet supported"
    if ruby: return "ruby is not yet supported"

    compiler = Compiler()
    compiler.annotator("value", generate.value)

    if args["client"]:
        compiler.annotator("service", generate.service_client)
    elif args["server"]:
        compiler.annotator("service", generate.service_server)
    else:
        assert False

    try:
        for name in filenames:
            with open(name, "rb") as fd:
                compiler.parse(name, fd.read())
    except IOError, e:
        return e
    except ParseError, e:
        return e
    finally:
        if java:
            compiler.write(java)

    try:
        compiler.compile()
    except CompileError, e:
        return e


    if java:
        j = Java()
        compiler.emit(j)
        j.write(java)

    if not java and not python and not ruby:
        return "no output languages specified"

def call_main():
    exit(main(docopt(__doc__)))

if __name__ == "__main__":
    call_main()
