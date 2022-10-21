import numpy as np

from dataclasses import dataclass
from abc import ABC, abstractmethod

from pathlib import Path


def runge_kutta(derivative_function, yn, dt):
    weights = [2, 2, 1]
    k = derivative_function(yn)
    yn_1 = k
    for i in range(3):
        k = derivative_function(yn + dt * k / weights[i])
        yn_1 += k * weights[i]
    yn_1 *= dt / 6
    yn_1 += yn
    return yn_1


@dataclass(frozen=True)
class SimulationResults:
    time: np.array
    height: np.array
    error: np.array
    action: np.array


class Controller(ABC):

    def __init__(self, sampling_rate=0.1):
        self.sampling_rate = sampling_rate

    @abstractmethod
    def calculate_action(self, readings, time, control_point):
        pass


def get_custom_controllers():
    custom_controllers = []
    for file_path in Path("Custom Controllers/").glob('**/*.py'):
        AuxiliaryDictionary = {
            'class': Controller
        }
        str_path = str(file_path)
        name = str_path.split('\\')[1]
        file = open(str_path, "r")
        custom_code = file.read()
        file.close()

        exec(custom_code, {'Controller': Controller, 'AuxiliaryDictionary': AuxiliaryDictionary})
        editable_variables = {}
        variables = vars(AuxiliaryDictionary['class']())
        for var in variables:
            if var.find('_') != 0:
                editable_variables[var] = variables[var]
        print(editable_variables)
        custom_controllers.append({
            'name': AuxiliaryDictionary['class'].__name__,
            'code': custom_code,
            'class': AuxiliaryDictionary['class']
        })
    return custom_controllers


class DiscretePIDController(Controller):

    def __init__(self, sampling_rate=0.1, Kp=8, Ki=0, Kv=0):
        Controller.__init__(self, sampling_rate)
        self.Kp = Kp
        self.Ki = Ki
        self.Kv = Kv
        self._error = 0
        self._integral_error = 0

    def calculate_action(self, readings, time, control_point=0.7):
        reading = readings[-1]
        last_error = self._error
        self._error = (control_point - reading)
        self._integral_error += self._error * self.sampling_rate
        error_derivative = (self._error - last_error) / self.sampling_rate
        control_action = max(self.Kp * self._error + error_derivative * self.Kv + self._integral_error * self.Ki, 0)
        return min(1, control_action)


class WaterTank:
    g = 9.81

    def __init__(self, max_height=1, tank_area=0.09, tank_escape_area=0.001 * np.pi, incoming_max_velocity=20,
                 input_area=0.0004 * np.pi):
        self.h_max = max_height
        self.k1 = np.sqrt(2 * self.g) * tank_escape_area / tank_area
        self.k2 = incoming_max_velocity * input_area / tank_area

        self.simulation_results = None

    def dy_dt(self, height, action):
        return self.k2 * action - self.k1 * np.sqrt(height)

    def simulate(self, total_time=10, dt=0.001, h0=0, controller=None, control_point=0.7,
                 onFinished=None, args=None,
                 progressCallback=None, callbackArgs=None,
                 returnValues=False
                 ):

        elapsed_time = 0

        if controller is None:
            controller = DiscretePIDController(0.1, 8, 1, 2)

        # Control Variables
        control_action = 0
        control_timer = 0

        last_percentage = 0

        nit = int(np.ceil(total_time / dt))
        time = np.zeros(nit)
        error = np.zeros(nit)
        action = np.zeros(nit)
        elapsed_time_string = [''] * nit

        current_height = h0
        height = np.zeros(nit)
        height[0] = h0
        error[0] = control_point - current_height
        elapsed_time_string[0] = '0:00'

        for i in range(1, nit):
            current_height = runge_kutta(lambda x: self.dy_dt(x, control_action), current_height, dt)
            if current_height <= 0:
                current_height = 0
            if current_height >= self.h_max:
                current_height = self.h_max

            elapsed_time += dt
            control_timer += dt
            height[i] = current_height
            time[i] = elapsed_time
            error[i] = control_point - current_height
            action[i] = control_action

            # Calculate the Control Action
            if control_timer >= controller.sampling_rate:
                control_timer -= controller.sampling_rate
                control_action = controller.calculate_action(height[:i], time[:i])

            percentage = int(100 * i / nit)
            if percentage != last_percentage:
                last_percentage = percentage
                if progressCallback:
                    if callbackArgs:
                        progressCallback(percentage, callbackArgs)
                    else:
                        progressCallback(percentage)

        self.simulation_results = SimulationResults(time, height, error, action)
        if onFinished:
            if args:
                onFinished(self.simulation_results, args)
            else:
                onFinished(self.simulation_results)

        if returnValues:
            return self.simulation_results


# class InvertedPendulum:
#     g = 9.81
#
#     def __init__(self, L=1, inital_theta=0.00001):
#         self.L
#         self.theta = 0
#
#
#     def iterate(self, action, dt=0.01):
#         dh = self.k2*action - self.k1*np.sqrt(self.h)
#         self.h += dh*dt
#         self.elapsed_time += dt
#         if self.h <= 0:
#             self.h = 0
#         if self.h >= self.h_max:
#             self.h = self.h_max
#
#     def get_reading(self):
#         return self.h + np.random.normal(0, 0.03)
