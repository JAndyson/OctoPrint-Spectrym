import octoprint.plugin
from octoprint.events import EventManager, Events
import octoprint.printer
import os
import re
import requests
import pigpio
import time
from gpiozero import OutputDevice, Device 
import gpiozero
from gpiozero.pins.mock import MockFactory
import threading


class SpectrymPlugin(octoprint.plugin.StartupPlugin,
                     octoprint.plugin.EventHandlerPlugin,
                     octoprint.plugin.SettingsPlugin,
                     octoprint.plugin.TemplatePlugin,
                     octoprint.plugin.OctoPrintPlugin):

    def get_settings_defaults(self):
        return dict(
            sleep_time = 1
        )

    def __init__(self):
        self._current_color_red = False
        self._current_color_green = False
        self.pin_factory = MockFactory()
        Device.pin_factory = MockFactory()
        os.system("sudo pigpiod")
        self._stop_event = threading.Event()
        self._running = False
       # self._settings = self.get_settings_defaults()
       # self.sleep_time = self._settings["sleep_time"]

    def on_after_startup(self):
        self._logger.info("Spectrym Plugin Loaded")
        sleep_time = self._settings.get_float(["sleep_time"])
        self._logger.info("Sleep time: " + str(sleep_time))

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]

    def on_settings_save(self, data):
        self._logger.info("Settings saved")
        old_time = self._settings.get_float(["sleep_time"])
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        new_time = self._settings.get_float(["sleep_time"])
        if old_time != new_time:
            self._logger.info("Sleep time changed")
            self.sleep_time = new_time

    def rewrite_m107(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        if cmd and cmd == "T0":
            self._logger.info("T0 Command detected through hook")
            self._set_color_red()
        elif cmd and cmd == "T1":
            self._logger.info("T1 Command detected through hook")
            self._set_color_green()
        elif cmd and cmd == "T3":
            self._stop_all_motors()
        
    def on_event(self, event, payload):
        if event == "PrintStarted":
            self._logger.info("Print started")
        elif event == "PrintCancelled" or event == "PrintDone":
            self._stop_all_motors()

    def _set_color_red(self):
        if not self._current_color_red:
            self._logger.info("color set red")
            self.step_pin = OutputDevice(23)
            self.dir_pin = OutputDevice(24)
            self.dir_pin.on()
            self._logger.info("Red color selected")
            self._current_color_red = True
            self._stop_event.clear()
            self.thread = threading.Thread(target=self._step_motor)
            self.thread.start()
    
    def _set_color_green(self):
        if not self._current_color_green:
            self.step_pin2 = OutputDevice(22)
            self.dir_pin2 = OutputDevice(27)
            self.dir_pin2.on()
            self._logger.info("Green color selected")
            self._current_color_green = True
            self._stop_event.clear()
            self.thread = threading.Thread(target=self._step_motor2)
            self.thread.start()

    def _step_motor(self):
        while not self._stop_event.is_set():
            self.step_pin.on()
            time.sleep(self.sleep_time)
            self.step_pin.off()
            time.sleep(self.sleep_time)
        self.step_pin.off()
        self.dir_pin.off()
        self.step_pin.close()
        self.dir_pin.close()

    def _step_motor2(self):
        while not self._stop_event.is_set():
            self.step_pin2.on()
            time.sleep(self.sleep_time)
            self.step_pin2.off()
            time.sleep(self.sleep_time)
        self.step_pin.off()
        self.dir_pin.off()
        self.step_pin2.close()
        self.dir_pin2.close()
            
    def _stop_all_motors(self):
        self._stop_event.set()
        self._current_color_red = False
        self._current_color_green = False
        self.thread.join()

__plugin_name__ = "Spectrym"
__plugin_pythoncompat__ = ">=3.7,<4"
__plugin_implementation__ = SpectrymPlugin()

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = SpectrymPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.rewrite_m107
    }