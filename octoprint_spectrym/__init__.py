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
        self._logger.info("Spectrym Plugin Loaded")
        self._logger.info("Enabling pigpio daemon")
        os.system("sudo pigpiod")

__plugin_name__ = "Spectrym"
__plugin_pythoncompat__ = ">=3.7,<4"
__plugin_implementation__ = SpectrymPlugin()

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = SpectrymPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.on_after_startup
    }