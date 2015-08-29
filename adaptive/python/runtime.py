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

import json


class AdaptiveValueType(object):
    __slots__ = ()
    __known_subclasses__ = {}  # name -> class

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        for slot_name in self.__slots__:
            if getattr(self, slot_name) != getattr(other, slot_name):
                return False
        return True

    def __to_jsonable__(self):
        # FIXME: Detect object cycles to avoid infinite recursion
        res = {"__adaptive_class_name__": self.__class__.__name__}
        for slot_name in self.__slots__:
            value = getattr(self, slot_name)
            if isinstance(value, AdaptiveValueType):
                res[slot_name] = value.__to_jsonable__()
            else:
                res[slot_name] = value
        return res

    @staticmethod
    def __from_jsonable__(value):
        class_name = value["__adaptive_class_name__"]
        class_ = AdaptiveValueType.__known_subclasses__[class_name]
        args = [value[slot_name] for slot_name in class_.__slots__]
        return class_(*args)


def AdaptiveValue(cls):
    AdaptiveValueType.__known_subclasses__[cls.__name__] = cls
    return cls


class AdaptiveJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, AdaptiveValueType):
            return obj.__to_jsonable__()
        return json.JSONEncoder.default(self, obj)


def adaptive_object_hook(obj_dict):
    try:
        return AdaptiveValueType.__from_jsonable__(obj_dict)
    except KeyError:
        return obj_dict


def serialize(obj):
    return json.dumps(obj, cls=AdaptiveJSONEncoder, separators=(',', ':'))


def deserialize(data):
    return json.loads(data, object_hook=adaptive_object_hook)


@AdaptiveValue
class AdaptiveException(AdaptiveValueType, Exception):
    __slots__ = "name", "value"

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return "%s: %s" % (self.name, self.value)


def assert_list_of(lst, typ, or_none=True):
    assert isinstance(lst, list), lst
    if or_none:
        for idx, value in enumerate(lst):
            assert value is None or isinstance(value, typ), (idx, value)
    else:
        for idx, value in enumerate(lst):
            assert isinstance(value, typ), (idx, value)
    return True
