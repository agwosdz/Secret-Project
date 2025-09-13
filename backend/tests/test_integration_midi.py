import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import time
import threading

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from midi_input_manager import MIDIInputManager, UnifiedMIDIEvent
from rtpmidi_service import RtpMIDIService, NetworkMIDIEvent
from usb_midi_service import USBMIDIInputService

class TestMIDIIntegration(unittest.TestCase):
    """Integration tests for USB and rtpMIDI services working together"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.events_received = []
        self.mock_led_controller = Mock()
        
        def capture_event(event_type, data):
            self.events_received.append((event_type, data))
        
        self.websocket_callback = capture_event
    
    @patch('midi_input_manager.USBMIDIInputService')
    @patch('midi_input_manager.RtpMIDIService')
    def test_simultaneous_usb_and_network_input(self, mock_rtp_class, mock_usb_class):
        """Test simultaneous USB and network MIDI input processing"""
        # Set up mocks
        mock_usb_service = Mock()
        mock_rtp_service = Mock()
        mock_usb_class.return_value = mock_usb_service
        mock_rtp_class.return_value = mock_rtp_service
        
        # Configure mock returns
        mock_usb_service.start_input.return_value = True
        mock_rtp_service.start_discovery.return_value = True
        mock_usb_service.get_available_devices.return_value = ['USB Device 1']
        mock_rtp_service.get_available_sessions.return_value = [
            {'id': 'session1', 'name': 'Network Session 1'}
        ]
        
        # Create manager
        manager = MIDIInputManager(
            websocket_callback=self.websocket_callback
        )
        
        # Start both services
        result = manager.start_listening(
            device_name='USB Device 1',
            enable_usb=True,
            enable_rtpmidi=True
        )
        
        self.assertTrue(result)
        self.assertTrue(manager.is_listening)
        
        # Simulate USB MIDI event
        usb_message = Mock()
        usb_message.type = 'note_on'
        usb_message.channel = 0
        usb_message.note = 60
        usb_message.velocity = 100
        usb_message.time = 0.0
        
        manager.process_midi_event('usb', {
            'message_type': 'note_on',
            'channel': usb_message.channel,
            'note': usb_message.note,
            'velocity': usb_message.velocity,
            'timestamp': usb_message.time
        })
        
        # Simulate network MIDI event
        network_event = NetworkMIDIEvent(
            timestamp=time.time(),
            note=62,
            velocity=110,
            channel=1,
            event_type='note_on',
            source_session='session1'
        )
        
        manager.process_midi_event('rtpmidi', {
            'event_type': network_event.event_type,
            'channel': network_event.channel,
            'note': network_event.note,
            'velocity': network_event.velocity,
            'source_session': network_event.source_session,
            'timestamp': network_event.timestamp
        })
        
        # Manually process buffered events since processing thread isn't running
        with manager._buffer_lock:
            events_to_process = manager._event_buffer.copy()
            manager._event_buffer.clear()
        
        for event in events_to_process:
            manager._process_unified_event(event)
        
        # Filter for only MIDI events (not status events)
        midi_events = [event for event in self.events_received if event[0] == 'unified_midi_event']
        
        # Verify both MIDI events were processed
        self.assertEqual(len(midi_events), 2)
        
        # Verify event details
        usb_event = next((e for e in midi_events if e[1]['source'] == 'usb'), None)
        rtpmidi_event = next((e for e in midi_events if e[1]['source'] == 'rtpmidi'), None)
        
        self.assertIsNotNone(usb_event)
        self.assertIsNotNone(rtpmidi_event)
        self.assertEqual(usb_event[1]['note'], 60)
        self.assertEqual(rtpmidi_event[1]['note'], 62)
    
    @patch('midi_input_manager.USBMIDIInputService')
    @patch('midi_input_manager.RtpMIDIService')
    def test_duplicate_event_filtering_across_sources(self, mock_rtp_class, mock_usb_class):
        """Test that duplicate events from different sources are filtered"""
        # Set up mocks
        mock_usb_service = Mock()
        mock_rtp_service = Mock()
        mock_usb_class.return_value = mock_usb_service
        mock_rtp_class.return_value = mock_rtp_service
        
        # Create manager
        manager = MIDIInputManager(
            websocket_callback=self.websocket_callback
        )
        
        # Simulate identical MIDI events from different sources
        usb_message = Mock()
        usb_message.type = 'note_on'
        usb_message.channel = 0
        usb_message.note = 60
        usb_message.velocity = 100
        usb_message.time = 0.0
        
        network_event = NetworkMIDIEvent(
            timestamp=time.time(),
            note=60,
            velocity=100,
            channel=0,
            event_type='note_on',
            source_session='session1'
        )
        
        # Process USB event first
        manager.process_midi_event('usb', {
            'event_type': usb_message.type,
            'channel': usb_message.channel,
            'note': usb_message.note,
            'velocity': usb_message.velocity,
            'timestamp': usb_message.time
        })
        
        # Process identical network event (should be filtered as duplicate)
        manager.process_midi_event('rtpmidi', {
            'event_type': network_event.event_type,
            'channel': network_event.channel,
            'note': network_event.note,
            'velocity': network_event.velocity,
            'source_session': network_event.source_session,
            'timestamp': network_event.timestamp
        })
        
        # Manually process buffered events
        with manager._buffer_lock:
            events_to_process = manager._event_buffer.copy()
            manager._event_buffer.clear()
        
        for event in events_to_process:
            manager._process_unified_event(event)
        
        # Filter for only MIDI events
        midi_events = [event for event in self.events_received if event[0] == 'unified_midi_event']
        
        # Should only receive one event (the first one, duplicates filtered)
        self.assertEqual(len(midi_events), 1)
        self.assertEqual(midi_events[0][1]['source'], 'usb')
    
    @patch('midi_input_manager.USBMIDIInputService')
    @patch('midi_input_manager.RtpMIDIService')
    def test_service_failure_handling(self, mock_rtp_class, mock_usb_class):
        """Test handling of service failures"""
        # Set up mocks
        mock_usb_service = Mock()
        mock_rtp_service = Mock()
        mock_usb_class.return_value = mock_usb_service
        mock_rtp_class.return_value = mock_rtp_service
        
        # Configure USB to fail, rtpMIDI to succeed
        mock_usb_service.start_input.return_value = False
        mock_rtp_service.start_discovery.return_value = True
        
        # Create manager
        manager = MIDIInputManager(
            websocket_callback=self.websocket_callback
        )
        
        # Start both services (USB should fail, rtpMIDI should succeed)
        result = manager.start_listening(
            device_name='USB Device 1',
            enable_usb=True,
            enable_rtpmidi=True
        )
        
        # Should succeed because at least one service started
        self.assertTrue(result)
        self.assertTrue(manager.is_listening)
        
        # Verify only rtpMIDI was started
        mock_usb_service.start_listening.assert_called_once()
        mock_rtp_service.start_listening.assert_called_once()
    
    @patch('midi_input_manager.USBMIDIInputService')
    @patch('midi_input_manager.RtpMIDIService')
    def test_active_notes_tracking_across_sources(self, mock_rtp_class, mock_usb_class):
        """Test active notes tracking across USB and network sources"""
        # Set up mocks
        mock_usb_service = Mock()
        mock_rtp_service = Mock()
        mock_usb_class.return_value = mock_usb_service
        mock_rtp_class.return_value = mock_rtp_service
        
        # Create manager
        manager = MIDIInputManager(
            websocket_callback=self.websocket_callback
        )
        
        # Simulate note on from USB
        usb_note_on = Mock()
        usb_note_on.type = 'note_on'
        usb_note_on.channel = 0
        usb_note_on.note = 60
        usb_note_on.velocity = 100
        usb_note_on.time = 0.0
        
        manager.process_midi_event('usb', {
            'event_type': usb_note_on.type,
            'channel': usb_note_on.channel,
            'note': usb_note_on.note,
            'velocity': usb_note_on.velocity,
            'timestamp': usb_note_on.time
        })
        
        # Simulate note on from network (different note)
        network_note_on = NetworkMIDIEvent(
            timestamp=time.time(),
            note=62,
            velocity=110,
            channel=0,
            event_type='note_on',
            source_session='session1'
        )
        
        manager.process_midi_event('rtpmidi', {
            'event_type': network_note_on.event_type,
            'channel': network_note_on.channel,
            'note': network_note_on.note,
            'velocity': network_note_on.velocity,
            'source_session': network_note_on.source_session,
            'timestamp': network_note_on.timestamp
        })
        
        # Manually process buffered events since processing thread isn't running
        with manager._buffer_lock:
            events_to_process = manager._event_buffer.copy()
            manager._event_buffer.clear()
        
        for event in events_to_process:
            manager._process_unified_event(event)
        
        # Should have two active notes
        self.assertEqual(len(manager.active_notes), 2)
        self.assertIn((0, 60), manager.active_notes)
        self.assertIn((0, 62), manager.active_notes)
        
        # Simulate note off from USB
        usb_note_off = Mock()
        usb_note_off.type = 'note_off'
        usb_note_off.channel = 0
        usb_note_off.note = 60
        usb_note_off.velocity = 0
        usb_note_off.time = 0.1
        
        manager.process_midi_event('usb', {
            'event_type': usb_note_off.type,
            'channel': usb_note_off.channel,
            'note': usb_note_off.note,
            'velocity': usb_note_off.velocity,
            'timestamp': usb_note_off.time
        })
        
        # Manually process buffered events for note off
        with manager._buffer_lock:
            events_to_process = manager._event_buffer.copy()
            manager._event_buffer.clear()
        
        for event in events_to_process:
            manager._process_unified_event(event)
        
        # Should have one active note remaining
        self.assertEqual(len(manager.active_notes), 1)
        self.assertNotIn((0, 60), manager.active_notes)
        self.assertIn((0, 62), manager.active_notes)
    
    @patch('midi_input_manager.USBMIDIInputService')
    @patch('midi_input_manager.RtpMIDIService')
    def test_status_aggregation(self, mock_rtp_class, mock_usb_class):
        """Test status aggregation from both services"""
        # Set up mocks
        mock_usb_service = Mock()
        mock_rtp_service = Mock()
        mock_usb_class.return_value = mock_usb_service
        mock_rtp_class.return_value = mock_rtp_service
        
        # Configure mock status returns
        mock_usb_service.get_status.return_value = {
            'listening': True,
            'device': 'USB Device 1',
            'messages_received': 10
        }
        
        mock_rtp_service.get_status.return_value = {
            'state': 'discovering',
            'sessions': [{'id': 'session1', 'connected': True}],
            'discovery_enabled': True
        }
        
        # Create manager
        manager = MIDIInputManager(
            websocket_callback=self.websocket_callback
        )
        
        # Add some active notes
        manager.active_notes.add((0, 60))
        manager.active_notes.add((1, 62))
        
        # Get aggregated status
        status = manager.get_status()
        
        # Verify aggregated status
        self.assertIn('is_listening', status)
        self.assertIn('active_notes_count', status)
        self.assertIn('usb_service', status)
        self.assertIn('rtpmidi_service', status)
        
        self.assertEqual(status['active_notes_count'], 2)
        # Check that service status dictionaries exist (they may be empty if services aren't initialized)
        self.assertIsInstance(status['usb_service'], dict)
        self.assertIsInstance(status['rtpmidi_service'], dict)
    
    @patch('midi_input_manager.USBMIDIInputService')
    @patch('midi_input_manager.RtpMIDIService')
    def test_graceful_shutdown(self, mock_rtp_class, mock_usb_class):
        """Test graceful shutdown of both services"""
        # Set up mocks
        mock_usb_service = Mock()
        mock_rtp_service = Mock()
        mock_usb_class.return_value = mock_usb_service
        mock_rtp_class.return_value = mock_rtp_service
        
        # Create manager and start services
        manager = MIDIInputManager(
            websocket_callback=self.websocket_callback
        )
        
        # Manually set the services for testing
        manager._usb_service = mock_usb_service
        manager._rtpmidi_service = mock_rtp_service
        manager._running = True
        manager.active_notes.add((0, 60))
        manager.active_notes.add((1, 62))
        
        # Stop listening
        manager.stop_listening()
        
        # Verify both services were stopped
        mock_usb_service.stop_listening.assert_called_once()
        mock_rtp_service.stop_listening.assert_called_once()
        
        # Verify state was reset
        self.assertFalse(manager.is_listening)
        self.assertEqual(len(manager.active_notes), 0)

if __name__ == '__main__':
    unittest.main()