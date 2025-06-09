import os

from typing import Optional
from config import appversion, config  # type: ignore

from sal.logger import PluginLogger
from sal.constants import PluginInfo, ConfigKeys, DefaultSettings
from sal.data_handler import DataHandler
from sal.settings import Settings
from sal.ui_manager import UIManager
from sal.http_client import HttpClient
from sal.system_lookup import SystemLookup
from sal.globals import this
from sal.utils import *

class Sal:
    """
    A class to represent a SAL (Service Abstraction Layer) object.
    This class is a placeholder and can be extended with methods and attributes as needed.
    """

    def __init__(self, plugin_name: str, version: str):
        """
        Initializes the SAL object.
        """
        self.plugin_name = plugin_name
        self.version = version


    def plugin_start(self, plugin_dir: str):
        """
        The Plugin start method.
        """
        # Initialize settings
        self.settings = Settings(self)
        
        # Initialize PluginLogger
        self.logger: PluginLogger = PluginLogger(self, plugin_dir=plugin_dir)
        
        # Initialize HTTP client
        self.http_client = HttpClient(
            plugin_name=PluginInfo.PLUGIN_NAME,
            plugin_version=self.version
        )
        self.http_client.start()

        # Initialize SystemLookup
        self.system_lookup = SystemLookup(
            http_client=self.http_client,
            settings=self.settings
        )

        # Initialize DataHandler
        self.data_handler = DataHandler(
            settings=self.settings,
            http_client=self.http_client,
            system_lookup=self.system_lookup,
            plugin_logger=self.logger,  # Pass the PluginLogger instance
            plugin_name=self.plugin_name,
            plugin_version=self.version,
            plugin_dir=plugin_dir
        )
        
        self.ui = UIManager(self)
    

    def plugin_stop(self):
        """
        The Plugin stop method.
        """
        PluginLogger.logger.info(f"Stopping plugin: {self.plugin_name} (v{self.version})")

        if self.settings:
            self.settings.save_settings()
            if self.settings.developer_mode:
                PluginLogger.logger.info("Plugin settings saved.")

        if hasattr(self, 'http_client') and self.http_client:
            self.http_client.stop()
            if self.settings.developer_mode:
                PluginLogger.logger.info("HTTP client stopped.")

        if hasattr(self, 'data_handler') and self.data_handler:
            self.data_handler.cleanup()
            if self.settings.developer_mode:
                PluginLogger.logger.info("Data handler cleaned up.")

        if hasattr(self, 'system_lookup') and self.system_lookup:
            self.system_lookup.cleanup()
            if self.settings.developer_mode:
                PluginLogger.logger.info("System lookup cleaned up.")

        PluginLogger.logger.info("Plugin stopped successfully.")
        return "Plugin stopped"
    

    def journal_entry(self, cmdr: str, is_beta: bool, system: str, station: str, entry: dict, state: str):
        """
        Parse an incoming journal entry and store the data we need.
        """
        self.data_handler.process_journal_entry(entry.copy(), cmdr)

