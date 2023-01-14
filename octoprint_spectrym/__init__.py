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
from gpiozero.pins.rpigpio import RPiGPIOFactory
import threading


class SpectrymPlugin(octoprint.plugin.StartupPlugin,
                     octoprint.plugin.EventHandlerPlugin,
                     octoprint.plugin.SettingsPlugin):

    def __init__(self, *args, **kwargs):
        self._regex_T0 = re.compile(r"^T0")  # match any T0 command
        self._regex_T1 = re.compile(r"^T1")  # match any T1 command
        self._current_color_red = False
        self._current_color_green = False
        #self.pin_factory = RPiGPIOFactory()
        #Device.pin_factory = RPiGPIOFactory()
        #os.system("sudo pigpiod")
        self._stop_event = threading.Event()
        self._running = False
        super(SpectrymPlugin, self).__init__(*args, **kwargs)
        self._printer = octoprint.printer.PrinterInterface()

    def on_after_startup(self):
        self._printer.register_callback(self.queuing_gcode, "gcodequeing")
        self._logger.info("Spectrym Plugin Loaded")

    def queuing_gcode(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        if cmd.startswith("T0"):
            self._logger.info("T0 command detected")
            self._stop_all_motors()
            self._set_color_red()
        if cmd.startswith("T1"):
            self._logger.info("T1 command detected")
            self._stop_all_motors()
            self._set_color_green()
    
    def on_event(self, event, payload):
        if event == "PrintStarted":
            self._logger.info("Print started")
            self._start_watcher()
        elif event == "PrintCancelled" or event == "PrintDone":
            self._stop_watcher()
            self._stop_all_motors()
        elif event == Events.TOOL_CHANGE:
            self._logger.info("Tool changed")
            

    def _start_watcher(self):
        self._watch_gcode = True
        self._watch_thread = threading.Thread(target=self._watch_loop)
        self._watch_thread.start()

    def _watch_loop(self):
        while self._watch_gcode:
            if self._printer.is_printing():
                current_gcode = self._printer.get_current_data()["job"]["file"]["gcode"]
                self._logger.info(current_gcode)
                if current_gcode.startswith("T0"):
                    self._logger.info("T0 command detected")
                    self._stop_all_motors()
                    self._set_color_red()
                elif current_gcode.startswith("T1"):
                    self._stop_all_motors()
                    self._set_color_green()
            time.sleep(1)

    def _stop_watcher(self):
        self._watch_gcode = False
        self._watch_thread.join()

#    def _get_current_gcode(self):
 #       headers = {"X-Api-Key": "D0585AC8B0E34E95901259D78CB67CC2"}
  #      # send a GET request to the /api/job endpoint
   #     r = requests.get("http://localhost:5000/api/job", headers=headers)
    #    r.raise_for_status()
#
 #       # check the status code of the response
  #      if r.status_code == 200:
   #         # get the current gcode command from the response
    #        data = r.json()
     #       return data["job"]["gcode"]
      #  else:
       #     self._logger.error(f"Error while trying to get current gcode: {r.status_code} - {r.text}")
        #    return None


    def _set_color_red(self):
        if not self._current_color_red:
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
            time.sleep(0.165)
            self.step_pin.off()
            time.sleep(0.165)
        self.step_pin.close()
        self.dir_pin.close()

    def _step_motor2(self):
        while not self._stop_event.is_set():
            self.step_pin2.on()
            time.sleep(0.165)
            self.step_pin2.off()
            time.sleep(0.165)
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
    }