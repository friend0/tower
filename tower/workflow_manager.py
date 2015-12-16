"""

"""
from __future__ import (absolute_import, division, print_function, unicode_literals)

import time

import msgpack
import zmq
from builtins import input
from builtins import object

from tower.logger import logging_thread

KILL_COMMAND = 'DEATH'

HOST = 'localhost'
PORT = 2002


class WorkflowManager(object):

    def __init__(self, log_directory=None):
        # self.logger = logger.getLogger('py_map_server')
        self.processes = {}
        self.threads = {}
        self.log_dir = log_directory
        self.context = zmq.Context()
        self.zmqLog = None
        self.start_logging(log_directory=log_directory)
        self.start_zmq_processes()

    def end(self):
        for process in self.processes.values():
            process.results_q.put(KILL_COMMAND)
            process.terminate()
        for thread in list(self.threads.values()):
            print(thread)
            # thread.kill()

    def init_model(self):
        pass

    def add_tower(self, tower):
        # todo: disallow adding tower before start of logger
        # todo: pass logger port to Towers? Or have them inherit from config?
        self.processes[tower.name] = tower

    def start_logging(self, log_directory=None):
        """

        Initialize the Logging Thread, and a ZMQ publisher to push to the logger.
        :param log_directory:
        :param test_dir: directory we want to use to store logs. Defaults to logs folder
        :return: None

        """
        logger = logging_thread.LogThread(worker_port=5555 + 128, log_directory=log_directory)
        logger.daemon = True
        self.threads['logging_thread'] = logger
        logger.start()
        self.zmqLog = self.context.socket(zmq.PUSH)
        self.zmqLog.connect("tcp://127.0.0.1:{0}".format(5555 + 128))
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

    def signal_handler(self, signal, frame):
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
    pub.bind("tcp://*:{0}".format(str(5683)))

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


