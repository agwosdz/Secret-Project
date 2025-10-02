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
    
    # Enhanced LED configuration
    "led_strip_type": "WS2811_STRIP_GRB",  # LED strip color order
    "color_profile": "standard",  # Color profile: standard, warm_white, cool_white, music_viz
    "performance_mode": "balanced",  # Performance mode: quality, balanced, performance
    
    # Advanced settings for enhanced LED control
    "white_balance": {"r": 1.0, "g": 1.0, "b": 1.0},  # White balance RGB multipliers
    "dither_enabled": True,  # Enable dithering for smoother color transitions
    "update_rate": 60,  # LED update rate (Hz)
    "power_limiting_enabled": False,  # Enable power limiting
    "max_power_watts": 100,  # Maximum power consumption (W)
    "thermal_protection_enabled": True,  # Enable thermal protection
    "max_temperature_celsius": 85,  # Maximum operating temperature (°C)
    
    # Enhanced GPIO configuration
    "gpio_pull_up": [],  # GPIO pins to configure with pull-up resistors
    "gpio_pull_down": [],  # GPIO pins to configure with pull-down resistors
    "pwm_range": 4096,  # PWM range for precise control
    "spi_speed": 8000000,  # SPI speed for SPI-based LED strips (Hz)
    
    # Piano configuration enhancements
    "piano_keys": 88,  # Number of piano keys
    "piano_octaves": 7,  # Number of octaves
    "piano_start_note": "A0",  # Starting note
    "piano_end_note": "C8",  # Ending note
    "key_mapping_mode": "chromatic",  # Key mapping mode: chromatic, white-keys-only, custom
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
    
    # Validate color profile
    if "color_profile" in config:
        valid_profiles = ["standard", "warm_white", "cool_white", "music_viz"]
        if config["color_profile"] not in valid_profiles:
            errors.append(f"color_profile must be one of: {', '.join(valid_profiles)}")
    
    # Validate performance mode
    if "performance_mode" in config:
        valid_modes = ["quality", "balanced", "performance"]
        if config["performance_mode"] not in valid_modes:
            errors.append(f"performance_mode must be one of: {', '.join(valid_modes)}")
    
    # Validate white balance
    if "white_balance" in config:
        white_balance = config["white_balance"]
        if not isinstance(white_balance, dict):
            errors.append("white_balance must be a dictionary")
        else:
            for color in ["r", "g", "b"]:
                if color not in white_balance:
                    errors.append(f"white_balance must include {color} value")
                elif not isinstance(white_balance[color], (int, float)) or not (0.0 <= white_balance[color] <= 2.0):
                    errors.append(f"white_balance.{color} must be between 0.0 and 2.0")
    
    # Validate update rate
    if "update_rate" in config:
        rate = config["update_rate"]
        if not isinstance(rate, (int, float)) or not (1 <= rate <= 120):
            errors.append("update_rate must be between 1 and 120 Hz")
    
    # Validate max power watts
    if "max_power_watts" in config:
        power = config["max_power_watts"]
        if not isinstance(power, (int, float)) or power <= 0:
            errors.append("max_power_watts must be a positive number")
    
    # Validate max temperature
    if "max_temperature_celsius" in config:
        temp = config["max_temperature_celsius"]
        if not isinstance(temp, (int, float)) or not (0 <= temp <= 150):
            errors.append("max_temperature_celsius must be between 0 and 150")
    
    # Validate GPIO pull resistor configurations
    for pull_key in ["gpio_pull_up", "gpio_pull_down"]:
        if pull_key in config:
            pins = config[pull_key]
            if not isinstance(pins, list):
                errors.append(f"{pull_key} must be a list")
            else:
                for pin in pins:
                    if not isinstance(pin, int) or not (0 <= pin <= 27):
                        errors.append(f"{pull_key} pin {pin} must be an integer between 0 and 27")
    
    # Validate PWM range
    if "pwm_range" in config:
        pwm_range = config["pwm_range"]
        if not isinstance(pwm_range, int) or not (256 <= pwm_range <= 65536):
            errors.append("pwm_range must be an integer between 256 and 65536")
    
    # Validate SPI speed
    if "spi_speed" in config:
        speed = config["spi_speed"]
        if not isinstance(speed, int) or not (1000000 <= speed <= 32000000):
            errors.append("spi_speed must be between 1MHz and 32MHz")
    
    # Validate piano configuration
    if "piano_keys" in config:
        keys = config["piano_keys"]
        if not isinstance(keys, int) or not (25 <= keys <= 128):
            errors.append("piano_keys must be between 25 and 128")
    
    if "piano_octaves" in config:
        octaves = config["piano_octaves"]
        if not isinstance(octaves, (int, float)) or not (2 <= octaves <= 10):
            errors.append("piano_octaves must be between 2 and 10")
    
    # Validate key mapping mode
    if "key_mapping_mode" in config:
        valid_modes = ["chromatic", "white-keys-only", "custom"]
        if config["key_mapping_mode"] not in valid_modes:
            errors.append(f"key_mapping_mode must be one of: {', '.join(valid_modes)}")
    
    # Validate boolean flags
    boolean_fields = [
        "dither_enabled", "power_limiting_enabled", "thermal_protection_enabled",
        "auto_detect_hardware", "validate_gpio_pins", "hardware_test_enabled",
        "led_invert"
    ]
    for field in boolean_fields:
        if field in config and not isinstance(config[field], bool):
            errors.append(f"{field} must be a boolean value")
    
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
    """Calculate estimated power consumption for LED strip with enhanced analysis"""
    # Power consumption per LED at full brightness (mA)
    led_power_specs = {
        "WS2812B": {"current_ma": 60, "voltage": 5.0, "max_temp": 85},
        "WS2813": {"current_ma": 60, "voltage": 5.0, "max_temp": 85},
        "WS2815": {"current_ma": 60, "voltage": 12.0, "max_temp": 85},
        "APA102": {"current_ma": 60, "voltage": 5.0, "max_temp": 85},
        "SK6812": {"current_ma": 60, "voltage": 5.0, "max_temp": 85}
    }
    
    led_spec = led_power_specs.get(led_type, led_power_specs["WS2812B"])
    power_per_led = led_spec["current_ma"]
    voltage = led_spec["voltage"]
    
    # Calculate power consumption
    total_current_ma = led_count * power_per_led * brightness
    total_current_amps = total_current_ma / 1000
    total_watts = round(total_current_amps * voltage, 2)
    
    # Calculate thermal considerations
    heat_dissipation_per_led = 0.2  # Watts per LED at full brightness
    total_heat = round(led_count * heat_dissipation_per_led * brightness, 2)
    
    # Power efficiency calculations
    efficiency = 0.85  # Typical LED strip efficiency
    actual_power_draw = round(total_watts / efficiency, 2)
    
    # Safety margins
    recommended_supply_amps = round(total_current_amps * 1.2, 2)  # 20% safety margin
    recommended_supply_watts = round(actual_power_draw * 1.3, 2)  # 30% safety margin
    
    return {
        "led_count": led_count,
        "brightness": brightness,
        "led_type": led_type,
        "voltage": voltage,
        "current_amps": round(total_current_amps, 3),
        "current_ma": round(total_current_ma),
        "power_watts": total_watts,
        "total_watts": total_watts,  # alias for compatibility
        "power_5v_watts": total_watts if voltage == 5.0 else round(total_current_amps * 5.0, 2),
        "actual_power_draw": actual_power_draw,
        "heat_dissipation_watts": total_heat,
        "efficiency": efficiency,
        "recommended_supply_amps": recommended_supply_amps,
        "recommended_supply_watts": recommended_supply_watts,
        "max_operating_temp": led_spec["max_temp"],
        "power_per_led_ma": power_per_led,
        "power_density": round(total_watts / max(led_count, 1), 3)  # Watts per LED
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


def get_color_profile_settings(profile_name):
    """Get predefined color profile settings"""
    profiles = {
        "standard": {
            "color_temperature": 6500,
            "gamma_correction": 2.2,
            "white_balance": {"r": 1.0, "g": 1.0, "b": 1.0},
            "color_balance": {"red": 1.0, "green": 1.0, "blue": 1.0}
        },
        "warm_white": {
            "color_temperature": 3000,
            "gamma_correction": 2.0,
            "white_balance": {"r": 1.0, "g": 0.9, "b": 0.7},
            "color_balance": {"red": 1.0, "green": 0.9, "blue": 0.7}
        },
        "cool_white": {
            "color_temperature": 8000,
            "gamma_correction": 2.4,
            "white_balance": {"r": 0.9, "g": 1.0, "b": 1.0},
            "color_balance": {"red": 0.9, "green": 1.0, "blue": 1.0}
        },
        "music_viz": {
            "color_temperature": 6500,
            "gamma_correction": 1.8,
            "white_balance": {"r": 1.0, "g": 1.0, "b": 1.0},
            "color_balance": {"red": 1.2, "green": 1.0, "blue": 1.1}
        }
    }
    return profiles.get(profile_name, profiles["standard"])


def get_performance_mode_settings(mode_name):
    """Get predefined performance mode settings"""
    modes = {
        "quality": {
            "update_rate": 60,
            "dither_enabled": True,
            "led_frequency": 800000,
            "pwm_range": 4096
        },
        "balanced": {
            "update_rate": 30,
            "dither_enabled": True,
            "led_frequency": 800000,
            "pwm_range": 2048
        },
        "performance": {
            "update_rate": 120,
            "dither_enabled": False,
            "led_frequency": 400000,
            "pwm_range": 1024
        }
    }
    return modes.get(mode_name, modes["balanced"])


def save_configuration_profile(profile_name, config):
    """Save a configuration as a named profile"""
    try:
        profiles_dir = CONFIG_DIR / "profiles"
        profiles_dir.mkdir(exist_ok=True)
        
        profile_file = profiles_dir / f"{profile_name}.json"
        
        # Validate configuration before saving
        validation_result = validate_config_comprehensive(config)
        if not validation_result["valid"]:
            logger.error(f"Cannot save invalid configuration profile: {validation_result['errors']}")
            return False, validation_result["errors"]
        
        with open(profile_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Configuration profile '{profile_name}' saved")
        return True, []
    except Exception as e:
        logger.error(f"Failed to save configuration profile: {e}")
        return False, [str(e)]


def load_configuration_profile(profile_name):
    """Load a named configuration profile"""
    try:
        profiles_dir = CONFIG_DIR / "profiles"
        profile_file = profiles_dir / f"{profile_name}.json"
        
        if not profile_file.exists():
            logger.error(f"Configuration profile '{profile_name}' not found")
            return None, ["Profile not found"]
        
        with open(profile_file, 'r') as f:
            config = json.load(f)
        
        # Validate loaded configuration
        validation_result = validate_config_comprehensive(config)
        if not validation_result["valid"]:
            logger.warning(f"Loaded profile has validation issues: {validation_result['warnings']}")
        
        logger.info(f"Configuration profile '{profile_name}' loaded")
        return config, validation_result.get("warnings", [])
    except Exception as e:
        logger.error(f"Failed to load configuration profile: {e}")
        return None, [str(e)]


def list_configuration_profiles():
    """List all available configuration profiles"""
    try:
        profiles_dir = CONFIG_DIR / "profiles"
        if not profiles_dir.exists():
            return []
        
        profiles = []
        for profile_file in profiles_dir.glob("*.json"):
            profile_name = profile_file.stem
            stat = profile_file.stat()
            profiles.append({
                "name": profile_name,
                "file": str(profile_file),
                "modified": stat.st_mtime,
                "size": stat.st_size
            })
        
        return sorted(profiles, key=lambda x: x["modified"], reverse=True)
    except Exception as e:
        logger.error(f"Failed to list configuration profiles: {e}")
        return []


def delete_configuration_profile(profile_name):
    """Delete a named configuration profile"""
    try:
        profiles_dir = CONFIG_DIR / "profiles"
        profile_file = profiles_dir / f"{profile_name}.json"
        
        if not profile_file.exists():
            logger.error(f"Configuration profile '{profile_name}' not found")
            return False, "Profile not found"
        
        profile_file.unlink()
        logger.info(f"Configuration profile '{profile_name}' deleted")
        return True, "Profile deleted successfully"
    except Exception as e:
        logger.error(f"Failed to delete configuration profile: {e}")
        return False, str(e)


def detect_hardware_capabilities():
    """Detect available hardware capabilities"""
    capabilities = {
        "gpio_available": False,
        "spi_available": False,
        "i2c_available": False,
        "pwm_available": False,
        "available_pins": [],
        "led_strips_detected": [],
        "power_supplies_detected": [],
        "system_info": {}
    }
    
    try:
        # Try to detect GPIO availability
        try:
            import RPi.GPIO as GPIO
            capabilities["gpio_available"] = True
            
            # Get available GPIO pins (excluding reserved ones)
            reserved_pins = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 15, 16, 17, 30, 31]
            power_ground_pins = [1, 2, 4, 6, 9, 14, 17, 20, 25, 30, 34, 39]
            all_reserved = set(reserved_pins + power_ground_pins)
            
            capabilities["available_pins"] = [pin for pin in range(2, 28) if pin not in all_reserved]
            
        except ImportError:
            logger.warning("RPi.GPIO not available - running on non-Raspberry Pi system")
        except Exception as e:
            logger.warning(f"GPIO detection failed: {e}")
        
        # Try to detect SPI availability
        try:
            import spidev
            capabilities["spi_available"] = True
        except ImportError:
            pass
        
        # Try to detect I2C availability
        try:
            import smbus
            capabilities["i2c_available"] = True
        except ImportError:
            pass
        
        # Try to detect PWM availability
        try:
            import pigpio
            capabilities["pwm_available"] = True
        except ImportError:
            pass
        
        # Get system information
        try:
            import platform
            import psutil
            
            capabilities["system_info"] = {
                "platform": platform.platform(),
                "processor": platform.processor(),
                "architecture": platform.architecture()[0],
                "python_version": platform.python_version(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "cpu_count": psutil.cpu_count(),
                "cpu_freq": psutil.cpu_freq().current if psutil.cpu_freq() else None
            }
        except ImportError:
            pass
        
        logger.info("Hardware detection completed")
        return capabilities
        
    except Exception as e:
        logger.error(f"Hardware detection failed: {e}")
        return capabilities


def apply_color_profile(config, profile_name):
    """Apply a color profile to the configuration"""
    profile_settings = get_color_profile_settings(profile_name)
    config.update(profile_settings)
    config["color_profile"] = profile_name
    return config


def apply_performance_mode(config, mode_name):
    """Apply a performance mode to the configuration"""
    mode_settings = get_performance_mode_settings(mode_name)
    config.update(mode_settings)
    config["performance_mode"] = mode_name
    return config