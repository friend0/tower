#!/usr/bin/env python
"""

A simple PID control loop for crazyflie using a set of Optitrack Flex13's

"""

import sys
import signal
import math
import msgpack
from pid import PID_V, PID_RP
import simplejson
from feedback.frames import FrameHistory
import zmq
import time


import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='./logs/octrl.log',
                    filemode='w')

formatter = logging.Formatter('%(asctime)s %(name)-8s %(levelname)-8s %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.info('Logging Initialized')

YAW_CAP = 200

sp_x = 0
sp_y = 0
sp_z = 100

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

# todo: All PID loops ought to be organized by a dictionary or an array. They can be looped through or updated by key
logger.info('ZMQ context set, connections configured')
# Roll, Pitch and Yaw PID controllers
r_pid = PID_RP(name="roll", P=35, I=0.3, D=8, Integrator_max=5, Integrator_min=-5, set_point=0,
               zmq_connection=pid_viz_conn)
p_pid = PID_RP(name="pitch", P=35, I=0.3, D=8, Integrator_max=5, Integrator_min=-5, set_point=0,
               zmq_connection=pid_viz_conn)
y_pid = PID_RP(name="yaw", P=5, I=0, D=0.35, Integrator_max=5, Integrator_min=-5, set_point=0,
               zmq_connection=pid_viz_conn)

# Vertical position and velocity PID loops
v_pid = PID_RP(name="position", P=0.6, D=0.0075, I=0.25, Integrator_max=100 / 0.035, Integrator_min=-100 / 0.035,
               set_point= .5,
               zmq_connection=pid_viz_conn)

# todo: Testing velocity controller in position role, in effect the thurst controller
#v_pid = PID_V(name="position", p=0.6, i=0.0075, d=0.25, set_point=.5)

#vv_pid = PID_RP(name="velocity", P=0.2, D=0.0005, I=0.15, Integrator_max=5 / 0.035, Integrator_min=-5 / 0.035,
#                set_point=0, zmq_connection=pid_viz_conn)

# todo: Testing Velocity Control on Velocity """
vv_pid = PID_V(name="velocity", p=0.25, i=1e-10, d=1e-10, set_point=0)

logger.info('PIDs Initialized')

def signal_handler(signal, frame):
    """

    This signal handler function detects a keyboard interrupt and responds by sending kill command to CF via client

    :param signal:
    :param frame:

    """
    logger.info('Kill Sequence Initiated')
    print 'Kill Command Detected...'
    cmd["ctrl"]["roll"] = 0
    cmd["ctrl"]["pitch"] = 0
    cmd["ctrl"]["thrust"] = 0
    cmd["ctrl"]["yaw"] = 0
    r_pid.reset_dt()
    p_pid.reset_dt()
    y_pid.reset_dt()
    v_pid.reset_dt()
    # vv_pid.reset_dt()

    # vv_pid.Integrator = 0.0
    r_pid.Integrator = 0.0
    p_pid.Integrator = 0.0
    y_pid.Integrator = 0.0
    on_detect_counter = 0
    client_conn.send_json(cmd, zmq.NOBLOCK)
    print 'Vehicle Killed'
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def wind_up_motors(time=1e-2):
    """

    Ramp up CF Motors to avoid current surge

    """
    try:
        print("Spinning up motors...")
        for i in range(2500, 4500, 1):
            cmd["ctrl"]["roll"] = 0
            cmd["ctrl"]["pitch"] = 0
            cmd["ctrl"]["yaw"] = 0
            cmd["ctrl"]["thrust"] = i / 100.0
            client_conn.send_json(cmd)
            time.sleep(time)
    except:
        print("Motor wind-up failed")

    print("Motor spin-up complete")
    client_conn.send_json(cmd)

if __name__ == '__main__':

    motors_not_wound = True
    frame_history = FrameHistory(filtering=False, extrapolating=False)
    logger.info('FrameHistory Initialized')
    x, y, z, yaw, roll, pitch = 0, 0, 0, 0, 0, 0
    ts, dt, prev_z, prev_vz, midi_acc, on_detect_counter, ctrl_time = 0, 0, 0, 0, 0, 0, 0
    prev_t, last_ts = time.time(), time.time()
    min_step, max_step = 7e-3, 9e-3 # s

    while True:

        try:
            # Receive Packet over ZMQ, unpack it
            packet = optitrack_conn.recv()
            frame_data = msgpack.unpackb(packet)
            optitrack_conn.send(b'Ack')

            if frame_history.update(frame_data) is None:
                print("Cont")
                continue
            detected = bool(frame_data[-1])
            logger.debug('Received: {}'.format(frame_data))

            if motors_not_wound:
                logger.info('Motors winding up...')
                motors_not_wound = False
                wind_up_motors(.01)  # Prime Motors with a ramp up period
                logger.info('Motors wound.')

            state = frame_history.filtered_frame.state
            logger.debug("Processed State: x:{} y:{} z:{} yaw:{} roll:{} pitch:{}".format(state[0], state[1], state[2],
                                                                                          state[3], state[4], state[5]))
            #print("State Feedback: x:{} y:{} z:{} yaw:{} roll:{} pitch:{}".format(state[0], state[1], state[2],
            #                                                                      state[3], state[4], state[5]))
            x, y, z, angle, roll, pitch = state[0], state[1], state[2], state[3], state[4], state[5]

            # Get the set-points (if there are any)
            try:
                while True:
                    ctrl_sp = ctrl_conn.recv_json(zmq.NOBLOCK)
                    yaw_sp = ctrl_sp["set-points"]["yaw"]
                    r_pid.set_point = ctrl_sp["set-points"]["roll"]
                    p_pid.set_point = ctrl_sp["set-points"]["pitch"]
                    midi_acc = ctrl_sp["set-points"]["velocity"]
                    logger.debug("Set Points: yaw_sp:{} roll_sp:{} pitch_sp{} midi_acc{}".format(yaw_sp, r_pid.set_point,
                                                                                                 p_pid.set_point, midi_acc))
            except zmq.error.Again:
                pass

            step = time.time() - last_ts
            logger.debug("Time Step: {}s".format(step))

            if (max_step >= step >= min_step) and detected:

                """
                check to see if we have been tracking the vehicle for more than 5 frames, e.g. if we are just starting or
                if we've lost tracking and are regaining it.
                """
                if on_detect_counter >= 0:
                    ctrl_time = int(round(time.time() * 1000))
                    #print "IN  : x={:4.2f}, y={:4.2f}, z={:4.2f}, yaw={:4.2f}".format(x, y, z, angle)

                    # Roll, Pitch, Yaw
                    roll_sp = roll = r_pid.update(x)
                    pitch_sp = pitch = p_pid.update(y)
                    yaw_out = yaw = y_pid.update(((angle - yaw_sp + 360 + 180) % 360) - 180)

                    # Thrust

                    # Velocity in z
                    velocity = v_pid.update(z)
                    logger.debug("V_PID: {}".format(velocity))
                    velocity = max(min(velocity, 10), -10)  # Limit vertical velocity between -1 and 1 m/sec
                    vv_pid.set_point = velocity
                    dt = (time.time() - prev_t)
                    curr_velocity = (z - prev_z) / dt
                    curr_acc = (curr_velocity - prev_vz) / dt
                    thrust_sp = vv_pid.update(curr_velocity) + 0.50
                    logger.debug("VV_PID: Out:{}".format(velocity))


                    # print "TH={:.2f}".format(thrust_sp)
                    # print "YAW={:.2f}".format(yaw)

                    prev_z = z
                    prev_vz = curr_velocity
                    prev_t = time.time()
                    """ Thrust was being generated as a decimal value instead of as percent in other examples """
                    thrust_sp = max(min(thrust_sp, .80), 0.40)

                    # thrust_sp = max(min(thrust_sp, 0.90), 0.40)

                    if yaw_out < -YAW_CAP:
                        yaw_out = -YAW_CAP
                    if yaw_out > YAW_CAP:
                        yaw_out = YAW_CAP

                    pitch_corr = pitch_sp * math.cos(math.radians(-angle)) - roll_sp * math.sin(math.radians(-angle))
                    roll_corr = pitch_sp * math.sin(math.radians(-angle)) + roll_sp * math.cos(math.radians(-angle))

                    #print "OUT: roll={:2.2f}, pitch={:2.2f}, thrust={:5.2f}, dt={:0.3f}, fps={:2.1f}".format(roll_corr,
                    #                                                                                         pitch_corr,
                    #                                                                                         thrust_sp, dt,
                    #                                                                                         1 / dt)
                    #print "OUT: alt={:1.4f}, thrust={:5.2f}, dt={:0.3f}, fps={:2.1f}, speed={:+0.4f}".format(z, thrust_sp,
                    #                                                                                         dt, 1 / dt,
                    #                                                                                         curr_velocity)

                    logger.debug("Control Output: roll={:2.2f}, pitch={:2.2f}, yaw={:2.2f}, \
                                 thrust={:5.2f}, speed_z={:5.2f}, dt={:0.3f}, fps={:2.1f}".format(roll_corr,
                                                                                                  pitch_corr,
                                                                                                  yaw_out,
                                                                                                  thrust_sp,
                                                                                                  curr_velocity,
                                                                                                  dt,
                                                                                                  1 / dt))

                    cmd["ctrl"]["roll"] = roll_corr
                    cmd["ctrl"]["pitch"] = pitch_corr
                    cmd["ctrl"]["thrust"] = thrust_sp * 100
                    cmd["ctrl"]["yaw"] = yaw_out
                else:
                    on_detect_counter += 1
                    logger.debug("Incremented 'on_detect_counter to: {}".format(on_detect_counter))
            else:
                # todo: let's make this a function
                cmd["ctrl"]["roll"] = 0
                cmd["ctrl"]["pitch"] = 0
                cmd["ctrl"]["thrust"] = 0
                cmd["ctrl"]["yaw"] = 0
                r_pid.reset_dt()
                p_pid.reset_dt()
                y_pid.reset_dt()
                v_pid.reset_dt()
                #vv_pid.reset_dt()

                #vv_pid.Integrator = 0.0
                r_pid.Integrator = 0.0
                p_pid.Integrator = 0.0
                y_pid.Integrator = 0.0
                on_detect_counter = 0
                logger.debug("Reset 'on_detect_counter' to 0, either lost tracking or fps out of bounds")
            client_conn.send_json(cmd)
            last_ts = time.time()

        except simplejson.scanner.JSONDecodeError as e:
            print e
