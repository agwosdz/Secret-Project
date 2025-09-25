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
    "pin": 19,  # Default GPIO pin (legacy)
    "piano_size": "88-key",  # Piano size: 25-key, 37-key, 49-key, 61-key, 76-key, 88-key, custom
    "gpio_pin": 19,  # GPIO pin for LED strip data
    "led_orientation": "normal",  # LED orientation: normal, reversed
    
    # Extended hardware configuration
    "led_type": "WS2812B",  # LED strip type: WS2812B, WS2813, WS2815, etc.
    "power_supply_voltage": 5.0,  # Power supply voltage (V)
    "power_supply_current": 10.0,  # Power supply max current (A)
    "gpio_power_pin": None,  # Optional GPIO pin for power control
    "gpio_ground_pin": None,  # Optional GPIO pin for ground reference
    "signal_level": 3.3,  # Signal voltage level (V)
    
    # Piano key mapping configuration
    "key_mapping": {},  # Custom key-to-LED mapping {midi_note: led_index or [led_indices]}
    "mapping_mode": "auto",  # Mapping mode: auto, manual, proportional, custom (legacy)
    "key_offset": 0,  # Offset for key mapping alignment
    "leds_per_key": 3,  # Number of LEDs to light up per key
    "mapping_base_offset": 0,  # Base offset for the entire mapping
    
    # Physical LED strip positioning parameters
    "leds_per_meter": 60,  # Physical LED density (LEDs per meter)
    "strip_length": 4.1,  # Physical strip length in meters (246 LEDs / 60 LEDs/m = 4.1m)
    "note_offsets": {},  # Note-specific offsets {note: offset_value}
    "global_shift": 0,  # Global shift applied to all note positions
    
    # Advanced timing and performance settings
    "led_frequency": 800000,  # LED strip frequency (Hz)
    "led_dma": 10,  # DMA channel for LED control
    "led_invert": False,  # Invert signal polarity
    "led_channel": 0,  # PWM channel
    "led_strip_type": "WS2811_STRIP_GRB",  # Strip color order
    
    # Color calibration settings
    "color_temperature": 6500,  # Color temperature (K)
    "gamma_correction": 2.2,  # Gamma correction value
    "color_balance": {"red": 1.0, "green": 1.0, "blue": 1.0},  # RGB balance
    
    # Hardware detection and validation
    "auto_detect_hardware": True,  # Enable automatic hardware detection
    "validate_gpio_pins": True,  # Validate GPIO pin availability
    "hardware_test_enabled": True,  # Enable hardware testing features
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
    
    # Validate optional GPIO pins
    for pin_name in ["gpio_power_pin", "gpio_ground_pin"]:
        if pin_name in config and config[pin_name] is not None:
            if not isinstance(config[pin_name], int) or not (0 <= config[pin_name] <= 27):
                errors.append(f"{pin_name} must be an integer between 0 and 27 or None")
    
    # Validate piano size
    if "piano_size" in config:
        valid_sizes = ["25-key", "37-key", "49-key", "61-key", "76-key", "88-key", "custom"]
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
    
    # Validate LED type
    if "led_type" in config:
        valid_led_types = ["WS2812B", "WS2813", "WS2815", "APA102", "SK6812"]
        if config["led_type"] not in valid_led_types:
            errors.append(f"led_type must be one of: {', '.join(valid_led_types)}")
    
    # Validate power supply settings
    if "power_supply_voltage" in config:
        voltage = config["power_supply_voltage"]
        if not isinstance(voltage, (int, float)) or not (3.0 <= voltage <= 12.0):
            errors.append("power_supply_voltage must be between 3.0V and 12.0V")
    
    if "power_supply_current" in config:
        current = config["power_supply_current"]
        if not isinstance(current, (int, float)) or not (0.5 <= current <= 50.0):
            errors.append("power_supply_current must be between 0.5A and 50.0A")
    
    # Validate signal level
    if "signal_level" in config:
        signal_level = config["signal_level"]
        if signal_level not in [3.3, 5.0]:
            errors.append("signal_level must be either 3.3V or 5.0V")
    
    # Validate mapping mode
    if "mapping_mode" in config:
        valid_mapping_modes = ["auto", "manual", "proportional", "custom"]
        if config["mapping_mode"] not in valid_mapping_modes:
            errors.append(f"mapping_mode must be one of: {', '.join(valid_mapping_modes)}")
    
    # Validate leds_per_key
    if "leds_per_key" in config:
        leds_per_key = config["leds_per_key"]
        if not isinstance(leds_per_key, int) or leds_per_key < 1:
            errors.append("leds_per_key must be a positive integer")
        elif leds_per_key > 10:
            errors.append("leds_per_key cannot exceed 10 for performance reasons")
    
    # Validate mapping_base_offset
    if "mapping_base_offset" in config:
        mapping_base_offset = config["mapping_base_offset"]
        if not isinstance(mapping_base_offset, int) or mapping_base_offset < 0:
            errors.append("mapping_base_offset must be a non-negative integer")
        elif mapping_base_offset >= config.get("led_count", 300):
            errors.append("mapping_base_offset must be less than led_count")
    
    # Validate LED frequency
    if "led_frequency" in config:
        frequency = config["led_frequency"]
        if frequency not in [400000, 800000]:
            errors.append("led_frequency must be either 400000Hz or 800000Hz")
    
    # Validate color temperature
    if "color_temperature" in config:
        color_temp = config["color_temperature"]
        if not isinstance(color_temp, (int, float)) or not (2700 <= color_temp <= 10000):
            errors.append("color_temperature must be between 2700K and 10000K")
    
    # Validate gamma correction
    if "gamma_correction" in config:
        gamma = config["gamma_correction"]
        if not isinstance(gamma, (int, float)) or not (1.0 <= gamma <= 3.0):
            errors.append("gamma_correction must be between 1.0 and 3.0")
    
    # Validate color balance
    if "color_balance" in config:
        color_balance = config["color_balance"]
        if not isinstance(color_balance, dict):
            errors.append("color_balance must be a dictionary")
        else:
            for color in ["red", "green", "blue"]:
                if color not in color_balance:
                    errors.append(f"color_balance must include {color} value")
                elif not isinstance(color_balance[color], (int, float)) or not (0.0 <= color_balance[color] <= 2.0):
                    errors.append(f"color_balance.{color} must be between 0.0 and 2.0")
    
    # Validate key mapping
    if "key_mapping" in config:
        key_mapping = config["key_mapping"]
        if not isinstance(key_mapping, dict):
            errors.append("key_mapping must be a dictionary")
        else:
            for midi_note, led_indices in key_mapping.items():
                try:
                    midi_note_int = int(midi_note)
                    if not (0 <= midi_note_int <= 127):
                        errors.append(f"MIDI note {midi_note} must be between 0 and 127")
                except ValueError:
                    errors.append(f"MIDI note {midi_note} must be a valid integer")
                
                # Accept both single LED index (int) and multiple LED indices (list[int])
                if isinstance(led_indices, int):
                    if led_indices < 0:
                        errors.append(f"LED index {led_indices} must be a non-negative integer")
                elif isinstance(led_indices, list):
                    if not led_indices:
                        errors.append(f"LED indices list for MIDI note {midi_note} cannot be empty")
                    for led_index in led_indices:
                        if not isinstance(led_index, int) or led_index < 0:
                            errors.append(f"LED index {led_index} must be a non-negative integer")
                else:
                    errors.append(f"LED indices for MIDI note {midi_note} must be an integer or list of integers")
    
    return errors


def validate_config_comprehensive(config):
    """Comprehensive configuration validation with cross-field checks"""
    # Normalize incoming configurations to support older/different shapes used by some callers/tests
    def _normalize_config_for_validation(input_config):
        normalized = dict(input_config) if isinstance(input_config, dict) else {}
        # Normalize brightness from 0-255 scale to 0.0-1.0 if needed
        b = normalized.get('brightness')
        if isinstance(b, (int, float)) and b > 1.0:
            try:
                if b <= 255:
                    normalized['brightness'] = round(float(b) / 255.0, 3)
            except Exception:
                pass
        # Normalize piano_size numeric to string form like "88-key"
        ps = normalized.get('piano_size')
        if isinstance(ps, int):
            normalized['piano_size'] = f"{ps}-key"
        # Map nested power_supply to flat keys
        if isinstance(normalized.get('power_supply'), dict):
            psup = normalized['power_supply']
            if 'voltage' in psup:
                normalized['power_supply_voltage'] = psup['voltage']
            if 'max_current' in psup:
                normalized['power_supply_current'] = psup['max_current']
        # Map nested gpio_pins to flat primary data pin
        if isinstance(normalized.get('gpio_pins'), dict):
            gp = normalized['gpio_pins']
            if gp.get('data_pin') is not None:
                normalized['gpio_pin'] = gp.get('data_pin')
        # Normalize orientation synonyms
        lo = normalized.get('led_orientation')
        if lo == 'bottom_up':
            normalized['led_orientation'] = 'reversed'
        elif lo == 'top_down':
            normalized['led_orientation'] = 'normal'
        # Normalize signal_level string like '3.3V' -> 3.3
        sl = normalized.get('signal_level')
        if isinstance(sl, str) and sl.strip().lower().endswith('v'):
            try:
                normalized['signal_level'] = float(sl.strip().lower().replace('v', ''))
            except Exception:
                pass
        # Map unknown mapping_mode values to supported ones
        mm = normalized.get('mapping_mode')
        if mm == 'linear':
            normalized['mapping_mode'] = 'auto'
        return normalized

    normalized = _normalize_config_for_validation(config)

    errors = validate_config(normalized)
    warnings = []
    
    # Cross-validation: Power consumption vs supply capacity
    if all(key in normalized for key in ["led_count", "brightness", "led_type", "power_supply_current", "power_supply_voltage"]):
        power_consumption = calculate_led_power_consumption(
            normalized["led_count"], 
            normalized["brightness"], 
            normalized["led_type"]
        )
        max_power = normalized["power_supply_voltage"] * normalized["power_supply_current"]
        
        if power_consumption.get("total_watts", 0) > max_power:
            errors.append(
                f"Power consumption ({power_consumption.get('total_watts', 0):.1f}W) exceeds "
                f"power supply capacity ({max_power:.1f}W)"
            )
        elif power_consumption.get("total_watts", 0) > max_power * 0.8:
            warnings.append(
                f"Power consumption ({power_consumption.get('total_watts', 0):.1f}W) is close to "
                f"power supply capacity ({max_power:.1f}W). Consider reducing brightness or LED count."
            )
    
    # Cross-validation: GPIO pin conflicts (support both flat and nested gpio_pins)
    gpio_pins_seen = []

    def _add_pin(pin_val):
        if pin_val is None:
            return
        if pin_val in gpio_pins_seen:
            errors.append(f"GPIO pin {pin_val} is used multiple times")
        gpio_pins_seen.append(pin_val)

    # Flat pins
    for pin_key in ["gpio_pin", "gpio_power_pin", "gpio_ground_pin"]:
        _add_pin(normalized.get(pin_key))

    # Nested pins
    gp = normalized.get('gpio_pins')
    if isinstance(gp, dict):
        for nested_key in ["data_pin", "clock_pin", "power_pin", "ground_pin"]:
            _add_pin(gp.get(nested_key))
    
    # Cross-validation: Piano size vs LED count consistency
    if "piano_size" in normalized and "led_count" in normalized and normalized["piano_size"] != "custom":
        piano_specs = get_piano_specs(normalized["piano_size"])
        recommended_leds = piano_specs["keys"] * 3  # Rough estimate
        
        if piano_specs["keys"] > 0 and abs(normalized["led_count"] - recommended_leds) > max(recommended_leds * 0.5, 1):
            warnings.append(
                f"LED count ({normalized['led_count']}) seems inconsistent with piano size "
                f"({normalized['piano_size']}). Recommended: ~{recommended_leds} LEDs"
            )
    
    return {
        "valid": len(errors) == 0,
        "is_valid": len(errors) == 0,  # alias for compatibility with some tests/clients
        "errors": errors,
        "warnings": warnings
    }


def backup_config():
    """Create a backup of the current configuration"""
    try:
        if CONFIG_FILE.exists():
            backup_file = CONFIG_FILE.with_suffix('.json.backup')
            import shutil
            shutil.copy2(CONFIG_FILE, backup_file)
            logger.info(f"Configuration backed up to {backup_file}")
            return True
    except Exception as e:
        logger.error(f"Failed to backup configuration: {e}")
        return False


def restore_config_from_backup():
    """Restore configuration from backup"""
    try:
        backup_file = CONFIG_FILE.with_suffix('.json.backup')
        if backup_file.exists():
            import shutil
            shutil.copy2(backup_file, CONFIG_FILE)
            logger.info(f"Configuration restored from {backup_file}")
            return True
        else:
            logger.warning("No backup file found")
            return False
    except Exception as e:
        logger.error(f"Failed to restore configuration: {e}")
        return False


def reset_config_to_defaults():
    """Reset configuration to default values"""
    try:
        backup_config()  # Backup current config first
        save_config(DEFAULT_CONFIG.copy())
        logger.info("Configuration reset to defaults")
        return True
    except Exception as e:
        logger.error(f"Failed to reset configuration: {e}")
        return False


def export_config(export_path):
    """Export configuration to a specified file"""
    try:
        config = load_config()
        export_file = Path(export_path)
        
        with open(export_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Configuration exported to {export_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to export configuration: {e}")
        return False


def import_config(import_path, validate_before_save=True):
    """Import configuration from a specified file"""
    try:
        import_file = Path(import_path)
        
        if not import_file.exists():
            logger.error(f"Import file {import_file} does not exist")
            return False
        
        with open(import_file, 'r') as f:
            imported_config = json.load(f)
        
        if validate_before_save:
            validation_result = validate_config_comprehensive(imported_config)
            if not validation_result["valid"]:
                logger.error(f"Imported configuration is invalid: {validation_result['errors']}")
                return False
        
        backup_config()  # Backup current config first
        save_config(imported_config)
        logger.info(f"Configuration imported from {import_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to import configuration: {e}")
        return False


def get_config_history():
    """Get configuration change history (if backup files exist)"""
    try:
        config_dir = CONFIG_FILE.parent
        backup_files = list(config_dir.glob("config.json.backup*"))
        
        history = []
        for backup_file in sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True):
            stat = backup_file.stat()
            history.append({
                "file": str(backup_file),
                "modified": stat.st_mtime,
                "size": stat.st_size
            })
        
        return history
    except Exception as e:
        logger.error(f"Failed to get configuration history: {e}")
        return []


def get_piano_specs(piano_size):
    """Get piano specifications based on size"""
    specs = {
        "25-key": {"keys": 25, "octaves": 2, "start_note": "C3", "end_note": "C5", "midi_start": 48, "midi_end": 72},
        "37-key": {"keys": 37, "octaves": 3, "start_note": "C2", "end_note": "C5", "midi_start": 36, "midi_end": 72},
        "49-key": {"keys": 49, "octaves": 4, "start_note": "C2", "end_note": "C6", "midi_start": 36, "midi_end": 84},
        "61-key": {"keys": 61, "octaves": 5, "start_note": "C2", "end_note": "C7", "midi_start": 36, "midi_end": 96},
        "76-key": {"keys": 76, "octaves": 6.25, "start_note": "E1", "end_note": "G7", "midi_start": 28, "midi_end": 103},
        "88-key": {"keys": 88, "octaves": 7.25, "start_note": "A0", "end_note": "C8", "midi_start": 21, "midi_end": 108},
        "custom": {"keys": 0, "octaves": 0, "start_note": "", "end_note": "", "midi_start": 0, "midi_end": 127}
    }
    return specs.get(piano_size, specs["88-key"])


def calculate_led_power_consumption(led_count, brightness=1.0, led_type="WS2812B"):
    """Calculate estimated power consumption for LED strip"""
    # Power consumption per LED at full brightness (mA)
    led_power_specs = {
        "WS2812B": 60,  # ~60mA per LED at full white
        "WS2813": 60,
        "WS2815": 60,
        "APA102": 60,
        "SK6812": 60
    }
    
    power_per_led = led_power_specs.get(led_type, 60)
    total_current = (led_count * power_per_led * brightness) / 1000  # Convert to Amps
    total_watts_5v = round(total_current * 5.0, 2)
    
    return {
        "current_amps": round(total_current, 2),
        "current_ma": round(total_current * 1000),
        "power_5v_watts": total_watts_5v,
        "total_watts": total_watts_5v,  # alias for compatibility
        "recommended_supply_amps": round(total_current * 1.2, 2)  # 20% safety margin
    }


def generate_auto_key_mapping(piano_size, led_count, led_orientation="normal", leds_per_key=None, mapping_base_offset=None):
    """Generate automatic key-to-LED mapping based on piano size and LED count
    
    Args:
        piano_size: Piano size (e.g., "88-key")
        led_count: Total number of LEDs
        led_orientation: LED orientation ("normal" or "reversed")
        leds_per_key: Number of LEDs per key (overrides calculation if provided)
        mapping_base_offset: Base offset for the entire mapping (default: 0)
    
    Returns:
        dict: Mapping of MIDI note to list of LED indices
    """
    specs = get_piano_specs(piano_size)
    key_count = specs["keys"]
    
    if key_count == 0:  # Custom piano size
        return {}
    
    # Use provided values or calculate defaults
    if mapping_base_offset is None:
        mapping_base_offset = 0
    
    # Adjust available LED count based on base offset
    available_leds = led_count - mapping_base_offset
    if available_leds <= 0:
        return {}
    
    # Calculate LEDs per key
    if leds_per_key is None:
        leds_per_key = available_leds // key_count
        remaining_leds = available_leds % key_count
    else:
        # When leds_per_key is specified, calculate how many keys we can map
        max_mappable_keys = available_leds // leds_per_key
        if max_mappable_keys < key_count:
            # Truncate to mappable keys
            key_count = max_mappable_keys
        remaining_leds = available_leds - (key_count * leds_per_key)
    
    mapping = {}
    led_index = mapping_base_offset
    
    for key_num in range(key_count):
        midi_note = specs["midi_start"] + key_num
        
        # Distribute remaining LEDs among first keys (only when leds_per_key is calculated)
        if leds_per_key is None or remaining_leds > 0:
            key_led_count = leds_per_key + (1 if key_num < remaining_leds else 0)
        else:
            key_led_count = leds_per_key
        
        # Create LED range for this key
        led_range = list(range(led_index, led_index + key_led_count))
        
        # Reverse LED order if orientation is reversed
        if led_orientation == "reversed":
            led_range = led_range[::-1]
        
        mapping[midi_note] = led_range
        led_index += key_led_count
    
    # Reverse entire mapping if orientation is reversed
    if led_orientation == "reversed":
        total_leds = led_count - 1
        reversed_mapping = {}
        for midi_note, led_list in mapping.items():
            reversed_mapping[midi_note] = [total_leds - led for led in led_list]
        mapping = reversed_mapping
    
    return mapping


def calculate_note_position(note, leds_per_meter, strip_length, note_offsets=None, global_shift=0, led_count=None, led_orientation="normal", debug=False, piano_size="88-key"):
    """
    Calculate LED position for a MIDI note using physical strip parameters and offsets.
    
    Args:
        note: MIDI note number (0-127)
        leds_per_meter: Total number of LEDs available for mapping
        strip_length: Physical strip length in meters (kept for compatibility)
        note_offsets: Dictionary of note-specific offsets {note: offset_value}
        global_shift: Global shift applied to all note positions
        led_count: Total number of LEDs (uses leds_per_meter if not provided)
        led_orientation: LED orientation ("normal" or "reversed")
        debug: Print debug information
        piano_size: Piano size to determine number of keys (default "88-key")
    
    Returns:
        int: LED position (0-based) or None if outside valid range
    """
    if note_offsets is None:
        note_offsets = {}
    
    # Determine number of keys based on piano size
    if piano_size == "88-key":
        num_keys = 88
    elif piano_size == "76-key":
        num_keys = 76
    elif piano_size == "61-key":
        num_keys = 61
    else:
        num_keys = 88  # default
    
    # Step 1: Process all offsets first
    # Load all offsets, and if note > offset set noteoffset to that shift
    note_offset = 0
    for offset_note, shift_value in note_offsets.items():
        if note > offset_note:
            note_offset = shift_value
    
    # Step 2: Process the global shift by incrementing/decrementing the note offset by shift
    note_offset += global_shift
    
    # Step 3: Get the strip density as leds_per_meter / number_of_keys
    strip_density = leds_per_meter / num_keys
    
    # Step 4: Calculate the note position as int(density * (note - 20) - note_offset)
    # Account for first MIDI note being 21
    note_position = int(strip_density * (note - 20) - note_offset)
    
    # Step 5: Apply orientation and bounds checking
    if led_count is None:
        led_count = leds_per_meter
    
    if debug:
        print(f"Note {note}: density={strip_density:.2f} (LEDs={leds_per_meter}/keys={num_keys}), raw_pos={note_position}, offset={note_offset}")
    
    if led_orientation == "normal":
        final_position = max(0, note_position)
    else:  # reversed
        final_position = max(0, led_count - 1 - note_position)  # Fix: subtract 1 for 0-based indexing
    
    # Ensure position is within LED strip bounds
    if final_position >= led_count:
        if debug:
            print(f"  Position {final_position} >= {led_count}, returning None")
        return None
    
    return final_position


def generate_density_based_mapping(piano_size, leds_per_meter, strip_length, note_offsets=None, global_shift=0, led_orientation="normal"):
    """
    Generate note-to-LED mapping using the density-based positioning algorithm.
    
    Args:
        piano_size: Piano size (e.g., "88-key")
        leds_per_meter: Physical LED density (LEDs per meter)
        strip_length: Physical strip length in meters
        note_offsets: Dictionary of note-specific offsets {note: offset_value}
        global_shift: Global shift applied to all note positions
        led_orientation: LED orientation ("normal" or "reversed")
    
    Returns:
        dict: Mapping of MIDI note to LED index
    """
    specs = get_piano_specs(piano_size)
    led_count = int(leds_per_meter * strip_length)
    mapping = {}
    
    for note in range(specs["midi_start"], specs["midi_end"] + 1):
        led_position = calculate_note_position(
            note=note,
            leds_per_meter=leds_per_meter,
            strip_length=strip_length,
            note_offsets=note_offsets,
            global_shift=global_shift,
            led_count=led_count,
            led_orientation=led_orientation
        )
        
        if led_position is not None:
            mapping[note] = led_position
    
    return mapping


def validate_gpio_pin_availability(pin, exclude_pins=None):
    """Validate if a GPIO pin is available for use"""
    if exclude_pins is None:
        exclude_pins = []
    
    # Reserved pins that should not be used
    reserved_pins = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 15, 16, 17, 30, 31]
    
    # Power and ground pins
    power_ground_pins = [1, 2, 4, 6, 9, 14, 17, 20, 25, 30, 34, 39]
    
    if pin in reserved_pins:
        return False, "Pin is reserved for system use"
    
    if pin in power_ground_pins:
        return False, "Pin is a power or ground pin"
    
    if pin in exclude_pins:
        return False, "Pin is already in use"
    
    if not 0 <= pin <= 40:
        return False, "Pin number out of valid range (0-40)"
    
    return True, "Pin is available"