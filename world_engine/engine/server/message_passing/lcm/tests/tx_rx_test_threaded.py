"""
This test is broken at the moment. Make it simpler
"""

print("Begin test")

import lcm
import threading

from message_passing import subscriber
from message_passing.lcm.publisher import publish_trajectory

print("Publishing Trajectory..")
publish_trajectory()
print("Published")
print("Launching subscription handler")
lc = lcm.LCM()

subscription = subscriber.subscriber

#subscription = lc.subscribe("EXAMPLE", subscriber.my_handler)

sets = [publish_trajectory, subscription]
args = {'publish_trajectory': {'kwargs': None}, 'subscriber': {'channel': "Example", 'data': subscriber.subscriber} }
threads = []

threads = []

class MyThreadWithArgs(threading.Thread):

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        threading.Thread.__init__(self, group=group, target=target, name=name,
                                  verbose=verbose)
        self.target = target
        self.kwargs = kwargs
        return

    def run(self):
        self.target(**self.kwargs)
        #print('running with {} and {}').format(self.target, self.kwargs)
        return

try:
    while len(threads) < 2:
        for member in sets:
            t = MyThreadWithArgs(target=member, kwargs=args[member.__name__])
            threads.append(t)
            t.start()
except KeyboardInterrupt:
    pass


