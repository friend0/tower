import threading
import multiprocessing

import zmq
import msgpack

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
        # self.map = MapInterface(settings['FILE_CONFIG']['filename'])
        threading.Thread.__init__(self)

    def run(self, context=None, worker_ip=None, worker_port=5555):
        context = context or zmq.Context.instance()
        # Socket to talk to dispatcher
        socket = context.socket(zmq.REP)
        if worker_ip is None:
            worker_ip = 'tcp://127.0.0.1:{}'
        socket.bind(worker_ip.format(worker_port))
        # while True:
        msg = socket.recv()
        lat_lon_array = msgpack.unpackb(msg)
        # print "Got", lat_lon_array
        # for lat, lon in grouper(lat_lon_array, 2):
        #    print lat, lon
        # coordinate_pairs = [Coordinate(lat=lat, lon=lon) for lon, lat in
        #                           grouper(lat_lon_array, 2)]
        # print coordinate_pairs
        # path_info = self.map.get_elevation_along_path(coordinate_pairs)
        # print path_info
        # self.q.put(path_info)
        socket.send(b"Ack")


# @todo: this worker class can be used more generally as a subscriber worker. Make it so.
class ZmqSubWorker(multiprocessing.Process):
    """

    This class is used to initiate a worker process listening to a ZMQ subscription.
    IP and Port can be specified on initialization, and multiprocessing queues are used to exchange information with
    parent processes.

    """

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


class ZmqPairWorker(threading.Thread):
    """

    This class is used to initiate a worker process implementing one-half of a ZMQ Pair.

    """

    def __init__(self, q, **kwargs):
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

        msg = socket.recv()
        unpack = msgpack.unpackb(msg)
        self.q.put(unpack)
