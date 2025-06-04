import tkinter as tk
from config import config # type: ignore
from core.logger import logger
from .constants import (
    CONFIG_PLUGIN_ENABLED,
    CONFIG_API_URL,
    CONFIG_API_KEY,
    CONFIG_DEV_MODE_ENABLED,
    CONFIG_SYSTEM_LOOKUP_ENABLED,
    DEFAULT_PLUGIN_ENABLED,
    DEFAULT_API_URL,
    DEFAULT_API_KEY,
    DEFAULT_DEV_MODE_ENABLED,
    DEFAULT_SYSTEM_LOOKUP_ENABLED,
)

class SettingsManager:
    """
    Manages the plugin\'s settings, loading them from EDMC\'s config and providing
    Tkinter variables for the UI.
    """
    def __init__(self):
        """Initialize the SettingsManager and load settings from EDMC\'s config."""

        # Load plugin_enabled setting
        raw_plugin_enabled = config.get(CONFIG_PLUGIN_ENABLED)
        logger.debug(f"Loading {CONFIG_PLUGIN_ENABLED}: raw value = '{raw_plugin_enabled}' (type: {type(raw_plugin_enabled).__name__})")
        plugin_enabled_value = DEFAULT_PLUGIN_ENABLED

        if raw_plugin_enabled is not None:
            if isinstance(raw_plugin_enabled, bool):
                plugin_enabled_value = raw_plugin_enabled
            elif isinstance(raw_plugin_enabled, str):
                val_lower = raw_plugin_enabled.lower()
                if val_lower in ['true', '1', 'yes']:
                    plugin_enabled_value = True
                elif val_lower in ['false', '0', 'no']:
                    plugin_enabled_value = False
        logger.debug(f"Loading {CONFIG_PLUGIN_ENABLED}: effective value = {plugin_enabled_value}")
        self.plugin_enabled_var = tk.BooleanVar(value=plugin_enabled_value)

        # Load API URL
        api_url_value = config.get(CONFIG_API_URL)
        logger.debug(f"Loading {CONFIG_API_URL}: raw value = '{api_url_value}'")
        if api_url_value is None:
            api_url_value = DEFAULT_API_URL
            logger.debug(f"Loading {CONFIG_API_URL}: using default = '{api_url_value}'")
        self.api_url_var = tk.StringVar(value=api_url_value)

        # Load API Key
        api_key_value = config.get(CONFIG_API_KEY)
        logger.debug(f"Loading {CONFIG_API_KEY}: raw value = '{api_key_value}'")
        if api_key_value is None:
            api_key_value = DEFAULT_API_KEY
        self.api_key_var = tk.StringVar(value=api_key_value)

        # Load Developer Mode Enabled setting
        raw_dev_mode_enabled = config.get(CONFIG_DEV_MODE_ENABLED)
        logger.debug(f"Loading {CONFIG_DEV_MODE_ENABLED}: raw value = '{raw_dev_mode_enabled}' (type: {type(raw_dev_mode_enabled).__name__})")
        dev_mode_enabled_value = DEFAULT_DEV_MODE_ENABLED
        if isinstance(raw_dev_mode_enabled, bool):
            dev_mode_enabled_value = raw_dev_mode_enabled
        elif isinstance(raw_dev_mode_enabled, str):
            dev_mode_enabled_value = raw_dev_mode_enabled.lower() == 'true'
        logger.debug(f"Loading {CONFIG_DEV_MODE_ENABLED}: effective value = {dev_mode_enabled_value}")
        self.dev_mode_enabled_var = tk.BooleanVar(value=dev_mode_enabled_value)

        # Load System Lookup Enabled setting
        raw_system_lookup_enabled = config.get(CONFIG_SYSTEM_LOOKUP_ENABLED)
        logger.debug(f"Loading {CONFIG_SYSTEM_LOOKUP_ENABLED}: raw value = '{raw_system_lookup_enabled}' (type: {type(raw_system_lookup_enabled).__name__})")
        system_lookup_enabled_value = DEFAULT_SYSTEM_LOOKUP_ENABLED
        if isinstance(raw_system_lookup_enabled, bool):
            system_lookup_enabled_value = raw_system_lookup_enabled
        elif isinstance(raw_system_lookup_enabled, str):
            val_lower = raw_system_lookup_enabled.lower()
            if val_lower in ['true', '1', 'yes']:
                system_lookup_enabled_value = True
            elif val_lower in ['false', '0', 'no']:
                system_lookup_enabled_value = False
        logger.debug(f"Loading {CONFIG_SYSTEM_LOOKUP_ENABLED}: effective value = {system_lookup_enabled_value}")
        self.system_lookup_enabled_var = tk.BooleanVar(value=system_lookup_enabled_value)

        # Python native type properties for easy access in code
        self.refresh_from_vars()
        if dev_mode_enabled_value:
            logger.info("SettingsManager initialized.")


    # Refresh internal properties from Tkinter variables
    def refresh_from_vars(self):
        """Update internal Python properties from Tkinter variables."""

        self.plugin_enabled = self.plugin_enabled_var.get()
        self.api_url = self.api_url_var.get()
        self.api_key = self.api_key_var.get()
        self.dev_mode_enabled = self.dev_mode_enabled_var.get()
        self.system_lookup_enable = self.system_lookup_enabled_var.get()

        if self.dev_mode_enabled:
            logger.debug(f"Settings refreshed. Plugin Enabled: {self.plugin_enabled}, Dev Mode: {self.dev_mode_enabled}, System Lookup Enabled: {self.system_lookup_enable}")


    # Save the current settings to EDMC's config.
    def save(self):
        """Save the current settings to EDMC\'s config."""
        if self.dev_mode_enabled:
            logger.info("Saving plugin settings...")

        # Plugin enabled setting
        plugin_enabled_to_save = self.plugin_enabled_var.get()
        logger.debug(f"Saving {CONFIG_PLUGIN_ENABLED} = {plugin_enabled_to_save} (type: {type(plugin_enabled_to_save).__name__})")
        config.set(CONFIG_PLUGIN_ENABLED, plugin_enabled_to_save)
        
        # API URL
        api_url_to_save = self.api_url_var.get()
        logger.debug(f"Saving {CONFIG_API_URL} = '{api_url_to_save}'")
        config.set(CONFIG_API_URL, api_url_to_save)
        
        # API Key
        api_key_to_save = self.api_key_var.get()
        logger.debug(f"Saving {CONFIG_API_KEY} = '{api_key_to_save}'")
        config.set(CONFIG_API_KEY, api_key_to_save)

        # Developer Mode Enabled setting
        dev_mode_enabled_to_save = self.dev_mode_enabled_var.get()
        logger.debug(f"Saving {CONFIG_DEV_MODE_ENABLED} = {dev_mode_enabled_to_save} (type: {type(dev_mode_enabled_to_save).__name__})")
        config.set(CONFIG_DEV_MODE_ENABLED, dev_mode_enabled_to_save)

        # System Lookup Enabled setting
        system_lookup_enabled_to_save = self.system_lookup_enabled_var.get()
        logger.debug(f"Saving {CONFIG_SYSTEM_LOOKUP_ENABLED} = {system_lookup_enabled_to_save} (type: {type(system_lookup_enabled_to_save).__name__})")
        config.set(CONFIG_SYSTEM_LOOKUP_ENABLED, system_lookup_enabled_to_save)
        
        # Update internal Python properties after saving
        self.refresh_from_vars()
        if self.dev_mode_enabled:
            logger.info("Plugin settings saved.")


    # Getters for Tkinter variables to use in UI components
    def is_system_lookup_enabled(self):
        return self.system_lookup_enabled_var.get()
    
    # Cleans up SettingsManager resources.
    def cleanup(self):
        """Cleans up the SettingsManager instance."""
        logger.info("Cleaning up SettingsManager resources.")
        pass


# Global instance of the SettingsManager
settings_manager = None

def initialize_settings():
    """Initialize the SettingsManager if it hasn't been created yet."""
    global settings_manager
    if settings_manager is None:
        settings_manager = SettingsManager()
    return settings_manager
