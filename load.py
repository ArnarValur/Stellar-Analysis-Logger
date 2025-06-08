from os import path

import sal.globals
from sal.sal import Sal
from sal.logger import PluginLogger
from sal.constants import (
    PluginInfo,
)

# Initialize the global Sal instance
sal.globals.this = this = Sal(PluginInfo.PLUGIN_NAME, PluginInfo.PLUGIN_VERSION)

def plugin_start3(plugin_dir):
    """
    Called when the plugin is loaded by EDMC (Python 3 version)
    """
    this.plugin_start(plugin_dir)
    return this.plugin_name


def plugin_stop():
    """
    Called when the plugin is unloded by EDMC
    """
    this.plugin_stop()


def journal_entry(cmdr, is_beta, system, station, entry, state):
    """
    Called for each journal entry
    """
   

def plugin_prefs(parent, cmdr: str, is_beta: bool):
    """
    Called to display the plugin's settings panel
    """
    return this.ui.get_settings_pref(parent, cmdr, is_beta)


def prefs_changed(cmdr: str, is_beta: bool) -> None:
    """
    Called when the plugin's settings are changed
    """
    #this.ui.save_plugin_prefs()
