__author__ = 'empire'

import numpy as np
import SocketServer, pickle
from threading import Thread, active_count
import sys
import os
import scipy.io
from wildBil import Vicinity

#! /usr/bin/env python

import SocketServer, subprocess, sys
from threading import Thread

my_unix_command = ['bc']
HOST = 'localhost'
PORT = 2002

x = np.array([[55, 1000, 45], [20, 3, 10]])


class Map_Interface(Vicinity):

    def __init__(self, filename):
        Vicinity.__init__(self, filename)
        self.adjacentElevations = np.zeros(3, 3)

    def updatePosition(self):
        '''
        Update Position with the Vicinity class
        Gives new coordinates so that Vacinity has the latest coordinates and elevation matrix

        Should make a call to the Vicinity classes function for retrieving elevation matrix, update the parameter of map_interface
        '''
        pass


class UDP_Interrupt(SocketServer.BaseRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """

    def setup(self):
        pass

    def handle(self):
        data = self.request[0].strip()
        print data
        socket = self.request[1]
        print "{}{} wrote:".format(self.client_address[0], self.client_address)
        print data
        print x
        socket.sendto(x.tostring('C'), self.client_address)
        #scipy.io.savemat('/Users/empire/Documents/MATLAB/hybridQuadSim/quaternionController/models/mapData.mat', mdict={'mapData': x})

    def finish(self):
        pass

class ThreadedUDPServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):

    pass

if __name__ == "__main__":
    map_server = ThreadedUDPServer((HOST, PORT), UDP_Interrupt)

    # terminate with Ctrl-C
    try:
        server_thread = Thread(target=map_server.serve_forever)
        server_thread.daemon = False
        server_thread.start()
        print "Server loop running in thread:", server_thread.name

    except KeyboardInterrupt:
        server_thread.kill()
        map_server.shutdown()
        sys.exit(0)