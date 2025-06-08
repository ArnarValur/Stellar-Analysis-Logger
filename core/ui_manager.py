import tkinter as tk
import myNotebook as nb # type: ignore

from tkinter import ttk
from .constants import CheckStates, PLUGIN_NAME_FOR_LOGGING
from .logger import logger
from .widgets import EntryPlus

class UIManager:
    def __init__(self, settings_manager, plugin_globals):
        """ Initializes the UIManager with the settings manager and plugin globals."""
        self.settings_manager = settings_manager
        self.plugin_globals = plugin_globals

    def create_settings_ui(self, parent, cmdr, is_beta):
        """ Creates the settings UI for the plugin."""
        if not self.settings_manager:
            return None

        frame = nb.Frame(parent)
        frame.columnconfigure(1, weight=1)

        # Plugin Enabled Checkbutton
        plugin_enabled_checkbutton = nb.Checkbutton(
            frame,
            text="Enable Plugin",
            variable=self.settings_manager.plugin_enabled_var,
            onvalue=CheckStates.STATE_ON.value,
            offvalue=CheckStates.STATE_OFF.value,
            command=lambda: self.plugin_globals.prefs_changed_callback(cmdr, is_beta)
        )
        plugin_enabled_checkbutton.grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)

        # API URL
        nb.Label(frame, text="API URL:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        api_url_entry = EntryPlus(frame, textvariable=self.settings_manager.api_url_var)
        api_url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        # API Key
        nb.Label(frame, text="API Key (Optional):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        api_key_entry = EntryPlus(frame, textvariable=self.settings_manager.api_key_var)
        api_key_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        # Developer Mode Checkbutton
        dev_mode_checkbutton = nb.Checkbutton(
            frame,
            text="Enable Developer Mode Logging",
            variable=self.settings_manager.dev_mode_enabled_var,
            onvalue=CheckStates.STATE_ON.value,
            offvalue=CheckStates.STATE_OFF.value,
            command=lambda: self.plugin_globals.prefs_changed_callback(cmdr, is_beta)
        )
        dev_mode_checkbutton.grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)

        # System Lookup Checkbutton
        system_lookup_checkbutton = nb.Checkbutton(
            frame,
            text="Enable System Lookup",
            variable=self.settings_manager.system_lookup_enabled_var,
            onvalue=CheckStates.STATE_ON.value,
            offvalue=CheckStates.STATE_OFF.value,
            command=lambda: self.plugin_globals.prefs_changed_callback(cmdr, is_beta)
        )
        system_lookup_checkbutton.grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)

        nb.Label(frame, text="Note: Some settings may require an EDMC restart to take full effect.").grid(row=5, column=0, columnspan=2, sticky=tk.W, padx=5, pady=10)

        return frame
