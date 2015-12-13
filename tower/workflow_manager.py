"""

"""
from __future__ import (absolute_import, division, print_function, unicode_literals)

from multiprocessing import Queue

import zmq
import msgpack
import time
import threading

from builtins import input
from builtins import object

from server.message_passing.zmq_workers import ZmqSubWorker
from utils import logging_thread

KILL_COMMAND = 'DEATH'

HOST = 'localhost'
PORT = 2002


class WorkflowManager(object):

    def __init__(self, test_directory=None):
        # self.logger = logger.getLogger('py_map_server')
        self.processes = {}
        self.threads = {}
        self.test_dir = test_directory
        self.context = zmq.Context()
        self.zmqLog = None

    def start(self):
        self.start_logging(self.test_dir)
        # self.start_server_process()
        self.start_zmq_processes()
        # self.start_web_services()

    def end(self):
        for process in self.processes.values():
            process.results_q.put(KILL_COMMAND)
            print(process)
            process.terminate()
        for thread in list(self.threads.values()):
            print(thread)
            # thread.kill()

    def init_model(self):
        pass

    def add_tower(self, tower):
        # todo: disallow adding tower before start of logging
        # todo: pass logging port to Towers? Or have them inherit from config?
        self.processes[tower.name] = tower

    def start_logging(self, test_dir=None):
        """

        Initialize the Logging Thread, and a ZMQ publisher to push to the logger.
        :param test_dir: directory we want to use to store logs. Defaults to logs folder
        :return: None

        """
        logger = logging_thread.LogThread(worker_port=5555+128, test_dir=test_dir)
        logger.daemon = True
        self.threads['logging_thread'] = logger
        logger.start()
        self.zmqLog = self.context.socket(zmq.PUB)
        self.zmqLog.bind("tcp://*:{}".format(str(5683)))
        time.sleep(.005)
        self.log("Log portal initialized", "info")

    def log(self, msg, level):
        msg = msgpack.packb([level, msg])
        self.zmqLog.send(msg)

    def start_web_services(self):
        # rt = Interrupt(5, web_post, url=None, data=None, headers=None)  # it auto-starts, no need of rt.start()
        pass

    def start_zmq_processes(self):
        """
        Initialize ZMQ communication links in a process, interface to QGIS
        :return:
        """

        # zmq_worker_qgis = ZmqSubWorker(qin=self.commands, qout=self.zmq_result)
        # zmq_worker_qgis.start()

        # self.threads['qgis_worker'] = zmq_worker_qgis
        # self.log("Threaded ZMQ loop running in: {}".format(zmq_worker_qgis.name))
        pass

    # todo: how to implement 'signal handler' kill switch for control processes
    def signal_handler(signal, frame):
        """

        This signal handler function detects a keyboard interrupt and responds by sending kill command to CF via client

        :param signal:
        :param frame:

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
        """
        pass


def publisher():
    # Prepare publisher
    ctx = zmq.Context.instance()
    pub = ctx.socket(zmq.PUB)
    pub.bind("tcp://*:{}".format(str(5683)))

    while True:
        # Send current clock (secs) to subscribers
        pub.send(msgpack.packb(str(time.time())))
        time.sleep(1e-3)            # 1msec wait

if __name__ == "__main__":

    subscriptions = []
    manager = WorkflowManager()
    manager.start()

    try:

        #pub_thread = threading.Thread(target=publisher)
        #pub_thread.start()

        command = input('Server Command:')
        print(command)
    except KeyboardInterrupt:
        pass

    if command == 'shutdown':
        print("Giving the kill command")
        manager.end()


