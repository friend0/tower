"""
Remote client for connecting to v-rep objects
"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from math import pi, sin
import time

from builtins import next
from past.utils import old_div
import numpy as np

from . import vrep



# Connection parameters
IPADDRESS = '127.0.0.1'
PORT = 20011
WAIT_UNTIL_CONNECTED = True
DO_NOT_RECONNECT_ONCE_DISCONNECTED = True
TIME_OUT_IN_MSEC = 5000
COMM_THREAD_CYCLE_IN_MS = 1

# Load the V-REP remote API
vrep.simxFinish(-1);  # just in case, close all opened connections

# Start the simulation on the server
clientID = vrep.simxStart(IPADDRESS, PORT, WAIT_UNTIL_CONNECTED, DO_NOT_RECONNECT_ONCE_DISCONNECTED,
                          TIME_OUT_IN_MSEC, COMM_THREAD_CYCLE_IN_MS);
print ('Program started')
if clientID != -1:
    print ('Connected to remote API server')

    # Now try to retrieve data in a blocking fashion (i.e. a service call):
    res, objs = vrep.simxGetObjects(clientID, vrep.sim_handle_all, vrep.simx_opmode_oneshot_wait)

    if res == vrep.simx_return_ok:
        print(('Number of objects in the scene: ', len(objs)))
    else:
        print(('Remote API function call returned with error code: ', res))

    res, targetObj = vrep.simxGetObjectHandle(clientID, 'Quadricopter_target', vrep.simx_opmode_oneshot_wait)
    print(('targetObj', targetObj))
    if res == vrep.simx_return_ok:
        print(('Number of objects in the scene: ', len(objs)))
    else:
        print(('Remote API function call returned with error code: ', res))

    time.sleep(2)
    # Now retrieve streaming data (i.e. in a non-blocking fashion):
    startTime = time.time()
    vrep.simxGetIntegerParameter(clientID, vrep.sim_intparam_mouse_x,
                                 vrep.simx_opmode_streaming)  # Initialize streaming

    # prop1Handle = vrep.simxGetObjectHandle(clientID, 'Quadricopter_propeller1', vrep.simx_opmode_oneshot)
    # prop2Handle = vrep.simxGetObjectHandle(clientID, 'Quadricopter_propeller2', vrep.simx_opmode_oneshot)
    # prop3Handle = vrep.simxGetObjectHandle(clientID, 'Quadricopter_propeller3', vrep.simx_opmode_oneshot)
    # prop4Handle = vrep.simxGetObjectHandle(clientID, 'Quadricopter_propeller4', vrep.simx_opmode_oneshot)

    # propellerRespondable1 = vrep.simxGetObjectHandle(clientID, 'Quadricopter_propeller_respondable1',
    # vrep.simx_opmode_oneshot)
    # propellerRespondable2 = vrep.simxGetObjectHandle(clientID, 'Quadricopter_propeller_respondable2',
    # vrep.simx_opmode_oneshot)
    # propellerRespondable3 = vrep.simxGetObjectHandle(clientID, 'Quadricopter_propeller_respondable3',
    # vrep.simx_opmode_oneshot)
    # propellerRespondable4 = vrep.simxGetObjectHandle(clientID, 'Quadricopter_propeller_respondable4',
    # vrep.simx_opmode_oneshot)

    sins = [sin(time) for time in np.linspace(0, old_div(pi, 2), 1000)]

    while time.time() - startTime < 5:
        err, robotPosition = vrep.simxGetObjectPosition(clientID, targetObj, -1, vrep.simx_opmode_oneshot_wait)
        print(('robotPosition: ', robotPosition))
        # robotPosition(1) += robotPosition(1) + .01;
        # robotPosition(2) += robotPosition(2) + .01;
        robotPosition[2] += .001 * next(sins);
        vrep.simxSetObjectPosition(clientID, targetObj, -1, robotPosition, vrep.simx_opmode_oneshot)


    # Now send some data to V-REP in a non-blocking fashion:
    vrep.simxAddStatusbarMessage(clientID, 'Hello V-REP!', vrep.simx_opmode_oneshot)

    # Before closing the connection to V-REP, make sure that the last command sent out had time to arrive.
    # You can guarantee this with (for example):
    vrep.simxGetPingTime(clientID)

    # Now close the connection to V-REP:
    vrep.simxFinish(clientID)
