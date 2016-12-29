import json
import socket
import unittest
import picklepipe


def _safe_close(pipe):
    try:
        pipe.close()
    except:
        pass


class TestJSONPipe(unittest.TestCase):
    def make_pipe_pair(self):
        rd, wr = picklepipe.make_pipe_pair(picklepipe.JSONPipe)
        assert isinstance(rd, picklepipe.BaseSerializingPipe)
        assert isinstance(wr, picklepipe.BaseSerializingPipe)
        self.addCleanup(_safe_close, rd)
        self.addCleanup(_safe_close, wr)
        return rd, wr

    def make_socketpair(self):
        from picklepipe.socketpair import socketpair
        return socketpair()

    def test_send_jsonable_objects(self):
        objects = ['abc',
                   1,
                   [1, '2', [3]],
                   {'a': ['b', 1, {'c': 'd', 'e': [2, 'f']}]}]
        for obj in objects:
            rd, wr = self.make_pipe_pair()
            wr.send_object(obj)
            self.assertEqual(obj, rd.recv_object(timeout=0.1))

    def test_send_non_jsonable_objects(self):
        objects = [set(),
                   socket.socket(),
                   {'a': [1, 2, '3', object()]}]
        for obj in objects:
            rd, wr = self.make_pipe_pair()
            try:
                wr.send_object(obj)
            except picklepipe.PipeSerializingError as e:
                self.assertIsInstance(e.exception, TypeError)
            else:
                self.fail('Didn\'t raise picklepipe.PipeSerializingError')
