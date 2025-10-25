from abc import ABC, abstractmethod
from pathlib import Path
import importlib.util
import inspect


class Controller(ABC):

    def __init__(self, ts=0.1):
        self.ts = ts

    @abstractmethod
    def calculate_action(self, readings, time, control_point):
        pass


def get_custom_controllers():
    custom_controllers = []
    controllers_path = Path("Controllers/")
    for file_path in controllers_path.glob('*.py'):
        # Ignore __init__.py files
        if file_path.name == '__init__.py':
            continue
        
        try:
            # Create a module spec from the file path
            module_name = file_path.stem
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find classes in the module that are subclasses of Controller
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, Controller) and obj is not Controller:
                    controller_class = obj
                    editable_variables = {}
                    # Inspect the __init__ parameters for default values
                    sig = inspect.signature(controller_class.__init__)
                    for param in sig.parameters.values():
                        if param.name != 'self' and param.default is not inspect.Parameter.empty:
                            # Convention: parameters not starting with '_' are user-editable
                            if not param.name.startswith('_'):
                                editable_variables[param.name] = param.default
                    
                    custom_controllers.append({
                        'name': controller_class.__name__,
                        'class': controller_class,
                        'variables': editable_variables
                    })
        except Exception as e:
            print(f"Error loading controller from {file_path}: {e}")
            
    return custom_controllers
