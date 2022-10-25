# Bibliotecas externasz
import os  # Biblioteca para direcionamento do endereço dos arquivos.
from bisect import bisect_left
import threading
import easygui as g
import openpyxl
from openpyxl.chart import Reference, ScatterChart, Series

import pygame  # Biblioteca para a janela do jogo e evento de mouse.
import pygame.freetype  # Sub biblioteca para a fonte.

# Meu código
from GUI import widgets as gui

# Classe do manager do Jogo.
from simulator import WaterTank, get_custom_controllers


class Application:
    def __init__(self, window):
        self.width = window.get_width()
        self.height = window.get_height()
        self.window = window

        self.tank_level = 0.0
        self.action_applied = 0.0
        self.running = True

        self.tank = WaterTank()
        self.controller = None
        self.simulation_results = None
        self.simulation_finished = False
        self.simulation_running = False
        self.simulation_displaying = False
        self.current_simulation_index = 0

        self.elapsed_time = 0
        self.elapsed_time_s = 0.0

        self.sprites = {
            'menu_item_idle': pygame.image.load(os.path.join("Assets/button_yellow", "button_plain.png")).convert_alpha(),
            'menu_item_hover': pygame.image.load(
                os.path.join("Assets/button_hover", "button_plain_hover.png")).convert_alpha(),
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
        buttons = {
            'run_simulation': gui.PushButton([195, 100-45-10], [45, 45], [self.sprites['run_idle'], self.sprites['run_pressed']]),
            'play': gui.PushButton([195+55, 100-45-10], [45, 45], [self.sprites['play_idle'], self.sprites['play_pressed']]),
            'restart': gui.PushButton([195+110, 100-45-10], [45, 45], [self.sprites['restart_idle'], self.sprites['restart_pressed']]),
            'pause': gui.PushButton([195+55, 100-45-10], [45, 45], [self.sprites['stop_idle'], self.sprites['stop_pressed']]),
            'save_data': gui.PushButton([195+165, 100-45-10], [45, 45], [self.sprites['save_idle'], self.sprites['save_pressed']]),
        }
        buttons['run_simulation'].connect_function(self.start_simulation)
        buttons['play'].connect_function(self.play_simulation)
        buttons['pause'].connect_function(self.pause_simulation)
        buttons['restart'].connect_function(self.reset)
        buttons['save_data'].connect_function(self.save_simulation_results)

        buttons['pause'].disable()

        panels = {
            'time_panel': gui.Panel([10, 10], [80, 30], self.sprites['panel'], border=gui.Border(1, gui.Color.BLACK), text=gui.Text('00:000', 16, gui.Color.BLACK)),
            'controller_select': gui.Panel([10, 100], [165, 30], self.sprites['panel'], border=gui.Border(1, gui.Color.BLACK), text=gui.Text('Escolha o controlador', 16, gui.Color.BLACK))
        }

        progress_bars = {
            'progresso': gui.ProgressBar([5, 575], [100, 20], border=gui.Border(1, gui.Color.BLACK), background_color=(100, 100, 100))
        }

        dropdown_menu = {
            'controller_select': gui.DropdownMenu([50, 140], [80, 30], [self.sprites['menu_item_idle'], self.sprites['menu_item_hover']], border=gui.Border(1, (0, 0, 0)), parent=None),
        }

        text_edits = {}

        self.custom_controllers = get_custom_controllers()

        self.custom_controller_id = 0
        for controller in self.custom_controllers:
            dropdown_menu['controller_select'].add_item(controller['name'])
            current_y = 100
            for name in controller['variables']:
                default_value = str(controller['variables'][name])
                new_panel = gui.Panel([450, current_y], [35, 30], self.sprites['panel'], border=gui.Border(1, gui.Color.BLACK),text=gui.Text(name.capitalize(), 16, gui.Color.BLACK))
                new_edit = gui.TextEdit([495, current_y], [60, 30], self.sprites['panel'], border=gui.Border(1, gui.Color.BLACK), text=gui.Text(default_value, 16, gui.Color.BLACK))
                if current_y > 100:
                    new_panel.disable()
                    new_edit.disable()
                panels[name.capitalize()+controller['name']] = new_panel
                text_edits[name.capitalize()+controller['name']] = new_edit
                current_y += 45

        dropdown_menu['controller_select'].connect_on_item_select(self.change_custom_controller)

        self.widgets = gui.Window(buttons, panels, text_edits, progress_bars, dropdown_menu)

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
            args = {}
            for name in self.custom_controllers[self.custom_controller_id]['variables']:
                key = name.capitalize()+self.custom_controllers[self.custom_controller_id]['name']
                value = self.widgets.text_edits[key].get_text_as_float()
                args[name] = value

            self.controller = self.custom_controllers[self.custom_controller_id]['class'](**args)

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

    #TODO
    def save_simulation_results(self):
        if self.simulation_finished:
            file = g.filesavebox('Save Simulation Results')
            self.save_data(file)

    def save_thread(self, file):
        data_size = len(self.simulation_results.time)
        headers = ['Time', 'Height', 'Error', 'Action']
        units = ['', ' (m)', ' (m)', '']
        max_time = self.simulation_results.time[data_size-1]

        wb = openpyxl.Workbook()
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
                    self.widgets.text_edits[key].disable()
                    self.widgets.panels[key].disable()
                else:
                    self.widgets.text_edits[key].enable()
                    self.widgets.panels[key].enable()

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