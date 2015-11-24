"""

WorldEngine is used as the data layer for the threaded server. Retrieves and processes data stored in raster images.
Manages

"""
from __future__ import (absolute_import, division, print_function, unicode_literals)

import collections
from collections import namedtuple

import affine

affine.set_epsilon(1e-12)  # must set epsilon to small value to prevent sensitive trip of degenerate matrix detection
import rasterio
from builtins import *
from geographiclib.geodesic import Geodesic
from numpy import math
from tower.map.space import Space
from tower.map.graph import Graph
from tower.controllers.swarm.swarm import Swarm

try:
    from osgeo import gdal
except ImportError:
    import osgeo.gdal as gdal

try:
    from osgeo import osr
except ImportError:
    import osgeo.gdal as osr


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


class Map(Space):
    """

    The Map Class offers both atomic and advanced map read operations

    The Map Class is built on top of the MapFile class for low-level file reading operations.
    Map depends on Rasterio, GDAL abstraction layers. Map is a concrete implementation of a space, and may contain
    one or many graph representations of itself, along with a dictionary of swarm located on the map.

    How Spaces, Vehicles, Graphs and Controllers work together is an open problem in this framework.

    """

    def __init__(self, filename=None, verbose=False, **kwargs):

        self.file_name = filename

        try:
            with rasterio.drivers():
                with rasterio.open(self.file_name, 'r') as ds:
                    self.affine = ds.meta['affine']
                    self.ncol = ds.meta['width']
                    self.nrow = ds.meta['height']
                    self.geo_transform = ds.meta['transform']
                    self.no_data_value = ds.meta['nodata']
                    self.crs = ds.crs
                    self.crs_wkt = ds.crs_wkt
                    self.meta = ds.meta
                    if verbose is True:
                        print(ds.crs)
                        print(ds.crs_wkt)
                        print("Metadata:{}".format(self.img.meta))
        except:
            raise Exception("Error opening file with Rasterio")
            sys.exit(1)  # todo: is this necessary?

        spheroid_start = self.crs_wkt.find("SPHEROID[") + len("SPHEROID")
        spheroid_end = self.crs_wkt.find("AUTHORITY", spheroid_start)
        self.spheroid = str(self.crs_wkt)[spheroid_start:spheroid_end].strip('[]').split(',')
        # todo: perhaps these ought to be properties, calculated lazily w/ most recent spheroid/geotransform
        self.semimajor = float(self.spheroid[1])
        self.inverse_flattening = float(self.spheroid[2])
        self.flattening = float(1 / self.inverse_flattening)
        self.semiminor = float(self.semimajor * (1 - self.flattening))
        self.eccentricity = math.sqrt(2 * self.flattening - self.flattening * self.flattening)

        self.rotation = self.geo_transform[2]  # rotation, 0 if image is 'north-up'
        self.originX = self.geo_transform[0]  # top-left x
        self.originY = self.geo_transform[3]  # top-left y
        self.pixelWidth = self.geo_transform[1]  # w/e pixel resoluton
        self.pixelHeight = self.geo_transform[5]  # n/s pixel resolution

        self.swarm = Swarm()    # A swarm is a collection of vehicles. A vehicle contains its own controller plugin
                                # that is updated regularly by swarm it belongs to

        self.graph = Graph()    # Graph object used for planning and controller logic.
                                # Each vehicle will probably alo need to carry arodun an instance of Graph or Path
                                # to keep track of it's path

        self.__units = 'degrees'
        self.__x = 'lon'
        self.__y = 'lat'
        self.__name = 'Coord'

    @property
    def units(self):
        return self.__units

    @property
    def x(self):
        return self.__x

    @property
    def y(self):
        return self.__y

    @property
    def name(self):
        return self.__name

    @property
    def origin(self):
        pass

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
        return collections.namedtuple(self.name, [self.x, self.y, 'units'], verbose=False)

    def get_point_elevation(self, coordinate, **kwargs):
        """

        Retrieve an elevation for a single Coordinate

        :param coordinate: Named tuple of type Coordinate containing a lat/lon pair
        :optional give kwargs `px` and `py` to retrieve a pixel directly

        """

        pixel = None
        # @todo:figure out how to add exceptions in rasterio
        # gdal.UseExceptions() #so it doesn't print to screen everytime point is outside grid

        px, py = kwargs.get('px', None), kwargs.get('py', None)
        if (px, py) is not (None, None):
            pass
        else:
            pixs = self.lat_lon_to_pixel(coordinate)
            px = pixs.x
            py = pixs.y

        try:  # in case raster isnt full extent
            # Window format is: ((row_start, row_stop), (col_start, col_stop))
            pixel = self.img.read(1, window=((py, py + 1), (px, px + 1)))
        except:
            RetrievePointException("Pixel read exception")

        return pixel[0][0]

    def get_distance_between(self, from_, to, *args, **kwargs):
        """

        :return: the distance between two
        """
        mode = kwargs.get('mode', 'fast')
        if mode is 'fast':
            return self.distance_on_unit_sphere(from_, to, units='km')
        elif True:
            return self.vincenty_inverse(from_, to)

    def get_edge(self, from_, to):
        """

        Sample data between two points

        :return: An array of points
        """
        pass

    def get_elevation_along_edge(self, from_, to):
        """

        Take as input an edge, which is an iterable of points, and get a set of elevations corresponding to
        the elevations at those points.

        :return: An iterable of the same length as input, where each output corresponds to the input coordinate given
        in the se

        """
        pass

    def get_surrounding_elevation(self, coordinate, window=4, *args, **kwargs):
        """
        Return a square matrix of size window w/ coordinate at center


        :param window: dimension of the square window to be read based on start Coordinates obtained
        :return: a square matrix with sides of length `window`
        """

        px, py = kwargs.get('px', None), kwargs.get('py', None)
        if (px, py) is not (None, None):
            pass
        else:
            pixs = self.lat_lon_to_pixel(coordinate)
            px = pixs.x
            py = pixs.y

        # Determine window
        topLeftX = px - math.floor(window / 2)
        topLeftY = py - math.floor(window / 2)
        try:  # in case raster isnt full extent
            # todo: use negative windowing feature of rasterio read
            elevations = self.img.read(1, window=((topLeftY, topLeftY + window), (topLeftX, topLeftX + window)))
            return elevations
        except:
            raise Exception("Couldn't retrieve given window")

    def lat_lon_to_pixel(self, coordinate):
        """

        First open the file with gdal (see if we can get around this), then retrieve its geotransform.
        Next, obtain a spatial reference, and perform a coordinate transformation.

        Return the pixel pair corresponding to the input coordinates given in lat/lon
        :param coordinate: A named Tuple of type 'Coordinate' containing a lat/lon pair
        :return: A named tuple of type PixelPair containing an x/y pair

        """

        inv_affine = ~self.affine
        px, py = inv_affine * (coordinate.lon, coordinate.lat)
        return px, py

    def pixel_to_lat_lon(self, col, row):
        """



        First open the file with gdal @todo:(see if we can get around this), then retrieve its geotransform.
        Next, obtain a spatial reference, and perform a coordinate transformation.

        :param col: x pixel
        :param row: y pixel
        :return: Return the geographic coordinate corresponding to the input coordinates given in pixel x/y


        """
        lon, lat = self.affine * (col, row)
        return self.point()(lon=lon, lat=lat, units=self.units)

    def distance_on_unit_sphere(self, coord1, coord2, lat_lon=None):
        # todo: need to make this work with ellipsoid earth models for more accurate distance calculations
        # todo:
        """

        Calculate the distance on a spherical earth model with radius hard-coded.


        :param coord1: start coordinates
        :param coord2: end coordinates
        :param lat_lon: Optional: give either 'lat' or 'lon' to get just the lateral or longitudinal distances by
        themselves
        :return: return the distance in km

        """
        if lat_lon is not None:
            if lat_lon is 'lat':
                lat1, lon1 = coord1.lat, coord1.lon
                lat2, lon2 = coord1.lat, coord2.lon
            elif lat_lon is 'lon':
                lat1, lon1 = coord1.lat, coord1.lon
                lat2, lon2 = coord2.lat, coord1.lon
            else:
                raise Exception("lat or lon not specified")
        else:
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

        return arc * self.semimajor  # scale to return in km

    def vincenty_inverse(self, coordinate_a, coordinate_b):
        """

        Returns the distance between two geographic points on the ellipsoid
        and the forward and reverse azimuths between these points.
        lats, longs and azimuths are in radians, distance in metres

        :param coordinate_a: decimal coordinate given as named tuple coordinate
        :param coordinate_b: decimal coordinate given as named tuple coordinate
        Note: The problem calculates forward and reverse azimuths as: coordinate_a -> coordinate_b

        """
        f, a = self.map_file.flattening, self.map_file.semimajor

        phi1 = math.radians(coordinate_a.lat)
        lambda1 = math.radians(coordinate_a.lon)

        phi2 = math.radians(coordinate_b.lat)
        lambda2 = math.radians(coordinate_b.lon)

        if (abs(phi2 - phi1) < 1e-8) and (abs(lambda2 - lambda1) < 1e-8):
            return {'distance': 0.0, 'forward_azimuth': 0.0, 'reverse_azimuth': 0.0}

        two_pi = 2.0 * math.pi

        b = a * (1 - f)

        tan_u1 = (1 - f) * math.tan(phi1)
        tan_u2 = (1 - f) * math.tan(phi2)

        U1 = math.atan(tan_u1)
        U2 = math.atan(tan_u2)

        lambda_ = lambda2 - lambda1
        last_lambda = -4000000.0  # an impossibe value
        omega = lambda_

        while (last_lambda < -3000000.0 or lambda_ != 0 and abs((last_lambda - lambda_) / lambda_) > 1.0e-9):
            sqr_sin_sigma = pow(math.cos(U2) * math.sin(lambda_), 2) + \
                            pow((math.cos(U1) * math.sin(U2) -
                                 math.sin(U1) * math.cos(U2) * math.cos(lambda_)), 2)
            Sin_sigma = math.sqrt(sqr_sin_sigma)
            Cos_sigma = math.sin(U1) * math.sin(U2) + math.cos(U1) * math.cos(U2) * math.cos(lambda_)
            sigma = math.atan2(Sin_sigma, Cos_sigma)
            Sin_alpha = math.cos(U1) * math.cos(U2) * math.sin(lambda_) / math.sin(sigma)
            alpha = math.asin(Sin_alpha)
            Cos2sigma_m = math.cos(sigma) - (2 * math.sin(U1) * math.sin(U2) / pow(math.cos(alpha), 2))
            C = (f / 16) * pow(math.cos(alpha), 2) * (4 + f * (4 - 3 * pow(math.cos(alpha), 2)))
            last_lambda = lambda_
            lambda_ = omega + (1 - C) * f * math.sin(alpha) * (sigma + C * math.sin(sigma) * \
                                                               (Cos2sigma_m + C * math.cos(sigma) * (
                                                                   -1 + 2 * pow(Cos2sigma_m, 2))))
        u2 = pow(math.cos(alpha), 2) * (a * a - b * b) / (b * b)
        A = 1 + (u2 / 16384) * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
        B = (u2 / 1024) * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))
        delta_sigma = B * Sin_sigma * (Cos2sigma_m + (B / 4) * (Cos_sigma * (-1 + 2 * pow(Cos2sigma_m, 2)) - \
                                                                (B / 6) * Cos2sigma_m * (-3 + 4 * sqr_sin_sigma) * \
                                                                (-3 + 4 * pow(Cos2sigma_m, 2))))

        s = b * A * (sigma - delta_sigma)
        alpha12 = math.atan2((math.cos(U2) * math.sin(lambda_)), \
                             (math.cos(U1) * math.sin(U2) - math.sin(U1) * math.cos(U2) * math.cos(lambda_)))
        alpha21 = math.atan2((math.cos(U1) * math.sin(lambda_)), \
                             (-math.sin(U1) * math.cos(U2) + math.cos(U1) * math.sin(U2) * math.cos(lambda_)))

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

    def vincenty_direct(self, coordinate_a, alpha12, s):
        """

        Returns the lat and long of projected point and reverse azimuth
        given a reference point and a distance and azimuth to project.
        lats, longs and azimuths are passed in decimal degrees
        Returns ( phi2,  lambda2,  alpha21 ) as a tuple

        :param coordinate_a: start coordinate
        :param alpha12: heading
        :param s: arc length

        """
        f, a = self.map_file.flattening, self.map_file.semimajor
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
        return self.point(lat=phi2, lon=lambda2), alpha21

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

        # todo: this is bad form - need to actually check what datum we're using for the map instance
        profile = []
        p = Geodesic.WGS84.Inverse(startCoord.lat, startCoord.lon, endCoord.lat, endCoord.lon)
        l = Geodesic.WGS84.Line(p['lat1'], p['lon1'], p['azi1'])

        for i in range(numSamples + 1):
            b = l.Position(i * p['s12'] / (numSamples))
            profile.append(self.point(b['lat2'], b['lon2']))
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

    def get_coordinates_along_path(self, segmentPairs, **kwargs):
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

        mask = np.ma.masked_values(data, self.nodatavalue)
        if mask is not None:
            # data = np.ma.masked_where(mask == True, 0)
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
                cax.patch.set_alpha(0)cl
                cax.set_frame_on(False)
                plt.colorbar(orientation='vertical')
                plt.show()
            except:
                pass

    '''


if __name__ == '__main__':
    map_ = Map('/Users/empire/Documents/GitHub/tower/tower/utils/images/scClipProjected.tif')
    point = map_.point()
    print(point(0, 0, 0))
    coord = map_.pixel_to_lat_lon(0, 100)
    print(coord)
    pixel = map_.lat_lon_to_pixel(coord)
    print(pixel)
