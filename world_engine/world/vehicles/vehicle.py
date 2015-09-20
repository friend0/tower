"""

The quadrotor class can be used to place various vehicles on a map.
The class keeps track of the vehicles starting point, and its current location
"""
from math import cos, sin, acos
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
        self.initialCoordinates = Coordinate(lat=initialLat, lon=initialLon)
        self.coordinates = Coordinate(lat=initialLat, lon=initialLon)
        self.heading = 0
        self.speed = 0
        self.weight = 1
        self.payload = 0
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
        # @todo:implement check on valid range for coords
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
        self.has_landed = False
        self.altitude = 0
        self.state = {'status': 'idle', 'flightId': self.name, 'hasLanded': self.has_landed, 'altitude': self.altitude,
                      'longitude': self.coordinates.lon, 'heading': self.heading, 'dataSource': 'UCSC_HSL',
                      'latitude': self.coordinates.lat, 'speed': 0.0}
        # @todo: interface to a physical model with a well-defined API for calculating state
        self.physical_model = None
        self.max_speed = 10
        self.max_acceleration = 10

    def eqn_of_motion(self, ground_speed, track_angle, rocd, dt):
        """
        Given the vehicles current coordinates, and given a speed and tracking angle, determine the new position of the
        vehicle for a given time step.

        :param ground_speed:
        :param track_angle:
        :return:
        """
        radius_earth = 3444.046647  # Nautical Miles
        knots_to_nmps = 2.777777777777778e-004  # Knots to nautical miles per second.
        fpm_to_fps = 0.01666666666667  # Feet per minute to feet per second.

        lambda_dot = (ground_speed*knots_to_nmps)*cos(track_angle)/radius_earth
        tau_dot = (ground_speed*knots_to_nmps)*sin(track_angle)/(radius_earth*cos(self.coordinates.lat));
        altitude_dot = rocd*fpm_to_fps;

        new_lambda = self.coordinates.lat + lambda_dot*dt
        new_tau = self.coordinates.lon + tau_dot*dt
        new_altitude = self.altitude + altitude_dot*dt

        return new_altitude, new_lambda, new_tau

    @property
    def battery(self):
        return self._battery

    @battery.setter
    def battery(self, val):
        """
        The percent of charge remaining on the battery

        :param val: the percentage of the battery, from zero to one-hundred
        :return:
        """
        if val < 0:
            self._battery = 0
        elif val > 100:
            self._battery = 100
        else:
            self._battery = val

    @property
    def weight(self):
        return self._weight

    @weight.setter
    def weight(self, val):
        """
        Used to limit weights to positive values

        :param val: an integer or float value representing the weight of the vehicle itsel
        """
        if val < 0:
            self._weight = 0
        else:
            self._weight = val

    @property
    def payload(self):
        return self._payload

    @payload.setter
    def payload(self, val):
        """
        Used to limit payloads to positive values
        :param val: an integer or float value representing the weight of the vehicles payload
        """
        if val < 0:
            self._payload = 0
        else:
            self._payload = val

    def vehicle_type(self):
        """"
        Return a string representing the type of vehicle this is.
        """
        return 'Fixed-rotor'

