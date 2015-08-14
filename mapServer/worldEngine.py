"""
WorldEngine

Used as the data layer for the threaded server. Retrieves and processes data stored in raster images.
Manages
"""
import csv
import string

__author__ = 'Ryan A. Rodriguez'

import rasterio
from osgeo import gdal, osr
import numpy as np
import matplotlib.pyplot as plt
from pylab import *
from vehicle import Quadrotor, Coordinate, PixelPair
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
    def __init__(self, bil_file, **kwargs):
        self.bil_file = bil_file
        self.hdr_file = bil_file.split('.')[0] + '.hdr'  # Not sure if we need this anymore
        self.img = rasterio.open(self.bil_file)
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

        verbose = kwargs.get('verbose', False)
        if verbose is True:
            print "GeoT:{}".format(self.geotransform)
            print "Metadata:{}".format(self.img.meta)


class RetrievePointException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Map(MapFile):
    def __init__(self, filename, **kwargs):
        super(Map, self).__init__(filename, **kwargs)
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

    def distance_on_unit_sphere(self, coord1, coord2):

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

    def get_point_elevation(self, coordinate, mode='coords'):
        """
        Retrieve an elevation for a single Coordinate
        :param coordinate: Named tuple of type Coordinate containing a lat'lon pair
        :param mode: Indicates whether we are passing in a Coordinate of lat/lon or a PixelPair of x/y
        """
        pixel = None
        #@todo:figure out how to add exceptions in rasterio
        #gdal.UseExceptions() #so it doesn't print to screen everytime point is outside grid

        cy = coordinate.lat
        cx = coordinate.lon

        if mode is 'coords':
            pixs = self.latLonToPixel(coordinate)
            px = pixs.x
            py = pixs.y
        elif mode is 'pixel':
            px = cx
            py = cy
        else:
            raise TypeError(mode + "is not a valid mode for reading pixels from raster.")

        try:  # in case raster isnt full extent
        # Window format is: ((row_start, row_stop), (col_start, col_stop))
            pixel = self.img.read(1, window=((py, py + 1), (px, px + 1)))
        except:
            RetrievePointException("Pixel read exception")

        return pixel[0][0]

    def get_surrounding_elevation(self, mode='coords', window=10, coordinates=None, vehicleName=None):
    #def get_surrounding_elevation(self, **kwargs):
    #    mode = kwargs.get('mode', 'coords')
    #    window = kwargs.get('window', 3)
    #    coordinates = kwargs.get('coordinates', None)
    #    vehicleName = kwargs.get('vehicleName', None)


        """
        Return a square matrix of size window x window

        :param mode: Specify if we are going to read coordinates by lat/lon ('coords' mode) or by pixel in x/y (
        'pixel' mode)
        :param window: dimension of the square window to be read based on start Coordinates obtained
        :param coordinates: Named tuple of type Coordinate; cannot be specified if also specifying a vehicleName
        :param vehicleName: The UUID of a vehicle object; used to retrieve the vehicle's current coordinates
        :return: a square matrix with sides of length window
        """
        px, py = None, None
        elevations = None
        coordinates = coordinates
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
            print(b['lat2'], b['lon2'])

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
            print elevation
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


    def get_elevation_along_path(self, segmentList, mode='coords'):

        """
        Query elevations along a path defined by a list of segments. Works by calling get_elevation_by_segment()
        iteratively on
        the segment list

        :param segmentList:
        :param mode:
        :return the distances between each coordinate, as well as the elevations at each coordinate
        """
        csvPath = r'/Users/empire/Dropbox/NASA-Collaboration/qgis/pathCSV/path4.csv'
        with open(csvPath, 'rb') as csvfile:
            mycsv = csv.reader(csvfile, delimiter=' ', quotechar='|')
            mycsv = list(mycsv)

            coordinateArray = []
            masterCoords = []
            masterDistance = []

            lines = [ent[0].split(',') for ent in mycsv[1:] if ent]

            cordura = [Coordinate(elem[1], elem[0]) for elem in [[float(e) for e in line if e] for line in lines]]

            print "Cordura!\n", len(cordura), cordura

            #for line in lines:
            #    line = [float(e) for e in line if e]
            #    coordinateArray.append(Coordinate(lat=float(line[1]), lon=float(line[0])))
            #    print line
            #print "CoordinateArray!\n"
            #print coordinateArray



            count = 0;
            for segmentStart, segmentEnd in pairwise(coordinateArray):
                count += 1
                masterDistance.append(self.distance_on_unit_sphere(segmentStart, segmentEnd))

                temp = (self.get_coordinates_in_segment(segmentStart, segmentEnd))
                for eachEntry in temp:
                    masterCoords.append(eachEntry)

            print "MasterDistance:\n", masterDistance, "Length:\n", len(masterDistance), count, "TotalLength:\n", sum(
                masterDistance)

            masterElevation = []
            for elem in masterCoords:
                masterElevation.append(self.get_point_elevation(elem))
                #print elem, '\n'
            print masterElevation
            return masterCoords


        #read CSV file with list of segment pairs

        pass

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
    #Enter file name, instantiate map and pre-process
    #filename = r'/Users/empire/Academics/UCSC/nasaResearch/californiaNed30m/elevation_NED30M_ca_2925289_01
    # /bayAreaBIL.bil'
    filename = r'/Users/empire/Academics/UCSC/nasaResearch/californiaNed30m/elevation_NED30M_ca_2925289_01/' \
               r'virtRasterCalifornia.vrt'
    #filename = r'/Users/empire/Academics/UCSC/nasaResearch/californiaNed30m/elevation_NED30M_ca_2925289_01_BIL' \
    #          r'/virtRasterCaliforniaBil.bil'

    map = Map(filename, verbose=True)

    #@todo: look at how tigres creates many of the same type of object without having to name all of them
    #Make a quadrotor, initialize position (need to do this in Matlab in RL)

    lon = -122.030796
    lat = 36.974117
    #quadrotor = Quadrotor(lat, lon)
    #map.add_vehicle(quadrotor)
    tCoord = Coordinate(lat, lon)
    print map.latLonToPixel(tCoord)
    #res = map.get_surrounding_elevation(mode='pixel', coords = (map.ncol/2, map.nrow/2), vehicleName=quadrotor.name,
    #  lon_window=20, lat_window=20)
    #res = map.get_surrounding_elevation(mode='pixel', coordinates=Coordinate(6000, 5000), lon_window=10, lat_window=10)
    #print "Surrounding Elevations{}, \nWindow Size of{}".format(res, shape(res))

    #print map.get_point_elevation(Coordinate(9719, 25110), mode='pixel')

    print map.get_elevation_along_path(None, mode='coords')

    print map.get_point_elevation(Coordinate(36.974117, -122.030796), mode='coords')
    res = map.get_coordinates_in_segment(Coordinate(36.974117, -122.030796), Coordinate(37.411372, -122.053471))
    #print res
    map.get_elevation_along_segment(res)

