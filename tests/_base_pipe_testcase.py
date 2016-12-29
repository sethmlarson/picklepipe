import socket
import struct
import selectors2
import unittest
import picklepipe


def _safe_close(pipe):
    try:
        pipe.close()
    except:
        pass


class BasePipeTestCase(unittest.TestCase):
    PIPE_TYPE = None

    def make_pipe_pair(self):
        rd, wr = picklepipe.make_pipe_pair(self.PIPE_TYPE)
        assert isinstance(rd, picklepipe.BaseSerializingPipe)
        assert isinstance(wr, picklepipe.BaseSerializingPipe)
        self.addCleanup(_safe_close, rd)
        self.addCleanup(_safe_close, wr)
        return rd, wr

    def make_socketpair(self):
        from picklepipe.socketpair import socketpair
        return socketpair()

    def patch_default_selector(self):
        from picklepipe import pipe
        old_default = pipe.selectors2.DefaultSelector
        self.addCleanup(setattr, pipe.selectors2, 'DefaultSelector', old_default)
        pipe.selectors2.DefaultSelector = pipe.selectors2.SelectSelector

    def test_send_single_object(self):
        rd, wr = self.make_pipe_pair()
        wr.send_object('abc')
        obj = rd.recv_object(timeout=1.0)
        self.assertEqual(obj, 'abc')

    def test_many_objects(self):
        rd, wr = self.make_pipe_pair()
        for i in range(100):
            wr.send_object(i)
        for i in range(100):
            obj = rd.recv_object(timeout=1.0)
            self.assertEqual(obj, i)

    def test_timeout(self):
        rd, wr = self.make_pipe_pair()
        self.assertRaises(picklepipe.PipeTimeout, rd.recv_object, timeout=0.3)

    def test_only_sent_object_length(self):
        rd, wr = self.make_pipe_pair()
        rd._buffer = b'\x00\x00\x00\x01'
        self.assertRaises(picklepipe.PipeTimeout, rd.recv_object, timeout=0.3)

    def test_only_sent_part_of_object_length(self):
        rd, wr = self.make_pipe_pair()
        rd._buffer = b'\x00\x00\x00'
        self.assertRaises(picklepipe.PipeTimeout, rd.recv_object, timeout=0.3)

    def test_only_sent_part_of_object(self):
        rd, wr = self.make_pipe_pair()
        rd._buffer = struct.pack('>I', 4) + b'\x00\x00\x00'
        self.assertRaises(picklepipe.PipeTimeout, rd.recv_object, timeout=0.3)

    def test_same_protocol(self):
        r, w = self.make_socketpair()
        rd = self.PIPE_TYPE(r, protocol=2)
        self.addCleanup(rd.close)
        wr = self.PIPE_TYPE(w, protocol=2)
        self.addCleanup(wr.close)

        self.assertEqual(wr.protocol, 2)
        self.assertEqual(rd.protocol, 2)

    def test_different_protocol(self):
        r, w = self.make_socketpair()
        rd = self.PIPE_TYPE(r, protocol=1)
        self.addCleanup(rd.close)
        wr = self.PIPE_TYPE(w, protocol=2)
        self.addCleanup(wr.close)

        self.assertEqual(wr.protocol, 1)
        self.assertEqual(rd.protocol, 1)

    def test_fileno(self):
        r, w = self.make_socketpair()
        rd = self.PIPE_TYPE(r, protocol=1)
        self.addCleanup(rd.close)
        wr = self.PIPE_TYPE(w, protocol=2)
        self.addCleanup(wr.close)

        self.assertEqual(rd.fileno(), r.fileno())
        self.assertEqual(wr.fileno(), w.fileno())

    def test_close_pipe(self):
        r, w = self.make_socketpair()
        rd = self.PIPE_TYPE(r, protocol=1)
        self.addCleanup(rd.close)
        wr = self.PIPE_TYPE(w, protocol=2)
        self.addCleanup(wr.close)

        self.assertIs(wr.closed, False)
        self.assertIs(rd.closed, False)

        wr.close()
        self.assertIs(wr.closed, True)

        rd.close()
        self.assertIs(rd.closed, True)

    def test_recv_unpicklable_object(self):
        rd, wr = self.make_pipe_pair()
        rd._recv_protocol()
        rd._buffer = struct.pack('>I', 6) + b'abc123'
        self.assertRaises(picklepipe.PipeDeserializingError, rd.recv_object, timeout=0.3)
        self.assertIs(rd.closed, False)

    def test_send_object_to_closed_reading_socket_before_proto(self):
        r, w = self.make_socketpair()
        rd = self.PIPE_TYPE(r, protocol=1)
        self.addCleanup(rd.close)
        wr = self.PIPE_TYPE(w, protocol=2)
        self.addCleanup(wr.close)

        r.close()
        self.assertRaises(picklepipe.PipeClosed, wr.send_object, 'abc')

    def test_send_object_to_closed_reading_socket_after_proto(self):
        r, w = self.make_socketpair()
        rd = self.PIPE_TYPE(r, protocol=1)
        self.addCleanup(rd.close)
        wr = self.PIPE_TYPE(w, protocol=2)
        self.addCleanup(wr.close)

        rd._recv_protocol()
        wr._recv_protocol()
        r.close()
        self.assertRaises(picklepipe.PipeClosed, wr.send_object, 'abc')

    def test_send_object_to_closed_writing_socket(self):
        r, w = self.make_socketpair()
        rd = self.PIPE_TYPE(r, protocol=1)
        self.addCleanup(rd.close)
        wr = self.PIPE_TYPE(w, protocol=2)
        self.addCleanup(wr.close)

        rd._recv_protocol()
        wr._recv_protocol()
        w.close()
        self.assertRaises(picklepipe.PipeClosed, wr.send_object, 'abc')

    def test_unserializable_object(self):
        rd, wr = self.make_pipe_pair()
        self.assertRaises(picklepipe.PipeSerializingError, wr.send_object, socket.socket())

    def test_pipe_as_context_manager(self):
        rd, wr = self.make_pipe_pair()
        with wr as c:
            self.assertIs(wr.closed, False)
            c.send_object('abc')
            obj = rd.recv_object(timeout=1.0)
            self.assertEqual(obj, 'abc')
            self.assertIs(wr.closed, False)
        self.assertIs(wr.closed, True)

    def test_reading_bytes_error(self):

        def bad_recv_bytes(n, timeout=None):
            raise OSError(1)

        rd, wr = self.make_pipe_pair()
        wr.send_object('abc')
        rd._recv_protocol()
        rd._read_bytes = bad_recv_bytes
        self.assertRaises(picklepipe.PipeClosed, rd.recv_object)
        self.assertIs(rd.closed, True)

    def test_no_data_for_recv_protocol(self):
        r, w = self.make_socketpair()
        rd = self.PIPE_TYPE(r)
        self.addCleanup(rd.close)

        self.assertRaises(picklepipe.PipeClosed, rd._recv_protocol)
        self.assertIs(rd.closed, True)

    def test_pipe_selectable(self):
        rd, wr = self.make_pipe_pair()
        selector = selectors2.DefaultSelector()
        selector.register(rd, selectors2.EVENT_READ)
        selector.register(wr, selectors2.EVENT_WRITE)

        events = selector.select(timeout=0.1)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][0].fileobj, wr)
        self.assertEqual(events[0][1], selectors2.EVENT_WRITE)

        wr.send_object('abc')

        events = selector.select(timeout=0.1)
        self.assertEqual(len(events), 2)
        index = 1 if events[0][0].fileobj == wr else 0

        self.assertEqual(events[index][0].fileobj, rd)
        self.assertEqual(events[index][1], selectors2.EVENT_READ)

    def test_pipe_init_max_size(self):
        for size in [0xFFFFFFFF + 1, -1, 'abc']:
            rd, wr = self.make_socketpair()
            self.assertRaises(ValueError, self.PIPE_TYPE, rd, max_size=size)

    def test_pipe_set_max_size(self):
        rd, wr = self.make_socketpair()
        pipe = self.PIPE_TYPE(rd)
        self.assertRaises(ValueError, pipe.set_max_size, 0xFFFFFFFF + 1)
        self.assertRaises(ValueError, pipe.set_max_size, -1)
        self.assertRaises(ValueError, pipe.set_max_size, 'abc')

        for size in range(20):
            pipe.set_max_size(size)
            self.assertEqual(pipe.max_size, size)

    def test_recv_zero_width_object(self):
        rd, _ = self.make_pipe_pair()
        rd._recv_protocol()
        rd._buffer = b'\x00\x00\x00\x00'
        self.assertRaises(picklepipe.PipeDeserializingError, rd.recv_object, timeout=0.3)
        self.assertIs(rd.closed, False)

    def test_recv_too_large_object(self):
        rd, _ = self.make_pipe_pair()
        rd._recv_protocol()
        rd.set_max_size(128)
        rd._buffer = struct.pack('>I', 129) + (b'x' * 129)
        self.assertRaises(picklepipe.PipeObjectTooLargeError, rd.recv_object, timeout=0.3)
        self.assertIs(rd.closed, False)

    def test_recv_too_large_object_cant_void(self):
        rd, _ = self.make_pipe_pair()
        rd._recv_protocol()
        rd.set_max_size(128)

        # This test puts the pipe into an unknown state of only partially
        # receiving a too-large object for the pipe.
        rd._buffer = struct.pack('>I', 129) + (b'x' * 128)
        self.assertRaises(picklepipe.PipeClosed, rd.recv_object, timeout=0.3)
        self.assertIs(rd.closed, True)
