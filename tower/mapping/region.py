# coding=utf-8
"""

Region will serve as an abstract base class (ABC) to implement a standard interface amongst both Map and Surface objects

"""
import abc


class Point(metaclass=abc.ABCMeta):
    """

    A Region must define it's atomic unit for representing a point in space. I.e. a map could potentially declare a
    tuple of the form (lat, lon), while a surface plot from a function or heightfield might declare (x, y).

    For the purpose of implementing autonomous navigation algorithms on top of simulated environments rgives us good
    reason to implement a universal API for accessing points on regions regardless of implementation specifics.

    """

    @abc.abstractproperty
    def lat(self):
        pass

    @abc.abstractproperty
    def lon(self):
        pass

    @abc.abstractproperty
    def x(self):
        pass

    @abc.abstractproperty
    def y(self):
        pass

    @abc.abstractproperty
    def units(self):
        pass


class Region(metaclass=abc.ABCMeta):
    """

    Region represents a three dimensional space in a general sense. It is used as the abstract base class supporting
    traditional mapping implementations with geographic coordinates in addition to surface or heightfields
    implemented as a function or a file.

    For our purposes, we'd like to align Optitrack's origin with that of the Surface defined by height-field
    or function. For Maps, we'd like to align the origin to some coordinate representing the center of the
    geographic region covered by the Tower.

    We take standard world coordinates as our convention. This means delta(y) is proportional to delta(lat)
    and that delta(x) corresponds to delta(lon). The relations between these quantities is abstracted

    """


    @abc.abstractproperty
    def origin(self):
        """
        
        ¯\_(ツ)_/¯
        :return:
        
        """
        pass
    
    @abc.abstractproperty
    def z_axis(self):
        """        
        
        Define how elevation will be measured?
                
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
    def get_edge(self, *args, **kwargs):
        """

        Sample data between two points

        :return: An array of points
        """
        pass

    @abc.abstractmethod
    def get_elevation_along_edge(self, edge):
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

