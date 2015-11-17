"""

Region will serve as an abstract base class (ABC) to implement a standard interface amongst both Map and Surface objects

"""


import abc

class Region(metaclass=abc.ABCMeta):

    @abc.abstractproperty
    def origin(self):
        pass

    @abc.abstractmethod
    def get_coordinates_along_path(self):
        pass

    @abc.abstractmethod
    def get_point_elevation(self):
        pass

    @abc.abstractmethod
    def get_surrounding_elevation(self):
        pass

    @abc.abstractmethod
    def get_coordinates_in_segment(self):
        pass

    @abc.abstractmethod
    def get_elevation_along_segment(self):
        pass

    @abc.abstractmethod
    def get_coordinates_along_path(self):
        pass

    @abc.abstractmethod
    def get_elevation_along_path(self):
        pass

    @abc.abstractmethod
    def get_coordinates_in_segment(self):
        pass
