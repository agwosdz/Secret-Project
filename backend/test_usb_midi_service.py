import unittest
from unittest.mock import Mock, patch, MagicMock, call
import threading
import time
from usb_midi_service import USBMIDIInputService

class TestUSBMIDIInputService(unittest.TestCase):
    """Unit tests for USBMIDIInputService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_led_controller = Mock()
        self.mock_websocket_callback = Mock()
        
        self.service = USBMIDIInputService(
            led_controller=self.mock_led_controller,
            websocket_callback=self.mock_websocket_callback
        )
        # Reset event count for clean test state
        self.service._event_count = 0
    
    def tearDown(self):
        """Clean up after tests"""
        if self.service.is_listening:
            self.service.stop_listening()
    
    @patch('usb_midi_service.mido')
    def test_get_available_devices(self, mock_mido):
        """Test device discovery"""
        mock_mido.get_input_names.return_value = ['Device 1', 'Device 2']
        
        devices = self.service.get_available_devices()
        
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0].name, 'Device 1')
        self.assertEqual(devices[0].id, 0)
        self.assertEqual(devices[1].name, 'Device 2')
        self.assertEqual(devices[1].id, 1)
    
    @patch('usb_midi_service.mido')
    def test_get_available_devices_error(self, mock_mido):
        """Test MIDI device discovery with error"""
        # Mock mido.get_input_names() raising an exception
        mock_mido.get_input_names.side_effect = Exception("MIDI error")
        
        devices = self.service.get_available_devices()
        
        self.assertEqual(devices, [])
        mock_mido.get_input_names.assert_called_once()
    
    def test_note_to_led_mapping(self):
        """Test MIDI note to LED index mapping"""
        # Test boundary cases
        self.assertEqual(self.service._map_note_to_led(21), 0)  # A0
        self.assertEqual(self.service._map_note_to_led(108), 87)  # C8
        self.assertEqual(self.service._map_note_to_led(60), 39)  # Middle C
        
        # Test out of range
        self.assertIsNone(self.service._map_note_to_led(20))  # Below range
        self.assertIsNone(self.service._map_note_to_led(109))  # Above range
    
    def test_velocity_to_brightness(self):
        """Test velocity to brightness conversion"""
        # Test minimum velocity
        brightness = self.service._velocity_to_brightness(0)
        self.assertAlmostEqual(brightness, 0.1, places=2)  # Min brightness is 0.1
        
        # Test maximum velocity
        brightness = self.service._velocity_to_brightness(127)
        self.assertEqual(brightness, 1.0)
        
        # Test middle velocity
        brightness = self.service._velocity_to_brightness(64)
        self.assertGreater(brightness, 0.1)
        self.assertLess(brightness, 1.0)
    
    def test_get_note_color(self):
        """Test note to color conversion"""
        # Test different notes
        color_c = self.service._get_note_color(60)  # Middle C
        color_cs = self.service._get_note_color(61)  # C#
        color_d = self.service._get_note_color(62)  # D
        
        # All should be RGB tuples
        self.assertIsInstance(color_c, tuple)
        self.assertIsInstance(color_cs, tuple)
        self.assertIsInstance(color_d, tuple)
        
        # Each should have 3 components
        self.assertEqual(len(color_c), 3)
        self.assertEqual(len(color_cs), 3)
        self.assertEqual(len(color_d), 3)
        
        # Colors should be different for different notes
        self.assertNotEqual(color_c, color_cs)
        self.assertNotEqual(color_cs, color_d)
    
    @patch('usb_midi_service.mido')
    def test_start_listening_success(self, mock_mido):
        """Test successful MIDI input start"""
        mock_port = Mock()
        mock_mido.open_input.return_value = mock_port
        
        result = self.service.start_listening('Test Device')
        
        self.assertTrue(result)
        self.assertTrue(self.service.is_listening)
        self.assertEqual(self.service.current_device, 'Test Device')
        mock_mido.open_input.assert_called_once_with('Test Device')
    
    @patch('usb_midi_service.mido')
    def test_start_listening_failure(self, mock_mido):
        """Test MIDI input start failure"""
        mock_mido.open_input.side_effect = Exception("Device not found")
        
        result = self.service.start_listening('Invalid Device')
        
        self.assertFalse(result)
        self.assertFalse(self.service.is_listening)
        self.assertIsNone(self.service.current_device)
        mock_mido.open_input.assert_called_once_with('Invalid Device')
    
    @patch('usb_midi_service.mido')
    def test_stop_listening(self, mock_mido):
        """Test MIDI input stop"""
        mock_port = Mock()
        mock_mido.open_input.return_value = mock_port
        
        # Start input first
        self.service.start_listening('Test Device')
        self.assertTrue(self.service.is_listening)
        
        # Stop input
        result = self.service.stop_listening()
        
        self.assertTrue(result)
        self.assertFalse(self.service.is_listening)
        mock_port.close.assert_called_once()
    
    def test_get_status_inactive(self):
        """Test status when service is inactive"""
        status = self.service.get_status()
        
        self.assertIn('state', status)
        self.assertIn('device', status)
        self.assertIn('is_listening', status)
        self.assertIn('active_notes', status)
        
        self.assertEqual(status['state'], 'idle')
        self.assertIsNone(status['device'])
        self.assertFalse(status['is_listening'])
        self.assertEqual(status['active_notes'], 0)
    
    @patch('usb_midi_service.mido')
    def test_get_status_active(self, mock_mido):
        """Test status when service is active"""
        mock_port = Mock()
        mock_mido.open_input.return_value = mock_port
        
        self.service.start_listening('Test Device')
        status = self.service.get_status()
        
        self.assertEqual(status['state'], 'listening')
        self.assertEqual(status['device'], 'Test Device')
        self.assertTrue(status['is_listening'])
    
    @patch('usb_midi_service.mido')
    def test_process_note_on(self, mock_mido):
        """Test processing MIDI note_on message"""
        mock_port = Mock()
        mock_mido.open_input.return_value = mock_port
        
        # Create mock MIDI message
        mock_msg = Mock()
        mock_msg.type = 'note_on'
        mock_msg.note = 60  # Middle C
        mock_msg.velocity = 64
        mock_msg.channel = 0
        
        self.service.start_listening('Test Device')
        self.service._process_midi_message(mock_msg)
        
        # Verify LED was turned on
        expected_led_index = 39  # Middle C maps to LED 39
        expected_color = (141, 0, 0)  # Red color with brightness applied
        
        self.mock_led_controller.turn_on_led.assert_called_once_with(
            expected_led_index, expected_color, auto_show=True
        )
        
        # Verify WebSocket callback
        self.mock_websocket_callback.assert_called_with(
            'midi_input',
            {
                'type': 'midi_input_event',
                'note': 60,
                'velocity': 64,
                'channel': 0,
                'event_type': 'note_on',
                'active_notes': 1,
                'timestamp': unittest.mock.ANY
            }
        )
        
        # Verify note tracking
        self.assertIn(60, self.service.active_notes)
    
    @patch('usb_midi_service.mido')
    def test_process_note_off(self, mock_mido):
        """Test processing MIDI note_off message"""
        mock_port = Mock()
        mock_mido.open_input.return_value = mock_port
        
        # Start input and simulate note_on first
        self.service.start_listening('Test Device')
        self.service._active_notes[60] = {
            'timestamp': time.time(), 
            'velocity': 64, 
            'channel': 0,
            'led_index': 39,  # Middle C maps to LED 39
            'color': (255, 0, 0)
        }
        
        # Create mock MIDI message
        mock_msg = Mock()
        mock_msg.type = 'note_off'
        mock_msg.note = 60
        mock_msg.velocity = 0
        mock_msg.channel = 0
        
        self.service._process_midi_message(mock_msg)
        
        # Verify LED was turned off
        expected_led_index = 39  # Middle C maps to LED 39
        
        self.mock_led_controller.turn_off_led.assert_called_once_with(
            expected_led_index, auto_show=True
        )
        
        # Verify WebSocket callback
        self.mock_websocket_callback.assert_called_with(
            'midi_input',
            {
                'type': 'midi_input_event',
                'note': 60,
                'velocity': 0,
                'channel': 0,
                'event_type': 'note_off',
                'active_notes': 0,
                'timestamp': unittest.mock.ANY
            }
        )
        
        # Verify note tracking
        self.assertNotIn(60, self.service.active_notes)
    
    @patch('usb_midi_service.mido')
    def test_process_unsupported_message(self, mock_mido):
        """Test processing unsupported MIDI message types"""
        mock_port = Mock()
        mock_mido.open_input.return_value = mock_port
        
        # Create mock MIDI message with unsupported type
        mock_msg = Mock()
        mock_msg.type = 'control_change'
        mock_msg.control = 64
        mock_msg.value = 127
        
        self.service.start_listening('Test Device')
        
        # This should not raise an exception
        self.service._process_midi_message(mock_msg)
        
        # LED controller should not be called
        self.mock_led_controller.turn_on_led.assert_not_called()
        self.mock_led_controller.turn_off_led.assert_not_called()
    
    def test_cleanup_on_stop(self):
        """Test proper cleanup when stopping input"""
        with patch('usb_midi_service.mido') as mock_mido:
            mock_port = Mock()
            mock_mido.open_input.return_value = mock_port
            
            # Start input and add some active notes
            self.service.start_listening('Test Device')
            for note in [60, 64, 67]:  # C major chord
                led_index = self.service._map_note_to_led(note)
                self.service._active_notes[note] = {
                    'timestamp': time.time(), 
                    'velocity': 64, 
                    'channel': 0,
                    'led_index': led_index,
                    'color': (255, 0, 0)
                }
            
            # Stop input
            self.service.stop_listening()
            
            # Verify all LEDs were turned off
            self.mock_led_controller.turn_off_all.assert_called_once()
            
            # Verify active notes were cleared
            self.assertEqual(len(self.service.active_notes), 0)
            
            # Verify port was closed
            mock_port.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()