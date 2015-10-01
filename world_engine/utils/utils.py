from itertools import izip, tee, izip_longest
from itertools import cycle
from threading import Timer
from time import strftime

def pairwise(iterable):
    "s -> (s0,s1), (s2,s3), (s4, s5), ..."
    a, b = tee(iterable)
    next(b, None)
    a = iter(iterable)
    return izip(a, b)


def grouper(iterable, n, fillvalue=None):
    """
    Collect data into fixed-length chunks or blocks
    grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    :param iterable:
    :param n:
    :param fillvalue:
    :rtype : object
    """

    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)

class Interrupt(object):

    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.daemon = True
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False
