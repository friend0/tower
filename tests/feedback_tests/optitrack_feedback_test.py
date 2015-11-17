"""

This file is used to listen to UDP packets multicast from the Motive server.
Right now there we set up a ZMQ.REQ connection to communicate between the Windows machine running Motive,
and the OSX machine running the controllers.

With proper UDP multicasting over the network, this scipt can be made to pass feedback to controllers directly.

"""
import zmq
import msgpack

from tower.controllers.feedback.optitrack import Optitrack as optitrack

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect('tcp://204.102.224.3:5000')

processor = optitrack()

while (1):
    # todo: need to fix multicast and get this running directly instead of being forwarded from Windows
    position, orientation = processor.recv_data(rigid_body_ids=[1])
    socket.send(msgpack.packb(position + orientation))  # Used to comm optitrack fdbk from second computer
    msg_in = socket.recv()  # Ack packet recv
