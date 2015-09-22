#
#   Weather update client
#   Connects SUB socket to tcp://localhost:5556
#   Collects weather updates and finds avg temp in zipcode
#

import time
import zmq

#  Socket to talk to server
context = zmq.Context()
socket = context.socket(zmq.SUB)

print("Collecting updates from QGIS...")
socket.connect("tcp://127.0.0.1:5555")

socket.setsockopt(zmq.SUBSCRIBE, '')

total_temp = 0
for update_nbr in range(5):
    string = socket.recv_string()
    print string

