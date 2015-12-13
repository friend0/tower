"""

The quadrotor class can be used to place various vehicles on a map.
The class keeps track of the vehicles starting point, and its current location
"""
from __future__ import (absolute_import, division, print_function, unicode_literals)
from uuid import uuid4
from abc import ABCMeta, abstractproperty

from future.utils import with_metaclass

"""
The vehicle, above all else, is our physical implement. It must understand its surroundings, and also how it's dynamics
inform the way that it can interact with the world.

To this end, the vehicle must inherit from a physical model. Fine or course, this model must - at minimum - describe how
a vehicle's point mass translates, and how the possible paths it may take are limited by the reality of under-actuation.
"""


class Quadrotor(with_metaclass(ABCMeta, object)):
    """

    Vehicle provides the abstract base for both flying and ground vehicles

    """
    conversion_table = \
        {'m/s': {'m/s': 1, 'km/h': 3.6, 'mph': 2.236936, 'kn': 1.943844, 'ft/s': 3.280840},
         'km/h': {'m/s': 0.277778, 'km/h': 1, 'mph': 0.621371, 'kn': 0.539957, 'ft/s': 0.911344},
         'mph': {'m/s': 0.44704, 'km/h': 1.609344, 'mph': 1, 'kn': 0.868976, 'ft/s': 1.466667},
         'kn': {'m/s': 0.514444, 'km/h': 1.852, 'mph': 1.150779, 'kn': 1, 'ft/s': 1.687810},
         'ft/s': {'m/s': 0.3048, 'km/h': 1.09728, 'mph': 0.681818, 'kn': 0.592484, 'ft/s': 1}
         }

    # todo: really, the vehicle ought to compose with coordinate systems.
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
