import time
import zmq

context = zmq.Context()
socket = context.socket(zmq.REP)

QGIS_INTERFACE_SOCKET = 5555
socket.bind("tcp://*:{}".format(QGIS_INTERFACE_SOCKET))  # which socket to choose?

while True:
    #  Wait for next request from client
    message = socket.recv()
    print("Received request: %s" % message)

    #  Do some 'work', i.e. figure out who sent the message, what it is
    # A simple way to do this might be to alot different sockets for different tasks
    time.sleep(1)

    #  Send reply back to client
    socket.send(b"World")