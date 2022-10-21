global Controller
global AuxiliaryDictionary


class OnOffHold(Controller):

    def __init__(self, sampling_rate=0.1):
        Controller.__init__(self, sampling_rate)
        self._parity = 0

    def calculate_action(self, readings, time, control_point=0.7):
        radius = 0.05
        reading = readings[-1]
        if self._parity == 0:
            if reading <= control_point*(1+radius):
                return 1
            else:
                self._parity = 1
                return 0
        else:
            if reading >= control_point*(1-radius):
                return 0
            else:
                self._parity = 0
                return 1


AuxiliaryDictionary['class'] = OnOffHold
