from itertools import izip, tee, izip_longest


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