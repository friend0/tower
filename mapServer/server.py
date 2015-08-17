"""
Threaded Socket Server over UDP for serving up map data
"""
import SocketServer
from threading import Thread
import sys
from re import split
from itertools import izip_longest
from ast import literal_eval
import re
import struct
import logging

import numpy as np

from map_interface import MapInterface


__author__ = "Ryan A. Rodriguez"
__copyright__ = "Copyright 2007"
__credits__ = []
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Ryan A. Rodriguez"
__email__ = "ryarodri@ucsc.edu"
__status__ = "Prototype"


# @todo:Switch all the print statements to logging


HOST = 'localhost'
PORT = 2002

x = np.array([[55, 1000, 45], [20, 3, 10], [1000000, 10, 20]])


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)

#@todo: think about including in a seperate module for exceptions
class CommandNotFound(Exception):
    """ Easy to understand naming conventions work best! """
    pass


class ThreadedUDPServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    """
    Override stock function in order to print client address on connect
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
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """

    def setup(self):
        """
        Instantiate the connection with the worldEngine, the MapInterface.
        @todo: figure out how to make the map interface a singleton class
        :rtype : None
        """
        filename = r'/Users/empire/Academics/UCSC/nasaResearch/californiaNed30m/elevation_NED30M_ca_2925289_01/' \
                   r'virtRasterCalifornia.vrt'
        if not hasattr(self, 'mapInterface'):
            self.mapInterface = MapInterface(filename)

    def handle(self):
        """
        Handles UDP requests to the server.
        The map interface class is responsible for parsing the request, and executing the requested function.
        :return:
        """
        socket = self.request[1]
        data = self.request[0].strip()
        logger.info("Address {} at {} wrote: '{}'".format(self.client_address[1], self.client_address[0], data))
        cmd_strn, ret = self.command_parse(data)
        self.command_response(cmd_strn, ret, self.request[1], self.client_address[0],
                              self.mapInterface.router[cmd_strn])

        # if pack[0] == 'coords':
        #     coords = Coordinate(float(pack[1]), float(pack[2]))
        #     ret = super(MapInterface, self.mapInterface).get_surrounding_elevation(window=3, coordinates=coords)
        #     ret = ret.astype(np.float32)
        # elif pack[0] == 'lonDistance':
        #     ret = super(MapInterface, self.mapInterface).get_elevation_along_path(None)
        #     ret = np.array(ret['lonDistance'])
        #     ret = ret.astype(np.float32)
        #     for idx, distTuple in enumerate(pairwise(ret[:-1])):
        #         #print distTuple[0] + distTuple[1]
        #         ret[idx + 1] = ret[idx + 1] + ret[idx]
        #         #print ret[idx]


    def finish(self):
        pass

    def command_parse(self, rawCommand):
        #find function and args
        """
        Parse raw input and execute specified function with args
        :param coords: coordinates in lat/lon
        :return: the command and arguments as a dictionary
        """
        pack = [x.strip() for x in split('[,()]*', rawCommand.strip())]
        raw_cmd = pack[0]
        argDict = {key: literal_eval(value) for key, value in grouper(pack[1:], 2)}
        cmd = self.mapInterface.commands[raw_cmd]
        ret = cmd(**argDict)
        logger.info("Command '{}' run with args {}".format(raw_cmd, argDict))
        return raw_cmd, ret


    def command_response(self, cmd_name, returned_data, socket, client_ip, client_address):
        #find function and args
        """
        Parse raw input and execute specified function with args
        :param coords: coordinates in lat/lon
        :return: the command and arguments as a dictionary
        """
        returned_data.astype(np.float32)
        response = returned_data.tostring('C')
        response_length = len(response)
        sign = 1
        response_arr = [response]

        if response_length > 256:
            response_arr = list(self.split_by_n(response, 256 * 4))

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


if __name__ == "__main__":

    filename = r'/Users/empire/Academics/UCSC/nasaResearch/californiaNed30m/elevation_NED30M_ca_2925289_01/' \
               r'virtRasterCalifornia.vrt'

    logger = logging.getLogger('py_map_server')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('spam.log')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info('Creating an instance of pyMapServer...')

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