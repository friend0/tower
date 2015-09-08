from __future__ import print_function
import optirx as rx
import sys
from Quaternion import Quat

def demo_recv_data():
    # pretty-printer for parsed
    try:
        from simplejson import dumps, encoder
        encoder.FLOAT_REPR = lambda o: ("%.4f" % o)
    except ImportError:
        from json import dumps, encoder
        encoder.FLOAT_REPR = lambda o: ("%.4f" % o)

    # the first optional command line argument:
    # if given, the number of packets to dump
    #todo: ought to take args from the stream until instructed to stop
    if sys.argv[1:]:
        max_count = int(sys.argv[1])
    else:
        max_count = float("inf")

    # the second optional command line argument
    # is the version string of the NatNet server;
    # may be necessary to receive data without
    # the initial SenderData packet
    if sys.argv[2:]:
        version = tuple(map(int, sys.argv[2]))
    else:
        version = (2, 7, 0, 0)  # the latest SDK version

    dsock = rx.mkdatasock()
    count = 0
    while count < max_count:
        data = dsock.recv(rx.MAX_PACKETSIZE)
        packet = rx.unpack(data, version=version)
        if type(packet) is rx.SenderData:
            version = packet.natnet_version
            print("NatNet version received:", version)
        if type(packet) in [rx.SenderData, rx.ModelDefs, rx.FrameOfData]:
            packet_dict = packet._asdict()
            all_bodies = packet_dict['rigid_bodies']
            for body in all_bodies:
                contortion = body._asdict()['orientation']
                euler = Quat([elem for elem in contortion]).equatorial
                print(euler)
            #print(dumps(packet._asdict(), indent=4))
        count += 1


if __name__ == "__main__":
    demo_recv_data()
