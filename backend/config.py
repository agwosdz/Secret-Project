#!/usr/bin/env python3
"""
Configuration management for Piano LED Visualizer
Handles persistent storage of configuration values
"""

import os
import json
import logging
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    "led_count": 246,  # Default LED count
    "max_led_count": 300,  # Maximum allowed LED count
    "brightness": 0.5,  # Default brightness
    "pin": 19,  # Default GPIO pin
}

# Configuration file path
CONFIG_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config():
    """Load configuration from file or create with defaults if not exists"""
    if not CONFIG_FILE.exists():
        # Create default configuration file
        save_config(DEFAULT_CONFIG)
        logger.info(f"Created default configuration file at {CONFIG_FILE}")
        return DEFAULT_CONFIG

    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            logger.info(f"Loaded configuration from {CONFIG_FILE}")
            return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        logger.info("Using default configuration")
        return DEFAULT_CONFIG


def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        logger.info(f"Saved configuration to {CONFIG_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")
        return False


def update_config(key, value):
    """Update a specific configuration value"""
    config = load_config()
    config[key] = value
    return save_config(config)


def get_config(key, default=None):
    """Get a specific configuration value"""
    config = load_config()
    return config.get(key, default)