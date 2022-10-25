import pygame

from application import Application



if __name__ == "__main__":
    window = pygame.display.set_mode((600, 600))
    pygame.init()
    app = Application(window)
    app.run()
