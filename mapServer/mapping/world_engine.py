"""
WorldEngine

Used as the data layer for the threaded server. Retrieves and processes data stored in raster images.
Manages
"""
import csv

__author__ = 'Ryan A. Rodriguez'

import rasterio
from osgeo import gdal, osr
from mapServer.server.server_conf import settings
import numpy as np
import matplotlib.pyplot as plt
from pylab import *
from mapServer.vehicles.vehicle import Coordinate, PixelPair
from geographiclib.geodesic import Geodesic
from itertools import izip, tee


def pairwise(iterable):
    "s -> (s0,s1), (s2,s3), (s4, s5), ..."
    a, b = tee(iterable)
    next(b, None)
    a = iter(iterable)
    return izip(a, b)


class ReadException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class MapFile(object):
    def __init__(self, filename, verbose=False):
        self.file = filename
        self.hdr_file = filename.split('.')[0] + '.hdr'  # Not sure if we need this anymore
        self.img = rasterio.open(self.file)
        self.geotransform = self.img.meta['transform']

        self.nodatavalue, self.data = None, None
        self.nodatavalue = self.img.meta['nodata']
        self.ncol = self.img.meta['width']
        self.nrow = self.img.meta['height']
        self.rotation = self.geotransform[2]     #rotation, 0 if image is 'north-up'
        self.originX = self.geotransform[0]      #top-left x
        self.originY = self.geotransform[3]      #top-left y
        self.pixelWidth = self.geotransform[1]   #w/e pixel resoluton
        self.pixelHeight = self.geotransform[5]  #n/s pixel resolution

        if verbose is True:
            print "GeoT:{}".format(self.geotransform)
            print "Metadata:{}".format(self.img.meta)


class RetrievePointException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Map(MapFile):
    def __init__(self, filename, verbose=False, **kwargs):
        super(Map, self).__init__(filename, verbose, **kwargs)
        self.fileName = filename
        self.adjacentElevations = np.zeros((3, 3))
        self.vehicles = {}

    def latLonToPixel(self, coords):
        """
        First open the file with gdal (see if we can get around this), then retrieve its geotransform.
        Next, obtain a spatial reference, and perform a coordinate transformation.

        Return the pixel pair corresponding to the input coordinates given in lat/lon
        :param coords: A named Tuple of type 'Coordinate' containing a lat/lon pair
        :return: A named tuple of type PixelPair containing an x/y pair
        """
        ds = gdal.Open(self.fileName)
        gt = self.geotransform
        srs = osr.SpatialReference()
        srs.ImportFromWkt(ds.GetProjection())
        srsLatLong = srs.CloneGeogCS()
        ct = osr.CoordinateTransformation(srsLatLong, srs)
        (x, y, holder) = ct.TransformPoint(coords.lon, coords.lat)
        x = (x - gt[0]) / gt[1]
        y = (y - gt[3]) / gt[5]
        pixelPairs = PixelPair(x=int(x), y=int(y))
        return pixelPairs

    @staticmethod
    def distance_on_unit_sphere(coord1, coord2):

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
        arc = math.acos(cos)

        # Remember to multiply arc by the radius of the earth
        # in your favorite set of units to get length.
        return arc * 6373 #for km, 3960 for feet

    @staticmethod
    def latlon_distance_on_unit_sphere(coord1, coord2, mode):

        if mode is 'lat':
            lat1, lon1 = coord1.lat, coord1.lon
            lat2, lon2 = coord1.lat, coord2.lon
        elif mode is 'lon':
            lat1, lon1 = coord1.lat, coord1.lon
            lat2, lon2 = coord2.lat, coord1.lon
        else:
            raise ValueError

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
        arc = math.acos(cos)

        # Remember to multiply arc by the radius of the earth
        # in your favorite set of units to get length.
        return arc * 6373 #for km, 3960 for feet

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
        #@todo:figure out how to add exceptions in rasterio
        #gdal.UseExceptions() #so it doesn't print to screen everytime point is outside grid

        if coordinates is not None:
            coord = coordinates
            pixs = self.latLonToPixel(coord)
            px = pixs.x
            py = pixs.y
        elif (lat, lon) is not (None, None):
            pixs = self.latLonToPixel(Coordinate(lat=lat, lon=lon))
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
            #@todo: raise an exception; trying to retrieve elevation based on coordinates and vehicle name, or neither
            #raise BaseException
            pass

        if vehicleName is not None:
            try:
                vehicle = self.vehicles[vehicleName]
                coordinates = vehicle.currentCoordinates

            except:
                RetrievePointException("Area read exception")

        if mode is 'coords':
            pixs = self.latLonToPixel(coordinates)
            px = pixs.x
            py = pixs.y
        elif mode is 'pixel':
            px = coordinates.lon
            py = coordinates.lat


        #Now determine window
        topLeftX = px - window / 2
        topLeftY = py - window / 2
        try: #in case raster isnt full extent
            """@todo: use negative windowing feature of rasterio read"""
            elevations = self.img.read(1, window=((topLeftY, topLeftY + window), (topLeftX, topLeftX + window)))
        except:
            print "exception"
        return elevations

    def get_coordinates_in_segment(self, startCoord, endCoord, mode='samples', numSamples=15, returnStyle='array'):
        """
        Get coordinates along the direct path between start and end coordinates

        :param startCoord: a Coordinate containing lat and lon, the starting point of the path.
        :param endCoord: a Coordinate containing lat and lon, the end point of the path.
        :param mode: determines how the elevation is sampled, either by pixel width, or a given sampling rate in
        'coordinate distance'
        :param numSamples: Number of
        :param returnStyle: Default return style is an array of Coordinates
        :rtype : not sure yet, perhaps determine this with an optional arg
        """

        profile = []
        p = Geodesic.WGS84.Inverse(startCoord.lat, startCoord.lon, endCoord.lat, endCoord.lon)
        l = Geodesic.WGS84.Line(p['lat1'], p['lon1'], p['azi1'])

        if mode is 'samples':
            num = 15
        elif mode is 'frequency':
            pass
        for i in range(numSamples + 1):
            b = l.Position(i * p['s12'] / num)
            profile.append(Coordinate(b['lat2'], b['lon2']))
            #print(b['lat2'], b['lon2'])

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
            #try to open the csv, raise exception if fail

            #after .csv is inspected, check if there are at least 2 entries
            #read in csv file as array of Coords
            pass
        elif mode is 'segments':
            if len(segmentPairs) < 2:
                """@todo:raise an exception"""
                pass
        else:
            """@todo: raise an exception if illegal mode provided"""
            pass

        if mode is 'coordinateTrace':
            for start, end in coordinateArray:
                profile.append(self.get_coordinates_in_segment(start, end, 15))

        #else:
        #    raise TypeError("Invalid mode of operation specified for retrieving elevation by segment")

        return profile


    def get_elevation_along_path(self, **kwargs):
        path = kwargs.get('path', None)

        """
        Query elevations along a path defined by a list of segments. Works by calling get_elevation_by_segment()
        iteratively on
        the segment list

        :param path: Path specified as CSV file or coordinates
        :return the distances between each coordinate, as well as the elevations at each coordinate
        """
        csvPath = r'/Users/empire/Dropbox/NASA-Collaboration/qgis/pathCSV/path4.csv'
        pathInfo = {}
        with open(csvPath, 'rb') as csvfile:
            mycsv = csv.reader(csvfile, delimiter=' ', quotechar='|')
            mycsv = list(mycsv)
            lines = [ent[0].split(',') for ent in mycsv[1:] if ent]
            #read in csv lines, turn raw coords into namedTuple Coordinate
            baseCoordinates = [Coordinate(lat=elem[1], lon=elem[0]) for elem in
                               [[float(e) for e in line if e] for line in lines]]
            coordsArray = [item for sublist in
                           [self.get_coordinates_in_segment(segmentStart, segmentEnd) for segmentStart, segmentEnd in
                            pairwise(baseCoordinates)] for item in sublist]

            distanceArray = [self.distance_on_unit_sphere(segmentStart, segmentEnd) for segmentStart, segmentEnd in
                             pairwise(coordsArray)]
            latDistanceArray = [self.latlon_distance_on_unit_sphere(segmentStart, segmentEnd, 'lat') for
                                segmentStart, segmentEnd in pairwise(coordsArray)]
            lonDistanceArray = [self.latlon_distance_on_unit_sphere(segmentStart, segmentEnd, 'lon') for
                                segmentStart, segmentEnd in pairwise(coordsArray)]


            #print "distance:\n", len(distanceArray), distanceArray
            elevationArray = [self.get_point_elevation(coordinate=elem) for elem in coordsArray]
            pathInfo = {'coords': coordsArray, 'elevation': elevationArray, 'distance': distanceArray,
                        'latDistance': latDistanceArray, 'lonDistance': lonDistanceArray}
            return np.array(pathInfo['elevation'])
            #return izip_longest(coordsArray, elevationArray, distanceArray)


    def planPath(self, startCoord, endCoord, **kwargs):
        """
        @todo From start coordinates to end coordinates, sample elevation. Determine Path
        optional args will determine how the path is optimized
        """

        pass

    def plot(self, **window):
        """@todo: turn this into a graph function"""
        #band = a.GetRasterBand(1)
        #imshow(a, interpolation='bilinear',cmap=cm.prism,alpha=1.0)
        if len(window) is not 0:
            #if window is not None and len(window) >= 4:
            data = self.img.read(1, window=((window['xStart'], window['xLen']),
                                            (window['yStart'], window['yLen'])))

        mask = np.ma.masked_values(self.data, self.nodatavalue)
        if mask is not None:
            #self.data = np.ma.masked_where(mask == True, 0)
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


if __name__ == '__main__':
    filename = settings['FILE_CONFIG']['filename']
    map = Map(filename, verbose=True)

    #quadrotor = Quadrotor(lat, lon)
    #map.add_vehicle(quadrotor)

    res = map.get_elevation_along_path(None)
    count = 0


