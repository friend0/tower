from __future__ import (absolute_import, division, print_function, unicode_literals)

from tower.swarm.vehicles.quadrotor import Quadrotor
from uuid import uuid4


class Crazyflie(Quadrotor):
    """

    The Crazyflie class serves as an interface between the Tower and the low-level controller plugin.
    Responsibilities of Crazyflie include:
    - Take position commands from Tower
    - Run controller and determine output commands


    """
    def __init__(self, controller, name=None, dynamics=None,  initial_coords=None, designation='crazyflie', rnge=0):
        self.dynamics = dynamics
        self.controller = controller
        self.designation = designation
        self.initial_coordinates = initial_coords

        # todo: self.coordinates = self.initial_coordinates
        #self.coordinates = self.initial_coordinates

        self.altitude = 0
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
