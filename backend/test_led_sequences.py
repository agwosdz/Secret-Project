import unittest
import json
import threading
import time
from unittest.mock import patch, MagicMock
from app import app

class TestLEDSequences(unittest.TestCase):
    def setUp(self):
        """Set up test client"""
        self.app = app.test_client()
        self.app.testing = True

    def tearDown(self):
        """Clean up after tests"""
        # Clean up is handled by mocks
        pass

    @patch('app.LEDController')
    def test_api_led_test_sequence_rainbow(self, mock_led_controller):
        """Test LED test sequence API with rainbow pattern"""
        mock_controller = MagicMock()
        mock_led_controller.return_value = mock_controller
        
        test_data = {
            'sequence_type': 'rainbow',
            'duration': 2,
            'led_count': 10,
            'gpio_pin': 18
        }
        
        response = self.app.post('/api/led-test-sequence',
                               data=json.dumps(test_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('Rainbow test sequence started', data['message'])
        
        # Verify LED controller was initialized
        mock_led_controller.assert_called_once_with(led_count=10, gpio_pin=18)

    @patch('app.LEDController')
    def test_api_led_test_sequence_chase(self, mock_led_controller):
        """Test LED test sequence API with chase pattern"""
        mock_controller = MagicMock()
        mock_led_controller.return_value = mock_controller
        
        test_data = {
            'sequence_type': 'chase',
            'duration': 3,
            'led_count': 20,
            'gpio_pin': 21
        }
        
        response = self.app.post('/api/led-test-sequence',
                               data=json.dumps(test_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('Chase test sequence started', data['message'])

    @patch('app.LEDController')
    def test_api_led_test_sequence_fade(self, mock_led_controller):
        """Test LED test sequence API with fade pattern"""
        mock_controller = MagicMock()
        mock_led_controller.return_value = mock_controller
        
        test_data = {
            'sequence_type': 'fade',
            'duration': 5,
            'led_count': 88,
            'gpio_pin': 18
        }
        
        response = self.app.post('/api/led-test-sequence',
                               data=json.dumps(test_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('Fade test sequence started', data['message'])

    @patch('app.LEDController')
    def test_api_led_test_sequence_piano_keys(self, mock_led_controller):
        """Test LED test sequence API with piano keys pattern"""
        mock_controller = MagicMock()
        mock_led_controller.return_value = mock_controller
        
        test_data = {
            'sequence_type': 'piano_keys',
            'duration': 4,
            'led_count': 88,
            'gpio_pin': 18
        }
        
        response = self.app.post('/api/led-test-sequence',
                               data=json.dumps(test_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('Piano keys test sequence started', data['message'])

    def test_api_led_test_sequence_invalid_type(self):
        """Test LED test sequence API with invalid sequence type"""
        test_data = {
            'sequence_type': 'invalid_type',
            'duration': 2,
            'led_count': 10,
            'gpio_pin': 18
        }
        
        response = self.app.post('/api/led-test-sequence',
                               data=json.dumps(test_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('Invalid sequence type', data['message'])

    def test_api_led_test_sequence_missing_data(self):
        """Test LED test sequence API with missing required data"""
        test_data = {
            'sequence_type': 'rainbow'
            # Missing duration, led_count, gpio_pin
        }
        
        response = self.app.post('/api/led-test-sequence',
                               data=json.dumps(test_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('Missing required parameters', data['message'])

    def test_api_led_test_sequence_no_data(self):
        """Test LED test sequence API with no JSON data"""
        response = self.app.post('/api/led-test-sequence',
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('No data provided', data['message'])

    def test_api_led_test_sequence_stop(self):
        """Test LED test sequence stop API"""
        response = self.app.post('/api/led-test-sequence/stop')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('Test sequence stopped', data['message'])

    @patch('app.test_sequence_thread')
    @patch('app.test_sequence_stop_event')
    def test_stop_sequence_when_running(self, mock_event, mock_thread):
        """Test stopping a running LED test sequence"""
        mock_thread.is_alive.return_value = True
        
        response = self.app.post('/api/led-test-sequence/stop')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('stopped', data['message'].lower())
        
        # Verify stop event was set
        mock_event.set.assert_called_once()

    def test_stop_sequence_when_not_running(self):
        """Test stopping when no sequence is running"""
        with patch('app.test_sequence_thread', None):
            response = self.app.post('/api/led-test-sequence/stop')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertIn('no sequence', data['message'].lower())

    @patch('app.LEDController')
    def test_api_led_test_sequence_already_running(self, mock_led_controller):
        """Test starting a sequence when one is already running"""
        mock_controller = MagicMock()
        mock_led_controller.return_value = mock_controller
        
        test_data = {
            'sequence_type': 'rainbow',
            'duration': 10,  # Long duration
            'led_count': 10,
            'gpio_pin': 18
        }
        
        # Start first sequence
        response1 = self.app.post('/api/led-test-sequence',
                                data=json.dumps(test_data),
                                content_type='application/json')
        
        self.assertEqual(response1.status_code, 200)
        
        # Try to start second sequence immediately
        response2 = self.app.post('/api/led-test-sequence',
                                data=json.dumps(test_data),
                                content_type='application/json')
        
        self.assertEqual(response2.status_code, 400)
        data = json.loads(response2.data)
        self.assertFalse(data['success'])
        self.assertIn('already running', data['message'])
        
        # Clean up
        self.app.post('/api/led-test-sequence/stop')

    def test_hue_to_rgb_conversion(self):
        """Test the _hue_to_rgb helper function"""
        from app import _hue_to_rgb
        
        # Test red (hue = 0)
        r, g, b = _hue_to_rgb(0)
        self.assertEqual((r, g, b), (255, 0, 0))
        
        # Test green (hue = 120)
        r, g, b = _hue_to_rgb(120)
        self.assertEqual((r, g, b), (0, 255, 0))
        
        # Test blue (hue = 240)
        r, g, b = _hue_to_rgb(240)
        self.assertEqual((r, g, b), (0, 0, 255))
        
        # Test yellow (hue = 60)
        r, g, b = _hue_to_rgb(60)
        self.assertEqual((r, g, b), (255, 255, 0))
        
        # Test cyan (hue = 180)
        r, g, b = _hue_to_rgb(180)
        self.assertEqual((r, g, b), (0, 255, 255))
        
        # Test magenta (hue = 300)
        r, g, b = _hue_to_rgb(300)
        self.assertEqual((r, g, b), (255, 0, 255))

    @patch('app.LEDController')
    @patch('app.socketio')
    def test_sequence_websocket_updates(self, mock_socketio, mock_led_controller):
        """Test that sequences send WebSocket updates"""
        mock_controller = MagicMock()
        mock_led_controller.return_value = mock_controller
        
        test_data = {
            'sequence_type': 'rainbow',
            'duration': 1,  # Short duration for quick test
            'led_count': 5,
            'gpio_pin': 18
        }
        
        response = self.app.post('/api/led-test-sequence',
                               data=json.dumps(test_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Wait a bit for the sequence to run
        time.sleep(0.5)
        
        # Check that WebSocket emit was called
        self.assertTrue(mock_socketio.emit.called)
        
        # Check for sequence start event
        calls = mock_socketio.emit.call_args_list
        start_calls = [call for call in calls if call[0][0] == 'test_sequence_started']
        self.assertGreater(len(start_calls), 0)

    @patch('app.LEDController')
    def test_sequence_error_handling(self, mock_led_controller):
        """Test error handling in LED sequences"""
        # Mock LED controller to raise an exception
        mock_led_controller.side_effect = Exception("GPIO initialization failed")
        
        test_data = {
            'sequence_type': 'rainbow',
            'duration': 2,
            'led_count': 10,
            'gpio_pin': 18
        }
        
        response = self.app.post('/api/led-test-sequence',
                               data=json.dumps(test_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('GPIO initialization failed', data['message'])

    def test_sequence_parameter_validation(self):
        """Test parameter validation for LED sequences"""
        # Test invalid duration (negative)
        test_data = {
            'sequence_type': 'rainbow',
            'duration': -1,
            'led_count': 10,
            'gpio_pin': 18
        }
        
        response = self.app.post('/api/led-test-sequence',
                               data=json.dumps(test_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        
        # Test invalid LED count (zero)
        test_data['duration'] = 2
        test_data['led_count'] = 0
        
        response = self.app.post('/api/led-test-sequence',
                               data=json.dumps(test_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        
        # Test invalid GPIO pin (out of range)
        test_data['led_count'] = 10
        test_data['gpio_pin'] = 99
        
        response = self.app.post('/api/led-test-sequence',
                               data=json.dumps(test_data),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

if __name__ == '__main__':
    unittest.main()