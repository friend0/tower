#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Ryan A. Rodriguez
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA  02110-1301, USA.

"""
Optitrack controller
"""

import sys
import signal
import math
import msgpack
from pid import PID, PID_V, PID_RP
import simplejson
import numpy as np
from feedback.transformations import euler_from_quaternion
from scipy import signal as sgnl


# Roll/pitch limit
CAP = 15000.0
# Thrust limit - 15%
TH_CAP = 55000

YAW_CAP = 200

sp_x = 0
sp_y = 0
sp_z = 100

import zmq
import time

cmd = {
    "version": 1,
    "client_name": "N/A",
    "ctrl": {
        "roll": 0.1,
        "pitch": 0.1,
        "yaw": 0.0,
        "thrust": 0.0
    }
}

"""
ZMQ setup
"""
context = zmq.Context()

client_conn = context.socket(zmq.PUSH)
client_conn.connect("tcp://127.0.0.1:1212")

optitrack_conn = context.socket(zmq.REP)
optitrack_conn.bind("tcp://204.102.224.3:5000")

# todo: update to a ZMQ subscriber model
# optitrack_conn = context.socket(zmq.SUB)
# optitrack_conn.setsockopt(zmq.SUBSCRIBE, "")
# optitrack_conn.connect("tcp://204.102.224.3:5000")

midi_conn = context.socket(zmq.PULL)
midi_conn.connect("tcp://192.168.0.2:1250")

pid_viz_conn = context.socket(zmq.PUSH)
pid_viz_conn.connect("tcp://127.0.0.1:5123")

ctrl_conn = context.socket(zmq.PULL)
ctrl_conn.connect("tcp://127.0.0.1:5124")

yaw_sp = 0

""" Roll, Pitch and Yaw PID controllers """
r_pid = PID_RP(name="roll", P=25, I=0.28, D=7, Integrator_max=5, Integrator_min=-5, set_point=0, zmq_connection=pid_viz_conn)
p_pid = PID_RP(name="pitch", P=25, I=0.28, D=7, Integrator_max=5, Integrator_min=-5, set_point=0, zmq_connection=pid_viz_conn)
y_pid = PID_RP(name="yaw", P=10, I= 0, D= 0.35, Integrator_max=5, Integrator_min=-5, set_point=0,
               zmq_connection=pid_viz_conn)
t_pid = PID_RP(name="thrust", P=20, I=5 * 0.035, D=8 * 0.035, set_point=1.6, Integrator_max=0.01,
               Integrator_min=-0.01 / 0.035, zmq_connection=pid_viz_conn)

""" Vertical position and velocity PID loops """
v_pid = PID_RP(name="position", P=0.5, D=0.0, I=0.28, Integrator_max=100 / 0.035, Integrator_min=-100 / 0.035,
               set_point=.5,
               zmq_connection=pid_viz_conn)
vv_pid = PID_RP(name="velocity", P=0.1, D=0.00315, I=0.28, Integrator_max=5 / 0.035, Integrator_min=-5 / 0.035,
                set_point=0, zmq_connection=pid_viz_conn)

f_x = 1000.0
f_y = f_x

MAX_THRUST = 65500

prev_z = 0
prev_t, prev_time = time.time(), time.time()

prev_vz = 0

dt = 0

midi_acc = 0

last_ts = time.time()
on_detect_counter = 0
max_step = 11  # ms
min_step = 5  # ms
ctrl_time = 0
ts = 0

rp_p = r_pid.Kp
rp_i = r_pid.Ki
rp_d = r_pid.Kd


def signal_handler(signal, frame):
    """
    This signal handler function detects a keyboard interrupt and responds by sending kill command to CF via client
    :param signal:
    :param frame:
    :return:
    """
    print 'Kill Command Detected...'
    cmd["ctrl"]["roll"] = 0
    cmd["ctrl"]["pitch"] = 0
    cmd["ctrl"]["thrust"] = 0
    cmd["ctrl"]["yaw"] = 0
    r_pid.reset_dt()
    p_pid.reset_dt()
    y_pid.reset_dt()
    v_pid.reset_dt()
    vv_pid.reset_dt()

    vv_pid.Integrator = 0.0
    r_pid.Integrator = 0.0
    p_pid.Integrator = 0.0
    y_pid.Integrator = 0.0
    on_detect_counter = 0
    client_conn.send_json(cmd, zmq.NOBLOCK)
    print 'Vehicle Killed'
    sys.exit(0)


def map_angle(angle):
    rem, mapped_angle = divmod(angle, 180)
    if rem > 0:
        mapped_angle = -180 + mapped_angle
    return mapped_angle


signal.signal(signal.SIGINT, signal_handler)

"""
Ramp up CF Motors to avoid current surge
"""


def wind_up_motors():
    try:
        print("Spinning up motors...")
        for i in range(2500, 4500, 1):
            cmd["ctrl"]["roll"] = 0
            cmd["ctrl"]["pitch"] = 0
            cmd["ctrl"]["yaw"] = 0
            cmd["ctrl"]["thrust"] = i / 100.0
            client_conn.send_json(cmd)
            time.sleep(0.001)
    except:
        print("Motor wind-up failed")

    print("Motor spin-up complete")
    client_conn.send_json(cmd)


def quat2euler(q):
    """

    Function for returning a set of Euler angles from a given quaternion. Uses a fixed rotation sequence.

    :param q:
    :return:

    """
    qx, qy, qz, qw = q
    sqx, sqy, sqz, sqw = q ** 2
    invs = 1.0 / (sqx + sqy + sqz + sqw)

    yaw = np.arctan2(2.0 * (qx * qz + qy * qw) * invs, (sqx - sqy - sqz + sqw) * invs)
    pitch = -np.arcsin(2.0 * (qx * qy - qz * qw) * invs)
    roll = np.arctan2(2.0 * (qy * qz + qx * qw) * invs, (-sqx + sqy - sqz + sqw) * invs)

    return np.array((yaw, pitch, roll))


current_frame = None

def butter_lowpass(cutoff, fs, order=4):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = sgnl.butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

b, a = butter_lowpass(20, 240)

def butter_lowpass_filter(b, a, data):
    y = sgnl.lfilter(b, a, data)
    return y


cutoff = 5
fs = 120
order = 4
b, a = butter_lowpass(cutoff, fs, order=order)

class Frame(object):

    def __init__(self, value=None):
        self._frame_data = np.array(value)
        self.time_stamp = time.time()

    @property
    def frame_data(self):
        if self._frame_data is not None:
            return self._frame_data
        else:
            return None

    @frame_data.setter
    def frame_data(self, value):
        self._frame_data = np.array(value)
        self.time_stamp = time.time()

    @property
    def detected(self):
        if self._frame_data is not None:
            return self._frame_data[-1]
        else:
            return None

    @property
    def state(self):
        if self._frame_data is not None:
            return self._frame_data[:6]
        else:
            return None


class FrameHistory(object):

    def __init__(self, extrapolation_max = 5):
        self.extrapolation_max = extrapolation_max
        self.smooth_operator = np.array([0, 0, 0, 0, 0, 0])  # no need to ask...
        self.current_frame  = None
        self.l_frame = None
        self.ll_frame = None
        self.filtered_frame = 0
        self.extrapolation_count = 0
        self.prev_time = time.time()


    def decode_packet(self, packet):
        detected = packet[-1]
        delta = packet[-2]
        x, y, z = packet[0], packet[1], packet[2]
        x, y, z = -x, z, y
        q = np.array([packet[3], packet[4], packet[5], packet[6]])
        #np.linalg.norm(q)  # (qx, qy, qz, qw)
        # print("X:{}, Y:{}, Z:{}".format(x, y, z))
        orientation = [elem * (180 / math.pi) for elem in euler_from_quaternion(q, axes='syxz')]
        yaw, roll, pitch = orientation[0], orientation[1], orientation[2]
        return [x, y, z, yaw, roll, pitch, detected]

    def can_extrapolate(self):
        # we can extrapolate position if we at least have two previous, consecutive data points.
        # if we've extrapolated for more then 4 or 5 frames, we should not continue to extrapolate

        if self.l_frame is not None and self.ll_frame is not None and self.extrapolation_count < self.extrapolation_max:
            return True
        else:
            return False

    def extrapolate(self):
        if self.can_extrapolate:
            self.extrapolation_count += 1
            dt = time.time() - self.prev_time # current time - last time we added a state to smooth operator
            frame_velocity = (self.l_frame - self.ll_frame)/(self.l_frame.time_stamp - self. ll_frame.time_stamp)
            state = self.l_frame.state + frame_velocity*dt
            return state
        else:
            self.extrapolation_count = 0
            return None


    def update(self, packet):
        # Check if body is being tracked by cameras
        self.current_frame = Frame(self.decode_packet(packet))

        if self.current_frame.detected:  # Unpack position, orientation add it to current frame, update frame history
            state = self.current_frame.state
            self.extrapolation_count = 0
        else:  # extrapolate
            state = self.extrapolate()

        if state is not None:  # not None if frame is valid, or we could extrapolate
            self.smooth_operator = np.vstack((self.smooth_operator, state))
            self.prev_time = time.time()

            if self.smooth_operator.shape[0] > 100:
                self.smooth_operator = np.delete(self.smooth_operator, 0, 0)
                # Filter
                filtered = []
                for column in range(len(self.current_frame.state + 1)):
                    #print column, self.smooth_operator[:, column]
                    filt = butter_lowpass_filter(b, a, self.smooth_operator[:, column])
                    #print("Filt: ", filt)
                    print("Last", filt[-1])
                    filtered.append(filt[-1])

                self.ll_frame = self.l_frame
                self.l_frame = self.filtered_frame
                self.filtered_frame = Frame(filtered)
                print self.filtered_frame.frame_data
                return self.filtered_frame  # indicate success in updating

        return None  # id frame was not valid, and we cannot extrapolate

frame_history = FrameHistory()
# Start gathering feedback, running controller
x, y, z, yaw, roll, pitch = 0, 0, 0, 0, 0, 0
motors_not_wound = True
while True:

    try:
        # Receive Packet over ZMQ, unpack it
        packet = optitrack_conn.recv()
        frame_data = msgpack.unpackb(packet)
        optitrack_conn.send(b'Ack')
        if frame_history.update(frame_data) is None:
            print("Cont")
            continue

        if motors_not_wound:
            motors_not_wound = False
            wind_up_motors()  # Prime Motors with a ramp up period

        state = frame_history.filtered_frame.state
        print("State: ", state)
        x, y, z, angle, roll, pitch = state[0], state[1], state[2], state[3], state[4], state[5]
        print x, y, z, angle, roll, pitch
        # Get the set-points (if there are any)
        try:
            while True:
                ctrl_sp = ctrl_conn.recv_json(zmq.NOBLOCK)
                yaw_sp = ctrl_sp["set-points"]["yaw"]
                r_pid.set_point = ctrl_sp["set-points"]["roll"]
                p_pid.set_point = ctrl_sp["set-points"]["pitch"]
                midi_acc = ctrl_sp["set-points"]["velocity"]
        except zmq.error.Again:
            pass


        """
        Run the controller if we are getting a frame rate better than 100fps. Do not run if we are running faster than
        ~150 fps
        """
        step = time.time() - last_ts
        print(step)
        #if (max_step > step > min_step) and detected:
        if (.009 >= step >= .007):

            """
            check to see if we have been tracking the vehicle for more than 5 frames, e.g. if we are just starting or
            if we've lost tracking and are regaining it.
            """
            if on_detect_counter >= 0:
                ctrl_time = int(round(time.time() * 1000))
                print "IN  : x={:4.2f}, y={:4.2f}, z={:4.2f}, yaw={:4.2f}".format(x, y, z, angle)

                safety = 10
                roll = r_pid.update(x)
                pitch = p_pid.update(y)
                thrust = t_pid.update(z)
                # angle is the yaw, yaw_sp is set to a constant zero (we can change if we like)
                yaw = y_pid.update(((angle - yaw_sp + 360 + 180) % 360) - 180)

                roll_sp = roll
                pitch_sp = pitch
                yaw_out = yaw

                velocity = v_pid.update(z)
                velocity = max(min(velocity, 10), -10)  # Limit vertical velocity between -1 and 1 m/sec
                vv_pid.set_point = velocity
                dt = (time.time() - prev_t)
                curr_velocity = (z - prev_z) / dt
                curr_acc = (curr_velocity - prev_vz) / dt
                thrust_sp = vv_pid.update(curr_velocity) + 0.50

                # print "TH={:.2f}".format(thrust_sp)
                # print "YAW={:.2f}".format(yaw)

                prev_z = z
                prev_vz = curr_velocity
                prev_t = time.time()
                """ Thrust was being generated as a decimal value instead of as percent in other examples """
                thrust_sp = max(min(thrust_sp, 1), 0.40)

                # thrust_sp = max(min(thrust_sp, 0.90), 0.40)

                if yaw_out < -YAW_CAP:
                    yaw_out = -YAW_CAP
                if yaw_out > YAW_CAP:
                    yaw_out = YAW_CAP

                pitch_corr = pitch_sp * math.cos(math.radians(-angle)) - roll_sp * math.sin(math.radians(-angle))
                roll_corr = pitch_sp * math.sin(math.radians(-angle)) + roll_sp * math.cos(math.radians(-angle))

                print "OUT: roll={:2.2f}, pitch={:2.2f}, thrust={:5.2f}, dt={:0.3f}, fps={:2.1f}".format(roll_corr,
                                                                                                         pitch_corr,
                                                                                                         thrust_sp, dt,
                                                                                                         1 / dt)
                print "OUT: alt={:1.4f}, thrust={:5.2f}, dt={:0.3f}, fps={:2.1f}, speed={:+0.4f}".format(z, thrust_sp,
                                                                                                         dt, 1 / dt,
                                                                                                         curr_velocity)
                # print "dt={:0.3f}, fps={:2.1f}".format(dt, 1/dt)
                cmd["ctrl"]["roll"] = roll_corr
                cmd["ctrl"]["pitch"] = pitch_corr
                cmd["ctrl"]["thrust"] = thrust_sp * 100
                cmd["ctrl"]["yaw"] = yaw_out
            else:
                on_detect_counter += 1
        else:
            # print "No detect"
            cmd["ctrl"]["roll"] = 0
            cmd["ctrl"]["pitch"] = 0
            cmd["ctrl"]["thrust"] = 0
            cmd["ctrl"]["yaw"] = 0
            r_pid.reset_dt()
            p_pid.reset_dt()
            y_pid.reset_dt()
            v_pid.reset_dt()
            vv_pid.reset_dt()

            vv_pid.Integrator = 0.0
            r_pid.Integrator = 0.0
            p_pid.Integrator = 0.0
            y_pid.Integrator = 0.0
            on_detect_counter = 0

        client_conn.send_json(cmd)
        last_ts = time.time()

    except simplejson.scanner.JSONDecodeError as e:
        print e
