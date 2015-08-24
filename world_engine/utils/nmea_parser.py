"""
Credit to a1ronzo/gps_tracker
"""
__author__ = 'empire'

import shutil

from pynmea import nmea
import matplotlib.pyplot as plt



######Global Variables#####################################################
# you must declare the variables as 'global' in the fxn before using#
filename = '../gpsDataBaskin_7_29_1538.txt'
ser = 0
lat = 0
lon = 0
pos_x = 0
pos_y = 0
alt = 0
i = 0 #x units for altitude measurment


#adjust these values based on your location and map, lat and long are in decimal degrees
TRX = -121.37455190525216          #top right longitude
TRY = 37.33752903098212           #top right latitude
BLX = -122.54056801878919          #bottom left longitude
BLY = 36.227194983437194            #bottom left latitude
BAUDRATE = 4800
lat_input = 0            #latitude of home marker
long_input = 0           #longitude of home marker


def position():
    #opens a the saved txt file, parses for lat and long, displays on map
    global lat, lon, lat_input, long_input, pos_x, pos_y, altitude
    global BLX, BLY, TRX, TRY

    #same process here as in altitude
    f1 = open('temp.txt', 'w')
    f1.truncate()
    shutil.copyfile(filename, 'temp.txt')
    f1.close()

    f1 = open('temp.txt', 'r') #open and read only
    try:
        for line in f1:
            if line[4] == 'G': # $GPGGA
                if len(line) > 50:
                    #print line
                    gpgga = nmea.GPGGA()
                    gpgga.parse(line)
                    lats = gpgga.latitude
                    longs = gpgga.longitude
                    #convert degrees,decimal minutes to decimal degrees
                    lat1 = (float(lats[2] + lats[3] + lats[4] + lats[5] + lats[6] + lats[7] + lats[8])) / 60
                    lat = (float(lats[0] + lats[1]) + lat1)
                    long1 = (float(longs[3] + longs[4] + longs[5] + longs[6] + longs[7] + longs[8] + longs[9])) / 60
                    lon = (float(longs[0] + longs[1] + longs[2]) + long1)

                    #calc position
                    pos_y = lat
                    pos_x = -lon #longitude is negaitve

                    #plot the x and y positions
                    plt.scatter(x=[pos_x], y=[pos_y], s=5, c='r')

                    #shows that we are reading through this loop
                    print pos_x
                    print pos_y
    finally:
        f1.close()

    #now plot the data on a graph
    #plt.scatter(x=[long_input], y=[lat_input], s = 45, c='b') #sets your home position
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('POSITION (in Decimal Degrees)')

    #lay the image under the graph
    #read a png file to map on
    im = plt.imread('../scClipProjected.tif')
    implot = plt.imshow(im, extent=[BLX, TRX, BLY, TRY])

    plt.show()


if __name__ == "__main__":
    position()
