from __future__ import (absolute_import, division, print_function, unicode_literals)
import threading
import logging

import zmq
import msgpack
import sys

import structlog
from logging import handlers


class LoggingConfig(object):
    def __init__(self):
        pass


class LogThread(threading.Thread):

    def __init__(self, worker_port=None, log_directory=None):
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

        # create file handler which logs messages down to the debug level to a file for postprocessing
        if log_directory is None:
            latest_experiment = logging.FileHandler('../logs/octrl.log', mode='w')
        else:
            latest_experiment = logging.FileHandler(log_directory+'/octrl.log', mode='w')

        latest_experiment.setLevel(logging.DEBUG)
        # create console handler with a higher log level
        console = logging.StreamHandler(sys.stderr)
        console.setLevel(logging.WARNING)

        if log_directory is None:
            rotating = handlers.RotatingFileHandler('../logs/experiment_history.log', mode='w', maxBytes=128e+6,
                                                    backupCount=5, delay=True)
        else:
            rotating = handlers.RotatingFileHandler(log_directory+'/experiment_history.log', mode='w', maxBytes=128e+6,
                                                    backupCount=5, delay=True)

        self.logger = structlog.getLogger()
        self.logger.setLevel(logging.DEBUG)

        try:
            rotating.doRollover()
        except AttributeError:
            # python2.6 quirk
            pass
        rotating.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console.setFormatter(formatter)
        self.logger.addHandler(latest_experiment)
        self.logger.addHandler(console)
        self.logger.addHandler(rotating)
        if worker_port is None:
            self.worker_port = 5555 + 128
        else:
            self.worker_port = worker_port
        self.logger.info('Logging thread started...')
        self.logger.info('Logging initialized in {} on port {}'.format(threading.current_thread(), worker_port))
        self.context = None
        self.socket = None

    def run(self):
        levels = {'info': self.logger.info, 'debug': self.logger.debug, 'warning': self.logger.warning,
                  'error': self.logger.error}
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PULL)
        self.socket.bind("tcp://127.0.0.1:{}".format(self.worker_port))
        self.logger.info('ZMQ subscriber socket initialized: ready to receive external log messages...')

        while 1:
            # todo: see if we can make this log to different levels
            msg = self.socket.recv()
            msg = msgpack.unpackb(msg)
            levels[msg[0]](msg[1])

