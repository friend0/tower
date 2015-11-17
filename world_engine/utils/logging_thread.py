from __future__ import print_function
import threading
import logging

import zmq


class LogThread(threading.Thread):
    def __init__(self, q, worker_port=None):
        threading.Thread.__init__(self)
        self.q = q
        self.logger = logging.getLogger('py_map_server')
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler('../logs/spam.log')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        self.logger.info('Creating an instance of pyMapServer...')
        self.logger.info('Instantiation succesful')

        if worker_port is None:
            worker_port = 5555 + 128
        context = zmq.Context.instance()
        self.socket = context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.SUBSCRIBE, '')

        worker_ip = 'tcp://localhost:{}'
        self.socket.connect(worker_ip.format(worker_port))

    def run(self):
        while 1:
            msg = self.socket.recv_string()
            print("Message received")
            # log_msg = msgpack.unpackb(msg)
            self.logger.info(msg)

            while not self.q.empty():
                self.logger.info(self.q.get())
