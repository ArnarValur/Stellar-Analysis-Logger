from core.logger import logger, setup_logging as setup_plugin_logging
import core.settings_manager

from core.http_client import initialize_http_client, stop_http_client
from core.data_handler import initialize_data_handler
from core.system_lookup import initialize_system_lookup

from core.ui_manager import UIManager
from core.constants import PLUGIN_NAME_FULL, PLUGIN_VERSION
from core.payload_logger import setup_payload_logging

import tkinter as tk
from tkinter import ttk

ui_manager_instance = None
plugin_globals = {}


def initialize_core_components(plugin_name, plugin_version, plugin_globals):
    """Centralized initialization of core plugin components."""
    settings = core.settings_manager.initialize_settings()
    http_client = initialize_http_client(plugin_name, plugin_version)
    system_lookup = initialize_system_lookup(http_client, settings)
    data_handler = initialize_data_handler(settings, http_client, system_lookup, plugin_name, plugin_version)
    ui_manager = UIManager(settings, plugin_globals)
    return settings, http_client, system_lookup, data_handler, ui_manager


def plugin_start3(plugin_dir):
    """Called when the plugin is loaded by EDMC (Python 3 version)"""
    global ui_manager_instance, plugin_globals

    setup_plugin_logging(plugin_dir)
    setup_payload_logging(plugin_dir)

    logger.info(f"Starting plugin {PLUGIN_NAME_FULL} v{PLUGIN_VERSION} from directory: {plugin_dir}")
    
    # Centralized Initialization
    plugin_globals['prefs_changed_callback'] = prefs_changed
    settings, http_client, system_lookup, data_handler, ui_manager_instance = initialize_core_components(
        PLUGIN_NAME_FULL, PLUGIN_VERSION, plugin_globals
    )
    
    return PLUGIN_NAME_FULL


def plugin_stop():
    """Called when the plugin is unloded by EDMC"""
    stop_http_client()

    # TODO: Create methods in core modules to handle cleanup
    if core.system_lookup.system_lookup_instance:
        logger.info("Stopping SystemLookup instance.")
        core.system_lookup.system_lookup_instance.cleanup()
        core.system_lookup.system_lookup_instance = None
    if core.data_handler.data_handler_instance:
        logger.info("Stopping DataHandler instance.")
        core.data_handler.data_handler_instance.cleanup()
        core.data_handler.data_handler_instance = None
    if core.settings.settings_manager:
        logger.info("Stopping SettingsManager instance.")
        core.settings.settings_manager.cleanup()
        core.settings.settings_manager = None
    logger.info(f"Stopping plugin {PLUGIN_NAME_FULL} v{PLUGIN_VERSION}")
    pass


def journal_entry(cmdr, is_beta, system, station, entry, state):
    """Called for each journal entry"""
    if core.settings_manager.settings_manager and core.settings_manager.settings_manager.dev_mode_enabled:
        logger.info(f"journal_entry called. Event type: {entry.get('event')}, CMDR: {cmdr}, System: {system}")

    if core.data_handler.data_handler_instance:
        logger.debug(f"Calling core.data_handler.data_handler_instance.process_journal_entry for event: {entry.get('event')}")
        core.data_handler.data_handler_instance.process_journal_entry(entry.copy(), cmdr)
    else:
        logger.error("core.data_handler.data_handler_instance is None, cannot process journal entry.")
    pass


def plugin_prefs(parent, cmdr, is_beta):
    """Called to display the plugin's settings panel"""
    if core.settings_manager.settings_manager and core.settings_manager.settings_manager.dev_mode_enabled:
        logger.info(f"plugin_prefs called for {PLUGIN_NAME_FULL}. Parent: {parent}")
    if not ui_manager_instance:
        logger.error("UIManager not initialized when trying to open prefs UI.")
        return None
    created_frame = ui_manager_instance.create_settings_ui(parent, cmdr, is_beta)
    if core.settings_manager.settings_manager and core.settings_manager.settings_manager.dev_mode_enabled:
        logger.info(f"plugin_prefs: create_settings_ui returned widget: {created_frame}, type: {type(created_frame).__name__}")
    return created_frame


def prefs_changed(cmdr, is_beta):
    """Called when the plugin's settings are changed"""
    if core.settings_manager.settings_manager and core.settings_manager.settings_manager.dev_mode_enabled:
        logger.info("Plugin settings changed by user.")
    # Access settings_manager via the module
    if core.settings_manager.settings_manager:
        core.settings_manager.settings_manager.save()
    pass
