import pickle
import picklepipe
from . import _base_pipe_testcase


class PickleTestCase(_base_pipe_testcase.BasePipeTestCase):
    PIPE_TYPE = picklepipe.PicklePipe

    def test_default_protocol(self):
        rd, wr = self.make_pipe_pair()
        self.assertEqual(rd.protocol, pickle.HIGHEST_PROTOCOL)
        self.assertEqual(wr.protocol, pickle.HIGHEST_PROTOCOL)
