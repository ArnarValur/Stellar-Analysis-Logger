import time
import json # ADDED
from datetime import datetime, timezone
from typing import Dict, Optional, Any

from .logger import logger
from .payload_logger import payload_logger
from .settings_manager import SettingsManager
from .http_client import HttpClient
# Remove get_by_path if not used, keep for now
from .utils import get_by_path 
# DATETIME_FORMAT is no longer used for isoformat(), RELEVANT_EVENTS is used
from .constants import RELEVANT_EVENTS

class DataHandler:
    """
    Processes relevant journal events, extracts specified data, formats it into
    a JSON payload according to the BGS-Tally-Explorer structure, 
    and sends it via the HttpClient.
    """
    def __init__(self, settings: SettingsManager, http_client: HttpClient, plugin_name: str, plugin_version: str):
        logger.info("Initializing DataHandler...")
        self.settings = settings
        self.http_client = http_client
        # plugin_name and plugin_version are not part of the reference payload structure
        # self.plugin_name = plugin_name
        # self.plugin_version = plugin_version
        logger.info("DataHandler initialized.")

    def process_journal_entry(self, entry: Dict[str, Any], cmdr_name: str):
        """Filters and processes a single journal entry."""
        event_name = entry.get('event') # Renamed for clarity vs event_type in payload

        if not self.settings.plugin_enabled:
            return

        if event_name not in RELEVANT_EVENTS:
            return
        
        logger.info(f"Processing relevant event: {event_name} for CMDR {cmdr_name}")

        payload = None
        try:
            # Use ISO 8601 format for timestamp, directly from entry or generated
            timestamp = entry.get('timestamp', datetime.now(timezone.utc).isoformat())

            if event_name == 'FSDJump':
                payload = self._build_system_entry_payload(entry, cmdr_name, timestamp)
            elif event_name == 'Scan':
                payload = self._build_scan_payload(entry, cmdr_name, timestamp)
            elif event_name == 'SAASignalsFound':
                payload = self._build_saasignalsfound_payload(entry, cmdr_name, timestamp)
        except Exception as e:
            logger.error(f"Error building payload for {event_name}: {e}", exc_info=True)
            return

        if payload:
            if not self.settings.api_url:
                logger.warning("API URL is not configured. Cannot send data.")
                # Log payload even if not sent, for debugging
                try:
                    payload_logger.info(f"Payload (not sent - API URL missing): {json.dumps(payload, indent=2)}")
                except Exception as e:
                    logger.error(f"Error logging payload to dedicated file: {e}", exc_info=True)
                return
            
            logger.debug(f"Prepared payload for {payload.get('event_type')}: {payload}")
            try:
                payload_logger.info(json.dumps(payload, indent=2))
            except Exception as e:
                logger.error(f"Error logging payload to dedicated file: {e}", exc_info=True)
            
            # Construct the full API URL with the /exploration/events suffix
            endpoint_suffix = "exploration/events"
            full_api_url = f"{self.settings.api_url.rstrip('/')}/{endpoint_suffix.lstrip('/')}"
            
            self.http_client.send_json_post_request(
                url=full_api_url,
                payload=[payload], # MODIFIED: Wrap the single payload in a list
                api_key=self.settings.api_key,
                callback=self._handle_api_response
            )
        else:
            logger.debug(f"No payload generated for event: {event_name}")

    # _get_common_payload_elements removed as its logic is now specific to each builder

    def _build_system_entry_payload(self, entry: Dict[str, Any], cmdr_name: str, timestamp: str) -> Optional[Dict[str, Any]]:
        logger.debug("Building SystemEntry payload (from FSDJump)...")
        payload = {
            'commander_name': cmdr_name,
            'event_timestamp': timestamp,
            'event_type': 'SystemEntry',
            'system_address': entry.get('SystemAddress'),
            'data': {
                'SystemAddress': entry.get('SystemAddress'),
                'StarSystem': entry.get('StarSystem'),
                'StarPos': entry.get('StarPos'),
                'WasDiscovered': entry.get('WasDiscovered'), # System-level discovery
                'BodyName': entry.get('Body'),  # Name of the arrival body (e.g., main star)
                'BodyID': entry.get('BodyID'),    # ID of the arrival body
                'Commander': cmdr_name # As per reference
            }
        }
        return payload

    def _build_scan_payload(self, entry: Dict[str, Any], cmdr_name: str, timestamp: str) -> Optional[Dict[str, Any]]:
        logger.debug("Building Scan payload...")
        event_subtype = None
        
        if entry.get('StarType'):
            event_subtype = 'StellarBodyScan'
        elif entry.get('PlanetClass'):
            event_subtype = 'PlanetaryBodyScan'
        else:
            # Check for asteroid cluster by looking for a 'Ring' in Parents
            parents = entry.get('Parents')
            if isinstance(parents, list):
                for parent_info in parents:
                    if isinstance(parent_info, dict) and 'Ring' in parent_info:
                        event_subtype = 'AsteroidClusterScan'
                        break
        
        if not event_subtype:
            logger.debug(f"Scan event for BodyName '{entry.get('BodyName')}' did not match known scan subtypes. Skipping.")
            return None

        payload = {
            'commander_name': cmdr_name,
            'event_timestamp': timestamp,
            'event_type': event_subtype,
            'system_address': entry.get('SystemAddress'),
            'body_id': entry.get('BodyID'), # Top-level body_id for scans
            'data': {}
        }
        
        scan_data = {
            'BodyName': entry.get('BodyName'),
            'BodyID': entry.get('BodyID'),
            'SystemAddress': entry.get('SystemAddress'), # Repeated in data as per reference
            'DistanceFromArrivalLS': entry.get('DistanceFromArrivalLS'),
            'Commander': cmdr_name, # Repeated in data as per reference
            'WasDiscovered': entry.get('WasDiscovered'),
            'WasMapped': entry.get('WasMapped')
        }

        if event_subtype == 'StellarBodyScan':
            logger.debug(f"StellarBodyScan detected for {entry.get('BodyName')}")
            scan_data.update({
                'StarType': entry.get('StarType'),
                'Subclass': entry.get('Subclass'),
                'StellarMass': entry.get('StellarMass'), # Solar masses
                'Radius': entry.get('Radius'), # Journal: meters. Ref implies direct use.
                'AbsoluteMagnitude': entry.get('AbsoluteMagnitude'),
                'Age_MY': entry.get('Age_MY'),
                'SurfaceTemperature': entry.get('SurfaceTemperature'), # K
                'Luminosity': entry.get('Luminosity'),
                'RotationPeriod': entry.get('RotationPeriod'), # seconds
                'AxialTilt': entry.get('AxialTilt') # degrees
            })
            if entry.get('Parents'): # Orbital characteristics for secondary stars
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
            logger.debug(f"PlanetaryBodyScan detected for {entry.get('BodyName')}")
            scan_data.update({
                'PlanetClass': entry.get('PlanetClass'),
                'TerraformState': entry.get('TerraformState'),
                'AtmosphereType': entry.get('AtmosphereType'),
                'AtmosphereComposition': entry.get('AtmosphereComposition', []),
                'Volcanism': entry.get('Volcanism'),
                'MassEM': entry.get('MassEM'), # Earth masses
                'Radius': entry.get('Radius'), # Journal: meters. Ref implies direct use.
                'SurfaceGravity': entry.get('SurfaceGravity'), # Journal: m/s^2. Ref implies direct use.
                'SurfaceTemperature': entry.get('SurfaceTemperature'), # K
                'SurfacePressure': entry.get('SurfacePressure'), # Journal: Pascals. Ref implies direct use.
                'Landable': entry.get('Landable'),
                'Materials': entry.get('Materials', []),
                'Composition': entry.get('Composition', {}),
                'TidalLock': entry.get('TidalLock')
            })
            if entry.get('Parents'):
                scan_data['Parents'] = entry.get('Parents')
            if entry.get('SemiMajorAxis') is not None: # Orbital characteristics
                scan_data.update({
                    'SemiMajorAxis': entry.get('SemiMajorAxis'),
                    'Eccentricity': entry.get('Eccentricity'),
                    'OrbitalInclination': entry.get('OrbitalInclination'),
                    'Periapsis': entry.get('Periapsis'),
                    'OrbitalPeriod': entry.get('OrbitalPeriod')
                })
            if entry.get('RotationPeriod') is not None: # Rotation data
                scan_data.update({
                    'RotationPeriod': entry.get('RotationPeriod'),
                    'AxialTilt': entry.get('AxialTilt')
                })

        elif event_subtype == 'AsteroidClusterScan':
            logger.debug(f"AsteroidClusterScan detected for {entry.get('BodyName')}")
            # Asteroid cluster specific data
            if entry.get('Parents'): 
                scan_data['Parents'] = entry.get('Parents')
            # Other asteroid specific fields can be added here if available in journal & needed

        # Rings data (common for StellarBodyScan and PlanetaryBodyScan as per reference)
        if event_subtype == 'StellarBodyScan' or event_subtype == 'PlanetaryBodyScan':
            if entry.get('Rings'):
                rings_data = []
                for ring_entry in entry.get('Rings', []): # Ensure it's entry.get('Rings', [])
                    ring_info = {
                        'Name': ring_entry.get('Name'),
                        'RingClass': ring_entry.get('RingClass'),
                        'MassMT': ring_entry.get('MassMT'),
                        'InnerRad': ring_entry.get('InnerRad'),
                        'OuterRad': ring_entry.get('OuterRad')
                    }
                    rings_data.append(ring_info)
                if rings_data: # Only add if there are rings
                    scan_data['Rings'] = rings_data
            
            # Reserve level for planetary rings (as per reference structure)
            if event_subtype == 'PlanetaryBodyScan' and entry.get('ReserveLevel'):
                scan_data['ReserveLevel'] = entry.get('ReserveLevel')
        
        payload['data'] = scan_data
        return payload

    def _build_saasignalsfound_payload(self, entry: Dict[str, Any], cmdr_name: str, timestamp: str) -> Optional[Dict[str, Any]]:
        logger.debug("Building SAASignalsFoundEvent payload...")
        payload = {
            'commander_name': cmdr_name,
            'event_timestamp': timestamp,
            'event_type': 'SAASignalsFoundEvent', # Consistent event type naming
            'system_address': entry.get('SystemAddress'),
            'body_id': entry.get('BodyID'), # SAASignalsFound has BodyID
            'data': {
                'BodyName': entry.get('BodyName'),
                'BodyID': entry.get('BodyID'), # Repeated in data for consistency
                'SystemAddress': entry.get('SystemAddress'), # Repeated in data
                'Signals': entry.get('Signals', []), # Ensure default to empty list
                'Genuses': entry.get('Genuses', []), # Ensure default to empty list
                'Commander': cmdr_name # Consistent with other data blocks
            }
        }
        return payload

    def _handle_api_response(self, success: bool, response_data: Any, status_code: Optional[int]):
        """Callback function to handle responses from the API."""
        # ADDED: Log API response to dedicated payload log file
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

# Global instance of DataHandler
data_handler_instance = None

def initialize_data_handler(settings: SettingsManager, http_client: HttpClient, plugin_name: str, plugin_version: str):
    global data_handler_instance
    if data_handler_instance is None:
        data_handler_instance = DataHandler(settings, http_client, plugin_name, plugin_version)
    return data_handler_instance
