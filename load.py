from core.logger import logger, setup_logging as setup_plugin_logging
import core.settings_manager

from core.http_client import initialize_http_client, stop_http_client
import core.http_client 

from core.data_handler import initialize_data_handler
import core.data_handler 

from core.ui_manager import UIManager
from core.constants import PLUGIN_NAME_FULL, PLUGIN_VERSION
from core.payload_logger import setup_payload_logging

import tkinter as tk
from tkinter import ttk

ui_manager_instance = None
plugin_globals = {}

def plugin_start3(plugin_dir):
    """Called when the plugin is loaded by EDMC (Python 3 version)"""
    # TODO: Clean up logging before production release
    global ui_manager_instance, plugin_globals

    # Initialize plugin-specific logging FIRST
    setup_plugin_logging(plugin_dir)
    setup_payload_logging(plugin_dir)

    logger.info(f"Starting plugin {PLUGIN_NAME_FULL} v{PLUGIN_VERSION} from directory: {plugin_dir}")
    
    core.settings_manager.initialize_settings()
    
    # Access settings_manager via the module
    logger.info(f"Plugin enabled: {core.settings_manager.settings_manager.plugin_enabled}")
    logger.info(f"API URL: {core.settings_manager.settings_manager.api_url}")
    
    initialize_http_client(PLUGIN_NAME_FULL, PLUGIN_VERSION)
    logger.info("HttpClient initialized.")
    
    initialize_data_handler(
        core.settings_manager.settings_manager, 
        core.http_client.http_client_instance,
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
    pass

def journal_entry(cmdr, is_beta, system, station, entry, state):
    """Called for each journal entry"""
    logger.info(f"journal_entry called. Event type: {entry.get('event')}, CMDR: {cmdr}, System: {system}")

    if core.data_handler.data_handler_instance:
        logger.debug(f"Calling core.data_handler.data_handler_instance.process_journal_entry for event: {entry.get('event')}")
        core.data_handler.data_handler_instance.process_journal_entry(entry.copy(), cmdr)
    else:
        logger.error("core.data_handler.data_handler_instance is None, cannot process journal entry.")
    pass

def plugin_prefs(parent, cmdr, is_beta):
    """Called to display the plugin's settings panel"""
    logger.info(f"plugin_prefs called for {PLUGIN_NAME_FULL}. Parent: {parent}")
    if not ui_manager_instance:
        logger.error("UIManager not initialized when trying to open prefs UI.")
        return None
    created_frame = ui_manager_instance.create_settings_ui(parent, cmdr, is_beta)
    logger.info(f"plugin_prefs: create_settings_ui returned widget: {created_frame}, type: {type(created_frame).__name__}")
    return created_frame

def prefs_changed(cmdr, is_beta):
    """Called when the plugin's settings are changed"""
    logger.info("Plugin settings changed by user.")
    # Access settings_manager via the module
    if core.settings_manager.settings_manager:
        core.settings_manager.settings_manager.save()
    pass
