import logging
import os # ADDED: For path manipulation
from .constants import PLUGIN_NAME_FOR_LOGGING, LOG_FILE_NAME # MODIFIED: Import LOG_FILE_NAME

# Use the plugin\'s folder name for the logger to make it easy to identify
# messages from this plugin.
logger = logging.getLogger(f"EDMC.{PLUGIN_NAME_FOR_LOGGING}")

def setup_logging(plugin_dir=None): # MODIFIED: Accept plugin_dir
    """Set up the logger for the plugin"""
    # If the logger already has handlers, it means EDMC has already set it up
    # or we have set it up in a previous call.
    if not logger.handlers: # MODIFIED: Check logger.handlers instead of logger.hasHandlers()
        logger.setLevel(logging.INFO)

        # Common formatter
        log_formatter = logging.Formatter(
            f'%(asctime)s | %(levelname)s | %(name)s | %(message)s'
        )
        log_formatter.default_time_format = '%Y-%m-%d %H:%M:%S' # CHANGED: More standard time format
        log_formatter.default_msec_format = '%s.%03d'

        # Console Handler (mimics EDMC default but might be redundant if EDMC also logs)
        # We keep it for now to ensure logs appear somewhere if EDMC doesn't pick them up.
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        logger.addHandler(console_handler)

        # File Handler (for the dedicated plugin log file)
        if plugin_dir and LOG_FILE_NAME:
            log_file_path = os.path.join(plugin_dir, LOG_FILE_NAME)
            try:
                file_handler = logging.FileHandler(log_file_path, mode='a') # 'a' for append
                file_handler.setFormatter(log_formatter)
                logger.addHandler(file_handler)
                logger.info(f"Dedicated logging to file: {log_file_path}")
            except Exception as e:
                logger.error(f"Failed to set up dedicated file logging to {log_file_path}: {e}")
        else:
            logger.warning("Plugin directory or log file name not provided, dedicated file logging disabled.")

    logger.info(f"Logging setup complete for {PLUGIN_NAME_FOR_LOGGING}")
