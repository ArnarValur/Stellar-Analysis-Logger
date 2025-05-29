import tkinter as tk
from tkinter import ttk
import myNotebook as nb # ADDED: Import myNotebook
from .constants import CheckStates
from .logger import logger
from .widgets import EntryPlus

class UIManager:
    def __init__(self, settings_manager, plugin_globals):
        logger.info("UIManager __init__ called.")
        self.settings_manager = settings_manager
        self.plugin_globals = plugin_globals

    def create_settings_ui(self, parent, cmdr, is_beta):
        logger.info("UIManager create_settings_ui called.")
        if not self.settings_manager:
            logger.error("SettingsManager not available for UIManager.")
            return None

        # frame = ttk.Frame(parent) # OLD
        frame = nb.Frame(parent) # MODIFIED: Use nb.Frame
        frame.columnconfigure(1, weight=1)

        # Plugin Enabled Checkbutton
        # Try with ttk.Checkbutton first, change to nb.Checkbutton if issues persist
        plugin_enabled_checkbutton = nb.Checkbutton( # MODIFIED: Use nb.Checkbutton
            frame,
            text="Enable Plugin",
            variable=self.settings_manager.plugin_enabled_var,
            onvalue=CheckStates.STATE_ON.value,
            offvalue=CheckStates.STATE_OFF.value,
            command=lambda: self.plugin_globals.prefs_changed_callback(cmdr, is_beta)
        )
        plugin_enabled_checkbutton.grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)

        # API URL
        # Try with ttk.Label first, change to nb.Label if issues persist
        nb.Label(frame, text="API URL:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2) # MODIFIED: Use nb.Label
        api_url_entry = EntryPlus(frame, textvariable=self.settings_manager.api_url_var)
        api_url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        # API Key
        # Try with ttk.Label first, change to nb.Label if issues persist
        nb.Label(frame, text="API Key (Optional):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2) # MODIFIED: Use nb.Label
        api_key_entry = EntryPlus(frame, textvariable=self.settings_manager.api_key_var)
        api_key_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        # Try with ttk.Label first, change to nb.Label if issues persist
        nb.Label(frame, text="Note: Some settings may require an EDMC restart to take full effect.").grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=10) # MODIFIED: Use nb.Label

        logger.info(f"UIManager create_settings_ui returning frame: {frame}, type: {type(frame).__name__}")
        return frame
