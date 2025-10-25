from controller import Controller


class OnOffHold(Controller):

    def __init__(self, ts=0.1, r=0.1):
        Controller.__init__(self, ts)
        self.r = r
        self._parity = 0

    def calculate_action(self, readings, time, control_point=0.7):
        reading = readings[-1]
        if self._parity == 0:
            if reading <= control_point*(1+self.r):
                return 1
            else:
                self._parity = 1
                return 0
        else:
            if reading >= control_point*(1-self.r):
                return 0
            else:
                self._parity = 0
                return 1