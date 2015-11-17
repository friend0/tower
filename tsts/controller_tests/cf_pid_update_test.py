from tower.controllers.pid_controller import PID_V

class CrazyflieController(object):

    def __init__(self, ref, gains=None):
        """
        @todo: accept dictionary of gains to initialize all the controllers' gain terms
        :param ref:
        :param gains:
        :return:
        """
        one = PID_V()
        self.reference = ref
        self.pitch_controller = PID_V(p=25, i=0.28, d=7, set_point=10)
        self.roll_controller = PID_V(p=25, i=0.28, d=7, set_point=10)
        self.yaw_controller = PID_V(p=5, i=0.0000001, d=0.35, set_point=10)
        self.thrust_controller = PID_V(p=20, i=5*0.035, d=8*0.035, set_point=10)

        self.position_controller = PID_V(p=.5, i=.28, d=0, set_point=10)
        self.velocity_controller = PID_V(p=.1, i=.28, d=.00315, set_point=10)
        self.controllers = [self.pitch_controller, self.roll_controller, self.yaw_controller, self.thrust_controller]

    def update_controllers(self, state):
        results = [pid.update(state) for pid in self.controllers]
        return results

if __name__ == '__main__':

    cf_controller = CrazyflieController(1)
    while 1:
        print cf_controller.update_controllers(4)