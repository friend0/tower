from mock import Mock

import tower
from tower import QuadrotorPID, Crazyflie


# create the mock object
mockRegion = Mock(name="Region")
# prepare the spec list
fooSpec = ["_fooValue", "source", "doFoo"]

# create the mock object
mockFoo = Mock(spec=fooSpec)

# create the mock object
mockControlLaw = Mock(name="Control")
# prepare the spec list
fooSpec = ["_fooValue", "source", "doFoo"]

# create the mock object
mockFoo = Mock(spec=fooSpec)

KILL_COMMAND = 'DEATH'

if __name__ == '__main__':
    #comment
    manager = tower.WorkflowManager()
    # todo: I don't know if I like this from a user perspective
    # instantiate a Tower
    tower_1 = tower.Tower(mockRegion, mockControlLaw, optitrack_args={'filtering': False})
    # instantiate a Manager

    # Instantiate Vehicles
    crazyflie = Crazyflie(QuadrotorPID(), name='Stringer')
    print(crazyflie.controller)
    # Add Vehicles to the Tower

    # Add Tower to Manager
    manager.add_tower(tower_1)

    # Start all Towers managed by Manager
    for ps in manager.processes.values():
        ps.start()
        print("Started {}".format(ps.name))

    command = raw_input('Server Command: ')
    print("Command was: {}".format(command))
    if command == 'shutdown':
        print("Giving the kill command")
        for process in manager.processes.values():
            print("Killing {}".format(process.name))
            process.results_q.put(KILL_COMMAND)
            print("joining")
            process.join()

        for thread in manager.threads.values():
            print(thread)
            # todo: ask threads to take the poison pill, then join
            #thread.kill()
    else:
        for ps in manager.processes.values():
            ps.terminate()



    # add vehicles, and a map to tower


