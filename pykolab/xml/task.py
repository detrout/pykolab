import kolabformat

from pykolab.translate import _

class Task(kolabformat.Task):
    def __init__(self, *args, **kw):
        kolabformat.Task.__init__(self, *args, **kw)

class TaskIntegrityError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

class InvalidTaskDateError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

