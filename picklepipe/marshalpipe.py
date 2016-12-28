import socket
import struct
import marshal

from .pipe import (BaseSerializingPipe,
                   PipeClosed)

__all__ = [
    'MarshalPipe'
]


class _MarshalSerializer(object):
    def __init__(self, version):
        self._version = version

    def loads(self, data):
        return marshal.loads(data)

    def dumps(self, obj):
        return marshal.dumps(obj, self._version)


class MarshalPipe(BaseSerializingPipe):
    """ Wraps an already connected socket and uses that
    socket as a interface to send pickled objects to a peer.
    Can be used to pickle not only single objects but also
    to pickle objects in a stream-able fashion. """
    def __init__(self, sock, version=None):
        """
        Creates a :class:`picklepipe.PicklePipe` instance wrapping
        a given socket.

        :param sock: Socket to wrap.
        :param version: Marshal version to favor.
        """
        super(MarshalPipe, self).__init__(sock, None)
        self._version = version
        self._version_sent = False
        self._version_recv = False

        self._send_version()

    @property
    def version(self):
        """ Highest version available between a peer
        and the current pipe owner. """
        self._recv_version()
        return self._version

    def send_object(self, obj):
        """ Pickles and sends and object to the peer.

        :param obj: Object to send to the peer.
        :raises: :class:`picklepipe.PicklePipeClosed` if the other end of the pipe is closed.
        """
        self._recv_version()
        super(MarshalPipe, self).send_object(obj)

    def recv_object(self, timeout=None):
        """ Receives a pickled object from the peer.

        :param float timeout: Number of seconds to wait before timing out.
        :return: Pickled object or None if timed out.
        :raises: :class:`picklepipe.PicklePipeClosed` if the other end of the pipe is closed.
        """
        self._recv_version()
        return super(MarshalPipe, self).recv_object(timeout)

    def _send_version(self):
        if not self._version_sent:
            self._sock.sendall(struct.pack('>B', self._version or marshal.version))
            self._version_sent = True

    def _recv_version(self):
        """ Resolves what the highest version number for
        pickling that is allowed by the peer. """
        if not self._version_recv:
            try:
                data = self._read_bytes(1)
                if len(data) == 0:
                    self.close()
                    raise PipeClosed()
                peer_version = struct.unpack('>B', data)[0]
                self._version = min(self._version or marshal.version, peer_version)
                self._version_recv = True
                self._serializer = _MarshalSerializer(self._version)
            except (OSError, socket.error):
                self.close()
                raise PipeClosed()
