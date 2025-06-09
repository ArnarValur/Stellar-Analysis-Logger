import os
import tkinter as tk
from sal.logger import PluginLogger

from sal.constants import *
from config import config  # type: ignore

class Settings:
    """
    Manages the plugin's settings, loading them from EDMC's config and providing
    Tkinter variables for the UI.
    """

    def __init__(self, sal):
        """Initialize the Settings and load settings from EDMC's config."""
        self.sal = sal
        self.load_settings()

        if self.developer_mode:
            # Example of using the logger passed from Sal instance
            PluginLogger.logger.info(f"SAL [Settings]: Developer mode is ON. \nRaw settings values:\nPluginEnabled: {self.PluginEnabled.get()}\nAPIUrl: {self.APIUrl.get()}\nAPIKey: {self.APIKey.get()}\nDeveloperMode: {self.DeveloperMode.get()}\nSystemLookup: {self.SystemLookup.get()}")


    def load_settings(self):
        """
        Load settings from EDMC's config.
        StringVars will hold "True" or "False" as strings.
        """
        # Determine string default based on boolean DefaultSettings values from constants.py
        # These defaults will be strings: "True" or "False"
        plugin_default_str = CheckSettings.SETTINGS_ON if DefaultSettings.PLUGIN_ENABLED else CheckSettings.SETTINGS_OFF
        dev_mode_default_str = CheckSettings.SETTINGS_ON if DefaultSettings.DEV_MODE_ENABLED else CheckSettings.SETTINGS_OFF
        system_lookup_default_str = CheckSettings.SETTINGS_ON if DefaultSettings.SYSTEM_LOOKUP_ENABLED else CheckSettings.SETTINGS_OFF

        # Get string value from config, or use the string default.
        # The value stored in StringVar must be "True" or "False".
        self.PluginEnabled:tk.StringVar = tk.StringVar(
            value=config.get_str(ConfigKeys.CONFIG_PLUGIN, default=plugin_default_str)
        )
        self.APIUrl:tk.StringVar = tk.StringVar(
            value=config.get_str(ConfigKeys.CONFIG_API_URL, default=DefaultSettings.API_URL)
        )
        self.APIKey:tk.StringVar = tk.StringVar(
            value=config.get_str(ConfigKeys.CONFIG_API_KEY, default=DefaultSettings.API_KEY)
        )
        self.DeveloperMode:tk.StringVar = tk.StringVar(
            value=config.get_str(ConfigKeys.CONFIG_DEV_MODE, default=dev_mode_default_str)
        )
        self.SystemLookup:tk.StringVar = tk.StringVar(
            value=config.get_str(ConfigKeys.CONFIG_SYSTEM_LOOKUP, default=system_lookup_default_str)
        )

        PluginLogger.logger.debug(f"Loading {ConfigKeys.CONFIG_PLUGIN}: config raw string was '{config.get_str(ConfigKeys.CONFIG_PLUGIN)}', effective string value = {self.PluginEnabled.get()}")
        PluginLogger.logger.debug(f"Loading {ConfigKeys.CONFIG_DEV_MODE}: config raw string was '{config.get_str(ConfigKeys.CONFIG_DEV_MODE)}', effective string value = {self.DeveloperMode.get()}")
        PluginLogger.logger.debug(f"Loading {ConfigKeys.CONFIG_SYSTEM_LOOKUP}: config raw string was '{config.get_str(ConfigKeys.CONFIG_SYSTEM_LOOKUP)}', effective string value = {self.SystemLookup.get()}")
        
        self.refresh_settings()


    def refresh_settings(self):
        """
        Refresh settings based on the current state of Tkinter StringVars.
        """
        self.plugin_enabled:bool = self.PluginEnabled.get() == str(True)  # Convert string to boolean
        self.api_url:str = self.APIUrl.get()
        self.api_key:str = self.APIKey.get()
        self.developer_mode:bool = self.DeveloperMode.get() == str(True)  # Convert string to boolean
        self.system_lookup_enabled:bool = self.SystemLookup.get() == str(True)  # Convert string to boolean
    

    def save_settings(self):
        """
        Save settings to EDMC's config using ConfigKeys.
        """
        config.set(ConfigKeys.CONFIG_PLUGIN, str(self.PluginEnabled.get()))
        config.set(ConfigKeys.CONFIG_API_URL, self.APIUrl.get())
        config.set(ConfigKeys.CONFIG_API_KEY, self.APIKey.get())
        config.set(ConfigKeys.CONFIG_DEV_MODE, str(self.DeveloperMode.get()))
        config.set(ConfigKeys.CONFIG_SYSTEM_LOOKUP, str(self.SystemLookup.get()))

        # Ensure self.logger is used if logging is needed here
        PluginLogger.logger.info("Saving SAL settings...")