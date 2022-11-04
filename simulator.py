import numpy as np

from abc import ABC, abstractmethod
from dataclasses import dataclass


# Data structure to save the simulation.
@dataclass(frozen=True)
class SimulationResults:
    time: np.array
    height: np.array
    error: np.array
    action: np.array


# Dynamic System class. Simulates a dynamic system on the form:
# dx_dt = f(x,t)
class DynamicSystem(ABC):
    a21 = 1 / 5
    a31, a32 = 3 / 40, 9 / 40
    a41, a42, a43 = 44 / 55, -56 / 15, 32 / 9
    a51, a52, a53, a54 = 19372 / 6561, -25360 / 2187, 64448 / 6561, -212 / 729
    a61, a62, a63, a64, a65 = 9017 / 3186, -355 / 33, 46732 / 5247, 49 / 176, -5103 / 18656
    a71, a73, a74, a75, a76 = 35 / 384, 500 / 1113, 125 / 192, -2187 / 6784, 11 / 84
    a81, a83, a84, a85, a86, a87 = 71 / 57600, -71 / 16695, 71 / 1920, -17253 / 339200, 22 / 525, -1 / 40

    def __init__(self, limits=None):
        keywords = ['dx_dt', 'x', 'action', 'dt']
        if limits is None:
            limits = {}
        self.limits = limits
        for keyword in keywords:
            if keyword not in limits.keys():
                self.limits[keyword] = [None, None]

        self.simulation_results = None

    def dx_dt(self, value, action=None):
        return self.limit(self._dx_dt(value, action), self.limits['dx_dt'])

    def simulate_45(self, total_time=10, dt=0.001, x0=0, tol=1e-6,
                    controller=None, control_point=0.7,
                    onFinished=None, args=None,
                    progressCallback=None, callbackArgs=None,
                    returnValues=False,
                    ):

        # Control Variables
        control_action = 0
        control_timer = 0

        self.limits['dt'] = [1e-12, controller.ts]

        # Simulation Variables
        xn = x0
        x = LinkedList(x0)
        time = LinkedList(0)
        error = LinkedList(control_point - xn)
        action = LinkedList(0)

        elapsed_time = 0

        # Progress
        last_percentage = 0

        while elapsed_time < total_time:
            # Add dt to the elapsed time, and the control timer.
            elapsed_time += dt
            control_timer += dt

            # Calculates the current value using the Dormand Prince Method
            xn, dt = self.dormand_prince(lambda aux: self.dx_dt(aux, control_action), xn, dt, tol)
            xn = self.limit(xn, self.limits['x'])

            # Assign the variables to their respective array.
            x.append(xn)
            time.append(elapsed_time)
            error.append(control_point - xn)
            action.append(control_action)

            # Calculate the Control Action if the system has a controller.
            if controller:
                if control_timer >= controller.ts:
                    control_timer -= controller.ts
                    control_action = controller.calculate_action(x.np_array(), time.np_array(), control_point)
            else:
                control_action = 0

            # Progress Callback.
            percentage = int(100 * elapsed_time / total_time)
            if percentage != last_percentage:
                last_percentage = percentage
                if progressCallback:
                    if callbackArgs:
                        progressCallback(percentage, callbackArgs)
                    else:
                        progressCallback(percentage)

        self.simulation_results = SimulationResults(time.np_array(), x.np_array(), error.np_array(), action.np_array())
        if onFinished:
            if args:
                onFinished(self.simulation_results, args)
            else:
                onFinished(self.simulation_results)

        if returnValues:
            return self.simulation_results

    def simulate(self, total_time=10, dt=0.001, x0=0,
                 controller=None, control_point=0.7,
                 onFinished=None, args=None,
                 progressCallback=None, callbackArgs=None,
                 returnValues=False,
                 ):

        print(control_point)
        # Control Variables
        control_action = 0
        control_timer = 0

        # Simulation Variables
        nit = int(np.ceil(total_time / dt))
        curr_x = x0
        x = np.zeros(nit)
        x[0] = x0
        time = np.zeros(nit)
        error = np.zeros(nit)
        error[0] = control_point - curr_x
        action = np.zeros(nit)
        elapsed_time_string = [''] * nit
        elapsed_time_string[0] = '0:00'

        elapsed_time = 0

        # Progress
        last_percentage = 0

        for i in range(1, nit):
            # Calculates the current value using the Runge Kutta Method.
            curr_x = self.runge_kutta(lambda aux: self.dx_dt(aux, control_action), curr_x, dt)
            curr_x = self.limit(curr_x, self.limits['x'])

            # Add dt to the elapsed time, and the control timer.
            elapsed_time += dt
            control_timer += dt

            # Assign the variables to their respective array.
            x[i] = curr_x
            time[i] = elapsed_time
            error[i] = control_point - curr_x
            action[i] = control_action

            # Calculate the Control Action if the system has a controller.
            if controller:
                if control_timer >= controller.ts:
                    control_timer -= controller.ts
                    control_action = controller.calculate_action(x[:i], time[:i], control_point)
            else:
                control_action = 0

            # Progress Callback.
            percentage = int(100 * i / nit)
            if percentage != last_percentage:
                last_percentage = percentage
                if progressCallback:
                    if callbackArgs:
                        progressCallback(percentage, callbackArgs)
                    else:
                        progressCallback(percentage)

        self.simulation_results = SimulationResults(time, x, error, action)
        if onFinished:
            if args:
                onFinished(self.simulation_results, args)
            else:
                onFinished(self.simulation_results)

        if returnValues:
            return self.simulation_results

    @abstractmethod
    def _dx_dt(self, value, action=None):
        pass

    @staticmethod
    def runge_kutta(derivative_function, xn, dt):
        weights = [2, 2, 1]
        k = derivative_function(xn)
        x_n1 = k
        for i in range(3):
            k = derivative_function(xn + dt * k / weights[i])
            x_n1 += k * weights[i]
        x_n1 *= dt / 6
        x_n1 += xn
        return x_n1

    def dormand_prince(self, derivative_function, xn, dt, tol=1e-6):
        k1 = derivative_function(xn)
        k2 = derivative_function(xn + dt * self.a21 * k1)
        k3 = derivative_function(xn + dt * (self.a31 * k1 + self.a32 * k2))
        k4 = derivative_function(xn + dt * (self.a41 * k1 + self.a42 * k2 + self.a43 * k3))
        k5 = derivative_function(xn + dt * (self.a51 * k1 + self.a52 * k2 + self.a53 * k3 + self.a54 * k4))
        k6 = derivative_function(
            xn + dt * (self.a61 * k1 + self.a62 * k2 + self.a63 * k3 + self.a64 * k4 + self.a65 * k5))
        xn_1 = xn + dt * (self.a71 * k1 + self.a73 * k3 + self.a74 * k4 + self.a75 * k5 + self.a76 * k6)
        k7 = derivative_function(xn_1)
        error = abs(
            dt * (self.a81 * k1 + self.a83 * k3 + self.a84 * k4 + self.a85 * k5 + self.a86 * k6 + self.a87 * k7))

        if error == 0:
            dt_new = 2*dt
        elif error > tol or (error < tol/10):
            a = np.power(tol * dt / (2 * error), 1 / 5)
            factor = 0.9 * a
            if factor > 2:
                dt_new = 2*dt
            elif 0.5 < factor:
                dt_new = dt/2
            else:
                dt_new = factor*dt
        else:
            dt_new = dt

        dt_new = self.limit(dt_new, self.limits['dt'])

        return xn_1, dt_new

    @staticmethod
    def limit(x, limits):
        out = x
        if limits[0]:
            out = max(limits[0], out)
        if limits[1]:
            out = min(limits[1], out)
        return out


# Implementation of Water Tank Dynamics.
class WaterTank(DynamicSystem):
    g = 9.81

    def __init__(self, max_height=1, tank_area=0.09, tank_escape_area=0.001 * np.pi, incoming_max_velocity=20,
                 input_area=0.0004 * np.pi):
        DynamicSystem.__init__(self, {
            'x': [0, max_height]
        })
        self._h_max = max_height
        self._k1 = np.sqrt(2 * self.g) * tank_escape_area / tank_area
        self._k2 = incoming_max_velocity * input_area / tank_area

    def _dx_dt(self, value, action=None):
        return self._k2 * action - self._k1 * np.sqrt(value)


class LinkedList:

    class Data:

        def __init__(self, val, index=0):
            self.val = val
            self.index = index
            self.next = None

        def __hash__(self):
            return self.index

    def __init__(self, initial_data=None):
        self.first = None
        self.length = 0
        self.last = None
        self.Nodes = {}
        if initial_data:
            self.append(initial_data)

    def append(self, data):
        new_node = self.Data(data, self.length)
        if self.last:
            self.Nodes[self.last].next = new_node
        self.Nodes[new_node] = new_node
        if self.length == 0:
            self.first = new_node
        elif self.length == 1:
            self.first.next = new_node
        self.last = new_node
        self.length += 1

    def np_array(self):
        array = np.zeros(self.length)
        curr = self.Nodes[self.first]
        for i in range(self.length):
            array[i] = curr.val
            curr = curr.next
        return array


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
