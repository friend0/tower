"""

Work in progress: Python implementation of the hybrid controller implemented in Python instead of Simulink

"""
from __future__ import absolute_import
from __future__ import division
from builtins import object
from past.utils import old_div
import math
from math import pi

import numpy as np

from .initialize import Tstep as Ts

""" Controller Constants"""
m = .028
g = 9.8
kp = '[0.09 0 0; 0 0.12 0; 0 0 0.15]'
kp = np.array(np.matrix(kp.strip('[]')))
kd = '[0.13 0 0; 0 0.15 0; 0 0 0.18]'
kd = np.array(np.matrix(kd.strip('[]')))


def sat(x, lower, upper):
    if x < lower:
        x = lower
    elif x > upper:
        x = upper
    return x


class pid_controller(object):
    def __init__(self):
        self.kix = 0  # u(t-1)
        self.kiy = 0
        self.kiz = 0
        self.last = {'x': self.kix, 'y': self.kiy, 'z': self.kiz}

        self.kix_t1 = 0
        self.kiy_t1 = 0
        self.kiz_t1 = 0
        self.accum = {'x': self.kix_t1, 'y': self.kiy_t1, 'z': self.kiz_t1}

    @staticmethod
    def static_var(varname, value):
        def decorate(func):
            setattr(func, varname, value)
            return func

        return decorate

    def forward_euler(self, axis, lower=None, upper=None):
        # y(k) = y(k-1) + T * u(k-1)
        accum = self.accum[axis]
        last = self.last[axis]
        accum += Ts * last
        return accum

    def reset(self):
        self.kix = 0  # u(t-1)
        self.kiy = 0
        self.kiz = 0

    def update(self, m, g, kp, kd, pR, pR_dot, pR_double_dot, p, p_punto):

        sat_T = 1.8 * m * g  # max thrust to almost double of weight
        sat_roll_pitch = old_div(pi, 4)  # max roll and pitch angle

        e3 = np.matrix('0 0 1')

        # Errors
        p_tilde = p - pR
        p_tilde_dot = pR_dot - pR_double_dot
        x_tilde = p[0] - pR[0]
        y_tilde = p[1] - pR[1]
        z_tilde = p[2] - pR[2]

        self.kix = self.forward_euler('x')
        self.kiy = self.forward_euler('y')
        self.kiz = self.forward_euler('z')
        iVec = np.transpose(np.matrix('{} {} {}'.format(self.kix, self.kiy, self.kiz)))

        K = - kd * p_tilde_dot - kp * p_tilde + iVec

        if np.linalg.norm(K) > m * g * 0.95:
            K = K / np.linalg.norm(K) * m * g * 0.95

        vc = m * g * e3 - m * pR_duepunti - K

        if np.linalg.norm(vc) < m * g * 0.05:
            vc = vc / np.linalg.norm(vc) * m * g * 0.05

        thrust = np.linalg.norm(vc)
        theta = math.asin(old_div((vc(1)), thrust))
        phi = math.atan2(-vc(2), vc(3))

        thrust = sat(thrust, -sat_T, sat_T)
        thrust = thrust / sat_T * 100  # scale to fit 0:100

        return phi, theta, thrust
