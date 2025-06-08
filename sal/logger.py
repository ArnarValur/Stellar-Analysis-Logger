import logging
import os
from os import path
from datetime import datetime
from sal.constants import PluginInfo


class PluginLogger:
    def __init__(self, sal, plugin_dir=None):
        # Accept a string or an object with plugin_name
        if isinstance(sal, str):
            logger_name = sal
        else:
            logger_name = getattr(sal, "plugin_name", str(sal))
        self.logger = logging.getLogger(f"EDMC.{logger_name}")
        self.logger.setLevel(logging.DEBUG)

        # Common formatter
        log_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
        )
        log_formatter.default_time_format = '%Y-%m-%d %H:%M:%S'
        log_formatter.default_msec_format = '%s.%03d'

        # Avoid adding handlers multiple times
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_formatter)
            self.logger.addHandler(console_handler)

            # File Handler (for the dedicated plugin log file)
            if plugin_dir:
                try:
                    current_date = datetime.now().strftime("%Y-%m-%d")
                    log_filename = f"{current_date}-{PluginInfo.PLUGIN_NAME_FOR_LOGGING}.log"
                    log_directory = os.path.join(plugin_dir, "logs")
                    os.makedirs(log_directory, exist_ok=True)
                    log_file_path = os.path.join(log_directory, log_filename)

                    file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
                    file_handler.setFormatter(log_formatter)
                    self.logger.addHandler(file_handler)
                except Exception as e:
                    self.logger.error(f"Failed to set up dedicated file logging: {e}")
            else:
                self.logger.warning("Plugin directory or log file name not provided, dedicated file logging disabled.")

    def get_logger(self):
        return self.logger