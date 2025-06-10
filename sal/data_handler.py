import json

from datetime import datetime, timezone
from typing import Dict, Optional, Any, Tuple

from sal.logger import PluginLogger
from sal.settings import Settings
from sal.http_client import HttpClient
from sal.system_lookup import SystemLookup
from sal.utils import get_by_path 
from sal.constants import PluginInfo, JournalEvents

class DataHandler:
    """
    Processes relevant journal events, extracts specified data, formats it into
    a JSON payload according to the reference structure, and sends it via the HttpClient.
    """
    def __init__(self, settings: Settings, http_client: HttpClient, system_lookup: SystemLookup, plugin_logger: PluginLogger, plugin_name: str, plugin_version: str, plugin_dir: str):
        """Initializes the DataHandler with settings and HTTP client."""
        self.settings: Optional[Settings] = settings
        self.http_client: Optional[HttpClient] = http_client
        self.system_lookup = system_lookup
        self.payload_logger = plugin_logger.get_payload_logger()

        # Cache for system lookup discovery status
        self._cached_system_address: Optional[int] = None
        self._cached_system_name: Optional[str] = None
        self._cached_was_discovered: Optional[bool] = None
        self._cached_discovery_source: Optional[str] = None


    # Processes a single journal entry and builds the appropriate payload.
    def process_journal_entry(self, entry: Dict[str, Any], cmdr_name: str):
        """Filters and processes a single journal entry."""
        if not self.settings or not self.http_client:
            PluginLogger.logger.error("process_journal_entry: DataHandler settings or http_client is None.")
            return

        event_name = entry.get('event')

        # Check if the plugin is enabled and if the event is relevant
        if not self.settings.plugin_enabled:
            return

        # Check if the event is one of the relevant events
        if event_name not in JournalEvents.__members__:
            return
        
        if self.settings.developer_mode:
            PluginLogger.logger.info(f"process_journal_entry: Processing relevant event: {event_name} for CMDR {cmdr_name}")

        # Build the payload based on the event type
        payload = None

        # Handle different event types with specific payload builders
        # TODO: I got "Location" event type in constants, but I don't remember why I added it there, something todo with CarrierJump?
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
            PluginLogger.logger.error(f"process_journal_entry: Error building payload for {event_name}: {e}", exc_info=True)
            return

        # If payload is built, send it to the API
        if payload:
            if not self.settings.api_url:
                PluginLogger.logger.warning("process_journal_entry: API URL not configured. Cannot send payload.")
                return
            
            if self.settings.developer_mode:
                if self.payload_logger:
                    self.payload_logger.debug(f"process_journal_entry: Prepared payload for {payload.get('event_type')}: {json.dumps(payload, indent=2)}")
            
            endpoint_suffix = "exploration/events"
            full_api_url = f"{self.settings.api_url.rstrip('/')}/{endpoint_suffix.lstrip('/')}"
            PluginLogger.logger.debug(f"process_journal_entry: Sending payload to API at {full_api_url}")
            self.http_client.send_json_post_request(
                url=full_api_url, 
                payload=payload,
                api_key=self.settings.api_key,
                callback=self._handle_api_response
            )
        else:
            if self.settings and self.settings.developer_mode: 
                PluginLogger.logger.debug(f"process_journal_entry: No payload built for event: {event_name}")
    

    # Gets system discovery status from SystemLookup or uses internal cache.
    def _get_system_discovery_status(self, event_system_address: int, event_system_name: Optional[str], event_original_was_discovered: Optional[bool]) -> Tuple[bool, str]:
        """
        Retrieves system discovery status, using an internal cache for the last processed system or querying SystemLookup if necessary.
        """
        if not self.system_lookup:
            PluginLogger.logger.warning("_get_system_discovery_status: SystemLookup is not available, cannot check system discovery status.")
            return event_original_was_discovered if event_original_was_discovered is not None else False, "journal_no_lookup"
        
        # Check check if the current system address matches the cached on in DataHandler
        if event_system_address == self._cached_system_address and \
            self._cached_was_discovered is not None and \
            self._cached_discovery_source is not None:
            PluginLogger.logger.debug(
                f"DataHandler cache found for system address {event_system_address}. "
                f"Status: {self._cached_was_discovered}, Source: {self._cached_discovery_source}"
            )
            
        # Cache miss or different system, so call SystemLookup
        PluginLogger.logger.debug(f"_get_system_discovery_status: Datahandler cache miss for system address {event_system_address}. Using cached status: {self._cached_was_discovered}, Source: {self._cached_discovery_source}.")

        name_for_lookup = event_system_name if event_system_name else ""

        was_discovered, discovery_source = self.system_lookup.check_system_discovery_status(
            name_for_lookup,
            event_system_address,
            event_original_was_discovered
        )

        # Update the cache
        self._cached_system_address = event_system_address
        self._cached_system_name = event_system_name
        self._cached_was_discovered = was_discovered
        self._cached_discovery_source = discovery_source

        PluginLogger.logger.debug(
            f"DataHandler updated cache for system address {event_system_address}. "
            f"Status: {was_discovered}, Source: {discovery_source}"
        )

        return was_discovered, discovery_source


    # Builds the payload for SystemEntry events
    def _build_system_entry_payload(self, entry: Dict[str, Any], cmdr_name: str, timestamp: str) -> Optional[Dict[str, Any]]:
        system_name = entry.get('StarSystem', '')
        system_address = entry.get('SystemAddress', 0)
        original_was_discovered = entry.get('WasDiscovered')
        
        # Use the cache helper method:
        was_discovered, discovery_source = self._get_system_discovery_status(
            system_address, system_name, original_was_discovered
        )

        PluginLogger.logger.debug(
            f"_build_system_entry_payload: SystemLookup status for system '{system_name}' (address: {system_address}): "
            f"WasDiscovered: {was_discovered}, DiscoverySource: {discovery_source}"
        )
        
        payload = {
            'commander_name': cmdr_name,
            'event_timestamp': timestamp,
            'event_type': 'SystemEntry',
            'system_address': system_address,
            'data': {
                'SystemAddress': system_address,
                'StarSystem': system_name,
                'StarPos': entry.get('StarPos'),
                'WasDiscovered': was_discovered,
                'DiscoverySource': discovery_source,
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

        system_name = entry.get('StarSystem', '')
        system_address = entry.get('SystemAddress', 0)
        original_was_discovered = entry.get('WasDiscovered')
        
        # Use the cache helper method to get discovery status
        was_discovered, discovery_source = self._get_system_discovery_status(
            system_address, system_name, original_was_discovered
        )

        PluginLogger.logger.debug(
            f"_build_scan_payload: SystemLookup status for system '{system_name}' (address: {system_address}): "
            f"WasDiscovered: {was_discovered}, DiscoverySource: {discovery_source}"
        )

        payload = {
            'commander_name': cmdr_name,
            'event_timestamp': timestamp,
            'event_type': event_subtype,
            'system_address': system_address,
            'body_id': entry.get('BodyID'),
            'data': {}
        }
        
        scan_data = {
            'BodyName': entry.get('BodyName'),
            'BodyID': entry.get('BodyID'),
            'SystemAddress': system_address,
            'DistanceFromArrivalLS': entry.get('DistanceFromArrivalLS'),
            'Commander': cmdr_name,
            'WasDiscovered': was_discovered,
            'WasMapped': entry.get('WasMapped'),
            'DiscoverySource': discovery_source
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
            # TODO: Investigate if we need to add more fields here
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
        system_name = entry.get('StarSystem', '')
        system_address = entry.get('SystemAddress', 0)
        original_was_discovered = None

        # Use the cache helper method to get discovery status
        was_discovered, discovery_source = self._get_system_discovery_status(
            system_address, system_name, original_was_discovered
        )
        PluginLogger.logger.debug(
            f"_build_carrier_jump_system_entry_payload: SystemLookup status for system '{system_name}' (address: {system_address}): "
            f"WasDiscovered: {was_discovered}, DiscoverySource: {discovery_source}")

        payload = {
            'commander_name': cmdr_name,
            'event_timestamp': timestamp,
            'event_type': 'SystemEntry',
            'system_address': system_address,
            'data': {
                'SystemAddress': system_address,
                'StarSystem': system_name,
                'StarPos': entry.get('StarPos'),
                'WasDiscovered': was_discovered,
                'DiscoverySource': discovery_source,
                'BodyName': entry.get('Body'),
                'BodyID': entry.get('BodyID'),
                'BodyType': entry.get('BodyType'),
                'Commander': cmdr_name
            }
        }
        return payload
    

    # Builds the payload for SAASignalsFound events
    def _build_saasignalsfound_payload(self, entry: Dict[str, Any], cmdr_name: str, timestamp: str) -> Optional[Dict[str, Any]]:
        system_address = entry.get('SystemAddress', 0)
        system_name = None
        original_was_discovered = None
        
        # Use the cache helper method to get discovery status
        was_discovered, discovery_source = self._get_system_discovery_status(
            system_address, system_name, original_was_discovered
        )
        PluginLogger.logger.debug(
            f"_build_saasignalsfound_payload: SystemLookup status for system address {system_address}: "
            f"WasDiscovered: {was_discovered}, DiscoverySource: {discovery_source}"
        )
        
        payload = {
            'commander_name': cmdr_name,
            'event_timestamp': timestamp,
            'event_type': 'SAASignalsFoundEvent',
            'system_address': system_address,
            'body_id': entry.get('BodyID'),
            'data': {
                'BodyName': entry.get('BodyName'),
                'BodyID': entry.get('BodyID'),
                'SystemAddress': system_address,
                'Signals': entry.get('Signals', []),
                'Genuses': entry.get('Genuses', []),
                'WasDiscovered': was_discovered,
                'DiscoverySource': discovery_source,
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
            if self.payload_logger:
                self.payload_logger.info(json.dumps(log_entry, indent=2))
        except Exception as e:
            PluginLogger.logger.error(f"Error logging API response to dedicated file: {e}", exc_info=True)

        if success:
            PluginLogger.logger.info(f"API request successful (Status: {status_code}). Response: {response_data}")
        else:
            PluginLogger.logger.error(f"API request failed (Status: {status_code}). Response: {response_data}")


    # Cleans up the DataHandler resources.
    def cleanup(self):
        """Cleans up the DataHandler instance."""
        PluginLogger.logger.info("Cleaning up DataHandler instance.")
        self.settings = None
        self.http_client = None
        self.system_lookup = None
        #Clear cache:
        self._cached_system_address = None
        self._cached_system_name = None
        self._cached_was_discovered = None
        self._cached_discovery_source = None
        pass
