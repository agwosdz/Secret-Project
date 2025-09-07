import pytest
from unittest.mock import Mock, patch
from usb_midi_service import USBMIDIInputService
from midi_parser import MIDIParser
from playback_service import PlaybackService


class TestMIDIMappingConfiguration:
    """Test cases for MIDI mapping with different piano configurations"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_led_controller = Mock()
        self.mock_websocket_callback = Mock()
    
    @patch('usb_midi_service.get_config')
    @patch('usb_midi_service.get_piano_specs')
    def test_usb_midi_service_88_key_normal(self, mock_get_specs, mock_get_config):
        """Test USB MIDI service with 88-key piano, normal orientation"""
        # Mock configuration
        mock_get_config.side_effect = lambda key, default=None: {
            'piano_size': '88-key',
            'led_orientation': 'normal'
        }.get(key, default)
        
        mock_get_specs.return_value = {
            'num_keys': 88,
            'min_midi_note': 21,
            'max_midi_note': 108
        }
        
        service = USBMIDIInputService(self.mock_led_controller, self.mock_websocket_callback)
        
        # Verify configuration was loaded correctly
        assert service.num_leds == 88
        assert service.min_midi_note == 21
        assert service.max_midi_note == 108
        assert service.led_orientation == 'normal'
    
    @patch('usb_midi_service.get_config')
    @patch('usb_midi_service.get_piano_specs')
    def test_usb_midi_service_61_key_reversed(self, mock_get_specs, mock_get_config):
        """Test USB MIDI service with 61-key piano, reversed orientation"""
        # Mock configuration
        mock_get_config.side_effect = lambda key, default=None: {
            'piano_size': '61-key',
            'led_orientation': 'reversed'
        }.get(key, default)
        
        mock_get_specs.return_value = {
            'num_keys': 61,
            'min_midi_note': 36,
            'max_midi_note': 96
        }
        
        service = USBMIDIInputService(self.mock_led_controller, self.mock_websocket_callback)
        
        # Verify configuration was loaded correctly
        assert service.num_leds == 61
        assert service.min_midi_note == 36
        assert service.max_midi_note == 96
        assert service.led_orientation == 'reversed'
    
    @patch('usb_midi_service.get_config')
    @patch('usb_midi_service.get_piano_specs')
    def test_midi_note_to_led_mapping_normal_orientation(self, mock_get_specs, mock_get_config):
        """Test MIDI note to LED mapping with normal orientation"""
        # Mock configuration for 88-key piano
        mock_get_config.side_effect = lambda key, default=None: {
            'piano_size': '88-key',
            'led_orientation': 'normal'
        }.get(key, default)
        
        mock_get_specs.return_value = {
            'num_keys': 88,
            'min_midi_note': 21,
            'max_midi_note': 108
        }
        
        service = USBMIDIInputService(self.mock_led_controller, self.mock_websocket_callback)
        
        # Test mapping for different MIDI notes
        test_cases = [
            (21, 0),    # Lowest note (A0) -> LED 0
            (60, 39),   # Middle C -> LED 39
            (108, 87),  # Highest note (C8) -> LED 87
        ]
        
        for midi_note, expected_led in test_cases:
            led_index = service._map_note_to_led(midi_note)
            assert led_index == expected_led, f"MIDI note {midi_note} should map to LED {expected_led}, got {led_index}"
    
    @patch('usb_midi_service.get_config')
    @patch('usb_midi_service.get_piano_specs')
    def test_midi_note_to_led_mapping_reversed_orientation(self, mock_get_specs, mock_get_config):
        """Test MIDI note to LED mapping with reversed orientation"""
        # Mock configuration for 88-key piano with reversed orientation
        mock_get_config.side_effect = lambda key, default=None: {
            'piano_size': '88-key',
            'led_orientation': 'reversed'
        }.get(key, default)
        
        mock_get_specs.return_value = {
            'num_keys': 88,
            'min_midi_note': 21,
            'max_midi_note': 108
        }
        
        service = USBMIDIInputService(self.mock_led_controller, self.mock_websocket_callback)
        
        # Test mapping for different MIDI notes (reversed)
        test_cases = [
            (21, 87),   # Lowest note (A0) -> LED 87 (reversed)
            (60, 48),   # Middle C -> LED 48 (reversed)
            (108, 0),   # Highest note (C8) -> LED 0 (reversed)
        ]
        
        for midi_note, expected_led in test_cases:
            led_index = service._map_note_to_led(midi_note)
            assert led_index == expected_led, f"MIDI note {midi_note} should map to LED {expected_led}, got {led_index}"
    
    @patch('usb_midi_service.get_config')
    @patch('usb_midi_service.get_piano_specs')
    def test_midi_note_out_of_range(self, mock_get_specs, mock_get_config):
        """Test MIDI note mapping for notes outside piano range"""
        # Mock configuration for 61-key piano
        mock_get_config.side_effect = lambda key, default=None: {
            'piano_size': '61-key',
            'led_orientation': 'normal'
        }.get(key, default)
        
        mock_get_specs.return_value = {
            'num_keys': 61,
            'min_midi_note': 36,
            'max_midi_note': 96
        }
        
        service = USBMIDIInputService(self.mock_led_controller, self.mock_websocket_callback)
        
        # Test notes outside range
        test_cases = [
            (20, None),  # Below minimum
            (35, None),  # Below minimum
            (97, None),  # Above maximum
            (127, None), # Above maximum
        ]
        
        for midi_note, expected_result in test_cases:
            led_index = service._map_note_to_led(midi_note)
            assert led_index == expected_result, f"MIDI note {midi_note} outside range should return None, got {led_index}"
    
    @patch('midi_parser.get_piano_specs')
    def test_midi_parser_configuration(self, mock_get_specs):
        """Test MIDI parser uses correct piano configuration"""
        mock_get_specs.return_value = {
            'num_keys': 76,
            'min_midi_note': 28,
            'max_midi_note': 103
        }
        
        with patch('midi_parser.get_config', return_value='76-key'):
            parser = MIDIParser()
            
            # Verify parser loaded correct configuration
            assert parser.led_count == 76
            mock_get_specs.assert_called_once_with('76-key')
    
    @patch('playback_service.get_config')
    @patch('playback_service.get_piano_specs')
    def test_playback_service_configuration(self, mock_get_specs, mock_get_config):
        """Test playback service uses correct piano configuration"""
        mock_get_config.side_effect = lambda key, default=None: {
            'piano_size': '49-key',
            'led_orientation': 'reversed'
        }.get(key, default)
        
        mock_get_specs.return_value = {
            'num_keys': 49,
            'min_midi_note': 36,
            'max_midi_note': 84
        }
        
        service = PlaybackService(self.mock_led_controller)
        
        # Verify service loaded correct configuration
        assert service.num_leds == 49
        assert service.min_midi_note == 36
        assert service.max_midi_note == 84
        assert service.led_orientation == 'reversed'


class TestPianoSizeVariations:
    """Test cases for different piano size configurations"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_led_controller = Mock()
        self.mock_websocket_callback = Mock()
    
    @pytest.mark.parametrize("piano_size,expected_specs", [
        ("25-key", {"num_keys": 25, "min_midi_note": 60, "max_midi_note": 84}),
        ("37-key", {"num_keys": 37, "min_midi_note": 48, "max_midi_note": 84}),
        ("49-key", {"num_keys": 49, "min_midi_note": 36, "max_midi_note": 84}),
        ("61-key", {"num_keys": 61, "min_midi_note": 36, "max_midi_note": 96}),
        ("76-key", {"num_keys": 76, "min_midi_note": 28, "max_midi_note": 103}),
        ("88-key", {"num_keys": 88, "min_midi_note": 21, "max_midi_note": 108}),
    ])
    @patch('usb_midi_service.get_config')
    @patch('usb_midi_service.get_piano_specs')
    def test_all_piano_sizes(self, mock_get_specs, mock_get_config, piano_size, expected_specs):
        """Test USB MIDI service with all supported piano sizes"""
        # Mock configuration
        mock_get_config.side_effect = lambda key, default=None: {
            'piano_size': piano_size,
            'led_orientation': 'normal'
        }.get(key, default)
        
        mock_get_specs.return_value = expected_specs
        
        service = USBMIDIInputService(self.mock_led_controller, self.mock_websocket_callback)
        
        # Verify configuration was loaded correctly
        assert service.num_leds == expected_specs['num_keys']
        assert service.min_midi_note == expected_specs['min_midi_note']
        assert service.max_midi_note == expected_specs['max_midi_note']
        
        # Test that first and last notes map correctly
        first_led = service._map_note_to_led(expected_specs['min_midi_note'])
        last_led = service._map_note_to_led(expected_specs['max_midi_note'])
        
        assert first_led == 0
        assert last_led == expected_specs['num_keys'] - 1


class TestLEDOrientationMapping:
    """Test cases for LED orientation mapping"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_led_controller = Mock()
        self.mock_websocket_callback = Mock()
    
    @patch('usb_midi_service.get_config')
    @patch('usb_midi_service.get_piano_specs')
    def test_orientation_mapping_consistency(self, mock_get_specs, mock_get_config):
        """Test that orientation mapping is consistent across the range"""
        # Test with 61-key piano
        mock_get_specs.return_value = {
            'num_keys': 61,
            'min_midi_note': 36,
            'max_midi_note': 96
        }
        
        # Test normal orientation
        mock_get_config.side_effect = lambda key, default=None: {
            'piano_size': '61-key',
            'led_orientation': 'normal'
        }.get(key, default)
        
        service_normal = USBMIDIInputService(self.mock_led_controller, self.mock_websocket_callback)
        
        # Test reversed orientation
        mock_get_config.side_effect = lambda key, default=None: {
            'piano_size': '61-key',
            'led_orientation': 'reversed'
        }.get(key, default)
        
        service_reversed = USBMIDIInputService(self.mock_led_controller, self.mock_websocket_callback)
        
        # Test that mappings are exact opposites
        for midi_note in range(36, 97):  # All notes in range
            normal_led = service_normal._map_note_to_led(midi_note)
            reversed_led = service_reversed._map_note_to_led(midi_note)
            
            if normal_led is not None and reversed_led is not None:
                # Should be exact opposites
                assert normal_led + reversed_led == 60  # 61 - 1 = 60