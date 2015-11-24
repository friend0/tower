"""

Tower Class

Manages vehicles in a region (Raster Terrain, Surface Function + Shape and Vector Files) using the specified control
laws. Control laws are specified in the provided framework.

"""

import multiprocessing
import inspect

import zmq

from mock import Mock

from utils.utils import grouper
from tower.map import Map
from tower.server import ZmqSubWorker



# create the mock object
mockRegion = Mock(name="Region")
# prepare the spec list
fooSpec = ["_fooValue", "source", "doFoo"]

# create the mock object
mockFoo = Mock(spec=fooSpec)

# create the mock object
mockControlLaw = Mock(name="Control")
# prepare the spec list
fooSpec = ["_fooValue", "source", "doFoo"]

# create the mock object
mockFoo = Mock(spec=fooSpec)

class Tower(multiprocessing.Process):

    def __init__(self, local_region, control_laws, worker_ip=None, worker_port=5555):
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
        self.region = local_region
        self.controller = control_laws

        if worker_ip is None:
            self.worker_ip = 'tcp://127.0.0.1:{}'
        else:
            self.worker_ip = worker_ip
        self.context = zmq.Context()

        self.results_q = multiprocessing.Queue()
        self.zmq_worker_qgis = ZmqSubWorker(qin=None, qout=self.results_q)
        self.zmq_worker_qgis.start()

        """ Configure API """
        # will not include statically defined methods
        self.map_api = dict((x, y) for x, y in inspect.getmembers(Map, predicate=inspect.ismethod))
        self.process_api = dict((x, y) for x, y in inspect.getmembers(self, predicate=inspect.ismethod))
        self.api = self.map_api.copy()
        self.api.update(self.process_api)

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

if __name__ == '__main__':
    tower = Tower(mockRegion, mockControlLaw)
    tower.run()


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