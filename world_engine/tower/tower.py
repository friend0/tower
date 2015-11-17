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
from tower.mapping import Map
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