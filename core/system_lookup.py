import urllib.parse
import json
from typing import Dict, Any, Optional, Tuple

from .http_client import HttpClient
from .logger import logger
from .settings_manager import SettingsManager

from .constants import (
    EDSM_API_SYSTEM_URL,
    SPANSH_API_SYSTEM_URL,
    EDASTRO_API_SYSTEM_URL
)

class SystemLookup:
    def __init__(self, http_client: HttpClient, settings_manager: SettingsManager):
        self.http_client = http_client
        self.settings_manager = settings_manager
        # Cache to avoid redundant API calls for the same system during a session
        self._discovery_cache = {}

    def _query_edsm(self, system_name: str) -> bool:
        """Query EDSM for system information.
        Returns True if the system is found in EDSM, False otherwise.
        :param system_name: The name of the system to query.
        :return: True if the system is found, False otherwise."""
        if not system_name:
            logger.warning("System name is empty, cannot query EDSM.")
            return False
        
        params = {
            'systemName': system_name,
            'showInformation': '1',
            'showPrimaryStar': '1'
        }

        logger.debug(f"Querying EDSM for system: {system_name}")
        if self.http_client is None:
            logger.error("HttpClient is None, cannot query EDSM.")
            return False
        
        response_data, status_code, error_message = self.http_client.send_get_request_sync(
            EDSM_API_SYSTEM_URL,
            params=params,
        )
        
        if error_message or status_code != 200:
            logger.debug(f"EDSM query failed for {system_name}: {error_message} (Status: {status_code})")
            return False
        
        if isinstance(response_data, dict):
            if not response_data or response_data.get('name') is None:
                logger.debug(f"System '{system_name}' not found in EDSM.")
                return False
            else:
                logger.debug(f"System '{system_name}' found in EDSM.")
                return True
        elif response_data is None and status_code == 200:
            logger.debug(f"System '{system_name}' not found in EDSM (null response).")
            return False
        else:
            logger.warning(f"Unexpected response format from EDSM for system '{system_name}'. Status: {status_code}, Data: {str(response_data)[:200]}")
            return False

    def is_system_known_edsm(self, system_name: str) -> bool:
        """Check if a system is known in EDSM.
        This method checks if the system lookup is enabled in settings before querying EDSM,
        and returns True if the system is known, False otherwise.
        :param system_name: The name of the system to check.
        :return: True if the system is known, False otherwise."""
        if self.settings_manager is None:
            logger.error("SettingsManager is None, cannot check system lookup.")
            return False
        if not self.settings_manager.is_system_lookup_enabled():
            logger.debug("System lookup is disabled, skipping EDSM query.")
            return False
        logger.debug(f"Checking if system '{system_name}' is known in EDSM.")
        return self._query_edsm(system_name)

    def _query_spansh(self, system_address: int) -> bool:
        """Query Spansh API for system information.
        URL: https://www.spansh.co.uk/api/system/{system_address}
        Returns True if the system is found in Spansh, False otherwise."""
        if not system_address:
            logger.warning("System address is empty, cannot query Spansh.")
            return False
        
        if self.http_client is None:
            logger.error("HttpClient is None, cannot query Spansh.")
            return False

        url = f"{SPANSH_API_SYSTEM_URL}/{system_address}"
        
        logger.debug(f"Querying Spansh for system address: {system_address}")
        response_data, status_code, error_message = self.http_client.send_get_request_sync(url)

        if error_message or status_code != 200:
            logger.debug(f"Spansh query failed for system {system_address}: {error_message} (Status: {status_code})")
            return False
        
        # Spansh uses either 'record' or 'system' structure depending on API version
        if isinstance(response_data, dict) and (response_data.get('system') or response_data.get('record')):
            logger.debug(f"System address {system_address} found in Spansh.")
            return True
        else:
            logger.debug(f"System address {system_address} not found in Spansh.")
            return False

    def _query_edastro(self, system_address: int) -> bool:
        """Query Edastro API for system information.
        URL: https://edastro.com/api/starsystem?q={system_address}
        Returns True if the system is found in Edastro, False otherwise."""
        if not system_address:
            logger.warning("System address is empty, cannot query Edastro.")
            return False

        if self.http_client is None:
            logger.error("HttpClient is None, cannot query Edastro.")
            return False

        params = {'q': str(system_address)}
        
        logger.debug(f"Querying Edastro for system address: {system_address}")
        response_data, status_code, error_message = self.http_client.send_get_request_sync(
            EDASTRO_API_SYSTEM_URL, 
            params=params
        )

        if error_message or status_code != 200:
            logger.debug(f"Edastro query failed for system {system_address}: {error_message} (Status: {status_code})")
            return False
        
        if isinstance(response_data, dict) and response_data.get('system'):
            logger.debug(f"System address {system_address} found in Edastro.")
            return True
        elif isinstance(response_data, list) and len(response_data) > 0:
            logger.debug(f"System address {system_address} found in Edastro.")
            return True
        else:
            logger.debug(f"System address {system_address} not found in Edastro.")
            return False

    def check_system_discovery_status(self, system_name: str, system_address: int, original_was_discovered: Optional[bool] = None) -> Tuple[bool, str]:
        """
        Check if a system has been discovered by querying multiple sources.
        Returns (is_discovered, source) where source indicates which API confirmed discovery.
        
        :param system_name: The name of the system
        :param system_address: The system address
        :param original_was_discovered: Original WasDiscovered value from journal
        :return: Tuple of (is_discovered, source_info)
        """
        if self.settings_manager is None or not self.settings_manager.is_system_lookup_enabled():
            logger.debug("System lookup is disabled, using original WasDiscovered value.")
            return original_was_discovered if original_was_discovered is not None else False, "journal"

        # Check cache first
        cache_key = f"{system_name}_{system_address}"
        if cache_key in self._discovery_cache:
            cached_result, cached_source = self._discovery_cache[cache_key]
            logger.debug(f"Using cached discovery status for {system_name}: {cached_result} ({cached_source})")
            return cached_result, cached_source

        discovery_sources = []
        
        # Check EDSM
        if system_name and self._query_edsm(system_name):
            discovery_sources.append("EDSM")
        
        # Check Spansh
        if system_address and self._query_spansh(system_address):
            discovery_sources.append("Spansh")
        
        # Check Edastro
        if system_address and self._query_edastro(system_address):
            discovery_sources.append("Edastro")

        # Determine result
        is_discovered = len(discovery_sources) > 0
        source_info = f"external:{','.join(discovery_sources)}" if discovery_sources else "external:none"
        
        # If external sources don't have data, fall back to journal value
        if not is_discovered and original_was_discovered is not None:
            is_discovered = original_was_discovered
            source_info = "journal_fallback"

        # Cache the result
        self._discovery_cache[cache_key] = (is_discovered, source_info)
        
        logger.info(f"Discovery status for {system_name}: {is_discovered} (sources: {source_info})")
        return is_discovered, source_info

    def cleanup(self):
        """Clean up resources used by SystemLookup."""
        logger.debug("Cleaning up SystemLookup resources.")
        self._discovery_cache.clear()
        self.http_client = None
        self.settings_manager = None

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