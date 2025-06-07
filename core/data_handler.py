import time
import json

from datetime import datetime, timezone
from typing import Dict, Optional, Any

from .logger import logger
from .payload_logger import payload_logger
from .settings_manager import SettingsManager
from .http_client import HttpClient
from .system_lookup import SystemLookup
from .utils import get_by_path 
from .constants import RELEVANT_EVENTS

class DataHandler:
    """
    Processes relevant journal events, extracts specified data, formats it into
    a JSON payload according to the reference structure, and sends it via the HttpClient.
    """
    def __init__(self, settings: SettingsManager, http_client: HttpClient, system_lookup: SystemLookup, plugin_name: str, plugin_version: str):
        """Initializes the DataHandler with settings and HTTP client."""
        self.settings: Optional[SettingsManager] = settings
        self.http_client: Optional[HttpClient] = http_client
        self.system_lookup = system_lookup


    # Processes a single journal entry and builds the appropriate payload.
    def process_journal_entry(self, entry: Dict[str, Any], cmdr_name: str):
        """Filters and processes a single journal entry."""
        if self.settings is None or self.http_client is None:
            logger.error("DataHandler settings or http_client is None.")
            return
        event_name = entry.get('event')

        # Check if the plugin is enabled and if the event is relevant
        if not self.settings.plugin_enabled:
            return

        # Check if the event is one of the relevant events
        if event_name not in RELEVANT_EVENTS:
            return
        
        if self.settings.dev_mode_enabled:
            logger.info(f"Processing relevant event: {event_name} for CMDR {cmdr_name}")

        # Build the payload based on the event type
        payload = None

        # Handle different event types with specific payload builders
        try:
            timestamp = entry.get('timestamp', datetime.now(timezone.utc).isoformat())
            if event_name == 'FSDJump':
                payload = self._build_system_entry_payload(entry, cmdr_name, timestamp)
            elif event_name == 'CarrierJump':
                payload = self._build_carrier_jump_system_entry_payload(entry, cmdr_name, timestamp)
            elif event_name == 'Scan':
                payload = self._build_scan_payload(entry, cmdr_name, timestamp)
            elif event_name == 'SAASignalsFound':
                payload = self._build_saasignalsfound_payload(entry, cmdr_name, timestamp)
        except Exception as e:
            logger.error(f"Error building payload for {event_name}: {e}", exc_info=True)
            return

        # If payload is built, send it to the API
        if payload:
            if not self.settings.api_url:
                logger.warning("API URL not configured. Cannot send payload.")
                return
            
            if self.settings.dev_mode_enabled:
                payload_logger.debug(f"Prepared payload for {payload.get('event_type')}: {payload}")
            
            endpoint_suffix = "exploration/events"
            full_api_url = f"{self.settings.api_url.rstrip('/')}/{endpoint_suffix.lstrip('/')}"
            
            self.http_client.send_json_post_request(
                url=full_api_url, 
                payload=payload,  # FIX: pass dict, not list
                api_key=self.settings.api_key,
                callback=self._handle_api_response
            )
        else:
            if self.settings.dev_mode_enabled:
                logger.debug(f"No payload built for event: {event_name}")


    # Builds the payload for SystemEntry events from FSDJump or CarrierJump
    def _build_system_entry_payload(self, entry: Dict[str, Any], cmdr_name: str, timestamp: str) -> Optional[Dict[str, Any]]:
        payload = {
            'commander_name': cmdr_name,
            'event_timestamp': timestamp,
            'event_type': 'SystemEntry',
            'system_address': entry.get('SystemAddress'),
            'data': {
                'SystemAddress': entry.get('SystemAddress'),
                'StarSystem': entry.get('StarSystem'),
                'StarPos': entry.get('StarPos'),
                'WasDiscovered': entry.get('WasDiscovered'),
                'BodyName': entry.get('Body'),
                'BodyID': entry.get('BodyID'),
                'Commander': cmdr_name
            }
        }
        return payload


    # Builds the payload for Scan events
    def _build_scan_payload(self, entry: Dict[str, Any], cmdr_name: str, timestamp: str) -> Optional[Dict[str, Any]]:
        event_subtype = None
        
        if entry.get('StarType'):
            event_subtype = 'StellarBodyScan'
        elif entry.get('PlanetClass'):
            event_subtype = 'PlanetaryBodyScan'
        else:
            parents = entry.get('Parents')
            if isinstance(parents, list):
                for parent_info in parents:
                    if isinstance(parent_info, dict) and 'Ring' in parent_info:
                        event_subtype = 'AsteroidClusterScan'
                        break
        
        if not event_subtype:
            return None

        payload = {
            'commander_name': cmdr_name,
            'event_timestamp': timestamp,
            'event_type': event_subtype,
            'system_address': entry.get('SystemAddress'),
            'body_id': entry.get('BodyID'),
            'data': {}
        }
        
        scan_data = {
            'BodyName': entry.get('BodyName'),
            'BodyID': entry.get('BodyID'),
            'SystemAddress': entry.get('SystemAddress'),
            'DistanceFromArrivalLS': entry.get('DistanceFromArrivalLS'),
            'Commander': cmdr_name,
            'WasDiscovered': entry.get('WasDiscovered'),
            'WasMapped': entry.get('WasMapped')
        }

        if event_subtype == 'StellarBodyScan':
            scan_data.update({
                'StarType': entry.get('StarType'),
                'Subclass': entry.get('Subclass'),
                'StellarMass': entry.get('StellarMass'),
                'Radius': entry.get('Radius'),
                'AbsoluteMagnitude': entry.get('AbsoluteMagnitude'),
                'Age_MY': entry.get('Age_MY'),
                'SurfaceTemperature': entry.get('SurfaceTemperature'),
                'Luminosity': entry.get('Luminosity'),
                'RotationPeriod': entry.get('RotationPeriod'),
                'AxialTilt': entry.get('AxialTilt')
            })
            if entry.get('Parents'):
                scan_data['Parents'] = entry.get('Parents')
            if entry.get('SemiMajorAxis') is not None:
                scan_data.update({
                    'SemiMajorAxis': entry.get('SemiMajorAxis'),
                    'Eccentricity': entry.get('Eccentricity'),
                    'OrbitalInclination': entry.get('OrbitalInclination'),
                    'Periapsis': entry.get('Periapsis'),
                    'OrbitalPeriod': entry.get('OrbitalPeriod')
                })
        
        elif event_subtype == 'PlanetaryBodyScan':
            scan_data.update({
                'PlanetClass': entry.get('PlanetClass'),
                'TerraformState': entry.get('TerraformState'),
                'AtmosphereType': entry.get('AtmosphereType'),
                'AtmosphereComposition': entry.get('AtmosphereComposition', []),
                'Volcanism': entry.get('Volcanism'),
                'MassEM': entry.get('MassEM'),
                'Radius': entry.get('Radius'),
                'SurfaceGravity': entry.get('SurfaceGravity'),
                'SurfaceTemperature': entry.get('SurfaceTemperature'),
                'SurfacePressure': entry.get('SurfacePressure'),
                'Landable': entry.get('Landable'),
                'Materials': entry.get('Materials', []),
                'Composition': entry.get('Composition', {}),
                'TidalLock': entry.get('TidalLock')
            })
            if entry.get('Parents'):
                scan_data['Parents'] = entry.get('Parents')
            if entry.get('SemiMajorAxis') is not None:
                scan_data.update({
                    'SemiMajorAxis': entry.get('SemiMajorAxis'),
                    'Eccentricity': entry.get('Eccentricity'),
                    'OrbitalInclination': entry.get('OrbitalInclination'),
                    'Periapsis': entry.get('Periapsis'),
                    'OrbitalPeriod': entry.get('OrbitalPeriod')
                })
            if entry.get('RotationPeriod') is not None:
                scan_data.update({
                    'RotationPeriod': entry.get('RotationPeriod'),
                    'AxialTilt': entry.get('AxialTilt')
                })

        elif event_subtype == 'AsteroidClusterScan':
            # Asteroid cluster specific data
            if entry.get('Parents'): 
                scan_data['Parents'] = entry.get('Parents')

        # Rings data (common for StellarBodyScan and PlanetaryBodyScan as per reference)
        if event_subtype == 'StellarBodyScan' or event_subtype == 'PlanetaryBodyScan':
            if entry.get('Rings'):
                rings_data = []
                for ring_entry in entry.get('Rings', []):
                    ring_info = {
                        'Name': ring_entry.get('Name'),
                        'RingClass': ring_entry.get('RingClass'),
                        'MassMT': ring_entry.get('MassMT'),
                        'InnerRad': ring_entry.get('InnerRad'),
                        'OuterRad': ring_entry.get('OuterRad')
                    }
                    rings_data.append(ring_info)
                if rings_data:
                    scan_data['Rings'] = rings_data
            
            # Reserve level for planetary rings (as per reference structure)
            if event_subtype == 'PlanetaryBodyScan' and entry.get('ReserveLevel'):
                scan_data['ReserveLevel'] = entry.get('ReserveLevel')
        
        payload['data'] = scan_data
        return payload


    # Builds the payload for CarrierJump events
    def _build_carrier_jump_system_entry_payload(self, entry: Dict[str, Any], cmdr_name: str, timestamp: str) -> Optional[Dict[str, Any]]:
        """
        Builds a SystemEntry payload from a CarrierJump event.
        The CarrierJump event provides destination system information.
        """

        payload = {
            'commander_name': cmdr_name,
            'event_timestamp': timestamp,
            'event_type': 'SystemEntry',
            'system_address': entry.get('SystemAddress'),
            'data': {
                'SystemAddress': entry.get('SystemAddress'),
                'StarSystem': entry.get('StarSystem'),
                'StarPos': entry.get('StarPos'),
                'WasDiscovered': None,
                'BodyName': entry.get('Body'),
                'BodyID': entry.get('BodyID'),
                'BodyType': entry.get('BodyType'),
                'Commander': cmdr_name
            }
        }
        return payload


    # Builds the payload for SAASignalsFound events
    def _build_saasignalsfound_payload(self, entry: Dict[str, Any], cmdr_name: str, timestamp: str) -> Optional[Dict[str, Any]]:
        payload = {
            'commander_name': cmdr_name,
            'event_timestamp': timestamp,
            'event_type': 'SAASignalsFoundEvent',
            'system_address': entry.get('SystemAddress'),
            'body_id': entry.get('BodyID'),
            'data': {
                'BodyName': entry.get('BodyName'),
                'BodyID': entry.get('BodyID'),
                'SystemAddress': entry.get('SystemAddress'),
                'Signals': entry.get('Signals', []),
                'Genuses': entry.get('Genuses', []),
                'Commander': cmdr_name
            }
        }
        return payload


    # Callback function to handle API responses
    def _handle_api_response(self, success: bool, response_data: Any, status_code: Optional[int]):
        """Callback function to handle responses from the API."""
        log_entry = {
            "type": "api_response",
            "success": success,
            "status_code": status_code,
            "response_data": response_data
        }
        try:
            payload_logger.info(json.dumps(log_entry, indent=2))
        except Exception as e:
            logger.error(f"Error logging API response to dedicated file: {e}", exc_info=True)

        if success:
            logger.info(f"API request successful (Status: {status_code}). Response: {response_data}")
        else:
            logger.error(f"API request failed (Status: {status_code}). Response: {response_data}")


    # Cleans up the DataHandler resources.
    def cleanup(self):
        """Cleans up the DataHandler instance."""
        logger.info("Cleaning up DataHandler instance.")
        self.settings = None
        self.http_client = None
        self.system_lookup = None
        pass


# Global instance of DataHandler
data_handler_instance = None


# Initializes the DataHandler singleton instance.
def initialize_data_handler(settings: SettingsManager, http_client: HttpClient, system_lookup: SystemLookup, plugin_name: str, plugin_version: str):
    """Initializes the DataHandler singleton instance."""
    global data_handler_instance
    if data_handler_instance is None:
        data_handler_instance = DataHandler(settings, http_client, system_lookup, plugin_name, plugin_version)
    return data_handler_instance
