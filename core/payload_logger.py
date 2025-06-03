import logging
import os
from datetime import datetime
from .constants import PLUGIN_NAME_FOR_LOGGING

#PAYLOAD_LOG_FILE_NAME = "Stellar-Analysis-Payloads.log"
payload_logger = logging.getLogger(f"{PLUGIN_NAME_FOR_LOGGING}.PayloadLogger")

def setup_payload_logging(plugin_dir: str):

    if payload_logger.handlers:
        return

    payload_logger.setLevel(logging.DEBUG)

    try:
        # Create dated filename
        current_date = datetime.now().strftime("%Y-%m-%d")
        payload_log_filename = f"{current_date}-{PLUGIN_NAME_FOR_LOGGING}-Payloads.log"

        # Payloads log directory
        payload_log_directory = os.path.join(plugin_dir, "logs", "payloads")
        os.makedirs(payload_log_directory, exist_ok=True)

        log_file_path = os.path.join(payload_log_directory, payload_log_filename)

        handler = logging.FileHandler(
            log_file_path,
            mode='a',
            encoding='utf-8'
        )
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        payload_logger.addHandler(handler)

        payload_logger.propagate = False
    except Exception as e:
        main_logger = logging.getLogger(f"EDMC.{PLUGIN_NAME_FOR_LOGGING}")
        if main_logger.handlers:
            main_logger.error(f"Failed to set up payload logging to {log_file_path if 'log_file_path' in locals() else 'unknown path'}: {e}")
        else:
            print(f"Failed to set up payload logging: {e}")