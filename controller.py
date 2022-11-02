from abc import ABC, abstractmethod

from pathlib import Path


class Controller(ABC):

    def __init__(self, ts=0.1):
        self.ts = ts

    @abstractmethod
    def calculate_action(self, readings, time, control_point):
        pass


def get_custom_controllers():
    custom_controllers = []
    for file_path in Path("Controllers/").glob('**/*.py'):
        AuxiliaryDictionary = {
            'class': Controller
        }
        str_path = str(file_path)
        file = open(str_path, "r")
        custom_code = file.read()
        file.close()

        exec(custom_code, {'Controller': Controller, 'AuxiliaryDictionary': AuxiliaryDictionary})
        editable_variables = {}
        variables = vars(AuxiliaryDictionary['class']())
        for var in variables:
            if var.find('_') != 0:
                editable_variables[var] = variables[var]
        custom_controllers.append({
            'name': AuxiliaryDictionary['class'].__name__,
            'code': custom_code,
            'class': AuxiliaryDictionary['class'],
            'variables': editable_variables
        })
    return custom_controllers
