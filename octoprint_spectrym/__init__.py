import octoprint.plugin
import os
import re
import requests
import pigpio
import time
from gpiozero import OutputDevice, Device 
import gpiozero
from gpiozero.pins.rpigpio import RPiGPIOFactory
import threading


class SpectrymPlugin(octoprint.plugin.StartupPlugin,
                     octoprint.plugin.EventHandlerPlugin,
                     octoprint.plugin.SettingsPlugin):

    def __init__(self):
        self._regex_T0 = re.compile(r"^T0")  # match any T0 command
        self._regex_T1 = re.compile(r"^T1")  # match any T1 command
        self._current_color_red = False
        self._current_color_green = False
        #self.pin_factory = RPiGPIOFactory()
        #Device.pin_factory = RPiGPIOFactory()
        #os.system("sudo pigpiod")
        self._stop_event = threading.Event()


    def on_after_startup(self):
        self._logger.info("Spectrym Plugin Loaded")
    
    def on_event(self, event, payload):
        if event == "PrintStarted":
            self._logger.info("Print started")
            self._gcode_watcher = self._watch()
            self.start()
        elif event == "PrintCancelled" or event == "PrintDone":
            self.stop()
            self._stop_all_motors()
        elif event == "UserLoggedIn":
            self._logger.info("User logged in")
            self._set_color_green()
            

    def start(self):
        self._running = True
        self._watch()

    def stop(self):
        self._running = False
        self._stop_all_motors()

    def _watch(self):
        while self._running:
            gcode = self._get_current_gcode()
            if gcode: 
                if self._regex_T0.match(gcode):
                # do something when a matching gcode command is seen
                    self._logger.info("T0 command detected")
                    self._stop_all_motors()
                    self._set_color_red()
                elif self._regex_T1.match(gcode):
                # do something when a matching gcode command is seen
                    self._stop_all_motors()
                    self._set_color_green()

    def _get_current_gcode(self):
        # send a GET request to the /api/job endpoint
        r = requests.get("http://localhost:5000/api/job")

        # check the status code of the response
        if r.status_code == 200:
            # get the current gcode command from the response
            data = r.json()
            return data["job"]["gcode"]
        else:
            self._logger.error(f"Error while trying to get current gcode: {r.status_code} - {r.text}")
            return None


    def _set_color_red(self):
        if not self._current_color_red:
            self.step_pin = OutputDevice(23)
            self.dir_pin = OutputDevice(24)
            self.dir_pin.on()
            self._logger.info("Red color selected")
            self._current_color_red = True
            self._stop_event.clear()
            thread = threading.Thread(target=self._step_motor)
            thread.start()
    
    def _set_color_green(self):
        if not self._current_color_green:
            self.step_pin2 = OutputDevice(22)
            self.dir_pin2 = OutputDevice(27)
            self.dir_pin2.on()
            self._logger.info("Green color selected")
            self._current_color_green = True
            self._stop_event.clear()
            thread = threading.Thread(target=self._step_motor2)
            thread.start()

    def _step_motor(self):
        while not self._stop_event.is_set():
            self.step_pin.on()
            time.sleep(0.165)
            self.step_pin.off()
            time.sleep(0.165)

    def _step_motor2(self):
        while not self._stop_event.is_set():
            self.step_pin2.on()
            time.sleep(0.165)
            self.step_pin2.off()
            time.sleep(0.165)
            
    
    def _stop_all_motors(self):
        self._stop_event.set()
        self._current_color_red = False
        self._current_color_green = False
        self.step_pin.off()
        self.dir_pin.off()

__plugin_name__ = "Spectrym"
__plugin_pythoncompat__ = ">=3.7,<4"
__plugin_implementation__ = SpectrymPlugin()

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = SpectrymPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
    }