"""Map Interface module
Used as a thin layer between the server and map classes
"""
from world_engine import Map


class AddVehicleException(Exception):
    """If vehicle has invlaid UUID (name) or does not exist
    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class MapInterface(Map):
    """
    Interface between Matlab and the MapData retrieval methods provided by 'WorldEngine'
    Used to interpret commands from UDP packets.
    """

    def __init__(self, filename):
        super(MapInterface, self).__init__(filename)

        self.commands = {'get_point_elevation': super(MapInterface, self).get_point_elevation,
                         'get_surrounding_elevation': super(MapInterface, self).get_surrounding_elevation,
                         'get_elevation_along_path': super(MapInterface, self).get_elevation_along_path
        }

        self.router = {'get_point_elevation': 24995,
                       'get_surrounding_elevation': 25000,
                       'get_elevation_along_path': 25005
        }

    def add_vehicle(self, vehicle):
        """
        Add vehicle to the dictionary representing vehicles present on the map

        :param vehicle:
        """
        try:
            self.vehicles[vehicle.name] = vehicle
        except:
            raise AddVehicleException("Vehicle does not have a name, or does not exist")

    def init_position(self, xCoords, yCoords, vehicleName=None):
        """
        Used to set the initial coordinates of the vehicle on the map. Can only be called once.

        :param xCoords: the x coordinate to be set
        :param yCoords: the y coordinate to be set
        :param vehicleName: Name of the vehicle to be updated; if vehicle is not present, adds it with init_position.
                Of type UUID
        """
        if not hasattr(self, 'initialCoordinates'):
            try:
                self.initialCoordinates.x = xCoords
                self.initialCoordinates.y = yCoords
                self.adjacentElevations = self.get_surrounding_elevation(self.initialCoordinates.x,
                                                                         self.initialCoordinates.y, self.north_pixels,
                                                                         self.east_pixels)
            except:
                print "Problem initializing coordinates"
        else:
            print "Currently initial coordinates may only be set once"

    def update_position(self, xCoords, yCoords, vehicleName=None):
        """
        Update Position with the Map class
        Gives new coordinates so that Map has the latest coordinates and elevation matrix
        Should make a call to the Vicinity classes function for retrieving elevation matrix, update the elevation
        parameter of map_interface.

        :param xCoords: the x coordinate to be set
        :param yCoords: the y coordinate to be set
        :param vehicleName: Name of the vehicle to be updated; if vehicle is not present, adds it with init_position.
                Of type UUID
        """

        self.currentCoordinates.x = xCoords
        self.currentCoordinates.y = yCoords
        self.adjacentElevations = self.get_vicinity(self.currentCoordinates.x, self.currentCoordinates.y,
                                                    self.north_pixels, self.east_pixels)


