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
from scipy import signal


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
r_pid = PID_RP(name="roll", P=0, I=0, D=0, Integrator_max=5, Integrator_min=-5, set_point=0,
               zmq_connection=pid_viz_conn)
p_pid = PID_RP(name="pitch", P=100, I=0, D=0, Integrator_max=5, Integrator_min=-5, set_point=0,
               zmq_connection=pid_viz_conn)
y_pid = PID_RP(name="yaw", P=5, I=0, D=0.35, Integrator_max=5, Integrator_min=-5, set_point=0,
               zmq_connection=pid_viz_conn)
t_pid = PID_RP(name="thrust", P=20, I=5 * 0.035, D=8 * 0.035, set_point=.150, Integrator_max=0.01,
               Integrator_min=-0.01 / 0.035, zmq_connection=pid_viz_conn)

""" Vertical position and velocity PID loops """
v_pid = PID_RP(name="position", P=.5, D=0.0, I=0.28, Integrator_max=100 / 0.035, Integrator_min=-100 / 0.035,
               set_point=.150,
               zmq_connection=pid_viz_conn)
vv_pid = PID_RP(name="velocity", P=0.35, D=0.00315, I=0.28, Integrator_max=5 / 0.035, Integrator_min=-5 / 0.035,
                set_point=0, zmq_connection=pid_viz_conn)

f_x = 1000.0
f_y = f_x

MAX_THRUST = 65500

prev_z = 0
prev_t, prev_time = time.time(), time.time()

prev_vz = 0

dt = 0

midi_acc = 0

last_ts = 0
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


b, a = signal.butter(4, 100, 'low', analog=True)
w, h = signal.freqs(b, a)


def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
    return b, a


def butter_lowpass_filter(b, a, data, cutoff, fs, order=5):
    y = signal.lfilter(b, a, data)
    return y


cutoff = 5
fs = 120
order = 4
b, a = butter_lowpass(cutoff, fs, order=order)

buffer, frame = np.array([0, 0, 0, 0, 0, 0]), np.array(None)


class Frame(object):

    def __init__(self, frame_data=None):
        self.data = frame_data
        self.time_stamp = time.time()

    @property
    def data(self):
        return self.data

    @data.setter
    def data(self, value):
        self._data = np.array(value)
        self.time_stamp = time.time()

ll_frame, l_frame, frame = Frame(), Frame(), Frame()

while True:

    try:
        # Receive Packet over ZMQ, unpack it
        packet = optitrack_conn.recv()
        unpackd = msgpack.unpackb(packet)
        optitrack_conn.send(b'Ack')

        # Check if body is being tracked by cameras
        detected = unpackd[-1]
        if detected:  # Unpack position, orientation
            delta = unpackd[-2]
            x, y, z = unpackd[0], unpackd[1], unpackd[2]
            y, z = -z, y
            q = np.linalg.norm(np.array([unpackd[3], unpackd[4], unpackd[5], unpackd[6]]))  # (qx, qy, qz, qw)
            # print("X:{}, Y:{}, Z:{}".format(x, y, z))
            orientation = [elem * (180 / math.pi) for elem in euler_from_quaternion(q, axes='syxz')]
            yaw, roll, pitch = orientation[0], orientation[1], orientation[2]
            ll_frame = l_frame
            l_frame = frame
            frame.data = [x, y, z, yaw, roll, pitch]


        else:  # extrapolate
            # determine if we can extrapolate
            # do we have valid l_frame and ll_frame + not exceeding max extrapolation?
            if l_frame is not None and ll_frame is not None:
                ll_frame = l_frame
                frame = l_frame
            if l_frame is not None and ll_frame is not None:
                dt = time.time() - prev_time
                frame_velocity = (l_frame - ll_frame)/(l_frame.time_stamp - ll_frame.time_stamp)  # must divide by time step to give m/s or deg/s, but we want m, deg
                ll_frame = l_frame
                l_frame = frame
                frame = l_frame + frame_velocity*dt
            print("Not Tracking!!")

        prev_time = time.time()

        buffer = np.vstack(buffer, frame)

        if buffer.shape[0] >= 5:
            buffer = np.delete(buffer, 0, 0)

            # Filter
            filt_frame = []
            for column in range(buffer.shape[1]):
                filt = butter_lowpass(b, a, buffer[:, column], cutoff, fs, order)
                filt_frame.append(filt)
            # Save as current frame for extrapolation and PIDs
            frame = filt_frame
            x, y, z, yaw, roll, pitch = frame[0], frame[1], frame[2], frame[3], frame[4], frame[5]

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

        # print "RP P/I/D={}/{}/{}".format(rp_p, rp_i, rp_d)
        x_r = (x / f_x) * z
        y_r = (y / f_y) * z

        """
        Run the controller if we are getting a frame rate better than 100fps. Do not run if we are running faster than
        ~150 fps
        """
        step = ts - last_ts
        #if (max_step > step > min_step) and detected:
        if (max_step > step > min_step):

            """
            check to see if we have been tracking the vehicle for more than 5 frames, e.g. if we are just starting or
            if we've lost tracking and are regaining it.
            """
            if on_detect_counter >= 0:
                ctrl_time = int(round(time.time() * 1000))
                print "IN  : x={:4.2f}, y={:4.2f}, z={:4.2f}, yaw={:4.2f}".format(x, y, z, yaw)
                print "CORR: x={:5.4f}, y={:5.4f}, z={:5.4f}".format(x_r, y_r, z)

                safety = 10
                roll = 0.0  # r_pid.update(x)
                pitch = p_pid.update(y)
                t_pid.update(z)
                y_pid.update(((yaw - yaw_sp + 360 + 180) % 360) - 180)

                roll_sp = roll
                pitch_sp = pitch
                yaw_out = yaw
                # thrust_sp = thrust+0.73

                velocity = v_pid.update(z)
                velocity = max(min(velocity, 10), -10)  # Limit vertical velocity between -1 and 1 m/sec
                # velocity = midi_acc
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
                thrust_sp = 100 * max(min(thrust_sp, .90), 0.40)

                # thrust_sp = max(min(thrust_sp, 0.90), 0.40)

                if yaw_out < -YAW_CAP:
                    yaw_out = -YAW_CAP
                if yaw_out > YAW_CAP:
                    yaw_out = YAW_CAP

                pitch_corr = pitch_sp * math.cos(math.radians(-yaw)) - roll_sp * math.sin(math.radians(-yaw))
                roll_corr = pitch_sp * math.sin(math.radians(-yaw)) + roll_sp * math.cos(math.radians(-yaw))

                print "OUT: roll={:2.2f}, pitch={:2.2f}, thrust={:5.2f}, dt={:0.3f}, fps={:2.1f}".format(roll_corr,
                                                                                                         pitch_corr,
                                                                                                         thrust_sp, dt,
                                                                                                         1 / dt)
                print "OUT: alt={:1.4f}, thrust={:5.2f}, dt={:0.3f}, fps={:2.1f}, speed={:+0.4f}".format(z, thrust_sp,
                                                                                                         dt, 1 / dt,
                                                                                                         curr_velocity)
                # print "dt={:0.3f}, fps={:2.1f}".format(dt, 1/dt)
                cmd["ctrl"]["roll"] = roll_corr / 30.0
                cmd["ctrl"]["pitch"] = pitch_corr / 30.0
                cmd["ctrl"]["thrust"] = thrust_sp
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
        last_ts = ts

    except simplejson.scanner.JSONDecodeError as e:
        print e
