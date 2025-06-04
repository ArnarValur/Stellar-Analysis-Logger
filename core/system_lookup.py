import urllib
import json
from typing import Dict, Any, Optional

from .http_client import HttpClient
from .logger import logger
from .settings_manager import SettingsManager

from .constants import (
    EDSM_API_SYSTEM_URL
)

class SystemLookup:
    def __init__(self, http_client: HttpClient, settings_manager: SettingsManager):
        self.http_client = http_client
        self.settings_manager = settings_manager

    # Queries EDSM for system information.
    def _query_edsm(self, system_name: str) -> bool:
        """Query EDSM for system information.
        Returns True if the system is found in EDSM, False otherwise."""
        if not system_name:
            logger.warning("System name is empty, cannot query EDSM.")
            return False
        
        params = {
            'systemName': urllib.parse.quote(system_name)
        }

        logger.debug(f"Querying EDSM for system: {system_name}")
        response_data, status_code, error_message = self.http_client.send_get_request_sync(
            EDSM_API_SYSTEM_URL,
            params=params,
        )

        if error_message or status_code != 200:
            logger.error(f"Error querying EDSM: {error_message} (Status code: {status_code})")
            return False
        
        if isinstance(response_data, dict):
            if not response_data:
                logger.info(f"System '{system_name}' not found in EDSM (empty dict response).")
                return False
            else:
                logger.info(f"System '{system_name}' found in EDSM.")
                return True
        elif response_data is None and status_code == 200:
            logger.info(f"System '{system_name}' not found in EDSM (null response).")
            return False
        else:
            logger.warning(f"Unexpected response format from EDSM for system '{system_name}'. Status: {status_code}, Data: {str(response_data)[:200]}")
            return False

    # Checks if a system is known in EDSM.
    def is_system_known_edsm(self, system_name: str) -> bool:
        """Check if a system is known in EDSM."""
        if not self.settings_manager.is_system_lookup_enabled():
            logger.debug("System lookup is disabled, skipping EDSM query.")
            return False
        
        logger.debug(f"Checking if system '{system_name}' is known in EDSM.")
        return self._query_edsm(system_name)
    

    # Placeholder for querying Spansh API (not implemented)
    def _query_spansh():
        spansh_result = False
        return spansh_result


    # Placeholder for querying Spansh API (not implemented)
    def _query_edastro():
        edastro_result = False
        return edastro_result


    # Cleans up the SystemLookup resources.
    def cleanup(self):
        """Clean up resources used by SystemLookup."""
        logger.debug("Cleaning up SystemLookup resources.")
        self.http_client = None
        self.settings_manager = None
        pass

# Global instance of SystemLookup
system_lookup_instance = None

# Initialize the SystemLookup instance
def initialize_system_lookup(http_client: HttpClient, settings_manager: SettingsManager):
    global system_lookup_instance
    if system_lookup_instance is None:
        system_lookup_instance = SystemLookup(http_client, settings_manager)
        logger.info("SystemLookup initialized.")
    else:
        logger.warning("SystemLookup instance already exists, skipping initialization.")
    return system_lookup_instance