"""

Pure Python Quaternion library

"""
from __future__ import (absolute_import, division, print_function, unicode_literals)
import numpy as np


class Quaternion(object):

    def __init__(self, q=None, **kwargs):
        """

        Specify the quaternion as a vector of the form: qw + qx*i + qy*j + qz*k, i.e. [1, 0, 0, 0]
        or by its component parts qw, qx, qy, qz. If the Quaternion is instantiated using the latter, component-wise
        method, all non-specified components will be zero.

        :param q: an array of elements corresponding to the components of the quaternion
        :param kwargs: specify the elements qw, qx, qy, qz individually.
        :return: A Quaternion object

        """
        # todo: check that q is of the right dimension, i.e. a 1*4 or a 4*1
        if q is not None:
            self.qw, self.qx, self.qy, self.qz = q[0], q[1], q[2], q[3]
            self.q = [self.qw, self.qx, self.qy, self.qz]
        else:
            self.qw, self.qx, self.qy, self.qz = kwargs.get('qw', 0), kwargs.get('qx', 0), \
                                                 kwargs.get('qy', 0), kwargs.get('qz', 0)
            self.q = [self.qw, self.qx, self.qy, self.qz]

    def __mul__(self, other):
        p = np.matrix([[self.qw, -self.qx, -self.qy, -self.qz],
                       [self.qx, self.qw, -self.qz, self.qy],
                       [self.qy, self.qz, self.qw, -self.qx],
                       [self.qz, -self.qy, self.qx, self.qw]])

        q = np.matrix([other.qw, other.qx, other.qy, other.qz])

        return p * q.transpose()

    def __rmul__(self, other):
        return other

    def __add__(self, other):
        qw = self.qw + other.qw
        qx = self.qx + other.qx
        qy = self.qy + other.qy
        qz = self.qz + other.qz

        return np.matrix([qw, qx, qy, qz])

    def __sub__(self, other):
        qw = self.qw - other.qw
        qx = self.qx - other.qx
        qy = self.qy - other.qy
        qz = self.qz - other.qz

        return np.matrix([qw, qx, qy, qz])

    def __div__(self, other):
        pass

    @property
    def q(self):
        return self._q

    @q.setter
    def q(self, value):
        self._q = np.matrix(value)
        [self.qw, self.qx, self.qy, self.qz] = self._q[(0, 0)], self._q[(0, 1)], self._q[(0, 2)], self._q[(0, 3)]


if __name__ == '__main__':

    quat = Quaternion(qw=1, qx=0, qy=0, qz=0)
    quat = Quaternion([1, 0, 0, 0])
    print(quat.qw)
    print(quat.qw, quat.qx, quat.qy, quat.qz)
    print(quat.q)
    print(quat * quat)

    quat = Quaternion([1, 0, 0, 0])
    print(quat.qw)
    print(quat.qw, quat.qx, quat.qy, quat.qz)
    print(quat.q)
    print(quat * quat)
