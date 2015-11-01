from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import next
import csv
from itertools import cycle
from time import strftime

import requests

from utils.utils import Interrupt

data_loop = [
    {'flightId': '00428', 'time': strftime("%Y-%m-%d %H:%M:%S"), 'latitude': 37.001170, 'longitude': -122.063043,
     'altitude': 300, 'speed': 8.3,
     'heading': 0, 'hasLanded': False, 'dataSource': "UCSC"},
    {'flightId': '00428', 'time': strftime("%Y-%m-%d %H:%M:%S"), 'latitude': 37.000868, 'longitude': -122.063808,
     'altitude': 300, 'speed': 8.3,
     'heading': 0, 'hasLanded': False, 'dataSource': "UCSC"},
    {'flightId': '00428', 'time': strftime("%Y-%m-%d %H:%M:%S"), 'latitude': 37.000752, 'longitude': -122.062966,
     'altitude': 300, 'speed': 8.3,
     'heading': 0, 'hasLanded': False, 'dataSource': "UCSC"}
]
trajectory = cycle(data_loop)


def web_post(path=None, url=None, data=None, headers=None):
    coord = next(path)
    payload = {'flightId': '00428', 'time': strftime("%Y-%m-%d %H:%M:%S"), 'latitude': 37.001170,
               'longitude': -122.063043,
               'altitude': 3000, 'speed': 48.27, 'heading': 0, 'hasLanded': False, 'dataSource': "UCSC"}
    time_stamp = strftime("%Y-%m-%d %H:%M:%S")
    payload['time'] = time_stamp
    payload['latitude'] = coord[0]
    payload['longitude'] = coord[1]
    r = requests.put("http://nasaforwarding.appspot.com/nasaforwarding/default/api/vehicles/5654313976201216.json",
                     data=payload)
    print(r)
    # @todo: return should interpret http code and decide what to return at that point
    return r


if __name__ == '__main__':

    # Read in CSV, make it into a cycle
    f = open('/Users/empire/Documents/GitHub/world_engine/world_engine/recon.csv')
    csv_f = csv.reader(f)

    coords = []
    trajectory = [row for row in csv_f]

    """
    for coordinate_pair in trajectory[1:]:
        for coord in reversed(coordinate_pair):
            coords.append(coord)
            float(coord)


    json_path = json.dumps(coords)
    print json_path
    """

    path = cycle(trajectory[1:])

    rt = Interrupt(5, web_post, path=path, url=None, data=None, headers=None)  # it auto-starts, no need of rt.start()
    while 1:
        pass
