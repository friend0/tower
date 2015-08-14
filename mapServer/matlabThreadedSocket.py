"""
Threaded Socket Server over UDP for serving up map data
"""
import numpy as np
import SocketServer
from threading import Thread
import sys
from worldEngine import Map, pairwise
from re import split
from collections import namedtuple
from vehicle import Coordinate
import re

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


class CommandNotFound(Exception):
    """ Easy to understand naming conventions work best! """
    pass


class AddVehicleException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class MapInterface(Map):
    """
    Interface between Matlab and the MapData retrieval methods provided by 'WorldEngine'
    Used to interpret commands from UDP packets,
    """

    def __init__(self, filename, northPixels=10, eastPixels=10):
        super(MapInterface, self).__init__(filename)
        Coordinate = namedtuple('Coordinate', 'x y')
        self.initialCoordinates = Coordinate(x=None, y=None)
        self.currentCoordinates = Coordinate(x=None, y=None)

        if (northPixels, eastPixels) == (None, None):
            (self.north_pixels, self.east_pixels) = (3, 3)
        else:
            try:
                (self.north_pixels, self.east_pixels) = (northPixels, eastPixels)
            except:
                raise CommandNotFound("Command not found. Check your syntax")

        self.adjacentElevations = np.zeros((self.north_pixels, self.east_pixels))
        self.commands = {'get_point_elevation': self.get_point_elevation,
                         'get_surrounding_elevation': self.get_surrounding_elevation,
                         'get_elevation_along_path': self.get_coordinates_in_segment,
                         'hello': self.hello}

    def hello(self):
        print("GoodbyeWorld")

    def add_vehicle(self, xCoords, yCoords, vehicle):
        """
        Add vehicle to the dictionary representing vehicles present on the map
        :param vehicle:
        """
        try:
            self.vehicles[vehicle.name] = vehicle
        except:
            raise AddVehicleException("Vehicle does not have a name, or does not exist")

    def init_position(self, xCoords, yCoords, vehicleName=None):
        """
        Used to set the initial coordinates of the vehicle on the map. Can only be called once.
        :param xCoords: the x coordinate to be set
        :param yCoords: the y coordinate to be set
        :param vehicleName: Name of the vehicle to be updated; if vehicle is not present, adds it with init_position.
                Of type UUID
        """
        if not hasattr(self, 'initialCoordinates'):
            try:
                self.initialCoordinates.x = xCoords
                self.initialCoordinates.y = yCoords
                self.adjacentElevations = self.get_surrounding_elevation(self.initialCoordinates.x,
                                                                         self.initialCoordinates.y, self.north_pixels,
                                                                         self.east_pixels)
            except:
                print "Problem initializing coordinates"
        else:
            print "Currently initial coordinates may only be set once"

    def update_position(self, xCoords, yCoords, vehicleName=None):
        """
        Update Position with the Map class
        Gives new coordinates so that Map has the latest coordinates and elevation matrix
        Should make a call to the Vicinity classes function for retrieving elevation matrix, update the elevation
        parameter of map_interface.

        :param xCoords: the x coordinate to be set
        :param yCoords: the y coordinate to be set
        :param vehicleName: Name of the vehicle to be updated; if vehicle is not present, adds it with init_position.
                Of type UUID
        """

        self.currentCoordinates.x = xCoords
        self.currentCoordinates.y = yCoords
        self.adjacentElevations = self.get_vicinity(self.currentCoordinates.x, self.currentCoordinates.y,
                                                    self.north_pixels, self.east_pixels)

    def determine_command(self, coords):
        #find function and args
        """
        Parse raw input and execute specified function with args
        :param coords: coordinates in lat/lon
        :return: the command that was executed
        """
        #print command
        ret = None
        coords = split('[,()]*', coords.strip())
        print coords
        coords = Coordinate(float(coords[0]), float(coords[1]))

        #print cmd(mode='coords', window=3, coordinates=Coordinate(36.974117, -122.030796))
        #try:
        ret = self.get_surrounding_elevation(window=3, coordinates=coords)
        #except:
        #    print "Command Not Found"
        return ret

    def get_surrounding_elevation(self, mode='coords', window=10, coordinates=None, vehicleName=None):
        pass

    def func_explode(self, s):
        pattern = r'(\w[\w\d_]*)\((.*)\)$'
        match = re.match(pattern, s)
        if match:
            return list(match.groups())
        else:
            return []


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
        """
        Instantiate the connection with the worldEngine, the MapInterface.
        @todo: figure out how to make the map interface a singleton class
        :rtype : None
        """
        if not hasattr(self, 'mapInterface'):
            self.mapInterface = MapInterface(filename)

    def handle(self):
        """
        Handles UDP requests to the server.
        The map interface class is responsible for parsing the request, and executing the requested function.
        :return:
        """
        data = self.request[0].strip()
        if data == '\n':
            print data
            print "Breaking"

        #print type(dat), struct.unpack(dat)
        print "Address {} at {} wrote: '{}'".format(self.client_address[1], self.client_address[0], data)
        #ret = np.array(1)
        #print ret, type(ret)

        """@todo:change function name, implement new function for json development"""

        pack = split('[,()]*', data.strip())
        coords = None
        ret = np.array(0)
        latDist = np.array(0)
        lonDist = np.array(0)
        linearDistance = np.array(0)

        if pack[0] == 'coords':
            coords = Coordinate(float(pack[1]), float(pack[2]))
            ret = super(MapInterface, self.mapInterface).get_surrounding_elevation(window=3, coordinates=coords)
            ret = ret.astype(np.float32)
        elif pack[0] == 'elevation':
            ret = super(MapInterface, self.mapInterface).get_elevation_along_path(None)
            ret = np.array(ret['elevation'])
            ret = ret.astype(np.float32)
        elif pack[0] == 'distance':
            ret = super(MapInterface, self.mapInterface).get_elevation_along_path(None)
            ret = np.array(ret['distance'])
            ret = ret.astype(np.float32)
            for idx, distTuple in enumerate(pairwise(ret[:-1])):
                #print distTuple[0] + distTuple[1]
                ret[idx + 1] = ret[idx + 1] + ret[idx]
                #print ret[idx]
        elif pack[0] == 'latDistance':
            ret = super(MapInterface, self.mapInterface).get_elevation_along_path(None)
            ret = np.array(ret['latDistance'])
            ret = ret.astype(np.float32)
            for idx, distTuple in enumerate(pairwise(ret[:-1])):
                #print distTuple[0] + distTuple[1]
                ret[idx + 1] = ret[idx + 1] + ret[idx]
                #print ret[idx]
        elif pack[0] == 'lonDistance':
            ret = super(MapInterface, self.mapInterface).get_elevation_along_path(None)
            ret = np.array(ret['lonDistance'])
            ret = ret.astype(np.float32)
            for idx, distTuple in enumerate(pairwise(ret[:-1])):
                #print distTuple[0] + distTuple[1]
                ret[idx + 1] = ret[idx + 1] + ret[idx]
                #print ret[idx]





                #prnt = [ elem1+elem2 for idx, distTuple in enumerate(pairwise(ret))]
                #print prnt
        print "lin", linearDistance
        print "lat", latDist
        print "lon", lonDist

        #print res, type(res)

        #ret = self.mapInterface.determine_command(data)
        print ret, type(ret)
        socket = self.request[1]

        if pack[0] == 'coords':
            socket.sendto(ret.tostring('C'), ('127.0.0.1', self.client_address[1]))  #for surrounding elvations
        elif pack[0] == 'elevation':
            socket.sendto(ret[:len(ret) / 2].tostring('C'),
                          ('127.0.0.1', self.client_address[1]))  #for elevatinos along path
            socket.sendto(ret[len(ret) / 2 + 1:].tostring('C'),
                          ('127.0.0.1', self.client_address[1]))  #for elevatinos along path
        elif pack[0] == 'distance':
            socket.sendto(ret[:len(ret) / 2].tostring('C'),
                          ('127.0.0.1', self.client_address[1]))  #for elevatinos along path
            socket.sendto(ret[len(ret) / 2 + 1:].tostring('C'),
                          ('127.0.0.1', self.client_address[1]))  #for elevatinos along path
        elif pack[0] == 'latDistance':
            socket.sendto(ret[:len(ret) / 2].tostring('C'),
                          ('127.0.0.1', self.client_address[1]))  #for elevatinos along path
            socket.sendto(ret[len(ret) / 2 + 1:].tostring('C'),
                          ('127.0.0.1', self.client_address[1]))  #for elevatinos along path
        elif pack[0] == 'lonDistance':
            socket.sendto(ret[:len(ret) / 2].tostring('C'),
                          ('127.0.0.1', self.client_address[1]))  #for elevatinos along path
            socket.sendto(ret[len(ret) / 2 + 1:].tostring('C'),
                          ('127.0.0.1', self.client_address[1]))  #for elevatinos along path

    def finish(self):
        pass


if __name__ == "__main__":

    filename = r'/Users/empire/Academics/UCSC/nasaResearch/californiaNed30m/elevation_NED30M_ca_2925289_01/' \
               r'virtRasterCalifornia.vrt'

    map_server = ThreadedUDPServer((HOST, PORT), UDP_Interrupt)
    server_thread = None
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