"""

The server module is responsible for managng the threaded UDP socket server.
This server is used to communicate with Matlab/Simulink simulations. It will be renamed appropriately soon

@todo: rename this module to indicate it's role in any Matlab connections
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import object
import socketserver
import re
import struct
from re import split
from ast import literal_eval
from threading import Timer
from time import strftime

import numpy as np
import requests

from tower import utils
from tower.map.map_interface import MapInterface
from server_conf.config import settings

HOST = 'localhost'
PORT = 2002


# @todo: think about including in a separate module for exceptions
class CommandNotFound(Exception):
    """ Command received does not match one listed in the command dictionary """
    pass


class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
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
        (data, self.socket), client_addr = socketserver.UDPServer.get_request(self)
        logger.info("Server connected to by:{}".format(client_addr))
        return (data, self.socket), client_addr


class UDP_Interrupt(socketserver.BaseRequestHandler):
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
        print(ret)
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

    def command_response(self, returned_data, socket, client_ip, client_address):
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
    data = {'flightId': 0o001, 'time': time_stamp, 'latitude': 36, 'longitude': -120, 'altitude': 50, 'speed': 100,
            'heading': 0, 'hasLanded': False, 'dataSource': "UCSC"}
    r = requests.post(url, json=data, headers=headers)
    print(r.status_code)
