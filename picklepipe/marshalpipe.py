import socket
import struct
import marshal

from .pipe import (BaseSerializingPipe,
                   PipeClosed)

__all__ = [
    'MarshalPipe'
]


class _MarshalSerializer(object):
    def __init__(self, protocol):
        self._protocol = protocol

    def loads(self, data):
        return marshal.loads(data)

    def dumps(self, obj):
        return marshal.dumps(obj, self._protocol)


class MarshalPipe(BaseSerializingPipe):
    """ Implementation of the :class:`picklepipe.BaseSerializingPipe`
    that uses the marshal protocol for serialization.

    See the `Python docs on the marshal module <https://docs.python.org/3/library/marshal.html>`_
    for more information. """
    def __init__(self, sock, protocol=None, max_size=None):
        """
        Creates a :class:`picklepipe.MarshalPipe` instance wrapping
        a given socket.

        :param sock: Socket to wrap.
        :param protocol: Marshal protocol to favor.
        """
        super(MarshalPipe, self).__init__(sock, None, max_size=max_size)
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

    def send_object(self, obj):
        self._recv_protocol()
        super(MarshalPipe, self).send_object(obj)

    def recv_object(self, timeout=None):
        self._recv_protocol()
        return super(MarshalPipe, self).recv_object(timeout)

    def fileno(self):
        self._recv_protocol()
        return super(MarshalPipe, self).fileno()

    def _send_protocol(self):
        if not self._protocol_sent:
            self._sock.sendall(struct.pack('>B', self._protocol or marshal.version))
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
                self._protocol = min(self._protocol or marshal.version, peer_protocol)
                self._protocol_recv = True
                self._serializer = _MarshalSerializer(self._protocol)
            except (OSError, socket.error):
                self.close()
                raise PipeClosed()
