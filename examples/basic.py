import tower
from mock import Mock
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

    # instantiate a Tower
    tower_1 = tower.Tower(mockRegion, mockControlLaw)
    manager = tower.WorkflowManager()
    manager.add_tower(tower_1)
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
            process.join()
        for thread in manager.threads.values():
            print(thread)
            thread.terminate()
    else:
        for ps in manager.processes.values():
            ps.terminate()



    # add vehicles, and a map to tower


