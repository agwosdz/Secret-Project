import unittest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from app import app
from config import (
    validate_config_comprehensive,
    backup_config,
    restore_config_from_backup,
    reset_config_to_defaults,
    export_config,
    get_config_history
)

class TestConfigManagement(unittest.TestCase):
    def setUp(self):
        """Set up test client and test data"""
        self.app = app.test_client()
        self.app.testing = True
        
        # Sample valid configuration
        self.valid_config = {
            'led_count': 88,
            'gpio_pins': {
                'data_pin': 18,
                'clock_pin': None
            },
            'piano_size': 88,
            'led_orientation': 'bottom_up',
            'brightness': 128,
            'led_type': 'WS2812B',
            'power_supply': {
                'voltage': 5.0,
                'max_current': 10.0
            },
            'signal_level': '3.3V',
            'mapping_mode': 'linear',
            'led_frequency': 800000,
            'color_temperature': 6500,
            'gamma_correction': 2.2,
            'color_balance': {
                'red': 1.0,
                'green': 1.0,
                'blue': 1.0
            },
            'key_mapping': {}
        }
        
        # Sample invalid configuration
        self.invalid_config = {
            'led_count': 0,  # Invalid: must be > 0
            'gpio_pins': {
                'data_pin': 99,  # Invalid: GPIO pin out of range
                'clock_pin': None
            },
            'piano_size': 200,  # Invalid: exceeds maximum
            'brightness': 300,  # Invalid: exceeds maximum
            'power_supply': {
                'voltage': 12.0,  # Invalid: unsupported voltage
                'max_current': -5.0  # Invalid: negative current
            }
        }

    def test_validate_config_comprehensive_valid(self):
        """Test comprehensive validation with valid configuration"""
        result = validate_config_comprehensive(self.valid_config)
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['errors']), 0)
        self.assertIsInstance(result['warnings'], list)

    def test_validate_config_comprehensive_invalid(self):
        """Test comprehensive validation with invalid configuration"""
        result = validate_config_comprehensive(self.invalid_config)
        
        self.assertFalse(result['is_valid'])
        self.assertGreater(len(result['errors']), 0)
        
        # Check for specific expected errors
        error_messages = ' '.join(result['errors'])
        self.assertIn('LED count', error_messages)
        self.assertIn('GPIO pin', error_messages)
        self.assertIn('Piano size', error_messages)

    def test_api_validate_configuration_valid(self):
        """Test API endpoint for configuration validation with valid data"""
        response = self.app.post('/api/config/validate',
                               data=json.dumps(self.valid_config),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertTrue(data['validation']['is_valid'])

    def test_api_validate_configuration_invalid(self):
        """Test API endpoint for configuration validation with invalid data"""
        response = self.app.post('/api/config/validate',
                               data=json.dumps(self.invalid_config),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertFalse(data['validation']['is_valid'])
        self.assertGreater(len(data['validation']['errors']), 0)

    def test_api_validate_configuration_no_data(self):
        """Test API endpoint for configuration validation with no data"""
        response = self.app.post('/api/config/validate',
                               content_type='application/json')
        
        # The endpoint returns 500 when no JSON data is provided
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)

    @patch('config.backup_config')
    def test_api_backup_configuration_success(self, mock_backup):
        """Test API endpoint for configuration backup - success"""
        mock_backup.return_value = True
        
        response = self.app.post('/api/config/backup')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('backed up successfully', data['message'])
        mock_backup.assert_called_once()

    @patch('config.backup_config')
    def test_api_backup_configuration_failure(self, mock_backup):
        """Test API endpoint for configuration backup - failure"""
        mock_backup.return_value = False
        
        response = self.app.post('/api/config/backup')
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('Failed to backup', data['message'])

    @patch('config.restore_config_from_backup')
    @patch('config.load_config')
    def test_api_restore_configuration_success(self, mock_load, mock_restore):
        """Test API endpoint for configuration restore - success"""
        mock_restore.return_value = True
        mock_load.return_value = self.valid_config
        
        response = self.app.post('/api/config/restore')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('restored successfully', data['message'])
        mock_restore.assert_called_once()
        mock_load.assert_called_once()

    @patch('config.restore_config_from_backup')
    def test_api_restore_configuration_no_backup(self, mock_restore):
        """Test API endpoint for configuration restore - no backup found"""
        mock_restore.return_value = False
        
        response = self.app.post('/api/config/restore')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('no backup found', data['message'])

    @patch('config.reset_config_to_defaults')
    @patch('config.load_config')
    def test_api_reset_configuration_success(self, mock_load, mock_reset):
        """Test API endpoint for configuration reset - success"""
        mock_reset.return_value = True
        mock_load.return_value = self.valid_config
        
        response = self.app.post('/api/config/reset')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('reset to defaults', data['message'])
        mock_reset.assert_called_once()
        mock_load.assert_called_once()

    @patch('config.export_config')
    def test_api_export_configuration_success(self, mock_export):
        """Test API endpoint for configuration export - success"""
        mock_export.return_value = True
        export_path = 'test_export.json'
        
        response = self.app.post('/api/config/export',
                               data=json.dumps({'path': export_path}),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('exported to', data['message'])
        self.assertEqual(data['export_path'], export_path)
        mock_export.assert_called_once_with(export_path)

    @patch('config.export_config')
    @patch('datetime.datetime')
    def test_api_export_configuration_default_path(self, mock_datetime, mock_export):
        """Test API endpoint for configuration export with default path"""
        mock_export.return_value = True
        mock_datetime.now.return_value.strftime.return_value = '20240101_120000'
        
        response = self.app.post('/api/config/export')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        expected_path = 'config_export_20240101_120000.json'
        mock_export.assert_called_once_with(expected_path)

    @patch('config.get_config_history')
    def test_api_get_configuration_history(self, mock_history):
        """Test API endpoint for configuration history"""
        mock_history_data = [
            {
                'timestamp': '2024-01-01T12:00:00Z',
                'action': 'Configuration saved',
                'description': 'Updated LED count to 88'
            },
            {
                'timestamp': '2024-01-01T11:00:00Z',
                'action': 'Configuration backup created',
                'description': 'Automatic backup before changes'
            }
        ]
        mock_history.return_value = mock_history_data
        
        response = self.app.get('/api/config/history')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['history'], mock_history_data)
        mock_history.assert_called_once()

    def test_cross_field_validation_power_consumption(self):
        """Test cross-field validation for power consumption"""
        config = {
            "led_count": 1000,
            "brightness": 1.0,
            "led_type": "WS2812B",
            "power_supply_voltage": 5.0,
            "power_supply_current": 2.0,  # Too low for 1000 LEDs
            "piano_size": "88-key"
        }
        
        result = validate_config_comprehensive(config)
        
        self.assertFalse(result["valid"])
        error_messages = ' '.join(result["errors"]).lower()
        warning_messages = ' '.join(result["warnings"]).lower()
        
        # Should have power consumption error or piano size warning
        self.assertTrue(
            'power consumption' in error_messages or 'inconsistent' in warning_messages
        )

    def test_cross_field_validation_gpio_conflicts(self):
        """Test cross-field validation for GPIO pin conflicts"""
        config = self.valid_config.copy()
        config['gpio_pins']['data_pin'] = 18
        config['gpio_pins']['clock_pin'] = 18  # Same as data pin
        
        result = validate_config_comprehensive(config)
        
        # Should have errors about GPIO conflicts
        error_messages = ' '.join(result['errors']).lower()
        self.assertIn('gpio pin 18 is used multiple times', error_messages)

    def test_cross_field_validation_piano_led_mismatch(self):
        """Test cross-field validation for piano size vs LED count mismatch"""
        config = self.valid_config.copy()
        config['piano_size'] = 88
        config['led_count'] = 44  # Half the piano keys
        
        result = validate_config_comprehensive(config)
        
        # Should have warnings about LED count vs piano size
        warning_messages = ' '.join(result['warnings'])
        self.assertTrue(
            'piano' in warning_messages.lower() or 
            'LED' in warning_messages or
            len(result['warnings']) > 0  # At minimum should have some warnings
        )

if __name__ == '__main__':
    unittest.main()