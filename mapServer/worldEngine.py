"""
WorldEngine

Used as the data layer for the threaded server. Retrieves and processes data stored in raster images.
Manages
"""
__author__ = 'Ryan A. Rodriguez'

import rasterio
#from osgeo import gdal
#import gdal
import gdalconst
import numpy as np
import matplotlib.pyplot as plt
from pylab import *
from collections import namedtuple
from vehicle import Quadrotor, Coordinate
import math
import sys;

from geographiclib.geodesic import Geodesic
from geographiclib.constants import *


class ReadException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class MapFile(object):
    def __init__(self, bil_file):
        self.bil_file = bil_file
        self.hdr_file = bil_file.split('.')[0] + '.hdr'
        print self.hdr_file

    def open_file(self):
        """
        Reads in whole bil file, gets info
        """
        #gdal.GetDriverByName('EHdr').Register()

        #If the file is not a bil, maybe try to convert it with rasterio first
        try:
            self.img = rasterio.open(self.bil_file)
            #band = rasterio.band(src, 1)
            #w = self.src.read(1, window=((0, 100), (0, 100)))
            #print "IMG Metadata", self.img.meta

            #self.img = gdal.Open(self.bil_file)
            #self.band = self.img.GetRasterBand(1)
        except:
            '''@todo:roll custom exception for this to raise, what exceptions are thrown? Double check this'''
            print 'Bil file {} is not found, or gdal could not read it'.format(self.bil_file)

    def read_file(self, **window):
        """
        Reads raster files and extracts metadata.
        If no window is provided, whole file will be read if the file is small enough,
        else a default window will be chosen

        :param Window arguments are expressed as follows:
            xStart: topLeft corner's x coordinate
            yStart: top left corner's y coordinate
            xLen: size of window in x direction
            yLen: size of window in y direction
        """
        if not all(kwargs in window for kwargs in ("xStart", "xLen", "yStart", "yLen")) and len(window) > 4:
            raise ReadException("Missing arguments for window during read")
        try:

            #self.geotransform = self.img.GetGeoTransform()
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

            if len(window) is not 0:
                #if window is not None and len(window) >= 4:
                self.data = self.img.read(1, window=((window['xStart'], window['xLen']),
                                                     (window['yStart'], window['yLen'])))
                #else:
                #    self.data = self.img.read(1, window=((0, 16989), (0, 41569)))

                #self.data = np.ma.masked_where(self.data < 0, self.data)

        except:
            raise ReadException('.bil file {} is not found, or gdal could not read it'.format(self.bil_file))

    def process_file(self, **window):
        """
        Open and read in raster file as numpy array
        results are stored in 'data' member, and all other parameters are found, read, and or updated
        **window args indicate that only a section of the raster ought to be read.

        :param window: Window arguments are expressed as follows:
            xStart: topLeft corner's x coordinate
            yStart: top left corner's y coordinate
            xLen: size of window in x direction
            yLen: size of window in y direction

        """
        self.open_file()
        self.read_file(**window)
        #self.data = np.ma.masked_where(self.data < 0, self.data)
        mask = np.ma.masked_values(self.data, self.nodatavalue)
        if mask is not None:
            #self.data = np.ma.masked_where(mask == True, 0)
            self.data = mask.filled(NaN)


class AddVehicleException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class RetrievePointException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Map(MapFile):
    def __init__(self, filename):
        super(Map, self).__init__(filename)
        self.fileName = filename
        self.adjacentElevations = np.zeros((3, 3))
        self.vehicles = {}

    def add_vehicle(self, vehicle):
        """

        :param vehicle:
        """
        try:
            self.vehicles[vehicle.name] = vehicle
        except:
            raise AddVehicleException("Vehicle does not have a name, or does not exist")

    def get_point_elevation(self, coordinate, mode='coords'):
        """
        Retrieve an elevation value for a single point given coordinate input
        :param coordinate:
        :param mode:
        """
        pixel = None
        #@todo:figure out how to add exceptions in rasterio
        #gdal.UseExceptions() #so it doesn't print to screen everytime point is outside grid

        cy = coordinate.lat
        cx = coordinate.lon

        # Convert from map to pixel coordinates.
        if mode is 'coords':
            px = int((cx - self.originX) / self.pixelWidth) #x pixel
            py = int((cy - self.originY) / self.pixelHeight) #y pixel
            print px, py, self.originX, self.originY, self.pixelWidth, self.pixelHeight
        elif mode is 'pixel':
            px = cx
            py = cy
        else:
            raise TypeError(mode + "is not a valid mode for reading pixels from raster.")

        #print "Px:{}, Py:{}".format(px, py), val
        try: #in case raster isnt full extent
            #structval = self.band.ReadRaster(px, py, 1, 1, buf_type=gdal.GDT_Float32) #Assumes 32 bit int aka 'float'
            pixel = self.img.read(1, window=((px, px + 1), (py, py + 1)))
            print "pixel", pixel
            #intval = struct.unpack('f', structval)
            #had to add 0.0000... so that it wouldn't truncate to integer and fail with constraint error my database
            #val = intval[0]
            #if intval[0] < -9999:
            #    val = -9999

        except:
            RetrievePointException("Pixel read exception")

        return pixel[0][0]

    def get_surrounding_elevation(self, mode='coords', lat_window=10, lon_window=10, **kwargs):
        """

        :param mode:
        :param lat_window:
        :param lon_window:
        :param kwargs:
        :return:
        """
        #determine boundary for manually throwing exceptions
        eastBoundary = self.originX + self.ncol
        westBoundary = self.originX
        northBoundary = self.originY
        southBoundary = self.originY + self.nrow

        elevations = None
        coordinates = kwargs.get('coordinates', None)
        vehicleName = kwargs.get('vehicleName', None)

        if bool(coordinates) ^ bool(vehicleName):
            #@todo: raise an exception; trying to retrieve elevation based on coordinates and vehicle name, or neither
            #raise BaseException
            pass
            #@todo: how to check if coords in either mode are the right format?
        if coordinates is not None:
            if mode is 'coords':
                px = int((coordinates.lon - self.originX) / self.pixelWidth) #x pixel
                py = int((coordinates.lat - self.originY) / self.pixelHeight) #y pixel
            elif mode is 'pixel':
                px = coordinates.lon
                py = coordinates.lat
        else:
            try:
                vehicle = self.vehicles[vehicleName]
                coords = vehicle.currentCoordinates

                if mode is 'coords':
                    px = int((coords.lon - self.originX) / self.pixelWidth) #x pixel
                    py = int((coords.lat - self.originY) / self.pixelHeight) #y pixel
                elif mode is 'pixel':
                    px = coords.lon
                    py = coords.lat

            except:
                RetrievePointException("Area read exception")


        #Now determine window
        topLeftX = px - lon_window / 2
        topLeftY = px + lat_window / 2
        try: #in case raster isnt full extent
            elevations = self.img.read(1, window=((topLeftX, topLeftX + lon_window), (topLeftY, topLeftY + lat_window)))
            #structval = self.band.ReadRaster(0, 0, 5, 5, 5, 5) #Assumes 32 bit int aka 'float'
            #structval = self.band.ReadRaster(self.RastStart.x, self.RastStart.y, self.ncols, self.nrows,
            # buf_type=gdal.GDT_Float32) #Assumes 32 bit int aka 'float'
            #intval = struct.unpack('f', structval)
            #had to add 0.0000... so that it wouldn't truncate to integer and fail with constraint error my database
            #if elevations[0] < -9999:
            #    elevations = -9999
        except:
            print "exception"
        return elevations

    def get_elevation_along_segment(self, startCoord, endCoord, numSegments=None, mode='coords', returnStyle='array'):
        """
        Algorithmic Development:
            1) determine the line between start and end
            2) sample points along the line

            How to do this?
        :param startCoord: a Coordinate containing lat and lon, the starting point of the path.
        :param endCoord: a Coordinate containing lat and lon, the end point of the path.
        :param mode: determines how the elevation is sampled, either by pixel width, or a given sampling rate in
        'coordinate distance'
        :rtype : not sure yet, perhaps determine this with an optional arg
        """

        profile = []
        p = Geodesic.WGS84.Inverse(startCoord.lat, startCoord.lon, endCoord.lat, endCoord.lon)
        l = Geodesic.WGS84.Line(p['lat1'], p['lon1'], p['azi1'])

        num = 15
        for i in range(num + 1):
            b = l.Position(i * p['s12'] / num)
            profile.append(Coordinate(b['lat2'], b['lon2']))
            print(b['lat2'], b['lon2'])

        return profile


    def get_elevation_along_path(self, startCoord, endCoord, mode='coords'):
        pass

    def planPath(self, startCoord, endCoord, **kwargs):
        """
        @todo From start coordinates to end coordinates, sample elevation. Determine Path
        optional args will determine how the path is optimized
        """

        pass


if __name__ == '__main__':
    #Enter file name, instantiate map and pre-process
    #filename = r'/Users/empire/Academics/UCSC/nasaResearch/californiaNed30m/elevation_NED30M_ca_2925289_01
    # /bayAreaBIL.bil'
    #filename = r'/Users/empire/Academics/UCSC/nasaResearch/californiaNed30m/elevation_NED30M_ca_2925289_01
    # /virtRasterCalifornia.vrt'
    filename = r'/Users/empire/Academics/UCSC/nasaResearch/californiaNed30m/elevation_NED30M_ca_2925289_01_BIL' \
               r'/virtRasterCaliforniaBil.bil'
    map = Map(filename)
    map.process_file()

    #@todo: look at how tigres creates many of the same type of object without having to name all of them
    #Make a quadrotor, initialize position (need to do this in Matlab in RL)
    lon = -122.030796
    lat = 36.974117
    quadrotor = Quadrotor(lat, lon)
    map.add_vehicle(quadrotor)

    #res = map.get_surrounding_elevation(mode='pixel', coords = (map.ncol/2, map.nrow/2), vehicleName=quadrotor.name,
    #  lon_window=20, lat_window=20)
    #res = map.get_surrounding_elevation(mode='pixel', coordinates=Coordinate(6000, 5000), lon_window=10, lat_window=10)
    #print "Surrounding Elevations{}, \nWindow Size of{}".format(res, shape(res))

    print map.get_point_elevation(Coordinate(1000, 1000), mode='pixel')
    #print map.get_elevation_along_segment(coordinate(1000, 1000), (1000, 1500))


    print map.get_elevation_along_segment(Coordinate(36.974117, -122.030796), Coordinate(37.411372, -122.053471))
    mx = -122
    my = 37
    #print map.readRastPix(mx, my)

    #band = a.GetRasterBand(1)
    #imshow(a, interpolation='bilinear',cmap=cm.prism,alpha=1.0)

    #fig = plt.figure(figsize=(10, 10))
    #ax = fig.add_subplot(111)
    #ax.set_title('colorMap')
    #plt.imshow(map.data)
    #ax.set_aspect('equal')

    #cax = fig.add_axes([0.12, 0.1, 0.78, 0.8])
    #cax.get_xaxis().set_visible(False)
    #cax.get_yaxis().set_visible(False)
    #cax.patch.set_alpha(0)
    #cax.set_frame_on(False)
    #plt.colorbar(orientation='vertical')
    #plt.show()
