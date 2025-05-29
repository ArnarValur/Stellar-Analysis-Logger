import tkinter as tk
from config import config # EDMC\'s config object
from core.logger import logger
from .constants import (
    CONFIG_PLUGIN_ENABLED,
    CONFIG_API_URL,
    CONFIG_API_KEY,
    DEFAULT_PLUGIN_ENABLED,
    DEFAULT_API_URL,
    DEFAULT_API_KEY,
)

class SettingsManager:
    """
    Manages the plugin\'s settings, loading them from EDMC\'s config and providing
    Tkinter variables for the UI.
    """
    def __init__(self):
        logger.info("Initializing SettingsManager...")

        # Load plugin_enabled setting
        raw_plugin_enabled = config.get(CONFIG_PLUGIN_ENABLED)
        logger.debug(f"Loading {CONFIG_PLUGIN_ENABLED}: raw value = '{raw_plugin_enabled}' (type: {type(raw_plugin_enabled).__name__})") # ADDED Logging
        plugin_enabled_value = DEFAULT_PLUGIN_ENABLED  # Default assumption
        if raw_plugin_enabled is not None:
            if isinstance(raw_plugin_enabled, bool): # Should not happen with config.get but good practice
                plugin_enabled_value = raw_plugin_enabled
            elif isinstance(raw_plugin_enabled, str):
                val_lower = raw_plugin_enabled.lower()
                if val_lower in ['true', '1', 'yes']:
                    plugin_enabled_value = True
                elif val_lower in ['false', '0', 'no']:
                    plugin_enabled_value = False
        logger.debug(f"Loading {CONFIG_PLUGIN_ENABLED}: effective value = {plugin_enabled_value}") # ADDED Logging
        self.plugin_enabled_var = tk.BooleanVar(value=plugin_enabled_value)

        # Load API URL
        api_url_value = config.get(CONFIG_API_URL) # Try to get existing value
        logger.debug(f"Loading {CONFIG_API_URL}: raw value = '{api_url_value}'") # ADDED Logging
        if api_url_value is None: # If not found, use default
            api_url_value = DEFAULT_API_URL
            logger.debug(f"Loading {CONFIG_API_URL}: using default = '{api_url_value}'") # ADDED Logging
        self.api_url_var = tk.StringVar(value=api_url_value)

        # Load API Key
        api_key_value = config.get(CONFIG_API_KEY) # Try to get existing value
        logger.debug(f"Loading {CONFIG_API_KEY}: raw value = '{api_key_value}'") # ADDED Logging
        if api_key_value is None: # If not found, use default
            api_key_value = DEFAULT_API_KEY
            logger.debug(f"Loading {CONFIG_API_KEY}: using default = '{api_key_value}'") # ADDED Logging
        self.api_key_var = tk.StringVar(value=api_key_value)

        # Python native type properties for easy access in code
        self.refresh_from_vars()
        logger.info("SettingsManager initialized.")

    def refresh_from_vars(self):
        """Update internal Python properties from Tkinter variables."""
        # .get() on tk.BooleanVar returns True or False.
        self.plugin_enabled = self.plugin_enabled_var.get()
        self.api_url = self.api_url_var.get()
        self.api_key = self.api_key_var.get()
        logger.debug(f"Settings refreshed. Plugin Enabled: {self.plugin_enabled}") # MODIFIED Log message

    def save(self):
        """Save the current settings to EDMC\'s config."""
        logger.info("Saving plugin settings...")
        # tk.BooleanVar.get() returns True/False. config.set will store these as "True"/"False" strings.
        
        plugin_enabled_to_save = self.plugin_enabled_var.get()
        logger.debug(f"Saving {CONFIG_PLUGIN_ENABLED} = {plugin_enabled_to_save} (type: {type(plugin_enabled_to_save).__name__})") # ADDED Logging
        config.set(CONFIG_PLUGIN_ENABLED, plugin_enabled_to_save)
        
        api_url_to_save = self.api_url_var.get()
        logger.debug(f"Saving {CONFIG_API_URL} = '{api_url_to_save}'") # ADDED Logging
        config.set(CONFIG_API_URL, api_url_to_save)
        
        api_key_to_save = self.api_key_var.get()
        logger.debug(f"Saving {CONFIG_API_KEY} = '{api_key_to_save}'") # ADDED Logging
        config.set(CONFIG_API_KEY, api_key_to_save)
        
        # Update internal Python properties after saving
        self.refresh_from_vars()
        logger.info("Plugin settings saved.")

# Global instance of the SettingsManager
# This will be None until plugin_start creates it.
settings_manager = None

def initialize_settings():
    global settings_manager
    if settings_manager is None:
        settings_manager = SettingsManager()
    return settings_manager
