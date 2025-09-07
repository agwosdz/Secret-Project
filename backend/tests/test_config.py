import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, mock_open
from config import (
    load_config, save_config, update_config, get_config,
    validate_config, get_piano_specs, DEFAULT_CONFIG
)


class TestConfigManagement:
    """Test cases for configuration management"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.test_config = {
            "piano_size": "88-key",
            "gpio_pin": 18,
            "led_orientation": "normal",
            "led_count": 88,
            "brightness": 0.7
        }
    
    def test_default_config_structure(self):
        """Test that default config has all required fields"""
        required_fields = [
            "led_count", "max_led_count", "brightness", "pin",
            "piano_size", "gpio_pin", "led_orientation"
        ]
        
        for field in required_fields:
            assert field in DEFAULT_CONFIG, f"Missing required field: {field}"
    
    @patch('config.CONFIG_FILE')
    def test_load_config_file_not_exists(self, mock_config_file):
        """Test loading config when file doesn't exist"""
        mock_config_file.exists.return_value = False
        
        with patch('config.save_config') as mock_save:
            mock_save.return_value = True
            config = load_config()
            
            assert config == DEFAULT_CONFIG
            mock_save.assert_called_once_with(DEFAULT_CONFIG)
    
    @patch('config.CONFIG_FILE')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_success(self, mock_file, mock_config_file):
        """Test successful config loading"""
        mock_config_file.exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(self.test_config)
        
        with patch('json.load', return_value=self.test_config):
            config = load_config()
            
            assert config == self.test_config
    
    @patch('config.CONFIG_FILE')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_json_error(self, mock_file, mock_config_file):
        """Test config loading with JSON error"""
        mock_config_file.exists.return_value = True
        
        with patch('json.load', side_effect=json.JSONDecodeError("test", "test", 0)):
            config = load_config()
            
            assert config == DEFAULT_CONFIG
    
    @patch('builtins.open', new_callable=mock_open)
    def test_save_config_success(self, mock_file):
        """Test successful config saving"""
        with patch('json.dump') as mock_dump:
            result = save_config(self.test_config)
            
            assert result is True
            mock_dump.assert_called_once_with(self.test_config, mock_file.return_value, indent=4)
    
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    def test_save_config_error(self, mock_file):
        """Test config saving with IO error"""
        result = save_config(self.test_config)
        
        assert result is False
    
    @patch('config.load_config')
    @patch('config.save_config')
    def test_update_config(self, mock_save, mock_load):
        """Test updating specific config value"""
        mock_load.return_value = self.test_config.copy()
        mock_save.return_value = True
        
        result = update_config("brightness", 0.8)
        
        assert result is True
        mock_save.assert_called_once()
        saved_config = mock_save.call_args[0][0]
        assert saved_config["brightness"] == 0.8
    
    @patch('config.load_config')
    def test_get_config(self, mock_load):
        """Test getting specific config value"""
        mock_load.return_value = self.test_config
        
        # Test existing key
        value = get_config("piano_size")
        assert value == "88-key"
        
        # Test non-existing key with default
        value = get_config("non_existing", "default_value")
        assert value == "default_value"
        
        # Test non-existing key without default
        value = get_config("non_existing")
        assert value is None


class TestConfigValidation:
    """Test cases for configuration validation"""
    
    def test_validate_valid_config(self):
        """Test validation of valid configuration"""
        valid_config = {
            "led_count": 88,
            "gpio_pin": 18,
            "piano_size": "88-key",
            "led_orientation": "normal",
            "brightness": 0.5
        }
        
        errors = validate_config(valid_config)
        assert errors == []
    
    def test_validate_invalid_led_count(self):
        """Test validation of invalid LED count"""
        # Test negative LED count
        config = {"led_count": -1}
        errors = validate_config(config)
        assert "led_count must be a positive integer" in errors
        
        # Test non-integer LED count
        config = {"led_count": "invalid"}
        errors = validate_config(config)
        assert "led_count must be a positive integer" in errors
        
        # Test LED count exceeding maximum
        config = {"led_count": 500, "max_led_count": 300}
        errors = validate_config(config)
        assert "led_count cannot exceed 300" in errors
    
    def test_validate_invalid_gpio_pin(self):
        """Test validation of invalid GPIO pin"""
        # Test negative GPIO pin
        config = {"gpio_pin": -1}
        errors = validate_config(config)
        assert "gpio_pin must be an integer between 0 and 27" in errors
        
        # Test GPIO pin too high
        config = {"gpio_pin": 30}
        errors = validate_config(config)
        assert "gpio_pin must be an integer between 0 and 27" in errors
        
        # Test non-integer GPIO pin
        config = {"gpio_pin": "invalid"}
        errors = validate_config(config)
        assert "gpio_pin must be an integer between 0 and 27" in errors
    
    def test_validate_invalid_piano_size(self):
        """Test validation of invalid piano size"""
        config = {"piano_size": "invalid-size"}
        errors = validate_config(config)
        assert "piano_size must be one of:" in errors[0]
        assert "25-key" in errors[0]
        assert "88-key" in errors[0]
    
    def test_validate_invalid_led_orientation(self):
        """Test validation of invalid LED orientation"""
        config = {"led_orientation": "invalid"}
        errors = validate_config(config)
        assert "led_orientation must be one of: normal, reversed" in errors
    
    def test_validate_invalid_brightness(self):
        """Test validation of invalid brightness"""
        # Test negative brightness
        config = {"brightness": -0.1}
        errors = validate_config(config)
        assert "brightness must be a number between 0.0 and 1.0" in errors
        
        # Test brightness too high
        config = {"brightness": 1.5}
        errors = validate_config(config)
        assert "brightness must be a number between 0.0 and 1.0" in errors
        
        # Test non-numeric brightness
        config = {"brightness": "invalid"}
        errors = validate_config(config)
        assert "brightness must be a number between 0.0 and 1.0" in errors
    
    def test_validate_multiple_errors(self):
        """Test validation with multiple errors"""
        config = {
            "led_count": -1,
            "gpio_pin": 50,
            "piano_size": "invalid",
            "led_orientation": "wrong",
            "brightness": 2.0
        }
        
        errors = validate_config(config)
        assert len(errors) == 5  # Should have 5 validation errors


class TestPianoSpecs:
    """Test cases for piano specifications"""
    
    def test_get_piano_specs_all_sizes(self):
        """Test getting specs for all supported piano sizes"""
        expected_sizes = {
            "25-key": {"num_keys": 25, "min_midi_note": 60, "max_midi_note": 84},
            "37-key": {"num_keys": 37, "min_midi_note": 48, "max_midi_note": 84},
            "49-key": {"num_keys": 49, "min_midi_note": 36, "max_midi_note": 84},
            "61-key": {"num_keys": 61, "min_midi_note": 36, "max_midi_note": 96},
            "76-key": {"num_keys": 76, "min_midi_note": 28, "max_midi_note": 103},
            "88-key": {"num_keys": 88, "min_midi_note": 21, "max_midi_note": 108}
        }
        
        for size, expected_specs in expected_sizes.items():
            specs = get_piano_specs(size)
            assert specs == expected_specs, f"Specs mismatch for {size}"
    
    def test_get_piano_specs_invalid_size(self):
        """Test getting specs for invalid piano size"""
        specs = get_piano_specs("invalid-size")
        # Should default to 88-key
        expected = {"num_keys": 88, "min_midi_note": 21, "max_midi_note": 108}
        assert specs == expected
    
    def test_piano_specs_consistency(self):
        """Test that piano specs are internally consistent"""
        for size in ["25-key", "37-key", "49-key", "61-key", "76-key", "88-key"]:
            specs = get_piano_specs(size)
            
            # Check that max_midi_note > min_midi_note
            assert specs["max_midi_note"] > specs["min_midi_note"]
            
            # Check that the range matches the number of keys
            note_range = specs["max_midi_note"] - specs["min_midi_note"] + 1
            assert note_range == specs["num_keys"]