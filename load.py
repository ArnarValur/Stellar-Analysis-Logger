from core.logger import logger, setup_logging as setup_plugin_logging # MODIFIED: Import setup_logging
import core.settings_manager
# MODIFIED: Import module to access instance directly, remove instance alias
from core.http_client import initialize_http_client, stop_http_client
import core.http_client 
# MODIFIED: Import module to access instance directly, remove instance alias
from core.data_handler import initialize_data_handler
import core.data_handler 
from core.ui_manager import UIManager # Import UIManager
from core.constants import PLUGIN_NAME_FULL, PLUGIN_VERSION # Import constants
from core.payload_logger import setup_payload_logging # ADDED: Import for payload logger

import tkinter as tk
from tkinter import ttk

# TODO: Initialize data handler

# Global instance of UIManager
ui_manager_instance = None

# Define a dictionary to act as a simple namespace for plugin globals
# that might be needed by UIManager, like a callback to prefs_changed.
plugin_globals = {}

def plugin_start3(plugin_dir): # Renamed from plugin_start
    """Called when the plugin is loaded by EDMC (Python 3 version)"""
    global ui_manager_instance, plugin_globals

    # Initialize plugin-specific logging FIRST
    setup_plugin_logging(plugin_dir) # ADDED: Call to setup dedicated logging
    setup_payload_logging(plugin_dir) # ADDED: Initialize payload logger

    logger.info(f"Starting plugin {PLUGIN_NAME_FULL} v{PLUGIN_VERSION} from directory: {plugin_dir}") # MODIFIED: Log plugin_dir
    
    core.settings_manager.initialize_settings() # Changed: Call via module
    
    # Access settings_manager via the module
    logger.info(f"Plugin enabled: {core.settings_manager.settings_manager.plugin_enabled}")
    logger.info(f"API URL: {core.settings_manager.settings_manager.api_url}")
    
    initialize_http_client(PLUGIN_NAME_FULL, PLUGIN_VERSION)
    logger.info("HttpClient initialized.")
    
    # MODIFIED: Pass the http_client_instance directly from its module
    initialize_data_handler(
        core.settings_manager.settings_manager, 
        core.http_client.http_client_instance, # Get current instance
        PLUGIN_NAME_FULL, 
        PLUGIN_VERSION
    )
    logger.info("DataHandler initialized.")

    # Make prefs_changed accessible to UIManager via plugin_globals
    plugin_globals['prefs_changed_callback'] = prefs_changed
    
    # Pass the initialized settings_manager from the module
    ui_manager_instance = UIManager(core.settings_manager.settings_manager, plugin_globals)
    logger.info("UIManager initialized.")
    
    return PLUGIN_NAME_FULL

def plugin_stop():
    """Called when the plugin is unloded by EDMC"""
    logger.info(f"Stopping plugin {PLUGIN_NAME_FULL}")
    stop_http_client()
    logger.info("HttpClient stopped.")
    # Note: data_handler and ui_manager cleanup might be needed if they hold resources
    pass

def journal_entry(cmdr, is_beta, system, station, entry, state):
    """Called for each journal entry"""
    logger.info(f"journal_entry called. Event type: {entry.get('event')}, CMDR: {cmdr}, System: {system}") # ADDED: Log entry
    # MODIFIED: Access data_handler_instance directly from the core.data_handler module
    if core.data_handler.data_handler_instance:
        logger.debug(f"Calling core.data_handler.data_handler_instance.process_journal_entry for event: {entry.get('event')}")
        core.data_handler.data_handler_instance.process_journal_entry(entry.copy(), cmdr)
    else:
        # MODIFIED: Log reflects the direct access path
        logger.error("core.data_handler.data_handler_instance is None, cannot process journal entry.")
    pass

def plugin_prefs(parent, cmdr, is_beta):
    """Called to display the plugin's settings panel"""
    logger.info(f"plugin_prefs called for {PLUGIN_NAME_FULL}. Parent: {parent}") # ADDED
    if not ui_manager_instance:
        logger.error("UIManager not initialized when trying to open prefs UI.")
        return None
    # UIManager is initialized with core.settings_manager.settings_manager, so it's fine
    #return ui_manager_instance.create_settings_ui(parent, cmdr, is_beta)
    # MODIFIED to add logging around the call
    created_frame = ui_manager_instance.create_settings_ui(parent, cmdr, is_beta)
    logger.info(f"plugin_prefs: create_settings_ui returned widget: {created_frame}, type: {type(created_frame).__name__}") # MODIFIED
    return created_frame

def prefs_changed(cmdr, is_beta):
    """Called when the plugin's settings are changed"""
    logger.info("Plugin settings changed by user.")
    # Access settings_manager via the module
    if core.settings_manager.settings_manager:
        core.settings_manager.settings_manager.save()
    pass
