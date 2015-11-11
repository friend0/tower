from __future__ import print_function
import zmq
import msgpack

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://127.0.0.1:5555")

# x, y, z, pitch, yaw, roll
if __name__ == '__main__':
    while True:
        msg = socket.recv()
        print("Got", msgpack.unpackb(msg))
        socket.send(msg)
