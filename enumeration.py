"""
Enumeration class - a crude way to form enumerations using classes

Author: Joe Taylor
Date: 30th July 2010 22:49
"""


class Enum(object):
    def __init__(self, name, *values):
        self.__name__ = name
        for v in values:
            setattr(self, v, EnumValue(self, v))


class EnumValue(object):
    def __init__(self, enum, value):
        self.__name__ = value
        self.enum = enum

    def __eq__(self, other):
        return repr(self) == repr(other)

    def __cmp__(self, other):
        return cmp(repr(self), repr(other))

    def __repr__(self):
        return "%s.%s" % (self.enum.__name__, self.__name__)
