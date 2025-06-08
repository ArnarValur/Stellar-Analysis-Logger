import os
import tkinter as tk

from sal.constants import *
from sal.logger import PluginLogger
from config import config  # type: ignore

PluginLogger = PluginLogger("sal", plugin_dir=PluginInfo.PLUGIN_DIR)
logger = PluginLogger.get_logger()

class Settings:
    """
    Manages the plugin's settings, loading them from EDMC's config and providing
    Tkinter variables for the UI.
    """

    def __init__(self, sal):
        """Initialize the Settings and load settings from EDMC's config."""
        self.sal = sal
        self.load_settings()

        logger.debug(f"Settings initialized with following values:\n"
                     f"Plugin Enabled: {self.PluginEnabled}\n"
        )


    def load_settings(self):
        """
        Load settings from EDMC's config.
        """
        self.PluginEnabled:tk.StringVar = tk.StringVar(value=config.get_str(ConfigKeys.CONFIG_PLUGIN, default=CheckSettings.SETTINGS_OFF))

        self.APIUrl:tk.StringVar = tk.StringVar(value=config.get_str(ConfigKeys.CONFIG_API_URL, default=DefaultSettings.API_URL))

        self.APIKey:tk.StringVar = tk.StringVar(value=config.get_str(ConfigKeys.CONFIG_API_KEY, default=DefaultSettings.API_KEY))

        self.DeveloperMode:tk.StringVar = tk.StringVar(value=config.get_str(ConfigKeys.CONFIG_DEV_MODE, default=CheckSettings.SETTINGS_OFF))

        self.SystemLookup:tk.StringVar = tk.StringVar(value=config.get_str(ConfigKeys.CONFIG_SYSTEM_LOOKUP, default=CheckSettings.SETTINGS_OFF))

        logger.debug(f"Loading {ConfigKeys.CONFIG_PLUGIN}: effective value = {self.PluginEnabled.get()}")
        
        self.refresh_settings()


    def refresh_settings(self):
        """
        Refresh settings from EDMC's config.
        """
        self.plugin_enabled:bool = (self.PluginEnabled.get() == CheckSettings.SETTINGS_OFF)
        self.api_url:str = self.APIUrl.get()
        self.api_key:str = self.APIKey.get()
        self.developer_mode:bool = (self.DeveloperMode.get() == CheckSettings.SETTINGS_ON)
        self.system_lookup_enabled:bool = (self.SystemLookup.get() == CheckSettings.SETTINGS_ON)
    

    def save_settings(self):
        """
        Save settings to EDMC's config.
        """
        config.set('PluginEnabled', self.PluginEnabled.get())
        config.set('APIUrl', self.APIUrl.get())
        config.set('APIKey', self.APIKey.get())
        config.set('DeveloperMode', self.DeveloperMode.get())
        config.set('SystemLookup', self.SystemLookup.get())

        
        logger.debug(f"Saving {ConfigKeys.CONFIG_PLUGIN}: value = {self.PluginEnabled.get()}")
        logger.debug("Settings saved to EDMC's config.")