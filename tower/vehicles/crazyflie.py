from __future__ import (absolute_import, division, print_function, unicode_literals)

from uuid import uuid4

import msgpack
import zmq

from tower.units.units import Speed, Weight
from tower.vehicles import Quadrotor


class Crazyflie(Quadrotor):
    """

    The Crazyflie class serves as an interface between the Tower and the low-level controller plugin.
    Responsibilities of Crazyflie include:
    - Take position commands from Tower
    - Run controller and determine output commands

    """
    index = 0

    def __init__(self, controller_plugin, name=None, dynamics=None, initial_coords=None, designation='crazyflie'):
        Crazyflie.index += 1
        self.id = uuid4()
        if name is None:
            self.name = 'Crazyflie_{}'.format(Crazyflie.index)
        else:
            self.name = name
        self.dynamics = dynamics
        self.controller = controller_plugin
        self.designation = designation
        self.initial_coordinates = initial_coords

        self.coordinates = self.initial_coordinates

        # todo: make tuples for these too
        self.altitude = 0
        self.heading = 0
        # todo: extend the speed, weight namedtuples to check for valid inputs
        self.speed = Speed(rate=0, unitsPerTime='km/h')
        self.weight = Weight(weight=30, units='g')
        self.payload = 0
        self.context = zmq.Context()
        self.zmqLog = None
        self.start_logging()

        if self.coordinates:
            longitude = self.coordinates.lon
            latitutde = self.coordinates.lat
        else:
            longitude = None
            latitutde = None

        current_state = {'status': 'idle', 'flightId': None, 'hasLanded': False, 'altitude': self.altitude,
                      'longitude': longitude, 'heading': self.heading, 'dataSource': 'UCSC_HSL',
                      'latitude': latitutde, 'speed': self.speed.rate, 'units': self.speed.unitsPerTime}

    def start_logging(self, port=5683):
        """

        :param port: the port to PUSH on
        :return: None

        """
        self.zmqLog = self.context.socket(zmq.PUSH)
        self.zmqLog.connect("tcp://127.0.0.1:{}".format(str(port)))
        self.log("Log portal initialized in {}, id:{}".format(self.name, self.id), "info")

    def log(self, msg,level):
        """

        Write to log through a ZMQ PUSH
        :param msg: the message to be logged
        :param level: the level of logging
        :return: None

        """
        if self.zmqLog is not None:
            msg = msgpack.packb([level, msg])
            self.zmqLog.send(msg)

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
