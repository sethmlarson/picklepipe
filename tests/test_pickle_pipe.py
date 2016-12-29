import picklepipe
from . import _base_pipe_testcase


class PickleTestCase(_base_pipe_testcase.BasePipeTestCase):
    PIPE_TYPE = picklepipe.PicklePipe

    def test_pipe_send_large_object(self):
        _, wr = self.make_pipe_pair()
        self.assertRaises(picklepipe.PipeObjectTooLargeError, wr.send_object, b'x' * (0xFFFFFFFF + 1))