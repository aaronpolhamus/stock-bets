"""Custom utils file with classes and methods to be shared across multiple bits of business logic
"""


class CustomException(Exception):
    def __init__(self, default_msg, msg=None):
        self._default_msg = default_msg
        self._msg = msg

    def __str__(self):
        if self._msg:
            return self._msg
        else:
            return self._default_msg
