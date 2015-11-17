#
#   Weather update server
#   Binds PUB socket to tcp://*:5556
#   Publishes random weather updates
#

from random import randrange
import time
import zmq

if __name__ == '__main__':

    context = zmq.Context()
    socket = context.socket(zmq.PUB)

    socket.bind("tcp://*:5683")
    time.sleep(.5)

    while True:
        zipcode = randrange(1, 100000)
        temperature = randrange(-80, 135)
        relhumidity = randrange(10, 60)

        socket.send_string("%i %i %i" % (zipcode, temperature, relhumidity))
