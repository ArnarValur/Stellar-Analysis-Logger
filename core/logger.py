import logging
import os
from .constants import PLUGIN_NAME_FOR_LOGGING, LOG_FILE_NAME

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
        if plugin_dir and LOG_FILE_NAME:
            log_file_path = os.path.join(plugin_dir, LOG_FILE_NAME)
            try:
                file_handler = logging.FileHandler(log_file_path, mode='a')
                file_handler.setFormatter(log_formatter)
                logger.addHandler(file_handler)
                logger.info(f"Dedicated logging to file: {log_file_path}")
            except Exception as e:
                logger.error(f"Failed to set up dedicated file logging to {log_file_path}: {e}")
        else:
            logger.warning("Plugin directory or log file name not provided, dedicated file logging disabled.")

    logger.info(f"Logging setup complete for {PLUGIN_NAME_FOR_LOGGING}")
