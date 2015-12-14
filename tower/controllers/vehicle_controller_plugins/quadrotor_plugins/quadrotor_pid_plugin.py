from __future__ import (absolute_import, division, print_function, unicode_literals)

from builtins import *

from tower.controllers import pid


class QuadrotorPID(object):
    """

    The Quadrotor PID plugin is designed to run 'on top of' vehicles with orientation set-point control;
    for example, the stock crazyflie. Given an object of type `Quadrotor,` instantiated with a QuadrotorPID controller,
    a vehicle simply needs to update the controller with the latest state feedback by calling `update`

    """
    def __init__(self, configs=None, *args, **kwargs):
        """

        @todo: accept dictionary of gains to initialize all the controllers' gain terms

        :param ref:
        :param gains:
        :return:

        """
        if configs is None:
            self.configs = \
                {'roll': {'gains': {'p':  15, 'i': .2, 'd':  7, 'set_point': 0}, 'pid_type': pid.PID_RP},
                 'pitch': {'gains': {'p':  15, 'i': .2, 'd':  7, 'set_point': 0}, 'pid_type': pid.PID_RP},
                 'yaw': {'gains': {'p':  5, 'i': 0, 'd':  0, 'set_point': 0}, 'pid_type': pid.PID_RP},
                 'position': {'gains': {'p':  1, 'i':  0, 'd':  0, 'set_point': 0}, 'pid_type': pid.PID_RP},
                 'velocity': {'gains': {'p':  .4, 'i':  1e-10, 'd':  1e-8, 'set_point': 0}, 'pid_type': pid.PID_V}
                 }
        else:
            self.configs = configs

        self.controllers = {'roll': None, 'pitch': None, 'yaw': None, 'position': None, 'velocity': None}

        #for controller in self.controllers:
            #print(self.configs[controller]['pid_type'])
            #print((self.configs[controller]['gains']))
            #print(self.configs[controller]['pid_type'](**self.configs[controller]['gains']))

        self.controllers = {controller: self.configs[controller]['pid_type'](**self.configs[controller]['gains']) for
                            controller in self.controllers}

        self.controllers = dict((controller, self.configs[controller]['pid_type'](**self.configs[controller]['gains']))
                                for controller in self.controllers)

    def __str__(self):
        controllers = str()
        controllers = list(self.configs.keys())
        final = ["Controller:\t{}:\n Gains:\t{} \n PID Type:\t{}".format(controller, self.configs[controller]['gains'],
                 self.configs[controller]['pid_type']) for controller in controllers]

        output = str()
        for elem in final:
            output += str(elem + '\n')
        return str("QuadrotorPID plugin with gains:\n" + output)

    def update(self, state):
        """

        Update all the PID controllers with new state feedback. Each vehicle updates it's controller with its
        new state, then returns a new control command.

        :param state: A dict of states, specified by controller, i.e. {'roll': roll_state (x), ...}
        :return: A dict of output values, i.e {'roll': roll_ctrl_output, ...}

        """
        # return {PID: self.controllers[PID].update(state) for PID in self.controllers}
        return dict((PID, self.controllers[PID].update(state)) for PID in self.controllers)


if __name__ == '__main__':

    cf_controller = QuadrotorPID()
    while 1:
        print(cf_controller.update(4))
