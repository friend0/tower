#!/usr/bin/python
import os
"""

Configuration file for the socket server; contains information about location of database, Host, Port, and etc.
Settings are contained in a dictionary named 'settings', currently holding the following information:

    - Fileconfig
        - filename
    - Host
    - Port

Example:

An minimal `settings` dictionary::


        settings = {

        'FILE_CONFIG':
            {'filename':
                 r'/Users/empire/Academics/UCSC/nasaResearch/californiaNed30m/elevation_NED30M_ca_2925289_01/' \
                 r'virtRasterCalifornia.vrt'},

        'HOST': 'localhost',
        'PORT': 2002

        }

"""
settings = {

    'FILE_CONFIG':
        {'filename':
             os.path.abspath("world_engine/tests/map_tests/bayArea.tif")},

    'HOST': 'localhost',
    'PORT': 2002,
    'WEB_REST_API': 'http://nasaforwarding.appspot.com/nasaforwarding/default/api',
    'MAP_PORT': 5555,
    'MODEL_PORT': 5555 + 256
}
