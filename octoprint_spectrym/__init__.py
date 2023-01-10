import octoprint.plugin
import os
import re
import requests
import pigpio
import time

class SpectrymPlugin(octoprint.plugin.StartupPlugin,
                     octoprint.plugin.EventHandlerPlugin,
                     octoprint.plugin.SettingsPlugin):

    def on_after_startup(self):
        os.system("sudo pigpiod")

    def on_event(self, event, payload):
        if event == "PrintStarted":
            self._gcode_watcher = self._watch
            self._gcode_watcher.start()
        elif event == "PrintCancelled" or event == "PrintDone":
            self._gcode_watcher.stop()

    def __init__(self):
        self._regex_T0 = re.compile(r"^T0")  # match any T0 command
        self._regex_T1 = re.compile(r"^T1")  # match any T1 command
        self._current_color_red = False
        self._current_color_green = False
        self._running = False

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
                    self._stop_all_motors()
                    self._set_color_red()
                elif self._regex_T1.match(gcode):
                # do something when a matching gcode command is seen
                    self._stop_all_motors()
                    self._set_color_green()

    def _get_current_gcode(self):
        # send a GET request to the /api/printer/printhead endpoint
        r = requests.get("http://localhost:5000/api/printer/printhead")

        # check the status code of the response
        if r.status_code == 200:
            # get the current gcode command from the response
            data = r.json()
            return data["current"]["command"]
        else:
            # handle the error
            return None


    def _set_color_red(self):
        if not self._current_color_red:
        # replace this with code that does something when a matching gcode command is seen
            # set up the pigpio library
            pi = pigpio.pi()

            # set up the pins for the first motor
            dir_pin = 14
            step_pin = 15 

            # set the direction of the motor
            pi.write(dir_pin, 1)  # 1 for clockwise, 0 for counterclockwise

            # set the motor to active
            self._current_color_red = True

            while self._current_color_red:
                # step the motor
                pi.write(step_pin, 1)
                time.sleep(0.01)  # delay for 10 milliseconds
                pi.write(step_pin, 0)
                time.sleep(0.01)  # delay for 10 milliseconds

            # clean up the pigpio library
            pi.stop()

    def _set_color_green(self):
        if not self._current_color_green:
            # set up the pigpio library
            pi = pigpio.pi()

            # set up the pins for the second motor
            dir_pin = 23
            step_pin = 24

            # set the direction of the motor
            pi.write(dir_pin, 1)  # 1 for clockwise, 0 for counterclockwise

            # set the motor to active
            self._current_color_green = True

            while self._current_color_green:
                # step the motor
                pi.write(step_pin, 1)
                time.sleep(0.01)  # delay for 10 milliseconds
                pi.write(step_pin, 0)
                time.sleep(0.01)    # delay for 10 milliseconds

            # clean up the pigpio library
            pi.stop()

    def _clear_color_red(self):
        if self._current_color_red:
            # set up the pigpio library
            pi = pigpio.pi()

            # set up the pins for the first motor
            dir_pin = 14
            step_pin = 15

            # set the motor to inactive
            self._current_color_red = False

            # clean up the pigpio library
            pi.stop()

    def _clear_color_green(self):
        if self._current_color_green:
            # set up the pigpio library
            pi = pigpio.pi()

            # set up the pins for the second motor
            dir_pin = 23
            step_pin = 24

            # set the motor to inactive
            self._current_color_green = False

            # clean up the pigpio library
            pi.stop()
    
    def _stop_all_motors(self):
        self._clear_color_red()
        self._clear_color_green()

__plugin_name__ = "Spectrym"
__plugin_pythoncompat__ = ">=3.7,<4"
__plugin_implementation__ = SpectrymPlugin()