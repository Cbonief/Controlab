import sys
import threading
import tkinter as tk

import pygame
from PyQt5.QtWidgets import QApplication, QStyleFactory, QMainWindow

from application import Application

import tkinter as tk



if __name__ == "__main__":

    window = pygame.display.set_mode((600, 600))
    pygame.init()
    app = Application(window)
    app.run()
