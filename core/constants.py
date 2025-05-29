from enum import Enum

# Plugin Information
PLUGIN_NAME_FOR_LOGGING = "StellarAnalysisLogger" # Used by logger.py, keep it simple
PLUGIN_NAME_FULL = "Stellar Analysis Logger" # Used for display in UI, etc.
PLUGIN_VERSION = "0.1.0"

# Checkbox states for Tkinter UI elements
# MODIFIED: Changed from str Enum to standard Enum with boolean values
# This is to ensure tk.BooleanVar works correctly with onvalue/offvalue
class CheckStates(Enum):
    STATE_OFF = False # Value for Tkinter Checkbutton offvalue
    STATE_ON = True  # Value for Tkinter Checkbutton onvalue

# Date/Time format for payloads
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# Journal events this handler is interested in
RELEVANT_EVENTS = {'FSDJump', 'Scan', 'SAASignalsFound'} # SAASignalsFound is now always relevant if plugin enabled

# Default settings values
DEFAULT_PLUGIN_ENABLED = False  # Plugin is disabled by default
DEFAULT_API_URL = ""
DEFAULT_API_KEY = ""

# Logging specific
LOG_FILE_NAME = "Stellar-Analysis-Logger.log"

# Config keys for EDMC config
CONFIG_PLUGIN_ENABLED = "SAL_PluginEnabled"
CONFIG_API_URL = "SAL_ApiUrl"
CONFIG_API_KEY = "SAL_ApiKey"
