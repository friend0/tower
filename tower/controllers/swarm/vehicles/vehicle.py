"""

The quadrotor class can be used to place various vehicles on a map.
The class keeps track of the vehicles starting point, and its current location
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from uuid import uuid4
from abc import ABCMeta, abstractproperty

from future.utils import with_metaclass

"""
The vehicle, above all else, is our physical implement. It must understand its surroundings, and also how it's dynamics
inform the way that it can interact with the world.

To this end, the vehicle must inherit from a physical model. Fine or course, this model must - at minimum - describe how
a vehicle's point mass translates, and how the possible paths it may take are limited by the reality of under-actuation.
"""


class Vehicle(with_metaclass(ABCMeta, object)):
    """

    Vehicle provides the abstract base for both flying and ground swarm

    """
    conversion_table = \
        {'m/s': {'m/s': 1, 'km/h': 3.6, 'mph': 2.236936, 'kn': 1.943844, 'ft/s': 3.280840},
         'km/h': {'m/s': 0.277778, 'km/h': 1, 'mph': 0.621371, 'kn': 0.539957, 'ft/s': 0.911344},
         'mph': {'m/s': 0.44704, 'km/h': 1.609344, 'mph': 1, 'kn': 0.868976, 'ft/s': 1.466667},
         'kn': {'m/s': 0.514444, 'km/h': 1.852, 'mph': 1.150779, 'kn': 1, 'ft/s': 1.687810},
         'ft/s': {'m/s': 0.3048, 'km/h': 1.09728, 'mph': 0.681818, 'kn': 0.592484, 'ft/s': 1}
         }

    @property
    def coordinates(self):
        return self._coordinates

    @coordinates.setter
    def coordinates(self, coordinate):
        if abs(coordinate.lat) > 90:
            raise ValueError("Invalid latitude")
        if abs(coordinate.lon) > 180:
            raise ValueError("Invalid longitude")
        self._coordinates = coordinate

    @abstractproperty
    def vehicle_type(self):
        """"

        Return a string representing the type of vehicle this is.

        """
        pass

    @abstractproperty
    def range(self):
        pass

    def speed_conversion(self, rate, units1, units2):

        try:
            conversion = self.conversion_table[units1][units2]
            return rate * conversion
        except KeyError:
            raise Exception("Not a valid conversion")


class Quadrotor(Vehicle):
    """

    The Quadrotor Vehicle Class

    This class is used as the base class for implementing particular quadrotor swarm with
    specific weights, payloads, battery and thrust capacities.

    """

    def __init__(self, controller=None, dynamics=None, name=None, initial_coords=None, designation='crazyflie', rnge=0):
        self.dynamics = dynamics
        self.controller = controller

        self.designation = designation
        self.initial_coordinates = initial_coords
        self.coordinates = self.initial_coordinates
        self.heading = 0
        self.speed = 0
        self.weight = 1
        self.payload = 0
        self.id = uuid4()
        if name is None:
            self.name = {self.designation + str(self.id): self.id}
        else:
            self.name = {name: self.id}

        self.state = {'status': 'idle', 'flightId': None, 'hasLanded': False, 'altitude': self.altitude,
                      'longitude': self.coordinates.lon, 'heading': self.heading, 'dataSource': 'UCSC_HSL',
                      'latitude': self.coordinates.lat, 'speed': self.speed}

    def update(self, state):
        return self.controller.update(state)

    def vehicle_type(self):
        """

        Return a string representing the type of vehicle this is.

        """
        return self.designation

    @property
    def range(self):
        return self.__range

    @range.setter
    def range(self, val):
        if range < 0:
            self.__range = 0
        # if range > power_density_of_battery:
        #    self._range = power_density_of_battery
        else:
            self.range = val

    @property
    def battery(self):
        return self._battery

    @battery.setter
    def battery(self, val):
        """

        The percent of charge remaining on the battery

        :param val: the percentage of the battery, from zero to one-hundred

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
        :param val: an integer or float value representing the weight of the swarm payload

        """
        if val < 0:
            self._payload = 0
        else:
            self._payload = val


if __name__ == '__main__':
    quad = Quadrotor()