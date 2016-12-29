import json
from .pipe import BaseSerializingPipe

__all__ = [
    'JSONPipe'
]


class _JSONSerializer(object):
    def loads(self, data):
        return json.loads(data.decode('utf-8'))

    def dumps(self, obj):
        return json.dumps(obj).encode('utf-8')


class JSONPipe(BaseSerializingPipe):
    """ Implementation of the :class:`picklepipe.BaseSerializingPipe`
    that serializes data into JSON using ``json.dumps`` and ``json.loads``.

    See the `Python docs on the marshal module <https://docs.python.org/3/library/marshal.html>`_
    for more information. """
    def __init__(self, sock, max_size=None):
        """
        Creates a :class:`picklepipe.JSONPipe` instance wrapping
        a given socket.

        :param sock: Socket to wrap.
        """
        super(JSONPipe, self).__init__(sock, _JSONSerializer(), max_size=max_size)
