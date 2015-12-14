"""

Tower Class

Manages vehicles in a region (Raster Terrain, Surface Function + Shape and Vector Files) using the specified control
laws. Control laws are specified in the provided framework.

"""
from __future__ import (absolute_import, division, print_function, unicode_literals)

import multiprocessing
import time

import msgpack
import zmq

from tower.controllers.feedback.frames import FrameHistory
from tower.utils.utils import grouper


class Tower(multiprocessing.Process):
    KILL_COMMAND = 'DEATH'

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

    client_conn = None
    pid_viz_conn = None
    ctrl_conn = None

    def __init__(self, local_region, control_laws, worker_ip=None, worker_port=5555, **optitrack_args):
        """

        :param local_region: a space inheriting from ABC region; most commonly, a map or a surface object
        :param control_laws: a tower plugin that specifies safety, stabilization, and management control laws.
                Safety control laws are responsible for ensuring safe behavior of vehicle in volume, i.e. kill commands
                capability. Stabilization control laws specify how a vehicle will be stabilized and commanded to
                trajectory. Management control laws generate reference trajectories for the stabilization controllers to
                follow.
        :param worker_ip: ZMQ IP address
        :param worker_port: ZMQ port

        """
        multiprocessing.Process.__init__(self)
        self.client_conn, self.ctrl_conn, self.pid_viz_conn = None, None, None
        self.optitrack_args = optitrack_args
        self.frame_history, self.optitrack_conn = None, None

        self.region = local_region
        self.controller = control_laws
        self.vehicles = {}

        self.results_q = multiprocessing.Queue()
        self.zmqLog = None

    def start_logging(self):
        """

        Initialize the ZMQ publisher channel to begin logger
        :return: None

        """
        self.zmqLog = self.context.socket(zmq.PUSH)
        self.zmqLog.connect("tcp://127.0.0.1:{}".format(str(5683)))
        time.sleep(.005)
        self.log("Log portal initialized in {}".format(self.name), "info")

    def log(self, msg, level):
        """

        Write to log through a ZMQ PUSH
        :param msg: the message to be logged
        :param level: the level of logger
        :return: None

        """
        if self.zmqLog is not None:
            msg = msgpack.packb([level, msg])
            self.zmqLog.send(msg)

    def initialize_optitrack(self, **kwargs):
        try:
            optitrack_conn = self.context.socket(zmq.REP)
            optitrack_conn.bind("tcp://204.102.224.3:5000")
            self.log('Initialize Optitrack REP socket', 'info')
        except Exception as err:
            self.log('Failed to initialize Optitrack REP socket, error: {}'.format(err), 'info')
            optitrack_conn = None
        return FrameHistory(**kwargs), optitrack_conn

    def zmq_setup(self):
        """

        Initialize relevant ZMQ connections
        Returns: tuple of ZMQ connections initialized

        """
        pass

    def add_vehicles(self, vehicles):
        for vehicle in vehicles:
            self.vehicles[vehicle.name] = vehicle

    def run(self, context=None, worker_ip=None):
        """

        Now that the ZMQ processes are up and running, check to see if they put any api calls on the results queue
        :param context:
        :param worker_ip:
        :return:

        """

        # rt = Interrupt(5, post_vehicle, data=self.update_data())  # it auto-starts, no need of rt.start()
        # todo: re-evaluate this, see what NEEDS to run for now.
        #  Need to run:
        #       - Controller Update
        #       - Optitrack Update (Frame History)
        #       - Zmq?

        self.context = zmq.Context()  # do this first, subzequent inits require a ZMQ context
        self.start_logging()    # do this next, start logger
        self.zmq_setup()
        self.frame_history, self.optitrack_conn = self.initialize_optitrack(**self.optitrack_args)

        # todo: verify these all work if we have multiple instances of Tower
        self.client_conn = self.context.socket(zmq.PUSH)
        self.client_conn.connect("tcp://127.0.0.1:1212")

        self.pid_viz_conn = self.context.socket(zmq.PUSH)
        self.pid_viz_conn.connect("tcp://127.0.0.1:5123")

        self.ctrl_conn = self.context.socket(zmq.PULL)
        self.ctrl_conn.connect("tcp://127.0.0.1:5124")

        #ctrl_conn = self.context.socket(zmq.PULL)
        #ctrl_conn.connect("tcp://127.0.0.1:5124")

        self.log('Running Tower', 'info')
        while 1:

            # todo: think about a nicer way to do this, potentially with ZMQ
            if not self.results_q.empty():
                msg = self.results_q.get()
                if msg == self.KILL_COMMAND:
                    self._kill()
                    return

            # Receive Packet over ZMQ, unpack it
            if self.optitrack_conn:
                frame_data = msgpack.unpackb(packet)
                self.optitrack_conn.send(b'Ack')
                detected = bool(frame_data[-1])
                if self.frame_history.update(frame_data) is None:
                    continue
            else:
                packet = None
                frame_data = None
                detected = False



            # Get the set-points (if there are any)
            # todo: this will probably only work out nicely for one vehicle
            # todo: need to gather individual set points and 'send' them to vehicle
                            #while True:



            #print("Not Here")
            try:
                while True:
                    ctrl_sp = self.ctrl_conn.recv_json(flags=zmq.NOBLOCK)
                    yaw_sp = ctrl_sp["set-points"]["yaw"]
                    # r_pid.set_point = ctrl_sp["set-points"]["roll"]
                    # p_pid.set_point = ctrl_sp["set-points"]["pitch"]
                    midi_acc = ctrl_sp["set-points"]["velocity"]

                    #logger.debug('set_points', yaw_sp=yaw_sp, roll_sp=r_pid.set_point, pitch_sp=p_pid.set_point,
                    #             midi_acc=midi_acc)
            except zmq.error.Again:
                pass

            if detected:
                for vehicle in self.vehicles:
                    """
                    todo: for operation with many vehicles, frame_data with all information will get passed to each
                    vehicle. Is there a simple way to just get info on relevant rigid body?
                    - How will we associate a rigid body iod with a vehicle/vehicle name/ vehicle ID?
                    """
                    vehicle.update(frame_data)

    def _kill(self):
        """

        Kill the currently running Tower instance safely, i.e. handle all vehicle threads safely first
        Returns:

        """
        # todo: handle vehicle threads here, misc cleanup here...
        self.cmd["ctrl"]["roll"] = 0
        self.cmd["ctrl"]["pitch"] = 0
        self.cmd["ctrl"]["thrust"] = 0
        self.cmd["ctrl"]["yaw"] = 0

        #r_pid.reset_dt()
        #p_pid.reset_dt()
        #y_pid.reset_dt()
        #v_pid.reset_dt()
        # vv_pid.reset_dt()

        # vv_pid.Integrator = 0.0
        #r_pid.Integrator = 0.0
        #p_pid.Integrator = 0.0
        #y_pid.Integrator = 0.0
        on_detect_counter = 0
        self.client_conn.send_json(self.cmd, zmq.NOBLOCK)
        self.log('Vehicle Killed', 'info')
        pass

    def decode_api_call(self, raw_cmd):
        """

        Tries to decode packets received by ZMQ by comparing against known function, or API calls

        :param raw_cmd: ZMQ packet to be processed as an API call

        """
        cmd = raw_cmd[0]
        cmd = self.api[cmd]
        argDict = dict((key, value) for key, value in grouper(raw_cmd[1:], 2))  # for python < 2.7 compatibility
        # argDict = {key: value for key, value in grouper(raw_cmd[1:], 2)}  # Only works for Python >= 2.7
        cmd(**argDict)  # callable functions in map must take kwargs in order to be called..


'''
class Tower(Map, multiprocessing.Process):
    """

    Map Process
    Defines ZMQ connection protocol and implements the thin API layer to the analytical map functions of the 'Map'
    module
    Can be used to implement high level logic relating to API calls

    """

    def __init__(self, file_name, worker_ip=None, worker_port=5555):
        super(Tower, self).__init__(file_name)
        multiprocessing.Process.__init__(self)
        if worker_ip is None:
            self.worker_ip = 'tcp://127.0.0.1:{}'
        else:
            self.worker_ip = worker_ip
        self.context = zmq.Context()

        """ Start ZMQ processes here"""
        """
         @todo: eventually, we want to find a way where we can have n zmq_messaging processes and k map processes and
         each map
         process listens for API calls with coordinates
        """

        self.results_q = multiprocessing.Queue()
        self.zmq_worker_qgis = ZmqSubWorker(qin=None, qout=self.results_q)
        self.zmq_worker_qgis.start()

        """ Configure API """
        # will not include statically defined methods
        self.map_api = dict((x, y) for x, y in inspect.getmembers(Map, predicate=inspect.ismethod))
        self.process_api = dict((x, y) for x, y in inspect.getmembers(self, predicate=inspect.ismethod))
        self.api = self.map_api.copy()
        self.api.update(self.process_api)

    # @todo: will need to manage the update of all swarm managed by the map - threads?
    def run(self, context=None, worker_ip=None):
        """
        Now that the ZMQ processes are up and running, check to see if they put any api calls on the results queue
        :param context:
        :param worker_ip:
        :return:

        """

        # rt = Interrupt(5, post_vehicle, data=self.update_data())  # it auto-starts, no need of rt.start()

        while 1:
            if not self.results_q.empty():
                msg = self.results_q.get()
                self.decode_api_call(msg)
                """ TODO: this is a really gross workaround for a weird problem. Seem like the message from QGIS is
                getting put onto the queue more than once """
                while not self.results_q.empty():
                    self.results_q.get()

    def decode_api_call(self, raw_cmd):
        """

        Tries to decode packets received by ZMQ by comparing against known function, or API calls

        :param raw_cmd: ZMQ packet to be processed as an API call

        """
        cmd = raw_cmd[0]

        # cmd = self.map_api[cmd]
        cmd = self.api[cmd]
        # for key, value in utils.grouper(raw_cmd[1:], 2):
        #    print key, value
        argDict = {key: value for key, value in grouper(raw_cmd[1:], 2)}
        cmd(**argDict)  # callable functions in map must take kwargs in order to be called..

    def qgis(self, *args, **kwargs):
        """

        Define the sequence of events that should happen when we've received a message from qgis
        :param args:
        :param kwargs:
        :return:

        """
        msg = kwargs.get('coordinate_pairs', None)
        coordinate_pairs = [Coordinate(lat=lat, lon=lon) for lon, lat in grouper(msg, 2)]
        path_info = self.get_elevation_along_path(**{'coordinate_pairs': coordinate_pairs})
        path = Path(path_info, mode='one-shot')

        print("QGIS Called")
        print(path_info)
        """
        @todo: now path class needs to be assigned to a vehicle, and we need to call equations of motion for that
        vehicle processing will consist of:
          - calling vinc_dist between adjacent points on a circular path
          - once we have tracking angle and distance between points, call vinc_pt with information on the swarm speed
          every five seconds.

        """

        ground_speed = 48.27  # km/h
        dt = .01  # 1 mS
        rocd = 0  # constant altitude
        # @todo: think about adding this to the creation of the path object
        count = 0
        tol = .1
        results = []
        while path.has_next():
            try:
                current_coord = next(path)  # get the current node, a Coord object
                next_coord = current_coord.__next__
                current_coord = current_coord.data
                # print current_coord, type(current_coord), next_coord, type(next_coord)
                if next_coord is not None:
                    inverse = self.vinc_inv(current_coord, next_coord)
                    distance = inverse['distance']
                    fwd_azimuth = inverse['forward_azimuth']
                    rev_azimuth = inverse['reverse_azimuth']
                    err = distance
                    remaining_distance = distance
                    count = 0
                    while remaining_distance > 1:
                        count += 1
                        # @todo will need to call physical model to get current velocity based on past state and
                        # acceleration
                        fpm_to_fps = 0.01666666666667  # Feet per minute to feet per second.
                        ellipsoidal_velocity = ground_speed  # is this correct?
                        ellipsoidal_distance = ellipsoidal_velocity * dt
                        remaining_distance -= ellipsoidal_distance
                        temp_coord, temp = self.vinc_dir(current_coord, fwd_azimuth, ellipsoidal_distance)
                        altitude = rocd * fpm_to_fps * dt
                        current_coord = temp_coord
                        err = distance - remaining_distance
                        if count >= 500:
                            results.append(current_coord)
                            count = 0

            except StopIteration:
                break
        f = open('recon.csv', 'wt')
        try:
            writer = csv.writer(f)
            writer.writerow(['Lat', 'Lon'])
            for elem in results:
                writer.writerow([elem.lat, elem.lon])
        finally:
            f.close()

        print("Results", results)

    def update_data(self):
        """

        :return:

        """
        for vehicle in self.swarm:
            # if type(vehicle) is Quadrotor:
            pass

'''
