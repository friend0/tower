"""

Pure Python Quaternion library

"""

from __future__ import (absolute_import, division, print_function, unicode_literals)
import numpy as np
import math

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
            self.q = np.array((self.qw, self.qx, self.qy, self.qz))
        else:
            self.qw, self.qx, self.qy, self.qz = kwargs.get('qw', 0), kwargs.get('qx', 0), \
                                                 kwargs.get('qy', 0), kwargs.get('qz', 0)
            self.q = np.array((self.qw, self.qx, self.qy, self.qz))

    def __mul__(self, other):
        p = np.array([[self.qw, -self.qx, -self.qy, -self.qz],
                       [self.qx, self.qw, -self.qz, self.qy],
                       [self.qy, self.qz, self.qw, -self.qx],
                       [self.qz, -self.qy, self.qx, self.qw]])

        q = np.array((other.qw, other.qx, other.qy, other.qz))

        return p.dot(q.transpose())

    def __rmul__(self, other):
        return other

    def __add__(self, other):
        qw = self.qw + other.qw
        qx = self.qx + other.qx
        qy = self.qy + other.qy
        qz = self.qz + other.qz

        return np.array((qw, qx, qy, qz))

    def __sub__(self, other):
        qw = self.qw - other.qw
        qx = self.qx - other.qx
        qy = self.qy - other.qy
        qz = self.qz - other.qz

        return np.array((qw, qx, qy, qz))

    def __div__(self, other):
        pass

    @property
    def q(self):
        return self._q

    @q.setter
    def q(self, value):
        if type(value) is not np.array:
            value = np.array(value)
        self._q = value
        self.qw, self.qx, self.qy, self.qz = self._q[0], self._q[1], self._q[2], self._q[3]

    @property
    def conjugate(self):
        return np.array((self.qw, -self.qx, -self.qy, -self.qz))

    @property
    def inverse(self):
        return self.conjugate/np.linalg.norm(self.q)


    def dcm(self):
        # first norm the quat
        np.linalg.norm(self.q)
        q0, q0_2 = self.qw, self.qw * self.qw
        q1, q1_2 = self.qx, self.qx * self.qx
        q2, q2_2 = self.qy, self.qy * self.qy
        q3, q3_2 = self.qz, self.qz * self.qz

        #r = np.array([[q0_2 + q1_2 - q2_2 - q3_2, 2*(q1*q2 + q0*q3), 2*(q1*q3 - q0*q2)],
        #               [2*(q1*q2 - q0*q3), q0_2 - q1_2 + q2_2 - q3_2, 2*(q2*q3 + q0*q1)],
        #               [2*(q1*q3 + q0*q2), 2*(q2*q3 - q0*q1), q0_2 - q1_2 - q2_2 + q3_2]])

        r = np.array([[1 - 2*q2_2 - 2*q3_2, 2*(q1*q2 + q0*q3), 2*(q1*q3 - q0*q2)],
                       [2*(q1*q2 - q0*q3), 1 - 2*q1_2 - 2*q3_2, 2*(q2*q3 + q0*q1)],
                       [2*(q1*q3 + q0*q2), 2*(q2*q3 - q0*q1), 1 - 2*q1_2 - 2*q2_2]])

        return r

    def quaternion_matrix(self):
        """Return homogeneous rotation matrix from quaternion.

        >>> M = quaternion_matrix([0.99810947, 0.06146124, 0, 0])
        >>> numpy.allclose(M, rotation_matrix(0.123, [1, 0, 0]))
        True
        >>> M = quaternion_matrix([1, 0, 0, 0])
        >>> numpy.allclose(M, numpy.identity(4))
        True
        >>> M = quaternion_matrix([0, 1, 0, 0])
        >>> numpy.allclose(M, numpy.diag([1, -1, -1, 1]))
        True

        """
        q = np.array(self.q, dtype=np.float64, copy=True)
        n = np.dot(q, q)
        #if n < _EPS:
        #    return np.identity(4)
        q *= math.sqrt(2.0 / n)
        q = np.outer(q, q)
        return np.array([
            [1.0-q[2, 2]-q[3, 3],     q[1, 2]-q[3, 0],     q[1, 3]+q[2, 0], 0.0],
            [    q[1, 2]+q[3, 0], 1.0-q[1, 1]-q[3, 3],     q[2, 3]-q[1, 0], 0.0],
            [    q[1, 3]-q[2, 0],     q[2, 3]+q[1, 0], 1.0-q[1, 1]-q[2, 2], 0.0],
            [                0.0,                 0.0,                 0.0, 1.0]])

    def euler(self, seq='zxy', mode='radians'):
        roll = math.atan2(self.qx*self.qz + self.qy*self.qw, -(self.qy*self.qz - self.qx*self.qw))
        pitch = math.acos(-self.qx - self.qy + self.qz + self.qw)
        yaw = math.atan2(self.qx*self.qz - self.qy*self.qw, self.qy*self.qz + self.qx*self.qw)

        if mode is not 'radians':
            return 180/math.pi*np.array([roll, pitch, yaw])
        return np.array([roll, pitch, yaw])


if __name__ == '__main__':

    quat = Quaternion(qw=1, qx=0, qy=0, qz=0)
    quat = Quaternion([1, 0, 0, 0])
    print(quat.qw)
    print(quat.qw, quat.qx, quat.qy, quat.qz)
    print(quat.q)
    print(quat * quat)
    quat = Quaternion(qw=.7071, qx=.7071, qy=0, qz=0)
    print(quat.dcm())


    quat = Quaternion([1, 0, 0, 0])
    print(quat.qw)
    print(quat.qw, quat.qx, quat.qy, quat.qz)
    print(quat.q)
    print(quat * quat)

    quat = Quaternion(qw=.7071, qx=.7071, qy=0, qz=0)
    print(quat.dcm())
    print(quat.quaternion_matrix())

    print(quat.inverse)
    print(quat.euler(mode='degrees'))

