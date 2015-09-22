import zmq
import msgpack

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://127.0.0.1:5555")

# x, y, z, pitch, yaw, roll
while True:
    msg = socket.recv()
    print "Got", msgpack.unpackb(msg)
    socket.send(msg)
