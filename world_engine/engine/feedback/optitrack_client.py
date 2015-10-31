"""

The optitrack client

"""
from __future__ import print_function
import optirx as rx
import sys
from Quaternion import Quat

try:
    from simplejson import dumps, encoder

    encoder.FLOAT_REPR = lambda o: ("%.4f" % o)
except ImportError:
    from json import dumps, encoder

    encoder.FLOAT_REPR = lambda o: ("%.4f" % o)
import time

RIGID_BODIES = 3


class OptitrackClient(Exception):
    pass


class OptitrackProcessor(object):
    def __init__(self, ip_address='204.102.224.2', version=None):
        self.dsock = rx.mkdatasock(ip_address)
        if version is None:
            version = (2, 7, 0, 0)  # the latest SDK version
        self.version = version
        pass

    def recv_data(self, mode='Euler', rigid_body_ids=None):
        """
        This function retrieves packets from the NatNet stream originating from Motive, the stream server
        for the optitrack motion capture server.

        :return: position and orientation, where position is in [x, y, z] in meters and orientation is given
        by the rigid body's Euler angles, or optionally, a rotation from the world to body frames via quaternion
        """

        def process_state(body, mode):
            location = body['position']
            if mode is 'quaternion':
                orientation = [elem for elem in body['orientation']]
            else:
                orientation = Quat([elem for elem in body['orientation']]).equatorial  # Euler Angles
            return list(location), (orientation).tolist()

        # the second optional command line argument
        # is the version string of the NatNet server;
        # may be necessary to receive data without
        # the initial SenderData packet

        data = self.dsock.recv(rx.MAX_PACKETSIZE)
        packet = rx.unpack(data, version=self.version)

        if type(packet) in [rx.SenderData, rx.ModelDefs, rx.FrameOfData]:
            all_bodies = packet[RIGID_BODIES]  # elem 3 contains info on all rigid bodies

            output = {}
            for body in all_bodies:
                body = body._asdict()
                if rigid_body_ids is not None:  # check if we care about this rigid body
                    if body['id'] in rigid_body_ids:
                        location, orientation = process_state(body, mode)
                    else:
                        continue
                else:
                    location, orientation = process_state(body, mode)
                output[str(body['id'])] = {'location': location, 'orientation': orientation}
            # time.sleep(.5)
            return location, orientation

    def close(self):
        self.dsock.close()
