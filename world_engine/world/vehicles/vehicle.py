"""

The quadrotor class can be used to place various vehicles on a map.
The class keeps track of the vehicles starting point, and its current location
"""
from math import cos, sin, acos
from uuid import uuid4
from abc import ABCMeta, abstractmethod, abstractproperty
from world.mapping.map import Map
from engine.server.server_conf import settings


"""
The vehicle, above all else, is our physical implement. It must understand its surroundings, and also how it's dynamics
inform the way that it can interact with the world.

To this end, the vehicle must inherit from a physical model. Fine or course, this model must - at minimum - describe how
a vehicle's point mass translates, and how the possible paths it may take are limited by the reality of under-actuation.
"""


class Vehicle(object):
    """

    Vehicle provides the abstract base for both flying and ground vehicles

    """
    __metaclass__ = ABCMeta

    def __init__(self, initial_coords):
        self.initial_coordinates = initial_coords
        self.coordinates = self.initial_coordinates
        self.heading = 0
        self.speed = 0
        self.weight = 1
        self.payload = 0
        self.name = uuid4()
        self.conversion_table = \
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

    This class is used as the base class for implementing particular quadrotor vehicles with
    specific weights, payloads, battery and thrust capacities.

    """

    def __init__(self, initial_coords, designation='crazyflie', rnge=0):
        super(Quadrotor, self).__init__(initial_coords)
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
        self.designation = designation
        self.range = rnge

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

    def eqn_of_motion(self, ground_speed, track_angle, rocd, dt=5):
        """

        Given the vehicles current coordinates, and given a speed and tracking angle, determine the new position of the
        vehicle for a given time step.

        :param rocd: rate of climb or decent
        :param dt: time step for integration
        :param ground_speed: speed in knots?
        :param track_angle:
        :return:

        """

        fpm_to_fps = 0.01666666666667  # Feet per minute to feet per second.


        # @todo will need to call physical model to get current velocity based on past state and acceleration

        ellipsoidal_velocity = ground_speed  # is this correct?
        ellipsoidal_distance = ellipsoidal_velocity * dt

        """
        Ok, what should actually be happening is that the Map will, for each vehicle that it is managing,
        run equations of motion. The equations of motion will indicate the ground distance ellipsoidal distance that the
        vehicle has traveled - this will be used by the map to update positions with the vincenty direct equation.
        Note that it may be necessary to get datum info from the map to calculate this with precision.

        Equations of motion will serve as an update for the state of the vehicle. In the future, vehicles will inherit a
        physical model which will provide this routine with a method for determining acceleration and
         """
        self.coordinates, temp = Map.vinc_dir(0.00335281068118, 6378137.0, self.coordinates, track_angle,
                                             ellipsoidal_distance)
        self.altitude = rocd * fpm_to_fps * dt

    def vehicle_type(self):
        return self.designation

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

    def range(self):
        return self._range
