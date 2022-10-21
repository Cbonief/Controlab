# Bibliotecas externas
import os  # Biblioteca para direcionamento do endereço dos arquivos.
from bisect import bisect_left
import threading

import pygame  # Biblioteca para a janela do jogo e evento de mouse.
import pygame.freetype  # Sub biblioteca para a fonte.

# Meu código
from matplotlib import pyplot as plt

from GUI import widgets as gui

# Classe do manager do Jogo.
from simulator import WaterTank, DiscretePIDController, get_custom_controllers


class Application:
    def __init__(self, window):
        self.width = window.get_width()
        self.height = window.get_height()
        self.window = window

        self.tank_level = 0.0
        self.action_applied = 0.0
        self.running = True

        self.Kp = 8
        self.Ki = 1
        self.Kv = 0.1

        self.tank = WaterTank()
        self.controller = DiscretePIDController(0.1, self.Kp, self.Ki, self.Kv)
        self.simulation_results = None
        self.simulation_finished = False
        self.simulation_running = False
        self.simulation_displaying = False
        self.current_simulation_index = 0

        self.elapsed_time = 0
        self.elapsed_time_s = 0.0

        self.sprites = {
            'menu_item_idle': pygame.image.load(os.path.join("Assets", "grey_button.png")).convert_alpha(),
            'menu_item_hover': pygame.image.load(
                os.path.join("Assets", "grey_button_pushed.png")).convert_alpha(),
            'run_idle': pygame.image.load(os.path.join("Assets/button_yellow", "button_arrow_top.png")).convert_alpha(),
            'run_pressed': pygame.image.load(
                os.path.join("Assets/button_hover", "button_arrow_top_hover.png")).convert_alpha(),
            'play_idle': pygame.image.load(os.path.join("Assets/button_yellow", "button_play.png")).convert_alpha(),
            'play_pressed': pygame.image.load(os.path.join("Assets/button_hover", "button_play_hover.png")).convert_alpha(),
            'save_idle': pygame.image.load(os.path.join("Assets/button_yellow", "button_save.png")).convert_alpha(),
            'save_pressed': pygame.image.load(
                os.path.join("Assets/button_hover", "button_save_hover.png")).convert_alpha(),
            'stop_idle': pygame.image.load(os.path.join("Assets/button_yellow", "button_pause.png")).convert_alpha(),
            'stop_pressed': pygame.image.load(
                os.path.join("Assets/button_hover", "button_pause_hover.png")).convert_alpha(),
            'restart_idle': pygame.image.load(os.path.join("Assets/button_yellow", "button_reload.png")).convert_alpha(),
            'restart_pressed': pygame.image.load(
                os.path.join("Assets/button_hover", "button_reload_hover.png")).convert_alpha(),
            'ok_idle': pygame.image.load(
                os.path.join("Assets/button_yellow", "button_yes.png")).convert_alpha(),
            'ok_pressed': pygame.image.load(
                os.path.join("Assets/button_hover", "button_yes_hover.png")).convert_alpha(),
            'panel': pygame.image.load(
                os.path.join("Assets", "painel.png")).convert_alpha()
        }
        main_menu_buttons = {
            'run_simulation': gui.PushButton([195, 100-45-10], [45, 45], [self.sprites['run_idle'], self.sprites['run_pressed']]),
            'play': gui.PushButton([195+55, 100-45-10], [45, 45], [self.sprites['play_idle'], self.sprites['play_pressed']]),
            'restart': gui.PushButton([195+110, 100-45-10], [45, 45], [self.sprites['restart_idle'], self.sprites['restart_pressed']]),
            'pause': gui.PushButton([195+55, 100-45-10], [45, 45], [self.sprites['stop_idle'], self.sprites['stop_pressed']]),
            'save_data': gui.PushButton([195+165, 100-45-10], [45, 45], [self.sprites['save_idle'], self.sprites['save_pressed']]),
            'save_controller': gui.PushButton([130, 100], [30, 30], [self.sprites['save_idle'], self.sprites['save_pressed']]),
        }
        main_menu_buttons['run_simulation'].connect_function(self.start_simulation)
        main_menu_buttons['play'].connect_function(self.play_simulation)
        main_menu_buttons['save_controller'].connect_function(self.save_controller)
        main_menu_buttons['pause'].connect_function(self.pause_simulation)
        main_menu_buttons['restart'].connect_function(self.reset)

        main_menu_buttons['pause'].disable()

        panels = {
            'time_panel': gui.Panel([10, 10], [80, 30], self.sprites['panel'], border=gui.Border(1, gui.Color.BLACK), text=gui.Text('00:000', 16, gui.Color.BLACK)),
            'Kp_panel': gui.Panel([15, 100], [35, 30], self.sprites['panel'], border=gui.Border(1, gui.Color.BLACK), text=gui.Text('Kp', 16, gui.Color.BLACK)),
            'Ki_panel': gui.Panel([15, 145], [35, 30], self.sprites['panel'], border=gui.Border(1, gui.Color.BLACK),text=gui.Text('Ki', 16, gui.Color.BLACK)),
            'Kv_panel': gui.Panel([15, 190], [35, 30], self.sprites['panel'], border=gui.Border(1, gui.Color.BLACK), text=gui.Text('Kv', 16, gui.Color.BLACK)),
            'controller_select': gui.Panel([10, 100], [165, 30], self.sprites['panel'], border=gui.Border(1, gui.Color.BLACK), text=gui.Text('Escolha o controlador', 16, gui.Color.BLACK))
        }

        panels['controller_select'].disable()

        text_edits = {
            'Kp': gui.TextEdit([60, 100], [60, 30], self.sprites['panel'], border=gui.Border(1, gui.Color.BLACK), text=gui.Text(str(self.Kp), 16, gui.Color.BLACK)),
            'Ki': gui.TextEdit([60, 145], [60, 30], self.sprites['panel'], border=gui.Border(1, gui.Color.BLACK), text=gui.Text(str(self.Ki), 16, gui.Color.BLACK)),
            'Kv': gui.TextEdit([60, 190], [60, 30], self.sprites['panel'], border=gui.Border(1, gui.Color.BLACK), text=gui.Text(str(self.Kv), 16, gui.Color.BLACK))
        }
        text_edits['Kp'].set_type(gui.TextType.Numeric)
        text_edits['Kv'].set_type(gui.TextType.Numeric)
        text_edits['Ki'].set_type(gui.TextType.Numeric)

        progress_bars = {
            'progresso': gui.ProgressBar([5, 575], [100, 20], border=gui.Border(1, gui.Color.BLACK), background_color=(100, 100, 100))
        }

        dropdown_menu = {
            'controller_select': gui.DropdownMenu([50, 140], [80, 30], [self.sprites['menu_item_idle'], self.sprites['menu_item_hover']], border=gui.Border(1, (0, 0, 0)), parent=None),
            'controller_type': gui.DropdownMenu([10, 50], [80, 30], [self.sprites['menu_item_idle'], self.sprites['menu_item_hover']], border=gui.Border(1, (0, 0, 0)), parent=None)
        }

        dropdown_menu['controller_type'].add_item('PID')
        dropdown_menu['controller_type'].add_item('Custom')
        dropdown_menu['controller_type'].connect_on_item_select(self.change_controller_type)

        self.custom_controllers = get_custom_controllers()

        self.custom_controller_id = None
        for controller in self.custom_controllers:
            dropdown_menu['controller_select'].add_item(controller['name'])

        dropdown_menu['controller_select'].connect_on_item_select(self.change_custom_controller)
        dropdown_menu['controller_select'].disable()

        self.widgets = gui.Window(main_menu_buttons, panels, text_edits, progress_bars, dropdown_menu)

    def run(self):
        timer = pygame.time.Clock()
        while self.running:
            pygame.draw.rect(self.window, (100, 200, 80), pygame.Rect(0, 0, self.width, self.height))
            self.event_handler()
            dt = timer.tick(60)# Recebe o tempo que passou entre frames em ms.

            if self.simulation_finished:
                if self.simulation_displaying:
                    self.set_time_text(get_elapsed_time_string(self.elapsed_time))
                    self.tank_level = self.simulation_results.height[self.current_simulation_index]

                    self.current_simulation_index = get_closest_index(self.simulation_results.time, self.elapsed_time_s)
                    self.elapsed_time += dt
                    self.elapsed_time_s += dt / 1000
            self.draw_tank()
            self.widgets.show(self.window)

            pygame.display.update()

    def start_simulation(self):
        if not self.simulation_running:
            if self.custom_controller_id >= 0:
                self.controller = self.custom_controllers[self.custom_controller_id]['class']()

            simulation_thread = threading.Thread(target=self.tank.simulate, args=(30, 0.001, 0, self.controller, 0.7,
                     self.on_simulation_finished, None,
                     self.update_progress_bar, None,
                     False,))
            simulation_thread.start()
            self.simulation_finished = False
            self.simulation_running = True

    def play_simulation(self):
        if self.simulation_finished:
            self.simulation_displaying = True
            self.widgets.buttons['pause'].enable()
            self.widgets.buttons['play'].disable()
        # self.root.withdraw()

    def on_simulation_finished(self, results):
        self.simulation_results = results
        self.simulation_finished = True
        self.simulation_running = False
        self.elapsed_time = 0
        self.elapsed_time_s = 0.0

    def update_progress_bar(self, percentage):
        value = percentage/100.0
        self.widgets.progress_bars['progresso'].set_value(value)

    def set_time_text(self, txt):
        self.widgets.panels['time_panel'].set_text(txt)

    def pause_simulation(self):
        if self.simulation_displaying:
            self.simulation_displaying = False
            self.widgets.buttons['play'].enable()
            self.widgets.buttons['pause'].disable()
        # self.root.deiconify()

    def reset(self):
        self.tank_level = 0.0
        self.elapsed_time = 0
        self.elapsed_time_s = 0.0
        self.simulation_finished = False
        self.simulation_displaying = False
        self.simulation_running = False
        self.set_time_text('00:000')

        self.widgets.buttons['play'].enable()
        self.widgets.buttons['pause'].disable()

    def save_controller(self):
        Kp = self.widgets.text_edits['Kp'].get_text_as_float()
        Ki = self.widgets.text_edits['Ki'].get_text_as_float()
        Kv = self.widgets.text_edits['Kv'].get_text_as_float()
        self.controller = DiscretePIDController(0.1, Kp, Ki, Kv)

    def change_custom_controller(self, item, item_id):
        self.custom_controller_id = item_id

    def change_controller_type(self, item, item_id):
        if item_id == 0:
            self.custom_controller_id = -1
            #PID
            self.widgets.buttons['save_controller'].enable()
            self.widgets.text_edits['Kp'].enable()
            self.widgets.text_edits['Ki'].enable()
            self.widgets.text_edits['Kv'].enable()
            self.widgets.panels['Kp_panel'].enable()
            self.widgets.panels['Ki_panel'].enable()
            self.widgets.panels['Kv_panel'].enable()
            self.widgets.panels['controller_select'].disable()
            self.widgets.dropdown_menus['controller_select'].disable()
            self.custom_controller_id = None
        elif item_id == 1:
            # Custom Controllers
            self.custom_controller_id = 0
            self.widgets.buttons['save_controller'].disable()
            self.widgets.text_edits['Kp'].disable()
            self.widgets.text_edits['Ki'].disable()
            self.widgets.text_edits['Kv'].disable()
            self.widgets.panels['Kp_panel'].disable()
            self.widgets.panels['Ki_panel'].disable()
            self.widgets.panels['Kv_panel'].disable()
            self.widgets.panels['controller_select'].enable()
            self.widgets.dropdown_menus['controller_select'].enable()

    def event_handler(self):
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()

            for button in self.widgets.buttons.values():
                button.event_handler(mouse_pos, event.type)
            for menu in self.widgets.dropdown_menus.values():
                menu.event_handler(mouse_pos, event.type)
                for button in menu.items:
                    button.event_handler(mouse_pos, event.type)
            if event.type == pygame.MOUSEBUTTONDOWN:
                for text_edit in self.widgets.text_edits.values():
                    text_edit.click_handler(mouse_pos)
            if event.type == pygame.KEYDOWN:
                for text_edit in self.widgets.text_edits.values():
                    text_edit.key_handler(event)

    def draw_tank(self):
        pygame.draw.rect(self.window, (0, 0, 0), pygame.Rect(300 - 100 - 2, 100 - 2, 204, 404))
        pygame.draw.rect(self.window, (122, 122, 122), pygame.Rect(300-100, 100, 200, 400))
        pygame.draw.rect(self.window, (0, 100, 255), pygame.Rect(300 - 100, 500 - self.tank_level * 400, 200, self.tank_level * 400))
        pygame.draw.line(self.window, (255, 0, 0), (300 - 120, 500 - 0.7 * 400), (300+120, 500 - 0.7 * 400))

    def close(self):
        self.running = False


def get_elapsed_time_string(elapsed_time):
    elapsed_time_text = ''
    ms = int(elapsed_time)%1000
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


def get_closest_index(myList, myNumber):
    pos = bisect_left(myList, myNumber)
    if pos == 0:
        return 0
    if pos == len(myList):
        return -1
    before = myList[pos - 1]
    after = myList[pos]
    if after - myNumber < myNumber - before:
        return pos
    else:
        return pos - 1

common_anode_encoding = [
    [1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 0, 0, 0, 0],
    [1, 1, 0, 1, 1, 0, 1],
    [1, 1, 1, 1, 0, 0, 1],
    [0, 1, 1, 0, 0, 1, 1],
    [1, 0, 1, 1, 0, 1, 1],
    [1, 0, 1, 1, 1, 1, 1],
    [1, 1, 1, 0, 0, 0, 0],
    [1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 0, 0, 1]
]

def get_seven_seg_encoding(number):
    return common_anode_encoding[number]