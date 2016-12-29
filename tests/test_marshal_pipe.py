import marshal
import picklepipe
from . import _base_pipe_testcase


class MarshalTestCase(_base_pipe_testcase.BasePipeTestCase):
    PIPE_TYPE = picklepipe.MarshalPipe

    def test_default_protocol(self):
        rd, wr = self.make_pipe_pair()
        self.assertEqual(rd.protocol, marshal.version)
        self.assertEqual(wr.protocol, marshal.version)
