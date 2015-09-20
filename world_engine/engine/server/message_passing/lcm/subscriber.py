"""
LCM subscriber class
"""
import message_passing.lcm
from exlcm import trajectory_t

#class Subscriber(object):
#    pass

def subscriber(channel=None, data=None, **kwargs):
    if bool(channel) ^ bool(data):
        #@todo: raise an exception, improper args input
        #raise BaseException
        pass
    if (channel, data) is (None, None):
        channel = kwargs.get('channel', None)
        data = kwargs.get('data', None)
    if (channel, data) is (None, None):
        #@todo: raise an exception, key error
        #raise BaseException
        pass

    print "Channel:{}, Data:{}".format(channel, data)
    msg = trajectory_t.decode(data)
    print("Received message on channel \"%s\"" % channel)
    print("   timestamp   = %s" % str(msg.timestamp))
    print("   position    = %s" % str(msg.position))
    print("   orientation = %s" % str(msg.orientation))
    print("   ranges: %s" % str(msg.ranges))
    print("   vehicle_name        = '%s'" % msg.vehicle_name)
    print("   enabled     = %s" % str(msg.enabled))
    print("")

def my_handler(channel, data):
    print "Channel:{}, Data:{}".format(channel, data)
    msg = trajectory_t.decode(data)
    print("Received message on channel \"%s\"" % channel)
    print("   timestamp   = %s" % str(msg.timestamp))
    print("   position    = %s" % str(msg.position))
    print("   orientation = %s" % str(msg.orientation))
    print("   num waypoints: %s" % str(msg.num_waypoints))
    print("   vehicle_name        = '%s'" % msg.vehicle_name)
    print("   enabled     = %s" % str(msg.enabled))
    print("")

lc = message_passing.lcm.LCM()
subscription = lc.subscribe("EXAMPLE", my_handler)

try:
    while True:
        lc.handle()
except KeyboardInterrupt:
    pass
