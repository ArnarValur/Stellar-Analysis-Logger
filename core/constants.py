from enum import Enum

# Plugin Information
PLUGIN_NAME_FOR_LOGGING = "StellarAnalysisLogger"
PLUGIN_NAME_FULL = "Stellar Analysis Logger"
PLUGIN_VERSION = "0.2.0"

# Checkbox states for Tkinter UI elements
class CheckStates(Enum):
    STATE_OFF = False
    STATE_ON = True

# Date/Time format for payloads
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# Journal events this handler is interested in
RELEVANT_EVENTS = {'FSDJump', 'Scan', 'SAASignalsFound', 'CarrierJump'}

# Default settings values
DEFAULT_PLUGIN_ENABLED = False
DEFAULT_API_URL = ""
DEFAULT_API_KEY = ""

# Logging specific
LOG_FILE_NAME = "Stellar-Analysis-Logger.log"

# Config keys for EDMC config
CONFIG_PLUGIN_ENABLED = "SAL_PluginEnabled"
CONFIG_API_URL = "SAL_ApiUrl"
CONFIG_API_KEY = "SAL_ApiKey"

# Timers for http_client
REQUEST_TIMEOUT_S = 10
WORKER_SLEEP_S = 1
