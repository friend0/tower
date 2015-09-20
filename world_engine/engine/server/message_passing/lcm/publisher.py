"""
The publisher module sits on top of LCM the Lightweight Communication and Marshaling library developed at MIT
The message types defined in the file 'types' serve as base template structures which are abstracted and automatically
marshalled so that we can pass data of any type we'd like and not have to worry about reconstructing it ourselves
"""
import message_passing.lcm
from exlcm import trajectory_t

def publish_trajectory():
    msg = trajectory_t()
    msg.timestamp = 0
    msg.position = (1, 2, 3)
    msg.orientation = (1, 0, 0, 0)
    msg.num_waypoints = 15
    msg.waypoints = range(msg.num_waypoints)
    msg.vehicle_name = str("Quadrotor")
    msg.enabled = True
    lc = message_passing.lcm.LCM()
    lc.publish("EXAMPLE", msg.encode())

while 1:
    publish_trajectory()

