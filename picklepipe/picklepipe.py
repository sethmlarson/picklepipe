import socket
import struct
try:
    import cPickle as pickle
except ImportError:
    import pickle

from .pipe import (BaseSerializingPipe,
                   PipeClosed)

__all__ = [
    'PicklePipe'
]


class _PickleSerializer(object):
    def __init__(self, protocol):
        self._protocol = protocol

    def loads(self, data):
        return pickle.loads(data)

    def dumps(self, obj):
        return pickle.dumps(obj, protocol=self._protocol)


class PicklePipe(BaseSerializingPipe):
    """ Implementation of the :class:`picklepipe.BaseSerializingPipe`
    that uses the pickling protocol for serialization.

    See the `Python docs on the pickle module <https://docs.python.org/3/library/pickle.html>`_
    for more information. """
    def __init__(self, sock, protocol=None, max_size=None):
        """
        Creates a :class:`picklepipe.PicklePipe` instance wrapping
        a given socket.

        :param sock: Socket to wrap.
        :param protocol: Pickling protocol to favor.
        """
        super(PicklePipe, self).__init__(sock, None, max_size=max_size)
        self._protocol = protocol
        self._protocol_sent = False
        self._protocol_recv = False

        self._send_protocol()

    @property
    def protocol(self):
        """ Highest protocol available between a peer
        and the current pipe owner. """
        self._recv_protocol()
        return self._protocol

    def fileno(self):
        self._recv_protocol()
        return super(PicklePipe, self).fileno()

    def send_object(self, obj):
        self._recv_protocol()
        super(PicklePipe, self).send_object(obj)

    def recv_object(self, timeout=None):
        self._recv_protocol()
        return super(PicklePipe, self).recv_object(timeout)

    def _send_protocol(self):
        if not self._protocol_sent:
            self._sock.sendall(struct.pack('>B', self._protocol or pickle.HIGHEST_PROTOCOL))
            self._protocol_sent = True

    def _recv_protocol(self):
        """ Resolves what the highest protocol number for
        pickling that is allowed by the peer. """
        if not self._protocol_recv:
            try:
                data = self._read_bytes(1, timeout=1.0)
                if len(data) == 0:
                    self.close()
                    raise PipeClosed()
                peer_protocol = struct.unpack('>B', data)[0]
                self._protocol = min(self._protocol or pickle.HIGHEST_PROTOCOL, peer_protocol)
                self._protocol_recv = True
                self._serializer = _PickleSerializer(self._protocol)
            except (OSError, socket.error):
                self.close()
                raise PipeClosed()
