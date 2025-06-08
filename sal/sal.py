
from sal.logger import PluginLogger
from sal.constants import PluginInfo, ConfigKeys, DefaultSettings
from sal.settings import Settings
from sal.ui_manager import UIManager

from config import appversion, config  # type: ignore

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
        pass


    def plugin_start(self, plugin_dir: str):
        """
        The Plugin start method.
        """
        self.plugin_dir = plugin_dir
        self.plugin_name = PluginInfo.PLUGIN_NAME

        self.logger: PluginLogger = PluginLogger(self, plugin_dir=plugin_dir)
        self.logger.get_logger().info(f"Starting plugin: {self.plugin_name} (v{self.version})") 

        self.settings: Settings = Settings(self)
        self.ui: UIManager = UIManager(self)
        

        return "Plugin started in directory: {plugin_dir}"
    

    def plugin_stop(self):
        """
        The Plugin stop method.
        """
        self.logger.get_logger().info(f"Stopping plugin: {self.plugin_name} (v{self.version})")
        self.settings.save_settings()
        self.logger.get_logger().info("Plugin settings saved.")
        return "Plugin stopped"


    