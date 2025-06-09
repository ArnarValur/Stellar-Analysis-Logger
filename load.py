from os import path

import sal.globals
from sal.sal import Sal
from sal.constants import (
    PluginInfo,
)

# Initialize the global Sal instance
# Ensure this is done safely, though it's typically top-level
if not hasattr(sal.globals, 'this') or sal.globals.this is None:
    sal.globals.this = Sal(PluginInfo.PLUGIN_NAME, PluginInfo.PLUGIN_VERSION)

# It's good practice to assign 'this' to a local variable for clarity if used extensively in this module,
# but direct use of sal.globals.this is also fine.
this = sal.globals.this # Local alias for convenience

def plugin_start3(plugin_dir):
    """
    Called when the plugin is loaded by EDMC (Python 3 version).
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
    Parse an incoming journal entry and store the data we need
    """
    this.journal_entry(cmdr, is_beta, system, station, entry, state)

def plugin_prefs(parent, cmdr: str, is_beta: bool):
    """
    Called to display the plugin's settings panel.
    Delegates to the Sal instance's UI manager.
    """
    if this and this.ui:
        return this.ui.get_settings_pref(parent, cmdr, is_beta)
    
    # Log an error if ui component is not available
    if this and this.logger:
        this.logger.get_logger().error("UI manager (this.ui) not available for plugin_prefs.")
    # Fallback: return None or a simple placeholder Frame if UI can't be generated
    # For maximum cleanliness in load.py, complex placeholder generation is omitted here.
    # Consider adding a simple tk.Frame with an error label if essential.
    return None


def prefs_changed(cmdr: str, is_beta: bool) -> None:
    """
    Called when the plugin's settings are changed.
    Delegates to the Sal instance's settings manager.
    """
    if this and this.settings:
        this.settings.save_settings()
    elif this and this.logger: # Log if settings object isn't available
        this.logger.get_logger().error("Settings manager (this.settings) not available for prefs_changed.")
