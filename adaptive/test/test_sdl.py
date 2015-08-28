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

import os
import pytest

import adaptive.sdl


sdl_names = "minimal.sdl", "longer.sdl", "petstore.sdl", # "petstore_full_fails.sdl"
sdl_data = {name: open(os.path.join(os.path.dirname(__file__), name)).read().strip()
            for name in sdl_names}


@pytest.fixture(params=sdl_names)
def sdl(request):
    return sdl_data[request.param]


def test_str_roundtrip(sdl):
    m = adaptive.sdl.SDL().parse(sdl)
    print str(m)
    print sdl
    if "defaults" not in sdl:
        assert str(m) == sdl
