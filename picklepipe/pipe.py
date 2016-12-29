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
    'PipeDeserializingError',
    'PipeObjectTooLargeError'
]
# Default size is 16MB.
DEFAULT_MAX_SIZE = 0xFFFFFF


def _check_max_size(max_size):
    if not isinstance(max_size, int):
        raise ValueError('max_size must be an integer value.')
    if max_size > 0xFFFFFFFF:
        raise ValueError('max_size cannot be more than %d' % max_size)
    if max_size < 0:
        raise ValueError('max_size cannot be negative.')


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


class PipeObjectTooLargeError(PipeError):
    """ Exception for when an object is too large for the
    pipe's max_size attribute. """
    pass


class BaseSerializingPipe(object):
    """ Wraps an already connected socket and uses that
    socket as a interface to send serialized objects to a peer. """
    def __init__(self, sock, serializer, max_size=None):
        """
        :param sock: Socket to wrap.
        :param serializer:
            Object that implements ``.dumps(obj)`` and
            ``.loads(data)`` to serialize objects.
        :param int max_size:
            Maximum size of a serialized object that this pipe is willing
            to deserialize. This value is meant to limit the pipe's maximum
            memory usage while deserializing objects.
        """
        # Setting up the socket and serializer.
        self._buffer = b''
        self._serializer = serializer
        self._sock = sock  # type: socket.socket
        self._sock.setblocking(False)

        # Adding the socket to the selector.
        self._selector = selectors2.DefaultSelector()
        self._selector.register(self._sock, selectors2.EVENT_READ)

        # Setting up the max_size attribute.
        if max_size is None:
            max_size = DEFAULT_MAX_SIZE
        _check_max_size(max_size)
        self._max_size = max_size

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def __del__(self):
        self.close()

    @property
    def max_size(self):
        """ Current setting for maximum size. """
        return self._max_size

    def set_max_size(self, max_size):
        """
        Sets the maximum size object that the pipe is willing to
        deserialize to limit memory usage of the pipe.

        :param int max_size:
            Maximum number of bytes to deserialize for a single object.
        """
        _check_max_size(max_size)
        self._max_size = max_size

    def close(self):
        """ Closes the pipe instance as well as the internal socket. """
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
        """ Attribute is True if the pipe instance is closed. """
        return self._sock is None

    def fileno(self):
        """ Returns the file descriptor for the
        internal interface being used. """
        return self._sock.fileno()

    def send_object(self, obj):
        """ Serializes and sends and object to the peer.

        :param obj: Object to send to the peer.
        :raises: :class:`picklepipe.PipeClosed` if the other end of the pipe is closed.
        """
        try:
            data = self._serializer.dumps(obj)
        except Exception as e:
            raise PipeSerializingError(e)
        data_len = len(data)

        # AppVeyor and Travis CI don't like it when you allocate >4GB.
        if data_len > 0xFFFFFFFF:  # Skip coverage.
            raise PipeObjectTooLargeError()

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
                if data_len == 0:
                    raise PipeDeserializingError(ValueError('Object cannot be zero width.'))
                if data_len > self._max_size:
                    # A sticky situation where we now need to void the object
                    # that is trying to be sent to us. Thing is we need to also
                    # complete this voiding before our timeout so if we can't
                    # finish voiding we should be conservative and close the pipe.
                    # Otherwise just notify that the object was too large.
                    data_to_read = data_len
                    while data_to_read > 0:
                        data = self._read_bytes(min(0xFFFFFF, data_to_read),
                                                timeout=t.remaining)
                        data_to_read -= len(data)
                        if not data and t.timed_out:
                            break
                    if data_to_read == 0:
                        raise PipeObjectTooLargeError()
                    else:
                        self.close()
                        raise PipeClosed()
                pickle_data = self._read_bytes(data_len, timeout=t.remaining)
                if len(pickle_data) != data_len:
                    self._buffer += len_data + pickle_data
                    raise PipeTimeout()
                try:
                    return self._serializer.loads(pickle_data)
                except Exception as e:
                    raise PipeDeserializingError(e)
        except (OSError, socket.error, selectors2.SelectorError, struct.error):
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
