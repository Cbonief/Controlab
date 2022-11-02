# Controlab-py

Controlab-py is a project I started during my college graduation in Electrical Engineering, while I was taking a classic control class.

At this moment, it simulates the physics of a water tank, and a controller attached to it. The simulation is done using the Runge Kutta, or Dormand Prince (or ODE45),
before it's displayed to the user. The idea is to have a visual tool to help understand how controllers work and dynamic systems work, whereas students are usually "stuck"
to block diagrams.

# Main Interface

<img src="https://user-images.githubusercontent.com/62687996/199091766-d7f9ef6a-3604-4a34-883a-d7d2a2483d19.png" alt="drawing" width="500"/>

# How to install

At this moment, there is not an official package release, but it's being worked on.

But you can still use the tool by cloning the repo, and running:

    pip install -r requirements.txt
    
# Usage and extra features.

The basic usage of the tool is very straight foward, just choose the controller and it's parameters. Unfortunately there isn't a system config area yet, so the system has
to be changed via code.

To add a controller that's not on the Controllers folder, just add a python file to the folder and program the controller using the following template.

    global Controller
    global AuxiliaryDictionary


    class CustomController(Controller):

      def __init__(self, ts=0.1):
        Controller.__init__(self, ts)

      @staticmethod
      def calculate_action(readings, time, control_point=0.7):
        pass


      AuxiliaryDictionary['class'] = CustomController

This allows for a new controller to be added without having to change the exisiting code. If a class variable represents an internal state, add an underline to it's name
so the GUI won't add an edit box for it.
