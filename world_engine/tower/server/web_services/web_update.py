from __future__ import print_function
from time import strftime

from builtins import next
import requests

from server_conf.config import settings
from world_engine.utils.utils import cycle

""" @todo: need to get this idea into a structure called 'trajectory', make methods to iterate over it.
In the future, this can be used to link simulation data to the web service/Ames """

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


def web_post(url=None, data=None, headers=None):
    time_stamp = strftime("%Y-%m-%d %H:%M:%S")
    payload = next(trajectory)
    payload['time'] = time_stamp
    r = requests.put("http://nasaforwarding.appspot.com/nasaforwarding/default/api/vehicles/5654313976201216.json",
                     data=payload)
    print(r)
    # @todo: return should interpret http code and decide what to return at that point
    return r


def call_request(url=None, data=None, headers=None):
    url = 'http://httpbin.org/post'
    headers = {'content-type': 'application/json'}
    time_stamp = strftime("%Y-%m-%d %H:%M:%S")
    data = {'flightId': 0o001, 'time': time_stamp, 'latitude': 36, 'longitude': -120, 'altitude': 50, 'speed': 100,
            'heading': 0, 'hasLanded': False, 'dataSource': "UCSC"}
    r = requests.post(url, json=data, headers=headers)
    print(r.status_code)


def post_vehicle(data):
    url_base = settings['WEB_REST_API']
    headers = {'content-type': 'application/json'}
    time_stamp = strftime("%Y-%m-%d %H:%M:%S")
    data = {'status': 'idle', 'flightId': '00428', 'hasLanded': 'True', 'altitude': 250.0, 'longitude': 37.1,
            'heading': 0.0, 'dataSource': 'UCSC', 'latitude': -122.0, 'speed': 0.0, 'id': 5654313976201216}
    r = requests.post(url_base + '/vehicles', json=data, headers=headers)
    print(r.status_code)
