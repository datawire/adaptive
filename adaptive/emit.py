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

from contextlib import contextmanager


class EmitterHelper(object):

    def __init__(self):
        self.lines = []
        self.last_appender = None

    def append(self, appender, line):
        if self.last_appender is not None and self.last_appender != appender:
            self.lines.append("")
        self.lines.append(line.rstrip())
        self.last_appender = appender

    def dump(self, fd):
        fd.write("\n".join(self.lines))
        fd.write("\n")

    def dumps(self):
        return "\n".join(self.lines) + "\n"


class Emitter(object):

    def __init__(self, prefix="", destination=None):
        self.prefix = prefix
        if destination is None:
            self.destination = EmitterHelper()
        elif isinstance(destination, Emitter):
            self.destination = destination.destination
        else:
            assert isinstance(destination, EmitterHelper), destination
            self.destination = destination
        self.indent_level = 0

    def out(self, line):
        self.destination.append(self, self.prefix + self.indent_level * "    " + line)

    def indent(self):
        self.indent_level += 1

    def dedent(self):
        assert self.indent_level > 0, (self.indent_level, self.destination.dumps())
        self.indent_level -= 1

    @contextmanager
    def indentation(self):
        self.indent()
        yield
        self.dedent()

    @contextmanager
    def block(self, start):
        self.out("%s {" % start)
        self.indent()
        yield
        self.dedent()
        self.out("}")

    def dump(self, fd):
        return self.destination.dump(fd)

    def dumps(self):
        return self.destination.dumps()

    __call__ = out


class RefEmitter(Emitter):
    """Helper to emit SDL for reference"""

    def module_head(self, mod):
        self.out("module %s {" % mod.name)
        self.indent()

    def module_tail(self, mod):
        self.dedent()
        self.out("};")

    def description(self, desc):
        self.out("desc %s;" % desc.content)

    def struct(self, st):
        self.out("struct %s {" % st.name)
        with self.indentation():
            for field in st.fields:
                self.out(str(field))
        self.out("};")

    def operation(self, op):
        self.out("%s %s(%s) {" % (op.type, op.name, ", ".join(str(p) for p in op.parameters)))
        with self.indentation():
            self.out("desc %s;" % op.description.content)
            # FIXME: Loop over contents of operation here, once they are parsed and available.
        self.out("};")
