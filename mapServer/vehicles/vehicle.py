"""

The quadrotor class can be used to place various vehicles on a map.
The class keeps track of the vehicles starting point, and its current location
"""

from collections import namedtuple
from uuid import uuid4
from abc import ABCMeta, abstractmethod, abstractproperty


Coordinate = namedtuple("Coordinate", ['lat', 'lon'], verbose=False)
PixelPair = namedtuple("PixelPair", ['x', 'y'], verbose=False)


class Path(object):

    pass


class Vehicle(object):
    __metaclass__ = ABCMeta

    def __init__(self, initialLat, initialLon):
        self.initialCoordinates = Coordinate(initialLat, initialLon)
        self.coordinates = Coordinate(initialLat, initialLon)
        self.name = uuid4()

    @abstractproperty
    def initialCoordinates(self):
        """
        Set the initial coordiantes of the vehicle
        :return: the initial coords
        """
        return self.__initialCoordinates

    @initialCoordinates.setter
    def initialCoordinates(self, val):
        #@todo:implement check on valid range for coords
        """
        Sets the initial coordinates, but checks if the coordinates are valid first
        :param val: A Coordinate of type named-tuple
        """
        pass

    @abstractproperty
    def coordinates(self):
        return self.__coordinates

    @coordinates.setter
    def coordinates(self, val):
        # todo: need to check that coords are valid params
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
    """ The Quadrotor Vehicle Class

    This class is used as the base class for implementing particular quadrotor vehicles with
    specific weights, payloads, battery and thrust capacities.
    """

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
        """
        The percent of charge remaining on the battery

        :param val: the percentage of the battery, from zero to one-hundred
        :return:
        """
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
        """
        Used to limit weights to positive values

        :param val: an integer or float value representing the weight of the vehicle itsel
        """
        if val < 0:
            self.__weight = 0
        else:
            self.__weight = val

    @property
    def payload(self):
        return self.__payload

    @payload.setter
    def payload(self, val):
        """
        Used to limit payloads to positive values
        :param val: an integer or float value representing the weight of the vehicles payload
        """
        if val < 0:
            self.__payload = 0
        else:
            self.__payload = val

    def vehicle_type(self):
        """"Return a string representing the type of vehicle this is."""
        return 'Fixed-rotor'