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


from abc import ABCMeta, abstractmethod, abstractproperty


class Vehicle(object):
    __metaclass__ = ABCMeta

    def __init__(self, initialLat, initialLon):
        self.initialCoordinates = Coordinate(initialLat, initialLon)
        self.coordinates = Coordinate(initialLat, initialLon)
        self.name = uuid4()


    @abstractproperty
    def initialCoordinates(self):
        return self.__initialCoordinates

    @initialCoordinates.setter
    def initialCoordinates(self, val):
        #@todo:implement check on valid range for coords
        pass

    @abstractproperty
    def coordinates(self):
        return self.__coordinates

    @coordinates.setter
    def coordinates(self, val):
        pass

    @abstractmethod
    def vehicle_type(self):
        """"Return a string representing the type of vehicle this is."""
        pass

    @property
    @abstractmethod
    def range(self):
        pass


class Quadrotor(Vehicle):
    def __init__(self, initialLat, initialLon):
        super(Quadrotor, self).__init__(initialLat, initialLon)
        self.battery = 100
        self.weight = 1
        self.payload = 0

    @property
    def battery(self):
        return self.__battery

    @battery.setter
    def battery(self, val):
        if val < 0:
            self.__battery = 0
        elif val > 100:
            self.__battery = 100
        else:
            self.__battery = val

    @property
    def weight(self):
        return self.__weight

    @weight.setter
    def weight(self, val):
        if val < 0:
            self.__weight = 0
        else:
            self.__weight = val

    @property
    def payload(self):
        return self.__payload

    @payload.setter
    def payload(self, val):
        if val < 0:
            self.__payload = 0
        else:
            self.__payload = val

    def vehicle_type(self):
        """"Return a string representing the type of vehicle this is."""
        return 'Fixed-rotor'