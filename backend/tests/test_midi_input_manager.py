import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import time

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from midi_input_manager import MIDIInputManager, UnifiedMIDIEvent, MIDIInputSource
from rtpmidi_service import NetworkMIDIEvent

class TestMIDIInputManager(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.mock_callback = Mock()
        
        # Create mock services
        self.mock_usb_service = Mock()
        self.mock_rtp_service = Mock()
        
        # Mock the service classes
        self.usb_patcher = patch('midi_input_manager.USBMIDIInputService')
        self.rtp_patcher = patch('midi_input_manager.RtpMIDIService')
        
        mock_usb_class = self.usb_patcher.start()
        mock_rtp_class = self.rtp_patcher.start()
        
        mock_usb_class.return_value = self.mock_usb_service
        mock_rtp_class.return_value = self.mock_rtp_service
        
        # Create manager and initialize services
        self.manager = MIDIInputManager(websocket_callback=self.mock_callback)
        self.manager.initialize_services()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.usb_patcher.stop()
        self.rtp_patcher.stop()
    
    def test_initialization(self):
        """Test manager initialization"""
        self.assertIsNotNone(self.manager._usb_service)
        self.assertIsNotNone(self.manager._rtpmidi_service)
        self.assertFalse(self.manager.is_listening)
        self.assertIsNotNone(self.manager._websocket_callback)
    
    def test_start_listening_usb_only(self):
        """Test starting USB MIDI listening only"""
        # Mock USB service to return True for start_listening
        self.mock_usb_service.start_listening.return_value = True
        # Mock rtpMIDI service to return False (not available)
        self.mock_rtp_service.start_listening.return_value = False
        
        result = self.manager.start_listening()
        
        self.assertTrue(result)
        self.assertTrue(self.manager.is_listening)
        self.mock_usb_service.start_listening.assert_called_once()
        self.mock_rtp_service.start_listening.assert_called_once()
    
    def test_start_listening_rtpmidi_only(self):
        """Test starting rtpMIDI listening only"""
        # Mock USB service to return False (not available)
        self.mock_usb_service.start_listening.return_value = False
        # Mock rtpMIDI service to return True for start_listening
        self.mock_rtp_service.start_listening.return_value = True
        
        result = self.manager.start_listening()
        
        self.assertTrue(result)
        self.assertTrue(self.manager.is_listening)
        self.mock_usb_service.start_listening.assert_called_once()
        self.mock_rtp_service.start_listening.assert_called_once()
    
    def test_start_listening_both_services(self):
        """Test starting both USB and rtpMIDI listening"""
        # Mock both services to return True for start_listening
        self.mock_usb_service.start_listening.return_value = True
        self.mock_rtp_service.start_listening.return_value = True
        
        result = self.manager.start_listening()
        
        self.assertTrue(result)
        self.assertTrue(self.manager.is_listening)
        self.mock_usb_service.start_listening.assert_called_once()
        self.mock_rtp_service.start_listening.assert_called_once()
    
    def test_start_listening_failure(self):
        """Test handling start listening failure"""
        # Mock both services to return False for start_listening
        self.mock_usb_service.start_listening.return_value = False
        self.mock_rtp_service.start_listening.return_value = False
        
        result = self.manager.start_listening()
        
        self.assertFalse(result)
        self.assertFalse(self.manager.is_listening)
        self.mock_usb_service.start_listening.assert_called_once()
        self.mock_rtp_service.start_listening.assert_called_once()
    
    def test_stop_listening(self):
        """Test stopping MIDI listening"""
        # First start listening to set up the state
        self.mock_usb_service.start_listening.return_value = True
        self.mock_rtp_service.start_listening.return_value = True
        self.manager.start_listening()
        
        # Verify we're listening
        self.assertTrue(self.manager.is_listening)
        
        # Now test stopping
        result = self.manager.stop_listening()
        
        self.assertTrue(result)
        self.assertFalse(self.manager.is_listening)
        self.mock_usb_service.stop_listening.assert_called_once()
        self.mock_rtp_service.stop_listening.assert_called_once()
    
    def test_get_available_devices(self):
        """Test getting available devices"""
        # Mock USB devices with proper MIDIDevice objects
        from usb_midi_service import MIDIDevice
        usb_devices = [
            MIDIDevice(name='USB Device 1', id=0, type='usb', status='available'),
            MIDIDevice(name='USB Device 2', id=1, type='usb', status='available')
        ]
        self.mock_usb_service.get_available_devices.return_value = usb_devices
        
        # Mock rtpMIDI sessions
        rtpmidi_sessions = [
            {'id': 'session1', 'name': 'Network Session 1'},
            {'id': 'session2', 'name': 'Network Session 2'}
        ]
        self.mock_rtp_service.get_available_sessions.return_value = rtpmidi_sessions
        
        devices = self.manager.get_available_devices()
        
        self.assertIn('usb_devices', devices)
        self.assertIn('rtpmidi_sessions', devices)
        
        # Check that USB devices are properly formatted
        expected_usb = [
            {'name': 'USB Device 1', 'id': 0, 'type': 'usb', 'status': 'available'},
            {'name': 'USB Device 2', 'id': 1, 'type': 'usb', 'status': 'available'}
        ]
        self.assertEqual(devices['usb_devices'], expected_usb)
        self.assertEqual(devices['rtpmidi_sessions'], rtpmidi_sessions)
    
    def test_process_usb_midi_event(self):
        """Test processing USB MIDI event"""
        # Create a unified event directly
        unified_event = UnifiedMIDIEvent(
            timestamp=time.time(),
            note=60,
            velocity=100,
            channel=0,
            event_type='note_on',
            source=MIDIInputSource.USB,
            source_detail='usb'
        )
        
        # Process the unified event directly
        self.manager._process_unified_event(unified_event)
        
        # Verify callback was called
        self.mock_callback.assert_called()
    
    def test_process_network_midi_event(self):
        """Test processing network MIDI event"""
        # Create a unified event for network MIDI
        unified_event = UnifiedMIDIEvent(
            timestamp=time.time(),
            note=60,
            velocity=100,
            channel=0,
            event_type='note_on',
            source=MIDIInputSource.RTPMIDI,
            source_detail='test_session'
        )
        
        # Process the unified event directly
        self.manager._process_unified_event(unified_event)
        
        # Verify callback was called
        self.mock_callback.assert_called()
    
    def test_duplicate_filtering(self):
        """Test duplicate event filtering"""
        # Create identical events
        event1 = UnifiedMIDIEvent(
            timestamp=time.time(),
            note=60,
            velocity=100,
            channel=0,
            event_type='note_on',
            source=MIDIInputSource.USB,
            source_detail='usb_device'
        )
        
        event2 = UnifiedMIDIEvent(
            timestamp=time.time(),
            note=60,
            velocity=100,
            channel=0,
            event_type='note_on',
            source=MIDIInputSource.RTPMIDI,
            source_detail='network_session'
        )
        
        # Process first event
        is_duplicate1 = self.manager._is_duplicate_event(event1)
        self.assertFalse(is_duplicate1)
        
        # Process second event (should be duplicate)
        is_duplicate2 = self.manager._is_duplicate_event(event2)
        self.assertTrue(is_duplicate2)
    
    def test_active_notes_tracking(self):
        """Test active notes tracking"""
        # Note on event
        note_on_event = UnifiedMIDIEvent(
            timestamp=time.time(),
            note=60,
            velocity=100,
            channel=0,
            event_type='note_on',
            source=MIDIInputSource.USB,
            source_detail='usb_device'
        )
        
        self.manager._update_active_notes(note_on_event)
        self.assertIn(60, self.manager._active_notes)
        
        # Note off event
        note_off_event = UnifiedMIDIEvent(
            timestamp=time.time(),
            note=60,
            velocity=0,
            channel=0,
            event_type='note_off',
            source=MIDIInputSource.USB,
            source_detail='usb_device'
        )
        
        self.manager._update_active_notes(note_off_event)
        self.assertNotIn(60, self.manager._active_notes)
    
    def test_get_status(self):
        """Test status retrieval"""
        # Mock service statuses
        usb_status = {'listening': True, 'device': 'Test Device'}
        rtpmidi_status = {'state': 'discovering', 'sessions': []}
        
        self.mock_usb_service.get_status.return_value = usb_status
        self.mock_rtp_service.get_status.return_value = rtpmidi_status
        
        status = self.manager.get_status()
        
        self.assertIn('is_listening', status)
        self.assertIn('active_notes_count', status)
        self.assertIn('usb_service', status)
        self.assertIn('rtpmidi_service', status)
        self.assertEqual(status['usb_service'], usb_status)
        self.assertEqual(status['rtpmidi_service'], rtpmidi_status)
    
    def test_get_active_services(self):
        """Test active services retrieval"""
        # Mock service states
        self.mock_usb_service.is_listening = True
        self.mock_rtp_service.state.value = 'discovering'
        
        services = self.manager.get_active_services()
        
        self.assertIn('usb', services)
        self.assertIn('rtpmidi', services)
    
    def test_unified_midi_event_creation(self):
        """Test UnifiedMIDIEvent creation"""
        event = UnifiedMIDIEvent(
            timestamp=1234567890.0,
            note=60,
            velocity=100,
            channel=1,
            event_type='note_on',
            source=MIDIInputSource.USB,
            source_detail='Test Device'
        )
        
        self.assertEqual(event.timestamp, 1234567890.0)
        self.assertEqual(event.note, 60)
        self.assertEqual(event.velocity, 100)
        self.assertEqual(event.channel, 1)
        self.assertEqual(event.event_type, 'note_on')
        self.assertEqual(event.source, MIDIInputSource.USB)
        self.assertEqual(event.source_detail, 'Test Device')
        self.assertFalse(event.processed)
    
    def test_event_key_generation(self):
        """Test event key generation for duplicate detection"""
        event = UnifiedMIDIEvent(
            timestamp=time.time(),
            note=60,
            velocity=100,
            channel=0,
            event_type='note_on',
            source=MIDIInputSource.USB,
            source_detail='usb_device'
        )
        
        key = event.get_event_key()
        expected_key = ('note_on', 0, 60, 100)
        self.assertEqual(key, expected_key)

if __name__ == '__main__':
    unittest.main()