'''
WildBil, Binary Interleaved by Line (BIL) Utility
Simple wrapper functions for GDAL
'''
__author__ = 'Ryan A. Rodriguez'

import rasterio
from osgeo import gdal
import gdal
import  gdalconst
import numpy as np
import matplotlib.pyplot as plt
import struct
import scipy.io
from pylab import *
from collections import namedtuple

class BilFile(object):

    def __init__(self, bil_file):
        self.bil_file = bil_file
        self.hdr_file = bil_file.split('.')[0]+'.hdr'

    def get_array(self, mask=None):
        '''
        Deprecate this function
        '''
        gdal.GetDriverByName('EHdr').Register()
        img = gdal.Open(self.bil_file, gdalconst.GA_ReadOnly)
        band = img.GetRasterBand(1)
        geotransform = img.GetGeoTransform()

        self.nodatavalue, self.data = None, None
        self.nodatavalue = band.GetNoDataValue()
        self.ncol = img.RasterXSize
        self.nrow = img.RasterYSize
        self.rotation = geotransform[2]     #rotation, 0 if image is 'north-up'
        self.originX = geotransform[0]      #top-left x
        self.originY = geotransform[3]      #top-left y
        self.pixelWidth = geotransform[1]   #w/e pixel resoluton
        self.pixelHeight = geotransform[5]  #n/s pixel resolution

        self.data = band.ReadAsArray()      #I don't think we ever want to do this at scale, will try to read in entire file as array

        print(type(self.data))
        #self.data = np.ma.masked_where(self.data == self.nodatavalue, self.data)
        #If data value is less than zero, saturate to zero
        self.data = np.ma.masked_where(self.data < 0, self.data)

        if mask is not None:
            self.data = np.ma.masked_where(mask == True, self.data)
        return self.nodatavalue, self.data

    def open_bil_file(self):
        '''
        Reads in whole bil file, gets info
        '''
        #gdal.GetDriverByName('EHdr').Register()

        #If the file is not a bil, maybe try to convert it with rasterio first
        try:
            self.img = rasterio.open(self.bil_file)
                #band = rasterio.band(src, 1)
                #w = self.src.read(1, window=((0, 100), (0, 100)))
            #print "src", self.src.meta

            gdal.GetDriverByName('EHdr').Register()
            #self.img = gdal.Open(self.bil_file)
            #self.band = self.img.GetRasterBand(1)
        except IOError:
                print 'Bil file {} is not found, or gdal could not read it'.format(self.bil_file)


    def read_bil_file(self):
        '''
        Reads in whole bil file
        '''
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

            self.data = self.img.read(1)      #I don't think we ever want to do this at scale, will try to read in entire file as array
            self.data = np.ma.masked_where(self.data < 0, self.data)
        except IOError:
            print '.bil file {} is not found, or gdal could not read it'.format(self.bil_file)

    def process_bil_file(self, mask=None):
        '''
        Open and read in bil file as array
        results are stored in 'data' member, and all other parameters are found, read, and or updated
        '''
        self.open_bil_file()
        self.read_bil_file()

        if mask is not None:
            self.data = np.ma.masked_where(mask, self.data)


class Map(BilFile):

    def __init__(self, filename):
        self.fileName = filename
        BilFile.__init__(self, filename)

    def readRastPix(self, mx, my):
        '''
        Retrieve an elevation value for a single point given coordinate input
        '''

        rast = self.fileName
        val = 0
        src_ds = gdal.Open(rast)
        gt = src_ds.GetGeoTransform()
        print gt
        rb = src_ds.GetRasterBand(1)
        gdal.UseExceptions() #so it doesn't print to screen everytime point is outside grid
        # Convert from map to pixel coordinates.

        px = int((mx - gt[0]) / gt[1]) #x pixel
        py = int((my - gt[3]) / gt[5]) #y pixel

        print "Px:{}, Py:{}".format(px, py)
        try: #in case raster isnt full extent
            structval = self.band.ReadRaster(px, py, 1, 1, buf_type=gdal.GDT_Float32) #Assumes 32 bit int aka 'float'
            intval = struct.unpack('f', structval)
            #had to add 0.0000... so that it wouldn't truncate to integer and fail with constraint error my database
            val = intval[0]
            if intval[0] < -9999:
                val = -9999
        except:
           pass
        src_ds = None
        return(val)

class Vicinity(Map):

    def __init__(self, filename):
        Map.__init__(self, filename)
        self.adjacentElevations = np.zeros((3, 3))
        self.RastStart = namedtuple("RastStart", ['x', 'y'], verbose=False)
        self.RastStart.x, self.RastStart.y = None, None

    def getVicinity(self, mx, my, north_pixels, east_pixels):
        '''
        @todo Need to figure out how to read just a section of the file at a time
        '''
        val = 0

        eastBoundary = self.originX + self.ncol
        westBoundary = self.originX
        northBoundary = self.originY
        southBoundary = self.originY + self.nrow

        #px = int((self.originX - self.originX) / self.pixelWidth)     #x pixel
        #py = int((self.originY - self.originY) / self.pixelHeight)    #y pixel

        self.RastStart.x = self.ncol/2
        self.RastStart.y = self.nrow/2

        print self.RastStart.x, self.RastStart.y

        try: #in case raster isnt full extent
            arr = []
            w = self.img.read(1, window=((0, 100), (0, 100)))
            #structval = self.band.ReadRaster(0, 0, 5, 5, 5, 5) #Assumes 32 bit int aka 'float'
            #structval = self.band.ReadRaster(self.RastStart.x, self.RastStart.y, self.ncols, self.nrows, buf_type=gdal.GDT_Float32) #Assumes 32 bit int aka 'float'
            #intval = struct.unpack('f', structval)
            print  "some intval shit", w, type(w)
            #had to add 0.0000... so that it wouldn't truncate to integer and fail with constraint error my database
            if w[0] < -9999:
                val = -9999
        except:
            print "exception"
            pass

        return val

    def planPath(self, startCoord, endCoords, **kwargs):
        '''
        @todo From start coordinates to end coordinates, sample elevation. Determine Path
        optional args will determine how the path is optimized
        '''
        pass

if __name__ == '__main__':

    filename = r'/Users/empire/Academics/UCSC/nasaResearch/californiaNed30m/elevation_NED30M_ca_2925289_01/bayAreaBIL.bil'

    vic = Vicinity(filename)
    #vic.ReadBilFileAsArray(filename)
    vic.process_bil_file()
    print vic.originX, vic.originY, vic.ncol, vic.nrow
    print vic.originX+vic.ncol, vic.originY+vic.nrow
    print vic.originX+vic.ncol/2, vic.originY+vic.nrow/2

    res = vic.getVicinity(vic.originX+vic.ncol/2, vic.originY+vic.nrow/2, 3, 3)
    print res, type(res)

    rast = filename
    mx = -122.07884
    my = 36.98056
    print vic.readRastPix(mx, my)
    mx = -122.10884
    my = 36.98056
    print vic.readRastPix(mx, my)

    vic.get_array(0)
    print(type(vic.data))

    #mat_a = matlab.double(np_a.tolist())
    #scipy.io.savemat('test.mat', dict(x=x, y=y))

    #a = ReadBilFile(filename)
    (height, width) = (vic.ncol, vic.nrow)

    #band = a.GetRasterBand(1)
    #imshow(a, interpolation='bilinear',cmap=cm.prism,alpha=1.0)

    fig = plt.figure(figsize=(10, 10))

    print('here!')

    ax = fig.add_subplot(111)
    ax.set_title('colorMap')
    plt.imshow(vic.data)
    ax.set_aspect('equal')

    print('see?')

    cax = fig.add_axes([0.12, 0.1, 0.78, 0.8])
    cax.get_xaxis().set_visible(False)
    cax.get_yaxis().set_visible(False)
    cax.patch.set_alpha(0)
    cax.set_frame_on(False)
    plt.colorbar(orientation='vertical')
    plt.show()
