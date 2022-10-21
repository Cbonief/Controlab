global Controller
global AuxiliaryDictionary


class OnOff(Controller):

    def __init__(self, sampling_rate=0.1):
        Controller.__init__(self, sampling_rate)

    @staticmethod
    def calculate_action(readings, time, control_point=0.7):
        if readings[-1] > control_point:
            return 0
        else:
            return 1


AuxiliaryDictionary['class'] = OnOff
