#!/usr/bin/env python
"""

A simple PID control loop for crazyflie using a set of Optitrack Flex13's

"""

import sys
import signal
import math
import time
import datetime
import logging
from logging import handlers

import msgpack
import simplejson
import zmq
import structlog

from engine.controllers import feedback
import tower.controllers.pid.pid as pid


def add_timestamp(_, __, event_dict):
    event_dict['timestamp'] = datetime.datetime.utcnow()
    return event_dict


# todo: will need to make sure a zmq context is created already? Will getcontext handle this?
def zmq_processor(_, __, event_dict):
    return event_dict


structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
        zmq_processor
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
logger = structlog.getLogger()
logger.setLevel(logging.DEBUG)
# create file handler which logs messages down to the debug level to a file for postprocessing
latest_experiment = logging.FileHandler('../../../../logs/octrl.log', mode='w')
latest_experiment.setLevel(logging.DEBUG)
# create console handler with a higher log level
console = logging.StreamHandler(stream=sys.stderr)
console.setLevel(logging.WARNING)

rotating = handlers.RotatingFileHandler('../../../../logs/experiment_history.log', mode='w', maxBytes=128e+6,
                                        backupCount=5, delay=True)
rotating.doRollover()
rotating.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
# add the handlers to logger
logger.addHandler(latest_experiment)
logger.addHandler(console)
logger.addHandler(rotating)
logger.info('Logging Initialized')

YAW_CAP = 200
yaw_sp = 0

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

logger.info('Setting up ZMQ context, sockets, connections...')

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
r_pid = pid.PID_RP(name="roll", P=35, I=0.3, D=8, Integrator_max=5, Integrator_min=-5, set_point=0,
                   zmq_connection=pid_viz_conn)
p_pid = pid.PID_RP(name="pitch", P=35, I=0.3, D=8, Integrator_max=5, Integrator_min=-5, set_point=0,
                   zmq_connection=pid_viz_conn)
y_pid = pid.PID_RP(name="yaw", P=5, I=0, D=0.35, Integrator_max=5, Integrator_min=-5, set_point=0,
                   zmq_connection=pid_viz_conn)

# Vertical position and velocity PID loops
v_pid = pid.PID_RP(name="position", P=0.6, D=0.0075, I=0.25, Integrator_max=100 / 0.035, Integrator_min=-100 / 0.035,
                   set_point=.5,
                   zmq_connection=pid_viz_conn)


# todo: Testing Velocity Control on Velocity """
vv_pid = pid.PID_V(name="velocity", p=0.25, i=1e-10, d=1e-10, set_point=0)

logger.info('PIDs Initialized')

prev_z, prev_vz, dt, prev_t, last_ts = 0, 0, 0, time.time(), time.time()
midi_acc = 0
on_detect_counter = 0
max_step = 11  # ms
min_step = 5  # ms
ctrl_time = 0
ts = 0


def wind_up_motors(step_time=1e-2):
    """

    Ramp up CF Motors to avoid current surge
    :param step_time: The amount ot time between acceleration steps

    """
    try:
        logger.info("Spinning up motors...")
        for i in range(2500, 4500, 1):
            cmd["ctrl"]["roll"] = 0
            cmd["ctrl"]["pitch"] = 0
            cmd["ctrl"]["yaw"] = 0
            cmd["ctrl"]["thrust"] = i / 100.0
            client_conn.send_json(cmd)
            time.sleep(step_time)
    except:
        logger.info("Motor wind-up failed")

    logger.info("Motor spin-up complete")
    client_conn.send_json(cmd)


def signal_handler(signal, frame):
    """

    This signal handler function detects a keyboard interrupt and responds by sending kill command to CF via client

    :param signal:
    :param frame:

    """
    logger.info('Kill Sequence Initiated')
    logger.info('Kill Command Detected...')
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
    logger.info('Vehicle Killed')
    sys.exit(0)


class Optitrack(object):
    pass


class swarm(object):

    def __init__(self):
        pass

class PidQuadControl(object):

    def __init__(self, configs=None, *args, **kwargs):
        """

        @todo: accept dictionary of gains to initialize all the controllers' gain terms

        :param ref:
        :param gains:
        :return:
        """
        self.feedback = None
        if configs is None:
            self.configs = \
                {'roll': {'gains': {'p': 0, 'i': 0, 'd': 0, 'set_point': 0}, 'pid_type': pid.PID_RP},
                 'pitch': {'gains': {'p': 0, 'i': 0, 'd': 0, 'set_point': 0}, 'pid_type': pid.PID_RP},
                 'yaw': {'gains': {'p': 0, 'i': 0, 'd': 0, 'set_point': 0}, 'pid_type': pid.PID_RP},
                 'position': {'gains': {'p': 0, 'i': 0, 'd': 0, 'set_point': 0}, 'pid_type': pid.PID_RP},
                 'velocity': {'gains': {'p': 0, 'i': 0, 'd': 0, 'set_point': 0}, 'pid_type': pid.PID_V}
                 }
        else:
            self.configs = configs

        self.controllers = {'roll': None, 'pitch': None, 'yaw': None, 'position': None, 'velocity': None}
        self.controllers = {controller: self.configs[controller]['pid_type'](**self.configs[controller]['gains']) for
                            controller in self.controllers}

    def update_controllers(self, state):
        """

        Update all the PID controllers with new state feedback

        :param state: A dict of states, specified by controller, i.e. {'roll': roll_state (x), ...}
        :return: A dict of output values, i.e {'roll': roll_ctrl_output, ...}

        """
        results = {PID: self.controllers[PID].update(state) for PID in self.controllers}
        return results


if __name__ == "__main__":

    signal.signal(signal.SIGINT, signal_handler)
    frame_history = feedback.FrameHistory(filtering=False)
    x, y, z, yaw, roll, pitch = 0, 0, 0, 0, 0, 0
    ts, dt, prev_z, prev_vz, midi_acc, on_detect_counter, ctrl_time = 0, 0, 0, 0, 0, 0, 0
    prev_t, last_ts = time.time(), time.time()
    min_step, max_step = 7e-3, 9e-3  # s
    motors_not_wound = True
    logger.info('FrameHistory Initialized')

    configs = \
            {'roll': {'gains': {'p': 0, 'i': 0, 'd': 0, 'set_point': 0}, 'pid_type': pid.PID_RP},
             'pitch': {'gains': {'p': 0, 'i': 0, 'd': 0, 'set_point': 0}, 'pid_type': pid.PID_RP},
             'yaw': {'gains': {'p': 0, 'i': 0, 'd': 0, 'set_point': 0}, 'pid_type': pid.PID_RP},
             'position': {'gains': {'p': 0, 'i': 0, 'd': 0, 'set_point': 0}, 'pid_type': pid.PID_RP},
             'velocity': {'gains': {'p': 0, 'i': 0, 'd': 0, 'set_point': 0}, 'pid_type': pid.PID_V}
             }
    controller = PidQuadControl(**configs)
    while True:

        try:
            # Receive Packet over ZMQ, unpack it
            packet = optitrack_conn.recv()
            frame_data = msgpack.unpackb(packet)
            optitrack_conn.send(b'Ack')

            if frame_history.update(frame_data) is None:
                logger.info("Cont")
                continue
            detected = bool(frame_data[-1])
            logger.debug('Received: {}'.format(frame_data))

            if motors_not_wound:
                logger.info('Motors winding up...')
                motors_not_wound = False
                wind_up_motors(.001)  # Prime Motors with a ramp up period
                logger.info('Motors wound.')

            state = frame_history.filtered_frame.state
            logger.debug('state', x=state[0], y=state[1], z=state[2], yaw=state[3], roll=state[4], pitch=state[5])
            x, y, z, angle, roll, pitch = state[0], state[1], state[2], state[3], state[4], state[5]

            # Get the set-points (if there are any)
            try:
                while True:
                    ctrl_sp = ctrl_conn.recv_json(zmq.NOBLOCK)
                    yaw_sp = ctrl_sp["set-points"]["yaw"]
                    r_pid.set_point = ctrl_sp["set-points"]["roll"]
                    p_pid.set_point = ctrl_sp["set-points"]["pitch"]
                    midi_acc = ctrl_sp["set-points"]["velocity"]
                    logger.debug('set_points', yaw_sp=yaw_sp, roll_sp=r_pid.set_point, pitch_sp=p_pid.set_point,
                                 midi_acc=midi_acc)
            except zmq.error.Again:
                pass

            step = time.time() - last_ts
            logger.debug('time_step', dt=step)

            if (max_step >= step >= min_step) and detected:

                """
                check to see if we have been tracking the vehicle for more than 5 frames, e.g. if we are just
                starting or
                if we've lost tracking and are regaining it.
                """
                if on_detect_counter >= 0:
                    ctrl_time = int(round(time.time() * 1000))
                    # print "IN  : x={:4.2f}, y={:4.2f}, z={:4.2f}, yaw={:4.2f}".format(x, y, z, angle)

                    # Roll, Pitch, Yaw
                    roll_sp = roll = r_pid.update(x)
                    pitch_sp = pitch = p_pid.update(y)
                    yaw_out = yaw = y_pid.update(((angle - yaw_sp + 360 + 180) % 360) - 180)

                    velocity = v_pid.update(z)
                    logger.debug('pid', name='v_pid', output=velocity)
                    velocity = max(min(velocity, 10), -10)  # Limit vertical velocity between -1 and 1 m/sec
                    vv_pid.set_point = velocity
                    dt = (time.time() - prev_t)
                    curr_velocity = (z - prev_z) / dt
                    curr_acc = (curr_velocity - prev_vz) / dt
                    thrust_sp = vv_pid.update(curr_velocity) + 0.50
                    logger.debug('pid', name='vv_pid', output=velocity)


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

                    logger.debug('output', roll=roll_corr, pitch=pitch_corr, yaw=yaw_out, \
                                 thrust=thrust_sp, velocity=curr_velocity, dt=dt, fps=1 / dt)

                    cmd["ctrl"]["roll"] = roll_corr
                    cmd["ctrl"]["pitch"] = pitch_corr
                    cmd["ctrl"]["thrust"] = thrust_sp * 100
                    cmd["ctrl"]["yaw"] = yaw_out
                else:
                    on_detect_counter += 1
                    logger.debug('Increment on_detect_counter', value=on_detect_counter)
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
                # vv_pid.reset_dt()

                # vv_pid.Integrator = 0.0
                r_pid.Integrator = 0.0
                p_pid.Integrator = 0.0
                y_pid.Integrator = 0.0
                on_detect_counter = 0
                logger.debug('Reset on_detect_counter', value=0)
            client_conn.send_json(cmd)
            last_ts = time.time()

        except simplejson.scanner.JSONDecodeError as e:
            print e
