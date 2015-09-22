"""
The server module is responsible for managng the threaded UDP socket server.
This server is used to communicate with Matlab/Simulink simulations, but can also be used in the implementation of other
decision making algorithms.
"""

import SocketServer
import numpy as np
import sys
import re
import struct
import logging
import requests
import utils
from threading import Thread
from re import split
from ast import literal_eval
from threading import Timer
from server_conf import settings
from world.mapping.map_interface import MapInterface
from time import strftime
from message_passing.zmq.zmq_workers import ZMQ_Worker, ZMQ_Worker_Sub
import Queue
import matplotlib.pyplot as plt
import zmq
import pymatbridge as pymat
from pymatbridge import Matlab

HOST = 'localhost'
PORT = 2002


# @todo: think about including in a separate module for exceptions
class CommandNotFound(Exception):
    """ Command received does not match one listed in the command dictionary """
    pass


class ThreadedUDPServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    """
    Threaded UDP server for receiving and responding to requests from client applications. We can run the server safely
    by doing:

    Example::

        map_server = ThreadedUDPServer((HOST, PORT), UDP_Interrupt)
        server_thread = None
        logger.info('Instantiation succesful')
        # terminate with Ctrl-C
        try:
            server_thread = Thread(target=map_server.serve_forever)
            server_thread.daemon = False
            logger.info("Threaded server loop running in: {}".format(server_thread.name))
            print("Threaded server loop running in: {}".format(server_thread.name))
            server_thread.start()

        except KeyboardInterrupt:
            server_thread.kill()
            map_server.shutdown()
            sys.exit(0)

    """

    def get_request(self):
        """
        Override native get_request function in order to print out who is connecting to the server
        @todo make this Python3 compatible by using superclasses. Will need to update socketServer package
        :return:
        """
        (data, self.socket), client_addr = SocketServer.UDPServer.get_request(self)
        logger.info("Server connected to by:{}".format(client_addr))
        return (data, self.socket), client_addr


class UDP_Interrupt(SocketServer.BaseRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client sockets, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """

    def setup(self):
        """
        Instantiate the connection with the worldEngine, the MapInterface.
        :rtype : None
        """
        # TODO : figure out how to make the map interface a singleton class

        if not hasattr(self, 'mapInterface'):
            self.mapInterface = MapInterface(settings['FILE_CONFIG']['filename'])

    def handle(self):
        """
        Handles UDP requests to the server.
        The map interface class is responsible for parsing the request, and executing the requested function.

        :return:
        """
        socket = self.request[1]
        data = self.request[0].strip()
        logger.info("Address {} at {} wrote: '{}'".format(self.client_address[1], self.client_address[0], data))
        cmd_strn, ret = self.command_service(data)
        print ret
        self.command_response(cmd_strn, ret, self.request[1], self.client_address[0],
                              self.mapInterface.router[cmd_strn])


    def command_service(self, rawCommand):
        """
        Parse raw input and execute specified function with args

        :param rawCommand: csv string from Matlab/Simulink of the form:
                'command, namedArg1, arg1, namedArg2, arg2, ..., namedArgN, argN'
        :return: the command and arguments as a dictionary
        """
        pack = [x.strip() for x in split('[,()]*', rawCommand.strip())]
        raw_cmd = pack[0]
        argDict = {key: literal_eval(value) for key, value in utils.grouper(pack[1:], 2)}
        cmd = self.mapInterface.commands[raw_cmd]
        ret = cmd(**argDict)
        logger.info("Command '{}' run with args {}".format(raw_cmd, argDict))
        return raw_cmd, ret

    def command_response(self, cmd_name, returned_data, socket, client_ip, client_address):
        """
        Parse raw input and execute specified function with args

        :param coords: coordinates in lat/lon
        :return: the command and arguments as a dictionary
        """
        returned_data.astype(np.float32)
        response = returned_data.tostring('C')
        response_length = len(response)
        response_arr = [response]

        if response_length > 256:
            response_arr = list(self.split_by_n(response_arr[0], 256 * 4))

        data = [response_length]
        s = struct.pack('f' * len(data), *data)
        socket.sendto(s, (client_ip, client_address))
        for response_packet in response_arr:
            socket.sendto(response_packet, (client_ip, client_address))

    @staticmethod
    def split_by_n(seq, n):
        """A generator to divide a sequence into chunks of n units."""
        while seq:
            yield seq[:n]
            seq = seq[n:]

    @staticmethod
    def func_explode(s):
        pattern = r'(\w[\w\d_]*)\((.*)\)$'
        match = re.match(pattern, s)
        if match:
            return list(match.groups())
        else:
            return []

    def finish(self):
        pass


class Interrupt(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.daemon = True
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


def call_request(url=None, data=None, headers=None):
    url = 'http://httpbin.org/post'
    headers = {'content-type': 'application/json'}
    time_stamp = strftime("%Y-%m-%d %H:%M:%S")
    data = {'flightId': 0001, 'time': time_stamp, 'latitude': 36, 'longitude': -120, 'altitude': 50, 'speed': 100,
            'heading': 0, 'hasLanded': False, 'dataSource': "UCSC"}
    r = requests.post(url, json=data, headers=headers)
    print r.status_code

#  @todo: remove executable from server file into a workflow_manager.py file
if __name__ == "__main__":

    logger = logging.getLogger('py_map_server')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('../../logs/spam.log')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info('Creating an instance of pyMapServer...')
    map_server = ThreadedUDPServer((HOST, PORT), UDP_Interrupt)
    server_thread = None
    logger.info('Instantiation succesful')

    zmq_result = Queue.Queue()

    # terminate with Ctrl-C
    try:
        """ Threaded UDP server ought to be a process"""
        server_thread = Thread(target=map_server.serve_forever)
        server_thread.daemon = False
        logger.info("Threaded server loop running in: {}".format(server_thread.name))
        print("Threaded server loop running in: {}".format(server_thread.name))
        server_thread.start()

        """ Interrupt used to update AMES every ~5s """
        #rt = Interrupt(5, call_request, url=None, data=None, headers=None)  # it auto-starts, no need of rt.start()


        # @todo: need to think about how to get ZMQ tasks up and running
        context = zmq.Context()
        zmq_worker_qgis = ZMQ_Worker_Sub(zmq_result)
        zmq_worker_qgis.start()

        logger.info("Threaded ZMQ loop running in: {}".format(zmq_worker_qgis.name))
        print("Threaded ZMQ loop running in: {}".format(zmq_worker_qgis.name))

        """ Instance of Matlab Engine should be  process"""
        mlab = Matlab()          # Matlab Bridge
        try:
            pass
            # mlab.start()
        except:
            pass

        """ remove wihle loops, processes remain persistent in their own threads"""
        while(1):
            if not zmq_result.empty():
                val = zmq_result.get()
                path_info = val
                elevations = path_info['elevation']
                distances = path_info['distance']
                lat_distance = path_info['latDistance']
                lon_distance = path_info['lonDistance']

                elevations = elevations[:-1]
                distances = [elem*1000 for elem in distances]
                lat_distance = [elem*1000 for elem in lat_distance]
                lon_distance = [elem*1000 for elem in lon_distance]

                distances = [sum(distances[:idx]) for idx, elem in enumerate(distances)]
                lat_distance = [sum(lat_distance[:idx]) for idx, elem in enumerate(lat_distance)]
                lon_distance = [sum(lon_distance[:idx]) for idx, elem in enumerate(lon_distance)]

                print len(distances), len(elevations), len(lat_distance), len(lon_distance)
                print distances
                print elevations
                print lat_distance
                print lon_distance

                """ Send to Matlab/trigger simulink """

                """ Get variables into workspace"""
                np.asarray(distances, dtype=np.float32)
                np.asarray(elevations, dtype=np.float32)
                np.asarray(lat_distance, dtype=np.float32)
                np.asarray(lon_distance, dtype=np.float32)

                print("Putting Control Variables Into Workspace..")
                #mlab.set_variable('elevations', elevations)
                #mlab.set_variable('distances', distances)
                #mlab.set_variable('lat_distances', lat_distance)
                #mlab.set_variable('lon_distances', lon_distance)
                print "Done\n"
                """ Run the simulink model, which takes the new workspace variables as inputs"""

                print("Getting Variables Back From Workspace:")
                #print 'elevations', mlab.get_variable('elevations')
                #print 'distances', mlab.get_variable('distances')
                #print 'lat_distances', mlab.get_variable('lat_distances')
                #print 'lon_distances', mlab.get_variable('lon_distances')
                # calculate polynomial
                z = np.polyfit(distances, elevations, 3)
                f = np.poly1d(z)

                # calculate new x's and y's
                x_new = np.linspace(distances[0], distances[-1], len(distances))
                y_new = f(x_new)

                plt.plot(distances, elevations, 'o', x_new, y_new)
                plt.xlim([distances[0]-1, distances[-1] + 1 ])
                plt.show()

    except KeyboardInterrupt:
        server_thread.kill()
        map_server.shutdown()
        sys.exit(0)
