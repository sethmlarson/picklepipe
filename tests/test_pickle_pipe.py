import picklepipe
from . import _base_pipe_testcase


class MarshalTestCase(_base_pipe_testcase.BasePipeTestCase):
    PIPE_TYPE = picklepipe.MarshalPipe
