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
    "piano_size": "88-key",  # Piano size: 61-key, 76-key, 88-key, custom
    "gpio_pin": 19,  # GPIO pin for LED strip
    "led_orientation": "normal",  # LED orientation: normal, inverted
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


def validate_config(config):
    """Validate configuration values"""
    errors = []
    
    # Validate LED count
    if "led_count" in config:
        if not isinstance(config["led_count"], int) or config["led_count"] <= 0:
            errors.append("led_count must be a positive integer")
        elif config["led_count"] > config.get("max_led_count", 300):
            errors.append(f"led_count cannot exceed {config.get('max_led_count', 300)}")
    
    # Validate GPIO pin
    if "gpio_pin" in config:
        if not isinstance(config["gpio_pin"], int) or not (0 <= config["gpio_pin"] <= 27):
            errors.append("gpio_pin must be an integer between 0 and 27")
    
    # Validate piano size
    if "piano_size" in config:
        valid_sizes = ["25-key", "37-key", "49-key", "61-key", "76-key", "88-key"]
        if config["piano_size"] not in valid_sizes:
            errors.append(f"piano_size must be one of: {', '.join(valid_sizes)}")
    
    # Validate LED orientation
    if "led_orientation" in config:
        valid_orientations = ["normal", "reversed"]
        if config["led_orientation"] not in valid_orientations:
            errors.append(f"led_orientation must be one of: {', '.join(valid_orientations)}")
    
    # Validate brightness
    if "brightness" in config:
        if not isinstance(config["brightness"], (int, float)) or not (0.0 <= config["brightness"] <= 1.0):
            errors.append("brightness must be a number between 0.0 and 1.0")
    
    return errors


def get_piano_specs(piano_size):
    """Get piano specifications based on size"""
    specs = {
        "25-key": {"num_keys": 25, "min_midi_note": 60, "max_midi_note": 84},   # C4-C6 (2 octaves)
        "37-key": {"num_keys": 37, "min_midi_note": 48, "max_midi_note": 84},   # C3-C6 (3 octaves)
        "49-key": {"num_keys": 49, "min_midi_note": 36, "max_midi_note": 84},   # C2-C6 (4 octaves)
        "61-key": {"num_keys": 61, "min_midi_note": 36, "max_midi_note": 96},   # C2-C7 (5 octaves)
        "76-key": {"num_keys": 76, "min_midi_note": 28, "max_midi_note": 103},  # E1-G7 (6+ octaves)
        "88-key": {"num_keys": 88, "min_midi_note": 21, "max_midi_note": 108},  # A0-C8 (full piano)
    }
    return specs.get(piano_size, specs["88-key"])  # Default to 88-key