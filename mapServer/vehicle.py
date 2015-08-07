"""

The quadrotor class can be used to place various vehicles on a map.
The class keeps track of the vehicles starting point, and its current location
"""
__author__ = 'Ryan Rodriguez'

from collections import namedtuple
from uuid import uuid4

Coordinate = namedtuple("Coordinate", ['lat', 'lon'], verbose=False)
PixelPair = namedtuple("PixelPair", ['x', 'y'], verbose=False)


class Path(object):
    pass


class Vehicle(object):
    def __init__(self, initialLat, initialLon):
        self.initialCoordinates = Coordinate(initialLat, initialLon)
        self.currentCoordinates = Coordinate(initialLat, initialLon)
        self.name = uuid4()

    def update_coordinates(self, lat, lon):
        self.currentCoordinates = Coordinate(lat, lon)

    def get_coordinates(self):
        coords = Coordinate(self.currentCoordinates.lat, self.currentCoordinates.lon)
        return coords


class Quadrotor(Vehicle):
    def __init__(self, initialLat, initialLon):
        super(Quadrotor, self).__init__(initialLat, initialLon)

