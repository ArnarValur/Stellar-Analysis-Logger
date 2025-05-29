# Development Journal - 2025-05-28: Stellar Analysis Logger

## Goal
Create a new Elite Dangerous Market Connector (EDMC) plugin named `Stellar-Analysis-Logger` to capture specific exploration-related journal events, format them into JSON payloads matching a reference structure, and prepare them for transmission to an external API.

## Key Requirements Implemented:
1.  **Event Capture**:
    *   Targets `FSDJump`, `Scan`, and `SAASignalsFound` journal events.
2.  **Data Extraction & Payload Formatting**:
    *   Payloads for `FSDJump`, `Scan`, and `SAASignalsFound` are structured to *exactly* match the data fields and nested `data` object structure from the reference `BGS-Tally-Explorer/bgstally/exploration_handler.py`.
    *   `FSDJump` maps to `event_type: SystemEntry`.
    *   `Scan` maps to `event_type: StellarBodyScan`, `PlanetaryBodyScan`, or `AsteroidClusterScan` based on journal data.
    *   `SAASignalsFound` maps to `event_type: SAASignalsFoundEvent`.
    *   Timestamps are in ISO 8601 format.
3.  **Data Transmission Preparation**:
    *   Formatted JSON payloads are intended to be sent to a user-configurable external API endpoint. The plugin appends `/exploration/events` to the configured base URL.
    *   The payload sent to the API will be a JSON array containing a single processed event object (e.g., `[ {event_data} ]`).
    *   Utilizes `core/http_client.py` for sending requests (threaded HTTP POST).
    *   URL validation (requiring `http://` or `https://` scheme) is implemented in `http_client.py`.
4.  **User Interface (Tkinter)**:
    *   A settings UI is provided via `core/ui_manager.py` using EDMC's `myNotebook` components.
    *   Allows configuration for:
        *   Enabling/disabling the plugin.
        *   API URL.
        *   Optional API key.
    *   Settings are persisted using EDMC's `config` object via `core/settings_manager.py`.
5.  **Logging**:
    *   Main plugin operations log to `Stellar-Analysis-Logger.log` (via `core/logger.py`).
    *   Dedicated payload logging to `Stellar-Analysis-Payloads.log` (via `core/payload_logger.py`) records the generated JSON payloads and API responses (or attempts).
6.  **Plugin Structure**:
    *   Follows an Object-Oriented Programming (OOP) structure.
    *   `load.py` delegates logic to specialized modules in a `core` directory.
7.  **Default State**: Plugin is disabled by default.

## Current Status (End of Day - 2025-05-28):
*   **Payload Generation**: Successfully capturing `FSDJump`, `Scan`, and `SAASignalsFound` events. Payloads are being generated and logged to `Stellar-Analysis-Payloads.log` for debugging purposes and with the correct structure and data, matching the reference.
*   **API URL Handling**: The plugin correctly constructs the full API endpoint. URL validation in `http_client.py` ensures a scheme is present.
*   **Simulated API Send**: Since no actual API server is running, HTTP requests are currently (and expectedly) failing due to connection errors (e.g., "Connection refused" or "Name or service not known" depending on the dummy URL used). This is logged in both the main log and the payload log.
*   **UI**: Settings UI is functional for enabling/disabling the plugin and configuring the API URL and key. Settings persistence is working.
*   **Key Debugging Steps Taken**:
    *   Resolved `sal_data_handler is None` error in `load.py` by changing how module instances (`data_handler_instance`, `http_client_instance`) are accessed (using `core.module_name.instance_name` instead of import-time aliasing).
    *   Corrected API URL validation to ensure a scheme (`http://` or `https://`) is required, preventing "Invalid URL" errors.

## Next Steps:
1.  **API Server Implementation (User Task)**: User will set up an external API server designed to receive the JSON payloads at the `/exploration/events` endpoint.
2.  **Live API Transmission Testing**: Once the API server is available:
    *   Configure the plugin with the live API URL.
    *   Test end-to-end data transmission.
    *   Verify the server receives the data correctly (JSON array with one event object).
    *   Check API responses are correctly logged in `Stellar-Analysis-Payloads.log`.
3.  **Refinements & Further Checks**:
    *   Review and enhance logging messages in `Stellar-Analysis-Logger.log` for clarity if needed.
    *   Ensure robust error handling for API interactions (timeouts, different HTTP error codes) in `HttpClient` and `DataHandler` is sufficient.
    *   Confirm logic for `AsteroidClusterScan` detection in `core/data_handler.py` remains robust with varied journal data.
    *   Address any necessary unit conversions for fields like `Radius`, `SurfaceGravity` if the API requires units different from the journal (currently assuming direct use based on reference).
    *   Remove unused `DATETIME_FORMAT` constant from `core/constants.py`.
    *   Remove `get_by_path` import from `core/data_handler.py` if confirmed it's no longer used.
    *   Final code cleanup and review.

## Core Files Developed/Modified:
*   `Stellar-Analysis-Logger/load.py`: Main plugin entry points, event handling dispatch.
*   `Stellar-Analysis-Logger/core/logger.py`: Main plugin logger.
*   `Stellar-Analysis-Logger/core/payload_logger.py`: Dedicated logger for JSON payloads and API responses.
*   `Stellar-Analysis-Logger/core/settings_manager.py`: Manages plugin settings.
*   `Stellar-Analysis-Logger/core/http_client.py`: Handles threaded HTTP POST requests.
*   `Stellar-Analysis-Logger/core/constants.py`: Shared constants, event lists, config keys.
*   `Stellar-Analysis-Logger/core/data_handler.py`: Core logic for event processing and payload generation.
*   `Stellar-Analysis-Logger/core/ui_manager.py`: Builds and manages the Tkinter settings UI.
*   `Stellar-Analysis-Logger/core/widgets.py`: Custom UI widgets (e.g., `EntryPlus`).
*   `Stellar-Analysis-Logger/core/utils.py`: Utility functions (currently `get_by_path`, may be unused).

## Reference File Used for Payload Structure:
*   `BGS-Tally-Explorer/bgstally/exploration_handler.py`
