"""
WorldEngine is used as the data layer for the threaded server. Retrieves and processes data stored in raster images.
Manages
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import next
from builtins import str
from builtins import range
from builtins import object

__metaclass__ = type
import csv
import inspect
#import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import rasterio
import sys
import zmq
from collections import namedtuple
from geographiclib.geodesic import Geodesic
from numpy import NaN, math

try:
    from osgeo import gdal
except ImportError:
    import osgeo.gdal as gdal

try:
    from osgeo import osr
except ImportError:
    import osgeo.gdal as osr

from world_engine.utils.utils import pairwise, grouper
from world_engine.engine.server.message_passing.zmq_workers import ZmqSubWorker

Coordinate = namedtuple("Coordinate", ['lat', 'lon'], verbose=False)
PixelPair = namedtuple("PixelPair", ['x', 'y'], verbose=False)


class ReadException(Exception):
    """

    ReadExceptions occur in response to invalid rasters or file paths

    """

    def __init__(self, strn):
        self.strn = strn

    def __str__(self):
        return repr(self.strn)

class ArgumentError(Exception):

    def __init__(self, message, errors=None):

        # Call the base class constructor with the parameters it needs
        """

        :param message: The error message output
        :param errors: An optional dict of error messages

        """

        super(ArgumentError, self).__init__(message)

        self.errors = errors

class MapFile(object):
    """MapFile abstracts the atomic raster file read/write processes.
    """

    def __init__(self, filename, verbose=False):
        """
        :param filename: path to the raster file to be opened
        :param verbose: indicate whether we would like to print out certain metrics regarding the file opened
        """
        self.file = filename
        try:
            self.img = rasterio.open(self.file)
        except RuntimeError as e:
            print('Unable to open {}'.format(str(self.file)))
            print(e)
            sys.exit(1)
        self.crs_wkt = self.img.crs_wkt
        spheroid_start = self.crs_wkt.find("SPHEROID[") + len("SPHEROID")
        spheroid_end = self.crs_wkt.find("AUTHORITY", spheroid_start)
        self.spheroid = str(self.crs_wkt)[spheroid_start:spheroid_end]
        self.spheroid = self.spheroid.strip('[]').split(',')
        self.semimajor = float(self.spheroid[1])
        self.inverse_flattening = float(self.spheroid[2])
        self.flattening = float(1 / self.inverse_flattening)
        self.semiminor = float(self.semimajor * (1 - self.flattening))
        self.eccentricity = math.sqrt(2 * self.flattening - self.flattening * self.flattening)
        self.geotransform = self.img.meta['transform']
        self.nodatavalue, self.data = None, None
        self.nodatavalue = self.img.meta['nodata']
        self.ncol = self.img.meta['width']
        self.nrow = self.img.meta['height']
        self.rotation = self.geotransform[2]  # rotation, 0 if image is 'north-up'
        self.originX = self.geotransform[0]  # top-left x
        self.originY = self.geotransform[3]  # top-left y
        self.pixelWidth = self.geotransform[1]  # w/e pixel resoluton
        self.pixelHeight = self.geotransform[5]  # n/s pixel resolution

        if verbose is True:
            print("GeoT:{}".format(self.geotransform))
            print("Metadata:{}".format(self.img.meta))


class RetrievePointException(Exception):
    """ReadExceptions occur in response to invalid queries on coordinates

    These invalid queries include coordinates that are not within the extent of the current raster,
    or those that are either not available or contain a recognized 'no-data' value.

    Note:
        I'm unsure how NaN values translate on the Matlab side. It is also
        possible to return the 'no-value' float directly. This value can typically be found in
        a raster files header, and are stored in the MapFile class' attribute `nodatavalue`

    Args:
        strn (str): Human readable string describing the exception.

    Attributes:
        strn (str): Human readable string describing the exception.

    """

    def __init__(self, strn):
        self.strn = strn

    def __str__(self):
        return repr(self.strn)


class Map(MapFile):
    """

    The Map Class offers both atomic and advanced map read operations

    The Map Class is built on top of the MapFile class for low-level file reading operations.
    Map depends on the GDAL and Rasterio abstraction layers.

    """

    def __init__(self, filename, verbose=False, **kwargs):
        super(Map, self).__init__(filename, verbose, **kwargs)
        self.file_name = filename
        self.adjacentElevations = np.zeros((3, 3))
        self.vehicles = {}
        self.ds = gdal.Open(self.file_name)

    def lat_lon_to_pixel(self, coords):
        """

        First open the file with gdal (see if we can get around this), then retrieve its geotransform.
        Next, obtain a spatial reference, and perform a coordinate transformation.

        Return the pixel pair corresponding to the input coordinates given in lat/lon
        :param coords: A named Tuple of type 'Coordinate' containing a lat/lon pair
        :return: A named tuple of type PixelPair containing an x/y pair

        """
        ds = self.ds
        gt = self.geotransform
        srs = osr.SpatialReference()
        srs.ImportFromWkt(ds.GetProjection())
        srs_lat_lon = srs.CloneGeogCS()
        ct = osr.CoordinateTransformation(srs_lat_lon, srs)
        (x, y, holder) = ct.TransformPoint(coords.lon, coords.lat)
        x = (x - gt[0]) / gt[1]
        y = (y - gt[3]) / gt[5]
        pixel_pair = PixelPair(x=int(x), y=int(y))
        return pixel_pair

    # todo: ought to take datum as input
    def pixel_to_lat_lon(self, pixel):
        """

        First open the file with gdal @todo:(see if we can get around this), then retrieve its geotransform.
        Next, obtain a spatial reference, and perform a coordinate transformation.

        Return the geographic coordinate corresponding to the input coordinates given in pixel x/y
        :param coords: A named Tuple of type 'Coordinate' containing a lat/lon pair
        :return: A named tuple of type PixelPair containing an x/y pair

        """
        # get the existing coordinate system
        ds = self.ds
        old_cs = osr.SpatialReference()
        old_cs.ImportFromWkt(ds.GetProjectionRef())

        # create the new coordinate system
        # @todo: this is ugly and doesnt work off of the datum of the image being read
        wgs84_wkt = """
        GEOGCS["WGS 84",
            DATUM["WGS_1984",
                SPHEROID["WGS 84",6378137,298.257223563,
                    AUTHORITY["EPSG","7030"]],
                AUTHORITY["EPSG","6326"]],
            PRIMEM["Greenwich",0,
                AUTHORITY["EPSG","8901"]],
            UNIT["degree",0.01745329251994328,
                AUTHORITY["EPSG","9122"]],
            AUTHORITY["EPSG","4326"]]"""
        new_cs = osr.SpatialReference()
        new_cs.ImportFromWkt(wgs84_wkt)

        # create a transform object to convert between coordinate systems
        transform = osr.CoordinateTransformation(old_cs, new_cs)

        # get the point to transform, pixel (0,0) in this case
        width = ds.RasterXSize
        height = ds.RasterYSize
        gt = ds.GetGeoTransform()
        minx = gt[0]
        miny = gt[3] + width * gt[4] + height * gt[5]
        latlong = transform.TransformPoint(minx, miny)
        return Coordinate(lon=latlong[0], lat=latlong[1])

    @staticmethod
    def distance_on_unit_sphere(coord1, coord2, units='km'):
        # todo: need to make this work with ellipsoid earth models for more accurate distance calculations
        # todo:
        """

        Calculate the distance on a spherical earth model with radius hard-coded.

        :param coord1: start coordinates
        :param coord2: end coordinates
        :param units: choose whether to return in km or feet
        :return: return the distance in km

        """

        lat1, lon1 = coord1.lat, coord1.lon
        lat2, lon2 = coord2.lat, coord2.lon

        # Convert latitude and longitude to
        # spherical coordinates in radians
        degrees_to_radians = math.pi / 180.0

        # phi = 90 - latitude
        phi1 = (90.0 - lat1) * degrees_to_radians
        phi2 = (90.0 - lat2) * degrees_to_radians

        # theta = longitude
        theta1 = lon1 * degrees_to_radians
        theta2 = lon2 * degrees_to_radians

        # Compute spherical distance from spherical coordinates.

        # For two locations in spherical coordinates
        # (1, theta, phi) and (1, theta', phi')
        # cosine( arc length ) =
        #    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
        # distance = rho * arc length

        cos = (math.sin(phi1) * math.sin(phi2) * math.cos(theta1 - theta2) +
               math.cos(phi1) * math.cos(phi2))
        """ @todo: need to implement domain check"""
        arc = math.acos(cos)

        if units is 'km':
            return arc * 6373
        else:
            return arc * 3960

    @staticmethod
    def lat_lon_distance_on_unit_sphere(coord1, coord2, lat_lon, units='km'):
        """

        Compute either the lateral or longitudinal distance from on point to another;
        This corresponds to finding the length of one of the legs of the right triangle between
        the two points.

        :param coord1: start coordinates
        :param coord2: end coordinates
        :param units: choose whether to return in km or miles
        :return: distance in units specified by 'units' param

        """

        if lat_lon is 'lat':
            lat1, lon1 = coord1.lat, coord1.lon
            lat2, lon2 = coord1.lat, coord2.lon
        elif lat_lon is 'lon':
            lat1, lon1 = coord1.lat, coord1.lon
            lat2, lon2 = coord2.lat, coord1.lon
        else:
            raise Exception("lat or lon not specified")

        # Convert latitude and longitude to
        # spherical coordinates in radians
        degrees_to_radians = math.pi / 180.0

        # phi = 90 - latitude
        phi1 = (90.0 - lat1) * degrees_to_radians
        phi2 = (90.0 - lat2) * degrees_to_radians

        # theta = longitude
        theta1 = lon1 * degrees_to_radians
        theta2 = lon2 * degrees_to_radians
        cos = (math.sin(phi1) * math.sin(phi2) * math.cos(theta1 - theta2) +
               math.cos(phi1) * math.cos(phi2))
        arc = math.acos(cos)

        # Remember to multiply arc by the radius of the earth
        # in your favorite set of units to get length.
        if units is 'km':
            return arc * 6373
        else:
            return arc * 3960

    @staticmethod
    def vinc_inv(f, a, coordinate_a, coordinate_b):
        """

        Returns the distance between two geographic points on the ellipsoid
        and the forward and reverse azimuths between these points.
        lats, longs and azimuths are in radians, distance in metres

        :param f: flattening of the geodesic
        :param a: the semimajor axis of the geodesic
        :param coordinate_a: decimal coordinate given as named tuple coordinate
        :param coordinate_b: decimal coordinate given as named tuple coordinate
        Note: The problem calculates forward and reverse azimuths as: coordinate_a -> coordinate_b

        """
        phi1 = math.radians(coordinate_a.lat)
        lembda1 = math.radians(coordinate_a.lon)

        phi2 = math.radians(coordinate_b.lat)
        lembda2 = math.radians(coordinate_b.lon)

        if (abs(phi2 - phi1) < 1e-8) and (abs(lembda2 - lembda1) < 1e-8):
            return {'distance': 0.0, 'forward_azimuth': 0.0, 'reverse_azimuth': 0.0}

        two_pi = 2.0 * math.pi

        b = a * (1 - f)

        TanU1 = (1 - f) * math.tan(phi1)
        TanU2 = (1 - f) * math.tan(phi2)

        U1 = math.atan(TanU1)
        U2 = math.atan(TanU2)

        lembda = lembda2 - lembda1
        last_lembda = -4000000.0  # an impossibe value
        omega = lembda

        # Iterate the following equations,
        #  until there is no significant change in lembda

        while (last_lembda < -3000000.0 or lembda != 0 and abs((last_lembda - lembda) / lembda) > 1.0e-9):
            sqr_sin_sigma = pow(math.cos(U2) * math.sin(lembda), 2) + \
                            pow((math.cos(U1) * math.sin(U2) -
                                 math.sin(U1) * math.cos(U2) * math.cos(lembda)), 2)

            Sin_sigma = math.sqrt(sqr_sin_sigma)

            Cos_sigma = math.sin(U1) * math.sin(U2) + math.cos(U1) * math.cos(U2) * math.cos(lembda)

            sigma = math.atan2(Sin_sigma, Cos_sigma)

            Sin_alpha = math.cos(U1) * math.cos(U2) * math.sin(lembda) / math.sin(sigma)
            alpha = math.asin(Sin_alpha)

            Cos2sigma_m = math.cos(sigma) - (2 * math.sin(U1) * math.sin(U2) / pow(math.cos(alpha), 2))

            C = (f / 16) * pow(math.cos(alpha), 2) * (4 + f * (4 - 3 * pow(math.cos(alpha), 2)))

            last_lembda = lembda

            lembda = omega + (1 - C) * f * math.sin(alpha) * (sigma + C * math.sin(sigma) * \
                                                              (Cos2sigma_m + C * math.cos(sigma) * (
                                                                  -1 + 2 * pow(Cos2sigma_m, 2))))

        u2 = pow(math.cos(alpha), 2) * (a * a - b * b) / (b * b)

        A = 1 + (u2 / 16384) * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))

        B = (u2 / 1024) * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))

        delta_sigma = B * Sin_sigma * (Cos2sigma_m + (B / 4) * \
                                       (Cos_sigma * (-1 + 2 * pow(Cos2sigma_m, 2)) - \
                                        (B / 6) * Cos2sigma_m * (-3 + 4 * sqr_sin_sigma) * \
                                        (-3 + 4 * pow(Cos2sigma_m, 2))))

        s = b * A * (sigma - delta_sigma)

        alpha12 = math.atan2((math.cos(U2) * math.sin(lembda)), \
                             (math.cos(U1) * math.sin(U2) - math.sin(U1) * math.cos(U2) * math.cos(lembda)))

        alpha21 = math.atan2((math.cos(U1) * math.sin(lembda)), \
                             (-math.sin(U1) * math.cos(U2) + math.cos(U1) * math.sin(U2) * math.cos(lembda)))

        if (alpha12 < 0.0):
            alpha12 += two_pi
        if (alpha12 > two_pi):
            alpha12 -= two_pi

        alpha21 += two_pi / 2.0
        if alpha21 < 0.0:
            alpha21 += alpha21 + two_pi
        if alpha21 > two_pi:
            alpha21 -= two_pi

        return {"distance": s, "forward_azimuth": alpha12, "reverse_azimuth": alpha21}

    @staticmethod
    def vinc_dir(f, a, coordinate_a, alpha12, s):
        """

        Returns the lat and long of projected point and reverse azimuth
        given a reference point and a distance and azimuth to project.
        lats, longs and azimuths are passed in decimal degrees
        Returns ( phi2,  lambda2,  alpha21 ) as a tuple

        """

        phi1, lambda1 = coordinate_a.lat, coordinate_a.lon
        piD4 = math.atan(1.0)
        two_pi = piD4 * 8.0
        phi1 = phi1 * piD4 / 45.0
        lambda1 = lambda1 * piD4 / 45.0
        alpha12 = alpha12 * piD4 / 45.0
        if alpha12 < 0.0:
            alpha12 += two_pi
        if alpha12 > two_pi:
            alpha12 -= two_pi

        b = a * (1.0 - f)
        tan_u1 = (1 - f) * math.tan(phi1)
        u1 = math.atan(tan_u1)
        sigma1 = math.atan2(tan_u1, math.cos(alpha12))
        sin_alpha = math.cos(u1) * math.sin(alpha12)
        cos_alpha_sq = 1.0 - sin_alpha * sin_alpha
        u2 = cos_alpha_sq * (a * a - b * b) / (b * b)

        # @todo: look into replacing A and B with vincenty's amendment, see if speed/accuracy is good
        A = 1.0 + (u2 / 16384) * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
        B = (u2 / 1024) * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))

        # Starting with the approx
        sigma = (s / (b * A))
        last_sigma = 2.0 * sigma + 2.0  # something impossible

        # Iterate the following 3 eqs unitl no sig change in sigma
        # two_sigma_m , delta_sigma
        while abs((last_sigma - sigma) / sigma) > 1.0e-9:
            two_sigma_m = 2 * sigma1 + sigma
            delta_sigma = B * math.sin(sigma) * (math.cos(two_sigma_m) + (B / 4) * (math.cos(sigma) *
                                                                                    (-1 + 2 * math.pow(
                                                                                        math.cos(two_sigma_m), 2) -
                                                                                     (B / 6) * math.cos(two_sigma_m) *
                                                                                     (-3 + 4 * math.pow(math.sin(sigma),
                                                                                                        2)) *
                                                                                     (-3 + 4 * math.pow(
                                                                                         math.cos(two_sigma_m), 2)))))
            last_sigma = sigma
            sigma = (s / (b * A)) + delta_sigma

        phi2 = math.atan2((math.sin(u1) * math.cos(sigma) + math.cos(u1) * math.sin(sigma) * math.cos(alpha12)),
                          ((1 - f) * math.sqrt(math.pow(sin_alpha, 2) +
                                               pow(math.sin(u1) * math.sin(sigma) - math.cos(u1) * math.cos(
                                                   sigma) * math.cos(alpha12), 2))))

        lmbda = math.atan2((math.sin(sigma) * math.sin(alpha12)), (math.cos(u1) * math.cos(sigma) -
                                                                   math.sin(u1) * math.sin(sigma) * math.cos(alpha12)))

        C = (f / 16) * cos_alpha_sq * (4 + f * (4 - 3 * cos_alpha_sq))
        omega = lmbda - (1 - C) * f * sin_alpha * (sigma + C * math.sin(sigma) *
                                                   (math.cos(two_sigma_m) + C * math.cos(sigma) *
                                                    (-1 + 2 * math.pow(math.cos(two_sigma_m), 2))))

        lambda2 = lambda1 + omega
        alpha21 = math.atan2(sin_alpha, (-math.sin(u1) * math.sin(sigma) +
                                         math.cos(u1) * math.cos(sigma) * math.cos(alpha12)))

        alpha21 += two_pi / 2.0
        if alpha21 < 0.0:
            alpha21 += two_pi
        if alpha21 > two_pi:
            alpha21 -= two_pi

        phi2 = phi2 * 45.0 / piD4
        lambda2 = lambda2 * 45.0 / piD4
        alpha21 = alpha21 * 45.0 / piD4
        return Coordinate(lat=phi2, lon=lambda2), alpha21

    def get_point_elevation(self, **kwargs):
        """
        Retrieve an elevation for a single Coordinate

        :param coordinate: Named tuple of type Coordinate containing a lat/lon pair
        :param mode: Indicates whether we are passing in a Coordinate of lat/lon or a PixelPair of x/y
        """
        mode = kwargs.get('mode', 'coords')
        coords = kwargs.get('coords', None)
        coordinates = kwargs.get('coordinate', None)
        lat = kwargs.get('lat', None)
        lon = kwargs.get('lon', None)
        px = kwargs.get('px', None)
        py = kwargs.get('py', None)

        pixel = None
        # @todo:figure out how to add exceptions in rasterio
        # gdal.UseExceptions() #so it doesn't print to screen everytime point is outside grid

        if coordinates is not None:
            coord = coordinates
            pixs = self.lat_lon_to_pixel(coord)
            px = pixs.x
            py = pixs.y
        elif (lat, lon) is not (None, None):
            pixs = self.lat_lon_to_pixel(Coordinate(lat=lat, lon=lon))
            px = pixs.x
            py = pixs.y
        elif (px, py) is not (None, None):
            pass
        else:
            raise TypeError(mode + "is not a valid mode for reading pixels from raster.")

        try:  # in case raster isnt full extent
            # Window format is: ((row_start, row_stop), (col_start, col_stop))
            pixel = self.img.read(1, window=((py, py + 1), (px, px + 1)))
        except:
            RetrievePointException("Pixel read exception")

        return pixel[0][0]

    def get_surrounding_elevation(self, *args, **kwargs):
        """
        Return a square matrix of size window x window

        :param mode: Specify if we are going to read coordinates by lat/lon ('coords' mode) or by pixel in x/y (
        'pixel' mode)
        :param window: dimension of the square window to be read based on start Coordinates obtained
        :param coordinates: Named tuple of type Coordinate; cannot be specified if also specifying a vehicleName
        :param vehicleName: The UUID of a vehicle object; used to retrieve the vehicle's current coordinates
        :return: a square matrix with sides of length window
        """

        mode = kwargs.get('mode', 'coords')
        window = kwargs.get('window', 3)
        coords = kwargs.get('coordinates', None)
        lat = kwargs.get('lat', None)
        lon = kwargs.get('lon', None)
        vehicleName = kwargs.get('vehicleName', None)

        px, py = None, None
        elevations = None
        coordinates = Coordinate(lat=lat, lon=lon)
        vehicleName = vehicleName

        if bool(coordinates) ^ bool(vehicleName):
            # @todo: raise an exception; trying to retrieve elevation based on csv_file and array of Coords, or neither
            ArgumentError("Attempting to retrieve elevation based on csv_file and array of Coords, or neither")

        if vehicleName is not None:
            try:
                vehicle = self.vehicles[vehicleName]
                coordinates = vehicle.currentCoordinates

            except:
                RetrievePointException("Area read exception")

        if mode is 'coords':
            pixs = self.lat_lon_to_pixel(coordinates)
            px = pixs.x
            py = pixs.y
        elif mode is 'pixel':
            px = coordinates.lon
            py = coordinates.lat


        # Now determine window
        topLeftX = px - window / 2
        topLeftY = py - window / 2
        try:  # in case raster isnt full extent
            """@todo: use negative windowing feature of rasterio read"""
            elevations = self.img.read(1, window=((topLeftY, topLeftY + window), (topLeftX, topLeftX + window)))
        except:
            print("exception")
        return elevations

    """ TODO: need to decide whether to use functions from the geodesic lib, or from vincenty """

    def get_coordinates_in_segment(self, startCoord, endCoord, numSamples=10, returnStyle='array'):
        """

        Get coordinates along the direct path between start and end coordinates

        :param startCoord: a Coordinate containing lat and lon, the starting point of the path.
        :param endCoord: a Coordinate containing lat and lon, the end point of the path.
        :param numSamples: Number of
        :param returnStyle: Default return style is an array of Coordinates
        :rtype : not sure yet, perhaps determine this with an optional arg

        """

        """ TODO: this is bad form - need to actually check what datum we're using for the map instance """
        profile = []
        p = Geodesic.WGS84.Inverse(startCoord.lat, startCoord.lon, endCoord.lat, endCoord.lon)
        l = Geodesic.WGS84.Line(p['lat1'], p['lon1'], p['azi1'])

        for i in range(numSamples + 1):
            b = l.Position(i * p['s12'] / (numSamples))
            profile.append(Coordinate(b['lat2'], b['lon2']))
        return profile

    def get_elevation_along_segment(self, coordinateArray):
        """
        A segment is an array of coordinates, or similar iterable structure of coords. This function returns a conjugate
        array of elevations corresponding to each coordinate element in the input array

        :param coordinateArray:
        :return:
        """
        elevationArray = []
        for coordinate in coordinateArray:
            elevation = self.get_point_elevation(coordinate)
            elevationArray.append(elevation)
        return elevationArray

    def get_coordinates_along_path(self, segmentPairs, readMode='segments', **kwargs):
        """
        A path is a set of connected segments. Specifically, this function is to be called with an array of coordinates.
        Iterating through this array pairwise, we call the get_coordinates_in_segment() function iteratively forming a
        new, continuous array or coordinate connecting many segments.

        :param segmentPairs: An array of coordinates representing the 'vertices' of the path to be traversed; depending
        on readMode, this can be either an array or a .csv file.
        :param kwargs: Optional arguments for the get_coordinates_in_segment() function
        :return: A continuous set of coordinate along a path, which is a set of connected linear segments
        """
        coordinateArray = kwargs.get('coordinateArray', None)
        mode = kwargs.get('mode', None)
        numSamples = kwargs.get('numSamples', None)
        profile = []

        if mode is 'file':
            # try to open the csv, raise exception if fail

            # after .csv is inspected, check if there are at least 2 entries
            # read in csv file as array of Coords
            pass
        elif mode is 'segments':
            if len(segmentPairs) < 2:
                # todo:raise an exception
                pass
        else:
            # todo: raise an exception if illegal mode provided
            pass

        if mode is 'coordinateTrace':
            for start, end in coordinateArray:
                profile.append(self.get_coordinates_in_segment(start, end, numSamples=15))

        # else:
        #    raise TypeError("Invalid mode of operation specified for retrieving elevation by segment")

        return profile


    # todo: think about how we want to return all of these values. This function is beginning to look like a script
    def get_elevation_along_path(self, **kwargs):
        """

        Query elevations along a path defined by a list of segments. Works by calling get_elevation_by_segment()
        iteratively on the segment list (CSV file)

        :param lat_lon_array: Path specified as an array of coordinates
        :return: A numpy array with elevations corresponding to each input coordinate

        """

        csv_file = kwargs.get('csv_file', None)
        lat_lon_array = kwargs.get('coordinate_pairs', None)
        if bool(csv_file) ^ bool(lat_lon_array):
            ArgumentError("Attempting to get elevation profile with file and array input, or neither.")

        mycsv = csv.reader(csv_file, delimiter=' ', quotechar='|')
        mycsv = list(mycsv)
        lines = [ent[0].split(',') for ent in mycsv[1:] if ent]

        if csv_file:
            coord_array = [Coordinate(lat=elem[1], lon=elem[0]) for elem in
                               [[float(e) for e in line if e] for line in lines]]

        else:
            coord_array = [item for sublist in
                           [self.get_coordinates_in_segment(segmentStart, segmentEnd) for segmentStart, segmentEnd in
                            pairwise(lat_lon_array)] for item in sublist]

        distanceArray = [self.distance_on_unit_sphere(segmentStart, segmentEnd) for segmentStart, segmentEnd in
                         pairwise(coord_array)]
        latDistanceArray = [self.lat_lon_distance_on_unit_sphere(segmentStart, segmentEnd, 'lat') for
                            segmentStart, segmentEnd in pairwise(coord_array)]
        lonDistanceArray = [self.lat_lon_distance_on_unit_sphere(segmentStart, segmentEnd, 'lon') for
                            segmentStart, segmentEnd in pairwise(coord_array)]
        # print "distance:\n", len(distanceArray), distanceArray
        elevationArray = [self.get_point_elevation(coordinate=elem) for elem in coord_array]
        pathInfo = {'coords': coord_array, 'elevation': elevationArray, 'distance': distanceArray,
                    'latDistance': latDistanceArray, 'lonDistance': lonDistanceArray}
        # return np.array(pathInfo['elevation'])
        return pathInfo

    def planPath(self, startCoord, endCoord, **kwargs):
        """
        From start coordinates to end coordinates, sample elevation. Determine Path
        optional args will determine how the path is optimized
        """

        pass

    '''
    def plot(self, **window):
        """
        This function is not yet ready to call. Used to be executed in main after point and elevation samplings.

        """
        # band = a.GetRasterBand(1)
        # imshow(a, interpolation='bilinear',cmap=cm.prism,alpha=1.0)
        if len(window) is not 0:
            # if window is not None and len(window) >= 4:
            data = self.img.read(1, window=((window['xStart'], window['xLen']),
                                            (window['yStart'], window['yLen'])))

        mask = np.ma.masked_values(self.data, self.nodatavalue)
        if mask is not None:
            # self.data = np.ma.masked_where(mask == True, 0)
            data = mask.filled(NaN)

        if map.data is not None:
            try:
                fig = plt.figure(figsize=(10, 10))
                ax = fig.add_subplot(111)
                ax.set_title('colorMap')
                plt.imshow(map.data)
                ax.set_aspect('equal')

                cax = fig.add_axes([0.12, 0.1, 0.78, 0.8])
                cax.get_xaxis().set_visible(False)
                cax.get_yaxis().set_visible(False)
                cax.patch.set_alpha(0)
                cax.set_frame_on(False)
                plt.colorbar(orientation='vertical')
                plt.show()
            except:
                pass

    '''



class Coord(object):
    def __init__(self, data, prev, next):
        self.data = data  # data is a named tuple of type coordinate
        self.prev = prev  # prev is a reference to the coordinate before
        self.next = next  # reference to the next coordinate

    def __str__(self):
        return str(self.data)


class Path(object):
    """

    The path class holds a dictionary of coordinates representing a path, and also stores corresponding information on:
    elevation, distance from last point, lat distance to next point, lon distance to next point,

    """

    def __init__(self, path_info, mode='circular'):

        self.path_info = path_info
        self.coordinates = self.path_info['coords']
        # dll of nodes, where node is a wrapper object 'Coord' for named tuple Coordinates
        self.nodes = [Coord(item, self.coordinates[idx - 1] if idx >= 1 else None,
                            self.coordinates[idx + 1] if idx < len(self.coordinates) - 1 else None) for idx, item in
                      enumerate(self.coordinates)]
        self.elevation = grouper(self.coordinates, 2)
        self.distance = grouper(self.path_info['distance'], 2)
        self.lat_distance = grouper(self.path_info['latDistance'], 2)
        self.lon_distance = grouper(self.path_info['lonDistance'], 2)
        self.idx = -1
        self.mode = mode

    def __iter__(self):
        return self

    def __next__(self):
        """

        Get the next Coord in path

        """
        if self.idx < len(self.nodes) - 1:
            self.idx += 1
            return self.nodes[self.idx]
        else:
            if self.mode is 'circular':
                self.idx = 0
            else:
                self.idx = len(self.nodes)
                raise StopIteration

    def has_next(self):
        """

        Return true if there are nodes left in dll

        """
        if self.idx < len(self.nodes):
            return True
        else:
            return False

    def previous(self):
        """

        Get the previous coordinate in path

        """

        pass


class MapProcess(Map, multiprocessing.Process):
    """

    Map Process
    Defines ZMQ connection protocol and implements the thin API layer to the analytical map functions of the 'Map'
    module
    Can be used to implement high level logic relating to API calls

    """

    def __init__(self, file_name, worker_ip=None, worker_port=5555):
        super(MapProcess, self).__init__(file_name)
        multiprocessing.Process.__init__(self)
        if worker_ip is None:
            self.worker_ip = 'tcp://127.0.0.1:{}'
        else:
            self.worker_ip = worker_ip
        self.context = zmq.Context()

        """ Start ZMQ processes here"""
        """
         @todo: eventually, we want to find a way where we can have n zmq_messaging processes and k map processes and each map
         process listens for API calls with coordinates
        """

        self.results_q = multiprocessing.Queue()
        self.zmq_worker_qgis = ZmqSubWorker(qin=None, qout=self.results_q)
        self.zmq_worker_qgis.start()

        """ Configure API """
        # will not include statically defined methods
        self.map_api = dict((x, y) for x, y in inspect.getmembers(Map, predicate=inspect.ismethod))
        self.process_api = dict((x, y) for x, y in inspect.getmembers(self, predicate=inspect.ismethod))
        self.api = self.map_api.copy()
        self.api.update(self.process_api)

    # @todo: will need to manage the update of all vehicles managed by the map - threads?
    def run(self, context=None, worker_ip=None):
        """
        Now that the ZMQ processes are up and running, check to see if they put any api calls on the results queue
        :param context:
        :param worker_ip:
        :return:

        """

        # rt = Interrupt(5, post_vehicle, data=self.update_data())  # it auto-starts, no need of rt.start()

        while 1:
            if not self.results_q.empty():
                msg = self.results_q.get()
                self.decode_api_call(msg)
                """ TODO: this is a really gross workaround for a weird problem. Seem like the message from QGIS is
                getting put onto the queue more than once """
                while not self.results_q.empty():
                    self.results_q.get()

    def decode_api_call(self, raw_cmd):
        """

        Tries to decode packets received by ZMQ by comparing against known function, or API calls

        :param raw_cmd: ZMQ packet to be processed as an API call

        """
        cmd = raw_cmd[0]

        # cmd = self.map_api[cmd]
        cmd = self.api[cmd]
        # for key, value in utils.grouper(raw_cmd[1:], 2):
        #    print key, value
        argDict = {key: value for key, value in grouper(raw_cmd[1:], 2)}
        cmd(**argDict)  # callable functions in map must take kwargs in order to be called..

    def qgis(self, *args, **kwargs):
        """

        Define the sequence of events that should happen when we've received a message from qgis
        :param args:
        :param kwargs:
        :return:

        """
        msg = kwargs.get('coordinate_pairs', None)
        coordinate_pairs = [Coordinate(lat=lat, lon=lon) for lon, lat in grouper(msg, 2)]
        path_info = self.get_elevation_along_path(**{'coordinate_pairs': coordinate_pairs})
        path = Path(path_info, mode='one-shot')

        print("QGIS Called")
        print(path_info)
        """
        @todo: now path class needs to be assigned to a vehicle, and we need to call equations of motion for that
        vehicle processing will consist of:
          - calling vinc_dist between adjacent points on a circular path
          - once we have tracking angle and distance between points, call vinc_pt with information on the vehicles speed
          every five seconds.

        """

        ground_speed = 48.27  # km/h
        dt = .01  # 1 mS
        rocd = 0  # constant altitude
        # @todo: think about adding this to the creation of the path object
        count = 0
        tol = .1
        results = []
        while path.has_next():
            try:
                current_coord = next(path)  # get the current node, a Coord object
                next_coord = current_coord.__next__
                current_coord = current_coord.data
                # print current_coord, type(current_coord), next_coord, type(next_coord)
                if next_coord is not None:
                    inverse = self.vinc_inv(self.flattening, self.semimajor, current_coord, next_coord)
                    distance = inverse['distance']
                    fwd_azimuth = inverse['forward_azimuth']
                    rev_azimuth = inverse['reverse_azimuth']
                    err = distance
                    remaining_distance = distance
                    count = 0
                    while remaining_distance > 1:
                        count += 1
                        # @todo will need to call physical model to get current velocity based on past state and
                        # acceleration
                        fpm_to_fps = 0.01666666666667  # Feet per minute to feet per second.
                        ellipsoidal_velocity = ground_speed  # is this correct?
                        ellipsoidal_distance = ellipsoidal_velocity * dt
                        remaining_distance -= ellipsoidal_distance
                        temp_coord, temp = self.vinc_dir(0.00335281068118, 6378137.0, current_coord, fwd_azimuth,
                                                         ellipsoidal_distance)
                        altitude = rocd * fpm_to_fps * dt
                        current_coord = temp_coord
                        err = distance - remaining_distance
                        if count >= 500:
                            results.append(current_coord)
                            count = 0

            except StopIteration:
                break
        f = open('recon.csv', 'wt')
        try:
            writer = csv.writer(f)
            writer.writerow(['Lat', 'Lon'])
            for elem in results:
                writer.writerow([elem.lat, elem.lon])
        finally:
            f.close()

        print("Results", results)

    def update_data(self):
        """

        :return:

        """
        for vehicle in self.vehicles:
            # if type(vehicle) is Quadrotor:
            pass
