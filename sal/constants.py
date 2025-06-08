import os
from enum import Enum

# Plugin Information
class PluginInfo:
    PLUGIN_NAME = "Stellar Analysis Logger"
    PLUGIN_VERSION = "0.6.0"
    PLUGIN_NAME_FOR_LOGGING = "StellarAnalysisLogger"
    PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

# Checkbox states for Tkinter UI elements
class CheckSettings(str, Enum):
    SETTINGS_OFF = False
    SETTINGS_ON = True

# Date/Time format for payloads
class DateTimeFormat:
    DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# Journal events this handler is interested in
class JournalEvents(Enum):
    FSDJump = "FSDJump"
    Scan = "Scan"
    SAASignalsFound = "SAASignalsFound"
    CarrierJump = "CarrierJump"
    Location = "Location"

# Default settings values
class DefaultSettings:
    PLUGIN_ENABLED = False
    API_URL = "https://api.example.com"
    API_KEY = "your_api_key_here"
    DEV_MODE_ENABLED = False    
    SYSTEM_LOOKUP_ENABLED = True

# Logging specific
class LoggingConfig:
    LOG_LEVEL = "DEBUG"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FILE_PATH = "logs/"
    LOG_FILE_SIZE_MB = 5  # Max size of log file before rotation
    LOG_BACKUP_COUNT = 3  # Number of backup log files to keep

# Config keys for EDMC config
class ConfigKeys:
    CONFIG_PLUGIN = "SAL_enabled"
    CONFIG_API_URL = "SAL_api_url"
    CONFIG_API_KEY = "SAL_api_key"
    CONFIG_DEV_MODE = "SAL_dev_mode"
    CONFIG_SYSTEM_LOOKUP = "SAL_system_lookup"

# Timers for http_client
class HttpClientTimers:
    REQUEST_TIMEOUT_S = 10
    WORKER_SLEEP_S = 1

# HTTP request methods
class RequestMethods(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

# API endpoints for system lookup
class ApiEndpoints:
    EDSM_API_SYSTEM_URL = "https://www.edsm.net/api-v1/system"
    SPANSH_API_SYSTEM_URL = "https://www.spansh.co.uk/api/system"
    EDASTRO_API_SYSTEM_URL = "https://edastro.com/api/starsystem"