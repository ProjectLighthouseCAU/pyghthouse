from enum import Enum

class ReID:
    def __init__(self):
        self._next = 0

    def __next__(self):
        n = self._next
        self._next += 1
        return n

    def __iter__(self):
        return self

class VerbosityLevel(Enum):
    NONE = 0
    WARN_ONCE = 1
    WARN = 2
    ALL = 3