from __future__ import print_function
import threading
import logging

import zmq
import msgpack
import sys

import structlog
from logging import handlers


class LogThread(threading.Thread):

    def __init__(self, worker_port=None, test_dir=None):
        threading.Thread.__init__(self)

        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt='iso'),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer()  # ,
                # zmq_processor
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        self.logger = structlog.getLogger()
        self.logger.setLevel(logging.DEBUG)
        # create file handler which logs messages down to the debug level to a file for postprocessing
        if test_dir is None:
            latest_experiment = logging.FileHandler('../logs/octrl.log', mode='w')
        else:
            print(test_dir)
            latest_experiment = logging.FileHandler(test_dir+'/octrl.log', mode='w')

        latest_experiment.setLevel(logging.DEBUG)
        # create console handler with a higher log level
        console = logging.StreamHandler(stream=sys.stderr)
        console.setLevel(logging.WARNING)
        if test_dir is None:
            rotating = handlers.RotatingFileHandler('../logs/experiment_history.log', mode='w', maxBytes=128e+6, backupCount=5, delay=True)
        else:
            rotating = handlers.RotatingFileHandler(test_dir+'/experiment_history.log', mode='w', maxBytes=128e+6, backupCount=5, delay=True)

        rotating.doRollover()
        rotating.setLevel(logging.DEBUG)

        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console.setFormatter(formatter)
        # add the handlers to logger
        self.logger.addHandler(latest_experiment)
        self.logger.addHandler(console)
        self.logger.addHandler(rotating)

        if worker_port is None:
            worker_port = 5555 + 128
        self.logger.info('Logging initialized in {} on port {}'.format(self.name, worker_port))

        context = zmq.Context.instance()
        self.socket = context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.SUBSCRIBE, "")

        worker_ip = 'tcp://localhost:{}'
        self.socket.connect(worker_ip.format(worker_port))

    def run(self):
        levels = {'info': self.logger.info, 'debug': self.logger.debug, 'warning': self.logger.warning,
                  'error': self.logger.error}
        while 1:
            # todo: see if we can make this log to different levels
            msg = self.socket.recv()
            msg = msgpack.unpackb(msg)
            levels[msg[0]](msg[1])

