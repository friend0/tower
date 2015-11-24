# coding=utf-8
"""

Region will serve as an abstract base class (ABC) to implement a standard interface amongst both Map and Surface objects

"""

from __future__ import (absolute_import, division, print_function, unicode_literals)
import abc
import collections

from future.utils import with_metaclass
from builtins import *


class Space(with_metaclass(abc.ABCMeta, object)):
    """

    `Space` represents a base class for flat, three-dimensional space. Concrete implementations of Space, will
    implement abstractions like curved space (geodetic map) while exposing only fundamental abstractions of flat space
    to planning algorithms.

    Space defines as  attribute the notion of a Point. Concrete implementations of Space may extend this idea to
    geographic coordinates, and etc., for example by making `lat` a property of the class `Map,` implementing Space.
    Eg.


    Space has a class attribute `Point`, which provides the Cartesian idea of a point in a plane


    For our purposes, we'd like to align Optitrack's origin with that of the Surface defined by height-field
    or function. For Maps, we'd like to align the origin to some coordinate representing the center of the
    geographic region covered by the Tower.

    We take standard world coordinates as our convention. This means delta(y) is proportional to delta(lat)
    and that delta(x) corresponds to delta(lon). The relations between these quantities is abstracted

    """

    # todo: include auto conversion dictionary, i.e. enable user to request target unit conversion from base unit

    @abc.abstractproperty
    def units(self):
        """

        A point should travel with its units, in case it needs to be converted
        :return:

        """
        pass

    @abc.abstractproperty
    def x(self):
        """

        Define how we refer to the x axis in concrete implementation

        :return: A string corresponding to x axis in concrete implementation. For example, a map
        implementation could expose a point's longitude through the x variable by returning 'lon'

        """
        pass

    @abc.abstractproperty
    def y(self):
        """

        Define how we refer to the x axis in concrete implementation

        :return: A string corresponding to y axis in concrete implementation. For example, a map
        implementation could expose a point's longitude through the y variable by returning 'lat'

        """
        pass

    @abc.abstractproperty
    def name(self):
        """


        """
        pass

    @abc.abstractmethod
    def point(self):
        """

        The point function is a named-tuple factory that wraps the underlying `point` abstraction of a space into
        a universal container with x first, followed by y, and then the units. This gives users of the Space ABC
        a way to define x and y once, then retrive a custom named-tuple object that is universally indexed by
        [x, y, units], allowing them to be passed around with well-defined compatibility criteria.

        A Map implementation of a space might do:
        Coord = Map.point('Coordinate')
        With `x` and `y` defined appropriately as 'lon' and 'lat' respectively, we could do:
        point_a = Coord('lon'=-122.0264, 'lat=36.9741')

        :param name: Provide a custom name for `point`, default is `Point`
        :return: A named tuple with fields corresponding to x, y, and units for concrete implementation of Space

        """
        return collections.namedtuple(self.name, [self.x, self.y, self.units])

    @abc.abstractproperty
    def origin(self):
        """

        ¯\_(ツ)_/¯
        :return:

        """
        pass

    @abc.abstractmethod
    def get_point_elevation(self):
        pass

    @abc.abstractmethod
    def get_distance_between(self, point_a, point_b, *args, **kwargs):
        """

        :return: the distance between two
        """
        pass

    @abc.abstractmethod
    def get_edge(self, from_, to):
        """

        Sample data between two points

        :return: An array of points
        """
        pass

    @abc.abstractmethod
    def get_elevation_along_edge(self, from_, to):
        """

        Take as input a edge, which is an iterable of points, and get a set of elevations corresponding to
        the elevations at those points.

        :return: An iterable of the same length as input, where each output corresponds to the input coordinate given
        in the se

        """
        pass

    @abc.abstractmethod
    def get_surrounding_elevation(self):
        pass
