import tkinter as tk
import myNotebook as nb # type: ignore
from tkinter import ttk
from .constants import CheckSettings, PluginInfo
from .widgets import EntryPlus

class UIManager:
    def __init__(self, sal):
        """Initializes the UIManager with the SAL instance."""
        self.sal = sal
        self.frame = None

    def get_settings_pref(self, parent_frame, cmdr, is_beta):
        """Creates the settings UI for the plugin."""
        frame = nb.Frame(parent_frame)
        frame.columnconfigure(1, weight=1)

        # Plugin Enabled Checkbutton
        plugin_enabled_checkbutton = nb.Checkbutton(
            frame,
            text="Enable Plugin",
            variable=self.sal.settings.PluginEnabled,
            onvalue=CheckSettings.SETTINGS_ON,
            offvalue=CheckSettings.SETTINGS_OFF, 
            command=self.sal.settings.save_settings
        )
        plugin_enabled_checkbutton.grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)

        # API URL
        nb.Label(frame, text="API URL:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        api_url_entry = EntryPlus(frame, textvariable=self.sal.settings.APIUrl) # Save on change
        api_url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        api_url_entry.bind("<FocusOut>", lambda event: self.sal.settings.save_settings())
        api_url_entry.bind("<Return>", lambda event: self.sal.settings.save_settings())

        # API Key
        nb.Label(frame, text="API Key (Optional):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        api_key_entry = EntryPlus(frame, textvariable=self.sal.settings.APIKey) # Save on change
        api_key_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        api_key_entry.bind("<FocusOut>", lambda event: self.sal.settings.save_settings())
        api_key_entry.bind("<Return>", lambda event: self.sal.settings.save_settings())

        # Developer Mode Checkbutton
        dev_mode_checkbutton = nb.Checkbutton(
            frame,
            text="Enable Developer Mode Logging",
            variable=self.sal.settings.DeveloperMode,
            onvalue=CheckSettings.SETTINGS_ON,
            offvalue=CheckSettings.SETTINGS_OFF,
            command=self.sal.settings.save_settings
        )
        dev_mode_checkbutton.grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)

        # System Lookup Checkbutton
        system_lookup_checkbutton = nb.Checkbutton(
            frame,
            text="Enable System Lookup",
            variable=self.sal.settings.SystemLookup,
            onvalue=CheckSettings.SETTINGS_ON,
            offvalue=CheckSettings.SETTINGS_OFF,
            command=self.sal.settings.save_settings
        )
        system_lookup_checkbutton.grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)

        nb.Label(frame, text="Note: Some settings may require an EDMC restart to take full effect.").grid(row=5, column=0, columnspan=2, sticky=tk.W, padx=5, pady=10)

        return frame
