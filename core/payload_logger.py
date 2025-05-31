import logging
import os
from logging.handlers import RotatingFileHandler
from .constants import PLUGIN_NAME_FOR_LOGGING

PAYLOAD_LOG_FILE_NAME = "Stellar-Analysis-Payloads.log"
payload_logger = logging.getLogger(f"{PLUGIN_NAME_FOR_LOGGING}.PayloadLogger")

def setup_payload_logging(plugin_dir: str):

    if payload_logger.handlers:
        return

    payload_logger.setLevel(logging.DEBUG)
    log_file_path = os.path.join(plugin_dir, PAYLOAD_LOG_FILE_NAME)

    # Use a rotating file handler for the payload log
    handler = RotatingFileHandler(
        log_file_path,
        maxBytes=5*1024*1024,
        backupCount=3,
        encoding='utf-8'
    )
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    payload_logger.addHandler(handler)

    payload_logger.propagate = False

