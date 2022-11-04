# Bibliotecas externasz
from os import path  # Biblioteca para direcionamento do endereço dos arquiv
from bisect import bisect_left
import threading
import easygui as g

from openpyxl import Workbook
from openpyxl.chart import Reference, ScatterChart, Series

import pygame  # Biblioteca para a janela do jogo e evento de mouse.
import pygame.freetype  # Sub biblioteca para a fonte.

# Meu código
from GUI import widgets as gui

# Classe do manager do Jogo.
from simulator import WaterTank
from controller import get_custom_controllers, Controller


class WaterTankWidget(gui.Widget):

    def __init__(self, position, parent=None):
        gui.Widget.__init__(self, position, parent)
        self.tank = WaterTank()
        self.tank_level = 0.0
        self.action_applied = 0.0
        self.control_point = 0.7

        self.selecting_control_point = False
        self.pressed = False
        self.frame_counter = 0

    def show(self, window, mouse_pos):
        if self.pressed:
            self.frame_counter += 1
            if self.frame_counter >= 2:
                self.selecting_control_point = True

        if self.selecting_control_point:
            self.control_point = (-mouse_pos[1] / 400.0) + (5 / 4)
            if self.control_point > 1:
                self.control_point = 1
            elif self.control_point < 0:
                self.control_point = 0
        pygame.draw.rect(window, (0, 0, 0), pygame.Rect(300 - 100 - 2, 100 - 2, 204, 404))
        pygame.draw.rect(window, (122, 122, 122), pygame.Rect(300-100, 100, 200, 400))
        pygame.draw.rect(window, (0, 100, 255), pygame.Rect(300 - 100, 500 - self.tank_level * 400, 200, 400*self.tank_level))
        pygame.draw.line(window, (255, 0, 0), (300 - 120, 500 - self.control_point * 400), (300+120, 500 - self.control_point * 400),8)

    def event_handler(self, mouse_position, event_type):
        if event_type == pygame.MOUSEBUTTONDOWN:
            if 300 - 120 - 2 <= mouse_position[0] <= 300+120+2 and \
                    500 - self.control_point * 400 - 4 <= mouse_position[1] <= 500 - self.control_point * 400 + 4:
                self.pressed = True
        elif event_type == pygame.MOUSEBUTTONUP:
            self.pressed = False
            self.frame_counter = 0
            self.selecting_control_point = False


class Application:
    def __init__(self, window):
        self.width = window.get_width()
        self.height = window.get_height()
        self.window = window

        self.tank_level = 0.0
        self.action_applied = 0.0
        self.running = True

        self.controller = None
        self.simulation_results = None
        self.simulation_finished = False
        self.simulation_running = False
        self.simulation_displaying = False
        self.current_simulation_index = 0

        self.elapsed_time = 0
        self.elapsed_time_s = 0.0

        sprites = {
            'arrow_left': pygame.image.load(
                path.join("Assets/button_yellow", "button_arrow_left.png")).convert_alpha(),
            'arrow_left_pressed': pygame.image.load(
                path.join("Assets/button_hover", "button_arrow_left_hover.png")).convert_alpha(),
            'settings': pygame.image.load(
                path.join("Assets/button_yellow", "button_setting.png")).convert_alpha(),
            'settings_pressed': pygame.image.load(path.join("Assets/button_hover", "button_setting_hover.png")).convert_alpha(),
            'menu_item_idle': pygame.image.load(
                path.join("Assets/button_yellow", "button_plain.png")).convert_alpha(),
            'menu_item_hover': pygame.image.load(
                path.join("Assets/button_hover", "button_plain_hover.png")).convert_alpha(),
            'run_idle': pygame.image.load(path.join("Assets/button_yellow", "button_arrow_top.png")).convert_alpha(),
            'run_pressed': pygame.image.load(
                path.join("Assets/button_hover", "button_arrow_top_hover.png")).convert_alpha(),
            'play_idle': pygame.image.load(path.join("Assets/button_yellow", "button_play.png")).convert_alpha(),
            'play_pressed': pygame.image.load(path.join("Assets/button_hover", "button_play_hover.png")).convert_alpha(),
            'save_idle': pygame.image.load(path.join("Assets/button_yellow", "button_save.png")).convert_alpha(),
            'save_pressed': pygame.image.load(
                path.join("Assets/button_hover", "button_save_hover.png")).convert_alpha(),
            'stop_idle': pygame.image.load(path.join("Assets/button_yellow", "button_pause.png")).convert_alpha(),
            'stop_pressed': pygame.image.load(
                path.join("Assets/button_hover", "button_pause_hover.png")).convert_alpha(),
            'restart_idle': pygame.image.load(path.join("Assets/button_yellow", "button_reload.png")).convert_alpha(),
            'restart_pressed': pygame.image.load(
                path.join("Assets/button_hover", "button_reload_hover.png")).convert_alpha(),
            'ok_idle': pygame.image.load(
                path.join("Assets/button_yellow", "button_yes.png")).convert_alpha(),
            'ok_pressed': pygame.image.load(
                path.join("Assets/button_hover", "button_yes_hover.png")).convert_alpha(),
            'panel': pygame.image.load(
                path.join("Assets", "painel.png")).convert_alpha()
        }

        buttons = {
            'settings': gui.PushButton([560, 15], [30, 30], [sprites['settings'], sprites['settings_pressed']]),
            'run_simulation': gui.PushButton([195, 100-45-10], [45, 45], [sprites['run_idle'], sprites['run_pressed']]),
            'play': gui.PushButton([195+55, 100-45-10], [45, 45], [sprites['play_idle'], sprites['play_pressed']]),
            'restart': gui.PushButton([195+110, 100-45-10], [45, 45], [sprites['restart_idle'], sprites['restart_pressed']]),
            'pause': gui.PushButton([195+55, 100-45-10], [45, 45], [sprites['stop_idle'], sprites['stop_pressed']]),
            'save_data': gui.PushButton([195+165, 100-45-10], [45, 45], [sprites['save_idle'], sprites['save_pressed']]),
        }
        buttons['settings'].connect_function(self.open_settings)
        buttons['run_simulation'].connect_function(self.start_simulation)
        buttons['play'].connect_function(self.play_simulation)
        buttons['pause'].connect_function(self.pause_simulation)
        buttons['restart'].connect_function(self.reset)
        buttons['save_data'].connect_function(self.save_simulation_results)

        buttons['pause'].disable()

        panels = {
            'time_panel': gui.Panel([10, 10], [80, 30], sprites['panel'], border=gui.Border(1, gui.Color.BLACK), text=gui.Text('00:000', 16, gui.Color.BLACK)),
            'controller_select': gui.Panel([10, 100], [165, 30], sprites['panel'], border=gui.Border(1, gui.Color.BLACK), text=gui.Text('Escolha o controlador', 16, gui.Color.BLACK))
        }

        progress_bars = {
            'progresso': gui.ProgressBar([5, 575], [100, 20], border=gui.Border(1, gui.Color.BLACK), background_color=(100, 100, 100))
        }

        dropdown_menu = {
            'controller_select': gui.DropdownMenu([50, 140], [80, 30], [sprites['menu_item_idle'], sprites['menu_item_hover']], border=gui.Border(1, (0, 0, 0)), parent=None),
        }

        text_edits = {}

        self.custom_controllers = get_custom_controllers()

        self.custom_controller_id = 0
        for controller in self.custom_controllers:
            dropdown_menu['controller_select'].add_item(controller['name'])
            current_y = 100
            for name in controller['variables']:
                default_value = str(controller['variables'][name])
                new_panel = gui.Panel([450, current_y], [35, 30], sprites['panel'], border=gui.Border(1, gui.Color.BLACK),text=gui.Text(name.capitalize(), 16, gui.Color.BLACK))
                new_edit = gui.TextEdit([495, current_y], [60, 30], sprites['panel'], border=gui.Border(1, gui.Color.BLACK), text=gui.Text(default_value, 16, gui.Color.BLACK))
                if current_y > 100:
                    new_panel.disable()
                    new_edit.disable()
                panels[name.capitalize()+controller['name']] = new_panel
                text_edits[name.capitalize()+controller['name']] = new_edit
                current_y += 45

        dropdown_menu['controller_select'].connect_on_item_select(self.change_custom_controller)

        self.tankWidget = WaterTankWidget([0, 0, 0])

        customs = {
            'tank': self.tankWidget
        }

        self.simulation_view = gui.Window(buttons, panels, text_edits, progress_bars, dropdown_menu, customs)
        self.simulation_view.enable()


        center_x = 350
        text_edits = {
            'dt': gui.TextEdit([center_x, 100], [65, 30], sprites['panel'], border=gui.Border(1, gui.Color.BLACK),
                                text=gui.Text('0.1', 16, gui.Color.BLACK)),
            'tank_height': gui.TextEdit([center_x, 145], [65, 30], sprites['panel'], border=gui.Border(1, gui.Color.BLACK),
                                text=gui.Text('1.0', 16, gui.Color.BLACK)),
            'tank_area': gui.TextEdit([center_x, 190], [65, 30], sprites['panel'], border=gui.Border(1, gui.Color.BLACK),
                                text=gui.Text('0.09', 16, gui.Color.BLACK)),
            'tank_escape_area': gui.TextEdit([center_x, 235], [65, 30], sprites['panel'], border=gui.Border(1, gui.Color.BLACK),
                                text=gui.Text('0.001', 16, gui.Color.BLACK)),
            'max_incoming_flow': gui.TextEdit([center_x, 280], [65, 30], sprites['panel'], border=gui.Border(1, gui.Color.BLACK),
                                text=gui.Text('20', 16, gui.Color.BLACK)),
        }

        center_x = center_x - 160
        panels = {
            'dt': gui.Panel([center_x, 100], [150, 30], sprites['panel'], border=gui.Border(1, gui.Color.BLACK),text=gui.Text('dt (s)', 16, gui.Color.BLACK)),
            'tank_height': gui.Panel([center_x, 145], [150, 30], sprites['panel'], border=gui.Border(1, gui.Color.BLACK),text=gui.Text('Tank Height (m)', 16, gui.Color.BLACK)),
            'tank_area': gui.Panel([center_x, 190], [150, 30], sprites['panel'], border=gui.Border(1, gui.Color.BLACK),text=gui.Text('Tank Area (m^2)', 16, gui.Color.BLACK)),
            'tank_escape_area': gui.Panel([center_x, 235], [150, 30], sprites['panel'], border=gui.Border(1, gui.Color.BLACK),text=gui.Text('Escape Area (m^2)', 16, gui.Color.BLACK)),
            'max_incoming_flow': gui.Panel([center_x, 280], [150, 30], sprites['panel'], border=gui.Border(1, gui.Color.BLACK),text=gui.Text('Max Flow (m^3/s)', 16, gui.Color.BLACK)),
        }

        buttons = {
            'go-back': gui.PushButton([10, 15], [45, 45], [sprites['arrow_left'], sprites['arrow_left_pressed']]),
        }
        buttons['go-back'].connect_function(self.return_to_simulation)

        self.configuration_view = gui.Window(buttons, panels, text_edits, {}, {})

    def run(self):
        timer = pygame.time.Clock()
        while self.running:
            pygame.draw.rect(self.window, (100, 200, 80), pygame.Rect(0, 0, self.width, self.height))
            self.event_handler()
            dt = timer.tick(60)

            if self.simulation_finished:
                if self.simulation_displaying:
                    self.set_time_text(get_elapsed_time_string(self.elapsed_time))
                    self.current_simulation_index = get_closest_index(self.simulation_results.time, self.elapsed_time_s)
                    self.tankWidget.tank_level = self.simulation_results.height[self.current_simulation_index]
                    self.elapsed_time += dt
                    self.elapsed_time_s += dt / 1000
            self.simulation_view.show(self.window, pygame.mouse.get_pos())
            self.configuration_view.show(self.window, pygame.mouse.get_pos())

            pygame.display.update()

    def open_settings(self):
        self.simulation_view.disable()
        self.configuration_view.enable()

    def return_to_simulation(self):
        self.simulation_view.enable()
        self.configuration_view.disable()

    def start_simulation(self):
        if not self.simulation_running:
            args = {}
            for name in self.custom_controllers[self.custom_controller_id]['variables']:
                key = name.capitalize()+self.custom_controllers[self.custom_controller_id]['name']
                value = self.simulation_view.text_edits[key].get_text_as_float()
                args[name] = value

            self.controller = self.custom_controllers[self.custom_controller_id]['class'](**args)

            simulation_thread = threading.Thread(target=self.tankWidget.tank.simulate, args=(10, 0.001, 0, self.controller, self.tankWidget.control_point,
                     self.on_simulation_finished, None,
                     self.update_progress_bar, None,
                     False,))
            simulation_thread.start()
            self.simulation_finished = False
            self.simulation_running = True
            self.simulation_view.buttons['play'].enable()
            self.simulation_view.buttons['pause'].disable()

    def play_simulation(self):
        if self.simulation_finished:
            self.simulation_displaying = True
            self.simulation_view.buttons['pause'].enable()
            self.simulation_view.buttons['play'].disable()

    def on_simulation_finished(self, results):
        self.simulation_results = results
        self.simulation_finished = True
        self.simulation_running = False
        self.elapsed_time = 0
        self.elapsed_time_s = 0.0

    def update_progress_bar(self, percentage):
        value = percentage/100.0
        self.simulation_view.progress_bars['progresso'].set_value(value)

    def set_time_text(self, txt):
        self.simulation_view.panels['time_panel'].set_text(txt)

    def pause_simulation(self):
        if self.simulation_displaying:
            self.simulation_displaying = False
            self.simulation_view.buttons['play'].enable()
            self.simulation_view.buttons['pause'].disable()

    def reset(self):
        self.tankWidget.tank_level = 0.0
        self.elapsed_time = 0
        self.elapsed_time_s = 0.0
        self.simulation_displaying = False
        self.simulation_running = False
        self.set_time_text('00:000')

        self.simulation_view.buttons['play'].enable()
        self.simulation_view.buttons['pause'].disable()

    def save_simulation_results(self):
        if self.simulation_finished:
            file = g.filesavebox('Save Simulation Results')
            self.save_data(file)

    def save_thread(self, file):
        data_size = len(self.simulation_results.time)
        headers = ['Time', 'Height', 'Error', 'Action']
        units = ['', ' (m)', ' (m)', '']
        max_time = self.simulation_results.time[data_size-1]

        wb = Workbook()
        sheet = wb.active
        sheet.append(headers)

        for i in range(0, data_size):
            sheet.append([
                self.simulation_results.time[i], self.simulation_results.height[i], self.simulation_results.error[i],
                self.simulation_results.action[i]
            ])
        for i in range(1, 4):
            header = headers[i]
            chart = ScatterChart()
            chart.title = header + ' x Time'
            chart.style = 13
            chart.x_axis.title = 'Time (s)'
            chart.y_axis.title = header + units[i]
            chart.x_axis.scaling.min = 0
            chart.x_axis.scaling.max = max_time

            x_values = Reference(sheet, min_col=1, min_row=2, max_row=data_size)
            y_values = Reference(sheet, min_col=i+1, min_row=2, max_row=data_size)
            series = Series(y_values, x_values)
            chart.series.append(series)

            row = 2+15*(i-1)
            sheet.add_chart(chart, 'F'+str(row))

        wb.save(file)

    def save_data(self, file):
        thread = threading.Thread(target=self.save_thread, args=(file,))
        thread.start()

    def change_custom_controller(self, item, item_id):
        self.custom_controller_id = item_id
        for index, controller in enumerate(self.custom_controllers):
            for name in controller['variables']:
                key = name.capitalize()+controller['name']
                if index != item_id:
                    self.simulation_view.text_edits[key].disable()
                    self.simulation_view.panels[key].disable()
                else:
                    self.simulation_view.text_edits[key].enable()
                    self.simulation_view.panels[key].enable()

    def event_handler(self):
        mouse_pos = pygame.mouse.get_pos()
        events = pygame.event.get()
        
        for event in events:
            if event.type == pygame.QUIT:
                self.close()

            self.simulation_view.event_handler(event, mouse_pos)
            self.configuration_view.event_handler(event, mouse_pos)

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