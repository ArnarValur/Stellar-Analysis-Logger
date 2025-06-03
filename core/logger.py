import logging
import os
from datetime import datetime
from .constants import PLUGIN_NAME_FOR_LOGGING

logger = logging.getLogger(f"EDMC.{PLUGIN_NAME_FOR_LOGGING}")

def setup_logging(plugin_dir=None):
    """Set up the logger for the plugin"""

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Common formatter
        log_formatter = logging.Formatter(
            f'%(asctime)s | %(levelname)s | %(name)s | %(message)s'
        )
        log_formatter.default_time_format = '%Y-%m-%d %H:%M:%S'
        log_formatter.default_msec_format = '%s.%03d'

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        logger.addHandler(console_handler)

        # File Handler (for the dedicated plugin log file)
        if plugin_dir:
            try:
                # Create dated filename
                current_date = datetime.now().strftime("%Y-%m-%d")
                log_filename = f"{current_date}-{PLUGIN_NAME_FOR_LOGGING}.log"

                # Logs directory
                log_directory = os.path.join(plugin_dir, "logs")
                os.makedirs(log_directory, exist_ok=True)

                log_file_path = os.path.join(log_directory, log_filename)

                file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
                file_handler.setFormatter(log_formatter)
                logger.addHandler(file_handler)
                
            except Exception as e:
                logger.error(f"Failed to set up dedicated file logging: {e}")
        else:
            logger.warning("Plugin directory or log file name not provided, dedicated file logging disabled.")