__author__ = 'empire'

import numpy as np
import SocketServer
from threading import Thread
import sys
import os
from wildBil import Vicinity
from re import split
from collections import namedtuple

'''
@todo:
Switch all te print statements to logging
'''

import SocketServer, subprocess, sys
from threading import Thread

HOST = 'localhost'
PORT = 2002

x = np.array([[55, 1000, 45], [20, 3, 10], [1000000, 10, 20]])


class Map_Interface(Vicinity):
    def __init__(self, filename, northPixels=None, eastPixels=None):
        super(Map_Interface, self).__init__(filename)
        Coordinate = namedtuple('Coordinate', 'x y')
        self.initialCoordinates = Coordinate(x=None, y=None)
        self.currentCoordinates = Coordinate(x=None, y=None)

        if (northPixels, eastPixels) == (None, None):
            (self.north_pixels, self.east_pixels) = (3, 3)
        else:
            try:
                (self.north_pixels, self.east_pixels) = (northPixels, eastPixels)
            except:
                print "Problem with North/East pixel arguments"

        self.adjacentElevations = np.zeros((northPixels, eastPixels))
        self.commands = {'get_vicinity': self.get_vicinity, 'get_elevation_at_point': self.get_elevation_at_point}

    def init_position(self, xCoords, yCoords):
        '''
        Used to set the initial coordinates of the vehicle on the map. Can only be called once.
        :param xCoords: the x coordinate to be set
        :param yCoords: the y coordinate to be set
        '''
        if not hasattr(self, 'initialCoordinates'):
            try:
                self.initialCoordinates.x = xCoords
                self.initialCoordinates.y = yCoords
                self.adjacentElevations = self.get_vicinity(self.initialCoordinates.x, self.initialCoordinates.y,
                                                            self.north_pixels, self.east_pixels)
            except:
                print "Problem initializing coordinates"
        else:
            print "Currently initial coordinates may only be set once"

    def update_position(self, xCoords, yCoords):
        '''
        Update Position with the Vicinity class
        Gives new coordinates so that Vacinity has the latest coordinates and elevation matrix
        Should make a call to the Vicinity classes function for retrieving elevation matrix, update the elevation
        parameter of map_interface.

        :param xCoords: the x coordinate to be set
        :param yCoords: the y coordinate to be set
        '''
        self.currentCoordinates.x = xCoords
        self.currentCoordinates.y = yCoords
        self.adjacentElevations = self.get_vicinity(self.currentCoordinates.x, self.currentCoordinates.y,
                                                        self.north_pixels, self.east_pixels)

    def get_elevation_at_point(self):
        pass

    def determine_command(self, command):
        #find function and args
        res = split('[,()]*', command.strip())
        command = filter(None, res)
        try:
            self.commands[command[0]]()
        except:
            print "Command Not Found"


class ThreadedUDPServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):

    def get_request(self):
        '''
        Override native get_request function in order to print out who is connecting to the server
        @todo make this Python3 compatible by using superclasses. Will need to update socketServer package
        :return:
        '''
        (data, self.socket), client_addr = SocketServer.UDPServer.get_request(self)
        print "Server connected to by:{}".format(client_addr)
        return (data, self.socket), client_addr


class UDP_Interrupt(SocketServer.BaseRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """


    def setup(self):
        self.mapInterface = Map_Interface(filename)
        pass

    def handle(self):
        data = self.request[0].strip()
        print "Address {} at {} wrote: '{}'".format(self.client_address[1], self.client_address[0], data)
        self.mapInterface.determine_command(data)
        socket = self.request[1]
        print x
        socket.sendto(x.tostring('C'), self.client_address)
        #scipy.io.savemat('/Users/empire/Documents/MATLAB/hybridQuadSim/quaternionController/models/mapData.mat', mdict={'mapData': x})

    def finish(self):
        pass


if __name__ == "__main__":
    filename = r'/Users/empire/Academics/UCSC/nasaResearch/californiaNed30m/elevation_NED30M_ca_2925289_01/bayAreaBIL.bil'

    map_server = ThreadedUDPServer((HOST, PORT), UDP_Interrupt)
    #map_interface = Map_Interface(filename)

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