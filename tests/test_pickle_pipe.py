import unittest
import picklepipe


class TestPicklePipe(unittest.TestCase):
    def make_pipe_pair(self):
        rd, wr = picklepipe.make_pipe_pair()
        self.addCleanup(rd.close)
        self.addCleanup(wr.close)
        return rd, wr

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
