import socket
import struct
import selectors2

from .socketpair import socketpair
from .timeout import Timeout

__all__ = [
    'BaseSerializingPipe',
    'make_pipe_pair',
    'PipeClosed',
    'PipeError',
    'PipeTimeout',
    'PipeSerializingError',
    'PipeDeserializingError'
]


class PipeError(Exception):
    """ Generic error for :class:`picklepipe.BaseSerializingPipe` """
    pass


class PipeTimeout(PipeError):
    """ Exception for when retrieving an object from
    a :class:`picklepipe.BaseSerializingPipe` times out. """
    pass


class PipeClosed(PipeError):
    """ Exception for when the peer has closed
    their end of the :class:`picklepipe.BaseSerializingPipe`. """
    pass


class PipeSerializingError(PipeError):
    """ Exception for when an object can't be serialized
    by the pipe's serializing object. """
    def __init__(self, exception):
        self.exception = exception


class PipeDeserializingError(PipeError):
    """ Exception for when an object can't be deserialized
    by the pipe's serializing object. """
    def __init__(self, exception):
        self.exception = exception


class BaseSerializingPipe(object):
    """ Wraps an already connected socket and uses that
    socket as a interface to send serialized objects to a peer. """
    def __init__(self, sock, serializer):
        """
        :param sock: Socket to wrap.
        :param serializer:
            Object that implements ``.dumps(obj)`` and
            ``.loads(data)`` to serialize objects.
        """
        self._buffer = b''
        self._serializer = serializer
        self._sock = sock  # type: socket.socket
        self._sock.setblocking(False)

        self._selector = selectors2.DefaultSelector()
        self._selector.register(self._sock, selectors2.EVENT_READ)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def __del__(self):
        self.close()

    def close(self):
        if self._sock is None:
            return
        try:
            self._sock.close()
            self._selector.unregister(self._sock)
            self._selector.close()
        except Exception:  # Skip coverage.
            pass
        self._sock = None
        self._selector = None

    @property
    def closed(self):
        return self._sock is None

    def fileno(self):
        """ Returns the file descriptor for the
        internal interface being used. """
        return self._sock.fileno()

    def send_object(self, obj):
        """ Pickles and sends and object to the peer.

        :param obj: Object to send to the peer.
        :raises: :class:`picklepipe.PipeClosed` if the other end of the pipe is closed.
        """
        try:
            data = self._serializer.dumps(obj)
        except Exception as e:
            raise PipeSerializingError(e)
        data_len = len(data)
        if data_len > 0xFFFFFFFF:
            raise ValueError('Serialized object is too large.')
        try:
            self._sock.sendall(struct.pack('>I', len(data)))
            self._sock.sendall(data)
        except (OSError, socket.error):
            self.close()
            raise PipeClosed()

    def recv_object(self, timeout=None):
        """ Receives a pickled object from the peer.

        :param float timeout: Number of seconds to wait before timing out.
        :return: Pickled object or None if timed out.
        :raises: :class:`picklepipe.PipeClosed` if the other end of the pipe is closed.
        """
        try:
            with Timeout(timeout) as t:
                len_data = self._read_bytes(4, timeout=t.remaining)
                if len(len_data) != 4:
                    self._buffer += len_data
                    raise PipeTimeout()
                data_len = struct.unpack('>I', len_data)[0]
                pickle_data = self._read_bytes(data_len, timeout=t.remaining)
                if len(pickle_data) != data_len:
                    self._buffer += len_data + pickle_data
                    raise PipeTimeout()
                try:
                    return self._serializer.loads(pickle_data)
                except Exception as e:
                    raise PipeDeserializingError(e)
        except (OSError, socket.error, selectors2.SelectorError):
            self.close()
            raise PipeClosed()

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
                    return buffer  # Skip coverage.
        return buffer


def make_pipe_pair(pipe_type, *args, **kwargs):
    """
    Given a types of :class:`picklepipe.BaseSerializingPipe` return
    a tuple containing two pipes instances that are connected to one another.

    :param type pipe_type: Type of pipe to connect to one another.
    :param args: Arguments to pass to the pipes init.
    :param kwargs: Key-word arguments to pass to the pipes init.
    :return: Tuple with two connected pipes.
    """
    rd, wr = socketpair()
    return (pipe_type(rd, *args, **kwargs),
            pipe_type(wr, *args, **kwargs))
