from __future__ import absolute_import, division, print_function, unicode_literals
import timeit
import functools
import time
import math
from collections import namedtuple

from builtins import str
import pytest

from tower.vehicles.vehicle import Quadrotor
from tower.mapping import Coordinate

coordinate_a = Coordinate(lat=36.974117, lon=-122.030796)
coordinate_b = Coordinate(lat=37.411891, lon=-122.052183)


def timeit(func):
    @functools.wraps(func)
    def newfunc(*args, **kwargs):
        startTime = time.time()
        func(*args, **kwargs)
        elapsedTime = time.time() - startTime
        print('function [{}] finished in {} ms'.format(
            func.__name__, int(elapsedTime * 1000)))

    return newfunc


Coordinate = namedtuple("Coordinate", ['lat', 'lon'], verbose=False)
vehicle = Quadrotor(None, Coordinate(0, 0))


@timeit
def test_speed_conversion():
    for each_unit in list(vehicle.conversion_table.keys()):
        assert vehicle.speed_conversion(1, str(each_unit), str(each_unit)) == 1
        assert vehicle.speed_conversion(0, str(each_unit), str(each_unit)) == 0
    assert vehicle.speed_conversion(-10, 'mph', 'km/h') == 1.609344 * -10
    assert vehicle.speed_conversion(1, 'km/h', 'm/s') == 0.277778


#todo: need to test quadrotor with dynamics class implementred
@timeit
def test_quadrotor_class():
    quadrotor = Quadrotor(None, Coordinate(0, 0))
    with pytest.raises(ValueError):
        quadrotor.coordinates = Coordinate(-91, 0)
    with pytest.raises(ValueError):
        quadrotor.coordinates = Coordinate(0, 181)
    quadrotor.coordinates = coordinate_a
    rate = 100 * quadrotor.conversion_table['km/h']['m/s']  # m/s
    dt = 48621.8048816 / rate
    rocd = 5
    print(quadrotor.coordinates)
    quadrotor.eqn_of_motion(rate, math.degrees(6.24423422267), rocd, dt)
    print(quadrotor.coordinates)
