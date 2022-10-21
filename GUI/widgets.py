import pygame
import pygame.freetype
from string import ascii_letters

from pygame.rect import Rect

pygame.freetype.init()

current_id = 0
ui_elements = {}


# Enumerador de cores. Adicionar as que forem necessárias.
class Color:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 255)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)


class Widget:
    def __init__(self, position, parent=None):
        global current_id
        global ui_elements
        if parent:
            self.parent_id = parent.get_id()
        self.id = current_id
        current_id += 1
        self.position = position
        self.global_position = position
        if parent:
            self.global_position[0] += parent.position[0]
            self.global_position[1] += parent.position[1]
        ui_elements[self.id] = self

    def get_parent_id(self):
        return self.parent_id

    def get_id(self):
        return self.id

    def set_parent(self, parent):
        self.parent_id = parent.get_id()
        self.global_position[0] = parent.position[0] + self.position[0]
        self.global_position[1] = parent.position[1] + self.position[1]

    def get_parent(self):
        global ui_elements
        return ui_elements[self.parent_id]


# Classe que determina uma borda:
# Contém uma grossura, e cor, além disso é necessário calcular os vértices de seu retângulo depois.
class Border:
    def __init__(self, width, color):
        self.width = width
        self.color = color
        self.vertices = None

    def calculate_vertices(self, rect):
        self.vertices = (
        rect.global_position[0] - self.width, rect.global_position[1] - self.width, rect.size[0] + 2 * self.width,
        rect.size[1] + 2 * self.width)


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
    return quadrature(position, circle.position) <= circle.size ** 2


class ToggleButton(Widget):
    def __init__(self, position, size, images, hint_text=None, parent=None):
        Widget.__init__(self, position, parent)
        self.visible = True
        self.clickable = True
        self.connected_function = None
        self.args = None
        self.hint_text = hint_text
        shape = 'Circular'
        if type(size) != int:
            shape = 'Retangular'
        self.size = size
        self.images = []
        for img in images:
            if shape == 'Retangular':
                self.images.append(pygame.transform.scale(img, self.size))
            else:
                self.images.append(pygame.transform.scale(img, [self.size, self.size]))
        self.is_pressed = False
        self.shape = shape
        self.frame_counter = 0
        self.properties_changed = False

    def connect_function(self, function, args=None):
        self.connected_function = function
        self.args = args

    def event_handler(self, mouse_position, event_type):
        if self.clickable and not self.properties_changed and event_type == pygame.MOUSEBUTTONDOWN:
            if self.shape == 'Retangular':
                if is_in_rect(mouse_position, self):
                    self.is_pressed = not self.is_pressed
                    if self.connected_function:
                        self.connected_function()
            else:
                if is_in_circle(mouse_position, self):
                    self.is_pressed = not self.is_pressed
                    if self.connected_function:
                        self.connected_function()

    def show(self, window):
        if self.visible:
            if self.is_pressed:
                window.blit(self.images[1], self.position)
            else:
                window.blit(self.images[0], self.position)
            if self.properties_changed:
                self.frame_counter += 1
                if self.frame_counter == 1:
                    self.frame_counter = 0
                    self.properties_changed = False
            if self.hint_text:
                text_render, _ = self.hint_text.font.render(self.hint_text.txt, self.hint_text.color)
                rect = text_render.get_rect(
                    center=(self.position[0] + self.size[0] // 2, self.position[1] + self.size[1] / 2))
                window.blit(text_render, rect)

    def disable(self):
        self.clickable = False
        self.visible = False
        self.properties_changed = True

    def enable(self):
        self.clickable = True
        self.visible = True
        self.properties_changed = True

    def make_unclickable(self):
        self.clickable = False

    def make_clickable(self):
        self.clickable = True


# Classe do botão
class PushButton(Widget):
    def __init__(self, position, size, images, pressed_animation_length=5, hint_text=None, parent=None):
        Widget.__init__(self, position, parent)
        self.visible = True
        self.clickable = True
        self.connected_function = None
        self.hint_text = hint_text
        shape = 'Circular'
        if type(size) != int:
            shape = 'Retangular'
        self.size = size
        self.images = []
        for img in images:
            if shape == 'Retangular':
                self.images.append(pygame.transform.scale(img, self.size))
            else:
                self.images.append(pygame.transform.scale(img, [self.size, self.size]))
        self.clicked = False
        self.double_clicked = False
        self.shape = shape
        self.pressed_animation_length = pressed_animation_length
        self.double_click_counter = 0
        self.frame_counter = 0
        self.properties_changed = False
        self.args = None

        self.mouse_over = False

        self.hover_active = False
        self.on_hover = None
        self.on_hover_args = None
        self.hover_image = None

        self.on_double_click = None
        self.on_double_click_args = None

    def connect_function(self, function, args=None):
        self.connected_function = function
        self.args = args

    def connect_function_on_hover(self, function, args=None, hover_image=None):
        self.on_hover = function
        self.on_hover_args = args
        self.hover_active = True
        img = hover_image
        if img:
            if self.shape == 'Retangular':
                img = pygame.transform.scale(img, self.size)
            else:
                img = pygame.transform.scale(img, [self.size, self.size])
        self.hover_image = img

    def connect_function_on_double_click(self, function, args=None):
        self.on_double_click = function
        self.on_double_click_args = args

    def event_handler(self, mouse_position, event_type):
        if self.clickable and not self.properties_changed:
            if self.shape == 'Retangular':
                if self.global_position[0] <= mouse_position[0] <= self.global_position[0] + self.size[0] and \
                        self.global_position[1] <= \
                        mouse_position[1] <= self.global_position[1] + self.size[1]:
                    self.mouse_over = True
                else:
                    self.mouse_over = False
            else:
                if quadrature(mouse_position, self.global_position) <= self.size ** 2:
                    self.mouse_over = True
                else:
                    self.mouse_over = False
            if self.mouse_over and event_type == pygame.MOUSEBUTTONDOWN:
                self.clicked = True

    def activate_hover_function(self):
        if self.on_hover:
            if self.on_hover_args is not None:
                self.on_hover(self.on_hover_args)
            else:
                self.on_hover()

    def activate_connected_function(self):
        if self.connected_function:
            if self.args is not None:
                self.connected_function(self.args)
            else:
                self.connected_function()

    def activate_double_click_function(self):
        if self.on_double_click:
            if self.on_double_click_args is not None:
                self.on_double_click(self.on_double_click_args)
            else:
                self.on_double_click()

    def show(self, window):
        if self.visible:
            if self.mouse_over and self.hover_active and not self.clicked:
                if self.hover_image:
                    window.blit(self.hover_image, self.global_position)
                self.activate_hover_function()
            elif self.clicked:
                window.blit(self.images[1], self.global_position)
                self.frame_counter += 1
                if self.frame_counter == self.pressed_animation_length:
                    self.frame_counter = 0
                    self.activate_connected_function()
                    self.clicked = False

                if self.clicked or self.double_click_counter > 0:
                    self.double_click_counter += 1
                    if self.clicked and 10 < self.double_click_counter < 25:
                        self.double_click_counter = 0
                        self.activate_double_click_function()
            else:
                window.blit(self.images[0], self.global_position)
            if self.properties_changed:
                self.frame_counter += 1
                if self.frame_counter == 1:
                    self.frame_counter = 0
                    self.properties_changed = False
            if self.hint_text:
                text_render, _ = self.hint_text.font.render(self.hint_text.txt, self.hint_text.color)
                rect = text_render.get_rect(
                    center=(self.global_position[0] + self.size[0] // 2, self.global_position[1] + self.size[1] / 2))
                window.blit(text_render, rect)

    def disable(self):
        self.clickable = False
        self.visible = False
        self.properties_changed = True

    def enable(self):
        self.clickable = True
        self.visible = True
        self.properties_changed = True

    def make_unclickable(self):
        self.clickable = False

    def make_clickable(self):
        self.clickable = True

    def disable_hover_event(self):
        self.hover_active = False

    def enable_hover_event(self):
        self.hover_active = True


class Panel(Widget):
    def __init__(self, position, size, image, border=Border(0, (0, 0, 0)), text=Text('None', 0, Color.BLACK),
                 parent=None, clickable=False):
        Widget.__init__(self, position, parent)
        self.enabled = True
        self.text = text
        self.size = size
        self.image = pygame.transform.scale(image, self.size)
        self.border = border
        self.border.calculate_vertices(self)
        self.clickable = clickable

    def show(self, window):
        if self.enabled:
            if self.border.width != 0:
                pygame.draw.rect(window, self.border.color, self.border.vertices)
            window.blit(self.image, self.position)
            if self.text.txt != 'None':
                text_render, _ = self.text.font.render(self.text.txt, self.text.color)
                text_rect = text_render.get_rect(
                    center=(self.position[0] + self.size[0] // 2, self.position[1] + self.size[1] // 2))
                window.blit(text_render, text_rect)

    def disable(self):
        self.enabled = False

    def enable(self):
        self.enabled = True

    def set_text(self, new_text):
        self.text.txt = new_text

    def clear_text(self):
        self.text.txt = 'None'


class TextEdit(Widget):

    def __init__(self, position, size, image, border=Border(0, (0, 0, 0)), text=Text('None', 0, Color.BLACK),
                 parent=None):
        Widget.__init__(self, position, parent)
        self.enabled = True
        self.text = text
        self.size = size
        self.image = pygame.transform.scale(image, self.size)
        self.border = border
        self.border.calculate_vertices(self)
        self.selected = False
        self.blink_frame_counter = 0
        self.selected_marker_on = False
        self.text_type = TextType.Generic

    def show(self, window):
        if self.enabled:
            if self.border.width != 0:
                pygame.draw.rect(window, self.border.color, self.border.vertices)
            window.blit(self.image, self.position)
            text_render, _ = self.text.font.render(self.text.txt, self.text.color)
            rect = text_render.get_rect(
                center=(self.position[0] + self.size[0] // 2, self.position[1] + self.size[1] / 2))
            window.blit(text_render, rect)
            if self.selected and self.selected_marker_on:
                x = rect.x
                w = rect.w
                pygame.draw.rect(window, (0, 0, 0), (x + w + 3, self.position[1] + 5, 2, self.size[1] - 10))

            if self.selected:
                self.blink_frame_counter += 1
                if self.blink_frame_counter == 30:
                    self.blink_frame_counter = 0
                    self.selected_marker_on = not self.selected_marker_on

    def click_handler(self, mouse_position):
        if self.position[0] <= mouse_position[0] <= self.position[0] + self.size[0] and self.position[1] <= \
                mouse_position[1] <= self.position[1] + self.size[1]:
            self.selected = True
            self.selected_marker_on = True
        else:
            self.selected = False
            self.selected_marker_on = False

    def key_handler(self, event):
        if self.enabled:
            if event.key == pygame.K_BACKSPACE and self.selected:
                self.text.txt = self.text.txt[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.selected = False
                self.selected_marker_on = False
            elif self.selected:
                temp_text = self.text.txt
                if ((event.unicode.isnumeric() or (
                        event.unicode == '.' and '.' not in temp_text)) and self.text_type == TextType.Numeric) or self.text_type == TextType.Generic:
                    temp_text += event.unicode
                    text_render, _ = self.text.font.render(temp_text, self.text.color)
                    rect = text_render.get_rect(
                        center=(self.position[0] + self.size[0] // 2, self.position[1] + self.size[1] / 2))
                    if rect.x + rect.w + 5 < self.position[0] + self.size[0]:
                        self.set_text(temp_text)

    def disable(self):
        self.enabled = False

    def enable(self):
        self.enabled = True

    def set_text(self, new_text):
        self.text.txt = new_text

    def get_text(self):
        return self.text.txt

    def get_text_as_float(self):
        return float(self.text.txt)

    def set_type(self, text_type):
        self.text_type = text_type


class ProgressBar(Widget):

    def __init__(self, position, size, border=Border(1, (0, 0, 0)), background_color=(100, 100, 100),
                 color=(0, 255, 100), parent=None):
        Widget.__init__(self, position, parent)
        self.enabled = True
        self.size = size
        self.border = border
        self.border.calculate_vertices(self)
        self.value = 0
        self.color = color
        self.background_color = background_color
        self.vertices = [self.global_position[0], self.global_position[1], 0, self.size[1]]
        self.background_vertices = [self.global_position[0], self.global_position[1], self.size[0], self.size[1]]

    def show(self, window):
        if self.enabled:
            if self.border.width != 0:
                pygame.draw.rect(window, self.border.color, self.border.vertices)
            pygame.draw.rect(window, self.background_color, self.background_vertices)
            if self.value > 0:
                pygame.draw.rect(window, self.color, self.vertices)

    def disable(self):
        self.enabled = False

    def enable(self):
        self.enabled = True

    def set_value(self, value):
        self.value = value
        self.vertices[2] = self.size[0] * self.value

    def reset(self):
        self.set_value(0)


class DropdownMenu(Widget):
    def __init__(self, position, size, images, border=Border(0, (0, 0, 0)), parent=None):
        Widget.__init__(self, position, parent)
        self.enabled = True
        self.size = size
        self.border = border
        self.border.calculate_vertices(self)
        self.images = []
        for img in images:
            self.images.append(pygame.transform.scale(img, self.size))

        self.items = []
        self.number_of_items = 0
        self.selected_item = None
        self.selected_item_id = 0
        self.selecting_item = False
        self.positions = []
        self.max_size = []

        self.on_item_select = None
        self.on_item_select_args = None

    def add_item(self, item):
        self.positions.append([0, self.number_of_items * self.size[1] + self.border.width])
        new_item_button = PushButton(self.positions[self.number_of_items], self.size, [self.images[0], self.images[0]],
                                     pressed_animation_length=1, hint_text=Text(item, 12, Color.BLACK), parent=self)
        new_item_button.connect_function_on_hover(self.on_item_hover, self.number_of_items, self.images[1])
        new_item_button.connect_function(self.on_item_click, self.number_of_items)

        if self.number_of_items == 0:
            new_item_button.disable_hover_event()
        else:
            new_item_button.disable()
        self.number_of_items += 1
        self.items.append(new_item_button)
        self.max_size = [self.size[0], self.number_of_items * self.size[1]]

    def on_item_hover(self, id):
        pass

    def on_item_click(self, id):
        if self.selecting_item:
            self.selected_item_id = id
            self.selected_item = self.items[id]
            self.selecting_item = False
            ordering = [id]
            for i in range(0, self.number_of_items):
                if i != id:
                    ordering.append(i)
            for index, order in enumerate(ordering):
                if index > 0:
                    self.items[order].enable_hover_event()
                    self.items[order].disable()
                else:
                    self.items[order].disable_hover_event()
                    self.items[order].enable()
                self.items[order].position = self.positions[index]
                self.items[order].global_position = [self.positions[index][0], self.positions[index][1]]
            if self.on_item_select:
                if self.on_item_select_args:
                    self.on_item_select(self.selected_item.hint_text.txt, self.selected_item_id, self.on_item_select_args)
                else:
                    self.on_item_select(self.selected_item.hint_text.txt, self.selected_item_id)
        elif id == self.selected_item_id:
            self.selecting_item = True
            for item in self.items:
                item.enable()

    def show(self, window):
        if self.enabled:
            self.items[self.selected_item_id].show(window)
            if self.selecting_item:
                for i in range(self.number_of_items):
                    if i != self.selected_item_id:
                        self.items[i].show(window)

    def event_handler(self, mouse_position, event_type):
        if self.selecting_item and event_type == pygame.MOUSEBUTTONDOWN:
            if not (self.global_position[0] <= mouse_position[0] <= self.global_position[0] + self.max_size[0] and
                    self.global_position[1] <= \
                    mouse_position[1] <= self.global_position[1] + self.max_size[1]):
                self.selecting_item = False

    def disable(self):
        self.enabled = False

    def enable(self):
        self.enabled = True

    def connect_on_item_select(self, function, args=None):
        self.on_item_select = function
        self.on_item_select_args = args


class Window:

    def __init__(self, buttons, panels, text_edits, progress_bars, dropdown_menus):
        self.text_edits = text_edits
        self.buttons = buttons
        self.panels = panels
        self.progress_bars = progress_bars
        self.dropdown_menus = dropdown_menus
        self.frame_counter = 0
        self.wait_complete = False

    def show(self, window):
        for button in self.buttons.values():
            button.show(window)
        for panel in self.panels.values():
            panel.show(window)
        for text_edit in self.text_edits.values():
            text_edit.show(window)
        for progress_bar in self.progress_bars.values():
            progress_bar.show(window)
        for dropdown_menu in self.dropdown_menus.values():
            dropdown_menu.show(window)
        if not self.wait_complete:
            self.frame_counter += 1
            if self.frame_counter == 3:
                self.wait_complete = True


def determine_text_center(self):
    avg = 0
    num = 0
    max_height = 0
    for c in ascii_letters:
        text_render, _ = self.text.font.render(c, self.text.color)
        rect = text_render.get_rect(center=(self.position[0] + self.size[0] // 2, self.position[1] + self.size[1] / 2))
        y = rect.y
        avg += y
        num += 1
        if rect.height > max_height:
            max_height = rect.height
    for i in range(0, 9):
        text_render, _ = self.text.font.render(str(i), self.text.color)
        rect = text_render.get_rect(center=(self.position[0] + self.size[0] // 2, self.position[1] + self.size[1] / 2))
        y = rect.y
        avg += y
        num += 1
        if rect.height > max_height:
            max_height = rect.height
    avg = avg / num
    return avg, max_height


def get_elapsed_time_string(elapsed_time):
    elapsed_time_text = ''
    ms = int(elapsed_time) % 1000
    s = int((elapsed_time - ms) / 1000)
    if s < 10:
        elapsed_time_text += '0'
    elapsed_time_text += str(s) + ':'
    if ms < 100:
        if ms < 10:
            if ms < 1:
                elapsed_time_text += '0'
            elapsed_time_text += '0'
        elapsed_time_text += '0'
    elapsed_time_text += str(ms)
    return elapsed_time_text

# TODO
#  1 - Refactor the window object so it only stores a collection of widgets, regardless of the type.
#  2 - Refactor each widget to only have an event handler function instead of having a click or key handler.
#  3 - Refactor the application and window object so that the window object call the event handler for each widgets it
#  has instead of the application calling it.
#  4 - Verify all click checks are on the global_position instead of local.
#  5 - Make position and global_position into @property so when a widgets changes position it will update it's children
#  position.
#  6 - Created Group class.
