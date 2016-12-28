import time

__all__ = [
    'Timeout'
]

# Use time.monotonic on Python 3.3+, otherwise
# try to use monotonic.monotonic, and finally
# just use time.time even though it's not comparable. :(
if hasattr(time, 'monotonic'):
    monotonic = time.monotonic
else:  # Skip coverage.
    try:
        from monotonic import monotonic
    except RuntimeError:
        monotonic = time.time


class Timeout(object):
    def __init__(self, timeout=None):
        self._timeout = timeout
        self._start_time = None

    @property
    def remaining(self):
        if self._timeout is None:
            return None
        else:
            return max(0.0, self._timeout - (monotonic() - self._start_time))

    @property
    def timed_out(self):
        return (self._timeout is not None and
                self._timeout - (monotonic() - self._start_time) <= 0.0)

    def __enter__(self):
        self._start_time = monotonic()
        return self

    def __exit__(self, *args):
        pass
