"""
Class for communicating with the cf_client over ZMQ. Currently broken.
"""
import time

try:
    import zmq
except ImportError as e:
    raise Exception("ZMQ library probably not installed ({})".format(e))


class ZMQ_Communicator(object):

    def __init__(self, context):
        context = context
        sender = context.socket(zmq.PUSH)
        bind_addr = "tcp://127.0.0.1:{}".format(1024 + 188)
        self.sender.connect(bind_addr)

        self.cmd_msg = {
            "version": 1,
            "ctrl": {
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 0.0,
                "thrust": 0
            }
        }
        print 'unlocking'
        self.cmd_msg["ctrl"]["thrust"] = 0
        self.sender.send_json(self.cmd_msg)

    def unlock(self):
        if self.unlocked:
            pass
        else:
            print 'unlocking'
            self.cmd_msg["ctrl"]["thrust"] = 0
            self.sender.send_json(self.cmd_msg)

    def update(self, cmd_msg):
        print("starting to send control commands!")

        # Unlocking thrust protection
        self.sender.send_json(self.cmd_msg)

