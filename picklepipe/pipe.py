import socket
import struct
import pickle
import selectors2

from .socketpair import socketpair
from .timeout import Timeout

__all__ = [
    'PicklePipe',
    'make_pipe_pair'
]


class PicklePipe(object):
    def __init__(self, sock, protocol=None):
        """ Wraps an already connected socket and uses that
        socket as a interface to send pickled objects to a peer.
        Can be used to pickle not only single objects but also
        to pickle objects in a streamable fashion. """
        self._buffer = b''
        self._closed = False
        self._protocol = protocol
        self._protocol_sent = False
        self._protocol_recv = False
        self._sock = sock  # type: socket.socket
        self._sock.setblocking(False)

        self._selector = selectors2.DefaultSelector()
        events = selectors2.EVENT_READ | selectors2.EVENT_WRITE
        self._selector.register(self._sock, events)

        self._send_protocol()
        self._closed = True

    def __del__(self):
        self.close()

    @property
    def protocol(self):
        """ Highest protocol available between a peer
        and """
        return self._protocol

    def close(self):
        if self._sock is None:
            raise ValueError('PicklePipe is already closed.')
        try:
            self._sock.close()
            self._selector.unregister(self._sock)
            self._selector.close()
        except Exception:
            pass
        self._sock = None
        self._selector = None

    @property
    def closed(self):
        return self._closed

    def fileno(self):
        """ Returns the file descriptor for the
        internal interface being used. """
        return self._sock.fileno()

    def send_object(self, obj):
        """ Pickles and sends and object to the peer.

        :param obj: Object to send to the peer.
        :raises: :class:`EOFError` if the other end of the pipe is closed.
        """
        self._recv_protocol()
        data = pickle.dumps(obj, protocol=self._protocol)
        data_len = len(data)
        if data_len > 0xFFFFFFFF:
            raise ValueError('Pickled object is too large.')
        try:
            self._sock.sendall(struct.pack('>I', len(data)))
            self._sock.sendall(data)
        except (OSError, socket.error):
            raise EOFError

    def recv_object(self, timeout=None):
        """ Receives a pickled object from the peer.

        :param float timeout: Number of seconds to wait before timing out.
        :return: Pickled object or None if timed out.
        :raises: :class:`EOFError` if the other end of the pipe is closed.
        """
        self._recv_protocol()
        with Timeout(timeout) as t:
            len_data = self._read_bytes(4, timeout=t.remaining)
            if len(len_data) != 4:
                self._buffer += len_data
                return None
            data_len = struct.unpack('>I', len_data)[0]
            pickle_data = self._read_bytes(data_len, timeout=t.remaining)
            if len(pickle_data) != data_len:
                self._buffer += len_data + pickle_data
                return None
            try:
                obj = pickle.loads(pickle_data)
            except pickle.UnpicklingError:
                return None
            return obj

    def _send_protocol(self):
        if not self._protocol_sent:
            self._sock.sendall(struct.pack('>B', self._protocol or pickle.HIGHEST_PROTOCOL))
            self._protocol_sent = True

    def _recv_protocol(self):
        """ Resolves what the highest protocol number for
        pickling that is allowed by the peer. """
        if not self._protocol_recv:
            peer_protocol = struct.unpack('>B', self._read_bytes(1))[0]
            self._protocol = min(self._protocol or pickle.HIGHEST_PROTOCOL, peer_protocol)
            self._protocol_recv = True

    def _read_bytes(self, n, timeout=None):
        if len(self._buffer) > n:
            buffer = self._buffer[:n]
            self._buffer = self._buffer[n:]
        else:
            buffer = self._buffer
            self._buffer = b''
        with Timeout(timeout) as t:
            while len(buffer) < n:
                try:
                    events = self._selector.select(t.remaining)
                    if events:
                        _, event = events[0]
                        if event & selectors2.EVENT_READ:
                            buffer += self._sock.recv(n - len(buffer))
                    if t.timed_out:
                        break
                except selectors2.SelectorError:
                    return buffer
        return buffer


def make_pipe_pair():
    sock1, sock2 = socketpair()
    return PicklePipe(sock1), PicklePipe(sock2)
