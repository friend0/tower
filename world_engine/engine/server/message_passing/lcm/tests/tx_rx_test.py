print("Begin test")

import lcm

from message_passing import subscriber
from message_passing.lcm.publisher import publish_trajectory

print("Publishing Trajectory..")
publish_trajectory()
print("Published")
print("Launching subscription handler")
lc = lcm.LCM()
subscription = lc.subscribe("EXAMPLE", subscriber.my_handler)

try:
    while True:
        publish_trajectory()
        lc.handle()
except KeyboardInterrupt:
    pass


