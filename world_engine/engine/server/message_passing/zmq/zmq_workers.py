import time
import threading
import zmq
import msgpack
import multiprocessing
#from world.mapping.map_interface import MapInterface
from engine.server.server_conf import settings
from itertools import izip, tee, izip_longest

""" @todo: remove this, or inherit from world_engine's pairwise"""
def pairwise(iterable):
    "s -> (s0,s1), (s2,s3), (s4, s5), ..."
    a, b = tee(iterable)
    next(b, None)
    a = iter(iterable)
    return izip(a, b)

def grouper(iterable, n, fillvalue=None):
    """
    Collect data into fixed-length chunks or blocks
    grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    :param iterable:
    :param n:
    :param fillvalue:
    :rtype : object
    """

    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)

"""
def worker_routine(worker_ip='tcp://127.0.0.1:{}', worker_port=5555, context=None):
    # Worker routine
    context = context or zmq.Context.instance()
    # Socket to talk to dispatcher
    socket = context.socket(zmq.REP)
    if worker_ip is None:
        worker_ip = 'tcp://127.0.0.1:{}'
    socket.bind(worker_ip.format(worker_port))
    map = MapInterface(settings['FILE_CONFIG']['filename'])
    while True:
        msg = socket.recv()
        lat_lon_array = msgpack.unpackb(msg)
        #print "Got", lat_lon_array
        #for lat, lon in grouper(lat_lon_array, 2):
        #    print lat, lon
        #coordinate_pairs = [Coordinate(lat=lat, lon=lon) for lon, lat in
        #                           grouper(lat_lon_array, 2)]
        #print coordinate_pairs
        #path_info = map.get_elevation_along_path(coordinate_pairs)

        #print len(x), len(y)


        # do some 'work'
        time.sleep(1)
        #send reply back to client
        socket.send(b"Ack")
"""

class ZMQ_Worker(threading.Thread):

    def __init__(self, q):
        self.q = q
        #self.map = MapInterface(settings['FILE_CONFIG']['filename'])
        threading.Thread.__init__(self)

    def run(self, context=None, worker_ip=None, worker_port=5555):
        context = context or zmq.Context.instance()
        # Socket to talk to dispatcher
        socket = context.socket(zmq.REP)
        if worker_ip is None:
            worker_ip = 'tcp://127.0.0.1:{}'
        socket.bind(worker_ip.format(worker_port))
        #while True:
        msg = socket.recv()
        lat_lon_array = msgpack.unpackb(msg)
        #print "Got", lat_lon_array
        #for lat, lon in grouper(lat_lon_array, 2):
        #    print lat, lon
        #coordinate_pairs = [Coordinate(lat=lat, lon=lon) for lon, lat in
        #                           grouper(lat_lon_array, 2)]
        #print coordinate_pairs
        #path_info = self.map.get_elevation_along_path(coordinate_pairs)
        #print path_info
        #self.q.put(path_info)
        socket.send(b"Ack")


# @todo: this worker class can be used more generally as a subscriber worker. Make it so.
class ZMQ_Worker_Sub(multiprocessing.Process):

    def __init__(self, qin, qout, worker_ip=None, worker_port=5555):
        self.qin = qin
        self.qout = qout
        self.context = zmq.Context()
        self.worker_ip = worker_ip
        self.worker_port = worker_port
        multiprocessing.Process.__init__(self)

    def run(self):
        context = self.context
        # Socket to talk to dispatcher
        socket = context.socket(zmq.SUB)
        socket.setsockopt(zmq.SUBSCRIBE, '')
        if self.worker_ip is None:
            worker_ip = 'tcp://127.0.0.1:{}'
        socket.connect(worker_ip.format(self.worker_port))
        while 1:
            msg = socket.recv()
            lat_lon_array = msgpack.unpackb(msg)
            self.qout.put(lat_lon_array)

class ZMQ_Worker_Pair(threading.Thread):

    def __init__(self, q,  **kwargs):
        self.role = kwargs.get('role', 'client')
        self.worker_port = kwargs.get('worker_port', 5555)
        self.q = q
        threading.Thread.__init__(self)

    def run(self, context=None, worker_ip=None):
        context = context or zmq.Context.instance()

        # Socket to talk to dispatcher
        socket = context.socket(zmq.PAIR)
        if self.role is 'server':
            socket.bind("tcp://127.0.0.1::%s" % self.worker_port)
        elif self.role is 'client':
            socket.connect("tcp://127.0.0.1::%s" % self.worker_port)

        if worker_ip is None:
            worker_ip = 'tcp://127.0.0.1:{}'
        socket.connect(worker_ip.format(self.worker_port))

        #while True:
        msg = socket.recv()
        unpack = msgpack.unpackb(msg)
        #for lat, lon in grouper(lat_lon_array, 2):
        #    print lat, lon
        #coordinate_pairs = [Coordinate(lat=lat, lon=lon) for lon, lat in
        #                           grouper(lat_lon_array, 2)]
        #print coordinate_pairs
        #path_info = self.map.get_elevation_along_path(coordinate_pairs)

        #print path_info
        # @todo:
        self.q.put(unpack)