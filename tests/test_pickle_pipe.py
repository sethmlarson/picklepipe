import pickle
import unittest
import picklepipe


class TestPicklePipe(unittest.TestCase):
    def make_pipe_pair(self):
        rd, wr = picklepipe.make_pipe_pair()
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
        self.assertRaises(picklepipe.PicklePipeTimeout, rd.recv_object, timeout=1.0)

    def test_only_sent_object_length(self):
        rd, wr = self.make_pipe_pair()
        rd._buffer = b'\x00\x00\x00\x01'
        self.assertRaises(picklepipe.PicklePipeTimeout, rd.recv_object, timeout=1.0)

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

    def test_erroring_socket(self):
        class FakeSocket(object):
            def __init__(self):
                self._sent = False

            def recv(self):
                return b'\x01'

            def setblocking(self, *_):
                pass

            def fileno(self):
                return 1234

            def sendall(self, *_):
                if self._sent:
                    raise OSError()
                self._sent = True

        # Only want to use the SelectSelector here.
        self.patch_default_selector()

        pipe = picklepipe.PicklePipe(FakeSocket())
        self.addCleanup(pipe.close)

        self.assertRaises(picklepipe.PicklePipeClosed, pipe.send_object, 'abc')
        self.assertIs(pipe.closed, True)
