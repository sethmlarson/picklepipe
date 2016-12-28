import os
import struct
import pickle
import unittest
import picklepipe


class TestPicklePipe(unittest.TestCase):
    def make_pipe_pair(self):
        rd, wr = picklepipe.make_pipe_pair(picklepipe.PicklePipe)
        self.addCleanup(rd.close)
        self.addCleanup(wr.close)
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

    def test_default_protocol(self):
        rd, wr = self.make_pipe_pair()
        self.assertEqual(rd.protocol, pickle.HIGHEST_PROTOCOL)
        self.assertEqual(wr.protocol, pickle.HIGHEST_PROTOCOL)

    def test_same_protocol(self):
        r, w = self.make_socketpair()
        rd = picklepipe.PicklePipe(r, protocol=2)
        self.addCleanup(rd.close)
        wr = picklepipe.PicklePipe(w, protocol=2)
        self.addCleanup(wr.close)

        self.assertEqual(wr.protocol, 2)
        self.assertEqual(rd.protocol, 2)

    def test_different_protocol(self):
        r, w = self.make_socketpair()
        rd = picklepipe.PicklePipe(r, protocol=1)
        self.addCleanup(rd.close)
        wr = picklepipe.PicklePipe(w, protocol=2)
        self.addCleanup(wr.close)

        self.assertEqual(wr.protocol, 1)
        self.assertEqual(rd.protocol, 1)

    def test_fileno(self):
        r, w = self.make_socketpair()
        rd = picklepipe.PicklePipe(r, protocol=1)
        self.addCleanup(rd.close)
        wr = picklepipe.PicklePipe(w, protocol=2)
        self.addCleanup(wr.close)

        self.assertEqual(rd.fileno(), r.fileno())
        self.assertEqual(wr.fileno(), w.fileno())

    def test_close_pipe(self):
        r, w = self.make_socketpair()
        rd = picklepipe.PicklePipe(r, protocol=1)
        self.addCleanup(rd.close)
        wr = picklepipe.PicklePipe(w, protocol=2)
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
        rd._buffer = struct.pack('>I', 128) + os.urandom(128)
        self.assertRaises(picklepipe.PipeUnserializingError, rd.recv_object, timeout=0.3)
        self.assertIs(rd.closed, False)

    def test_send_object_to_closed_reading_socket_before_proto(self):
        r, w = self.make_socketpair()
        rd = picklepipe.PicklePipe(r, protocol=1)
        self.addCleanup(rd.close)
        wr = picklepipe.PicklePipe(w, protocol=2)
        self.addCleanup(wr.close)

        r.close()
        self.assertRaises(picklepipe.PipeClosed, wr.send_object, 'abc')

    def test_send_object_to_closed_reading_socket_after_proto(self):
        r, w = self.make_socketpair()
        rd = picklepipe.PicklePipe(r, protocol=1)
        self.addCleanup(rd.close)
        wr = picklepipe.PicklePipe(w, protocol=2)
        self.addCleanup(wr.close)

        rd._recv_protocol()
        wr._recv_protocol()
        r.close()
        self.assertRaises(picklepipe.PipeClosed, wr.send_object, 'abc')

    def test_send_object_to_closed_writing_socket(self):
        r, w = self.make_socketpair()
        rd = picklepipe.PicklePipe(r, protocol=1)
        self.addCleanup(rd.close)
        wr = picklepipe.PicklePipe(w, protocol=2)
        self.addCleanup(wr.close)

        rd._recv_protocol()
        wr._recv_protocol()
        w.close()
        self.assertRaises(picklepipe.PipeClosed, wr.send_object, 'abc')
