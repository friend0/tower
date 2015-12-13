from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import *


class Swarm(object):
    def __init__(self, quadrotors=None, hetrogenous=False):
        self.quadrotors = {}