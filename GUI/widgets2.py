from abc import ABC, abstractmethod

import pygame
import pygame.freetype
from string import ascii_letters
import numpy as np
pygame.freetype.init()


class MultipleParentError(Exception):
    pass


UUID = 0
EntityMap = {

}


class Entity(ABC):

    def __init__(self, position=None, parent=None):
        global UUID
        global EntityMap

        self.UUID = UUID
        UUID += 1

        if position is None:
            position = np.array([0, 0])

        self.has_children = False
        self.has_parent = False
        self._position = position
        self._position_anchor = np.array([0, 0])
        self._global_position = position
        self.parent_id = None

        self.children_ids = []
        if parent:
            self.has_parent = True
            self.parent_id = parent.get_id()
            parent.children_ids.append(self.UUID)
            self.position_anchor = parent.global_position
            parent.has_children = True
        EntityMap[self.UUID] = self

        self.interacting = False
        self.visible = False
        self.clickable = False
        self.check_keyboard = False

    @property
    def position(self):
        return self._position

    @property
    def global_position(self):
        return self._global_position

    @property
    def position_anchor(self):
        return self._position_anchor

    @position.setter
    def position(self, value):
        difference = np.subtract(value, self._position)
        self._global_position = np.add(self._global_position, difference)
        self._position = np.array(value)
        self.update_children()

    @position_anchor.setter
    def position_anchor(self, value):
        self._position_anchor = np.array(value)
        self._global_position = self._position + self._position_anchor
        self.update_children()

    @global_position.setter
    def global_position(self, value):
        difference = np.subtract(value, self._global_position)
        self._global_position = np.array(value)
        self._position = np.add(self._global_position, self._position, difference)
        self.update_children()

    def update_children(self):
        if self.has_children:
            global EntityMap
            for child_id in self.children_ids:
                EntityMap[child_id].position_anchor = self._global_position

    def get_parent_id(self):
        return self.parent_id

    def get_id(self):
        return self.UUID

    def get_parent(self):
        global EntityMap
        return EntityMap[self.parent_id]

    def get_child(self, child_index):
        return self.children_ids[child_index]

    def get_children(self):
        global EntityMap
        return list(map(lambda child_id: EntityMap[child_id], self.children_ids))

    def set_parent(self, parent):
        self.position_anchor = parent.global_position
        self.update_children()
        parent.children_ids.append(self.UUID)

    def __repr__(self):
        rpr = "\nWidget\t\t\t  #{}".format(self.UUID)
        anchor = "\nAnchor\t\t\t[{}, {}]".format(self._position_anchor[0],self._position_anchor[1])
        local_position = "\nPosition\t\t[{}, {}]".format(self._position[0],self._position[1])
        global_position = "\nGlobal Position\t[{}, {}]".format(self._global_position[0],self._global_position[1])

        return rpr+anchor+local_position+global_position

    def on_frame_update(self, context):
        self.display(context.window)
        children = self.get_children()
        if self.interacting:
            for event in context.events:
                self.event_handler(events)

    def display(self, window):
        if self.visible:
            self.__display(window)
            children = self.get_children()
            for child in children:
                child.display()

    def __display(self, window):
        pass

    def event_handler(self, event, mouse_pos):
        if self.clickable:
            self.__click_handler(event, mouse_pos)
        if self.check_keyboard:
            self.__keyboard_handler(event, mouse_pos)

    def __click_handler(self, event, mouse_pos):
        pass

    def __keyboard_handler(self, event, mouse_pos):
        pass


class Scene(Entity, ABC):

    def __init__(self):
        Entity.__init__(self)
        self.widgets = {}
        self.scene_id = 0
        self.frame_counter = 0
        self.visible = False

    def start(self, delay=0):
        self.visible = True

    def close(self):
        self.visible = False

    def event_handler(self, events):
        for event in pygame.event.get():
            for widget in self.widgets.values():
                widget.event_handler(self, event, pygame)

    def add_widget(self, widget):
        self.widgets.append(widget.get_id())


w1 = Entity([1,2])
w2 = Entity([2,1], w1)

w1.position = [4,3]

print(w1.position)
print(w2.position)

# Classe que determina uma borda:
# Contém uma grossura, e cor, além disso é necessário calcular os vértices de seu retângulo depois.
class Border:
    def __init__(self, width, color):
        self.width = width
        self.color = color
        self.vertices = None

    def calculate_vertices(self, rect):
        self.vertices = (rect.global_position[0] - self.width, rect.global_position[1] - self.width, rect.size[0] + 2*self.width, rect.size[1] + 2*self.width)


class Text:

    def __init__(self, text, pt, color, font='Comic Sans MS'):
        self.txt = text
        self.pt = pt
        self.color = color
        self.font = pygame.freetype.SysFont(font, pt)


class TextType:
    Generic = 0
    AlphaNumeric = 1
    Numeric = 2


# Retorna o quadratura de dois vetores p, q, ou seja, o quadrado da distância entre eles.
def quadrature(p, q):
    return (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2


# Determina se uma posição está dentro do retângulo, definido pela posição do vértice superior esquerdo
# e o tamanho de suas arestas.
def is_in_rect(position, rect):
    if rect.position[0] <= position[0] <= rect.position[0] + rect.size[0]:
        if rect.position[1] <= position[1] <= rect.position[1] + rect.size[1]:
            return True
        else:
            return False
    else:
        return False


# Determina se uma posição está dentro do círculo, definido pela posição do centro e o seu raio.
def is_in_circle(position, circle):
    return quadrature(position, circle.position) <= circle.size**2

