import logging
import os
from os import path
from datetime import datetime
from sal.constants import PluginInfo


class PluginLogger:
    """
    A logger for the EDMC plugin, providing logging capabilities for both the plugin and payloads.
    This logger supports different logging levels and can log to both console and a dedicated file.
    It also supports a separate payload logger for detailed payload logging.
    """
    _developer_mode: bool = False

    def __init__(self, sal, plugin_dir=None):
        self.logger = PluginLogger.logger = logging.getLogger(f"EDMC.{PluginInfo.PLUGIN_NAME_FOR_LOGGING}")
        PluginLogger.logger = self.logger
        
        self.payload_logger = None

        if hasattr(sal, 'settings') and sal.settings is not None:
            PluginLogger._developer_mode = sal.settings.developer_mode
            
            if PluginLogger._developer_mode:
                self.logger.setLevel(logging.DEBUG)
            else:
                self.logger.setLevel(logging.INFO)
        else:
            PluginLogger._developer_mode = False
            self.logger.setLevel(logging.INFO)

        # Common formatter
        log_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
        )
        log_formatter.default_time_format = '%Y-%m-%d %H:%M:%S'
        log_formatter.default_msec_format = '%s.%03d'

        for handler in list(self.logger.handlers):
            if isinstance(handler, (logging.FileHandler, logging.StreamHandler)):
                self.logger.removeHandler(handler)
                if isinstance(handler, logging.FileHandler):
                    handler.close()

        # Add Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        self.logger.addHandler(console_handler)

        # File Handler (for the dedicated plugin log file)
        if plugin_dir:
            try:
                current_date = datetime.now().strftime("%Y-%m-%d")
                log_filename = f"{current_date}-{PluginInfo.PLUGIN_NAME_FOR_LOGGING}.log"
                log_directory = os.path.join(str(plugin_dir), "logs")
                os.makedirs(log_directory, exist_ok=True)
                log_file_path = os.path.join(log_directory, log_filename)

                file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
                file_handler.setFormatter(log_formatter)
                self.logger.addHandler(file_handler)
                self.setup_payload_logger(plugin_dir)
            except Exception as e:
                print(f"ERROR [PluginLogger]: Failed to set up dedicated file logging for {log_file_path if 'log_file_path' in locals() else 'UNKNOWN PATH'}: {e}")
                self.logger.error(f"Failed to set up dedicated file logging: {e}", exc_info=True)
        else:
            self.logger.warning("PluginLogger: Plugin directory not provided, dedicated file logging disabled.")


    def setup_payload_logger(self, plugin_dir: str):
        """Sets up a dedicated logger for payloads."""
        if not plugin_dir:
            self.logger.warning("PluginLogger: Plugin directory not provided, payload logging disabled.")
            return

        payload_logger_name = f"{PluginInfo.PLUGIN_NAME_FOR_LOGGING}.PayloadLogger"
        self.payload_logger = logging.getLogger(payload_logger_name)

        if self.payload_logger.handlers:
            self.logger.info("PluginLogger: Payload logger handlers already exist. Skipping setup.")
            return

        self.payload_logger.setLevel(logging.DEBUG)

        log_file_path = "unknown_path_for_payload_log"  # Initialize for use in except block
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            payload_log_filename = f"{current_date}-{PluginInfo.PLUGIN_NAME_FOR_LOGGING}-Payloads.log"
            payload_log_directory = os.path.join(str(plugin_dir), "logs", "payloads")
            os.makedirs(payload_log_directory, exist_ok=True)
            log_file_path = os.path.join(payload_log_directory, payload_log_filename)

            handler = logging.FileHandler(
                log_file_path,
                mode='a',
                encoding='utf-8'
            )
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.payload_logger.addHandler(handler)
            self.payload_logger.propagate = False
        except Exception as e:
            # Use the main logger for error reporting if it's available
            if self.logger and self.logger.handlers:
                self.logger.error(f"PluginLogger: Failed to set up payload logging to {log_file_path}: {e}", exc_info=True)
            else:
                # Fallback if the main logger itself isn't configured
                print(f"CRITICAL [PluginLogger]: Failed to set up payload logging to {log_file_path}, and main logger has no handlers: {e}")


    @classmethod
    def is_developer_mode(cls) -> bool:
        """
        Check if the plugin is running in developer mode.
        """
        return cls._developer_mode
    

    def get_logger(self):
        return self.logger


    def get_payload_logger(self):
        if not self.payload_logger:
            self.logger.warning("PluginLogger: Payload logger requested but not configured. Returning None.")
            # Optionally, you could try to configure it here if plugin_dir was stored
        return self.payload_logger