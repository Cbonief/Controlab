from controller import Controller


class PID(Controller):

    def __init__(self, ts=0.1, Kp=8, Ki=0, Kv=0):
        Controller.__init__(self, ts)
        self.Kp = Kp
        self.Ki = Ki
        self.Kv = Kv
        self._error = 0
        self._integral_error = 0

    def calculate_action(self, readings, time, control_point=0.7):
        reading = readings[-1]
        last_error = self._error
        self._error = (control_point - reading)
        self._integral_error += self._error * self.ts
        error_derivative = (self._error - last_error) / self.ts
        control_action = max(self.Kp * self._error + error_derivative * self.Kv + self._integral_error * self.Ki, 0)
        return min(1, control_action)
