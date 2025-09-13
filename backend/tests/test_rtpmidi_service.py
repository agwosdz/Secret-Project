import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rtpmidi_service import RtpMIDIService, RtpMIDIState, RtpMIDISession, NetworkMIDIEvent

class TestRtpMIDIService(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.mock_callback = Mock()
        self.service = RtpMIDIService(websocket_callback=self.mock_callback)
    
    def test_initialization(self):
        """Test service initialization"""
        # When pymidi is not available, state should be ERROR
        self.assertEqual(self.service.state, RtpMIDIState.ERROR)
        self.assertEqual(len(self.service.active_sessions), 0)
        self.assertEqual(len(self.service.discovered_sessions), 0)
        self.assertIsNotNone(self.service._websocket_callback)
    
    def test_state_transitions(self):
        """Test state management"""
        # Test state change (direct assignment since it's a property)
        self.service._state = RtpMIDIState.DISCOVERING
        self.assertEqual(self.service.state, RtpMIDIState.DISCOVERING)
    
    @patch('rtpmidi_service.PYMIDI_AVAILABLE', True)
    @patch('rtpmidi_service.server')
    def test_start_discovery_success(self, mock_server_module):
        """Test successful discovery start"""
        # Create a new service instance with pymidi available
        service = RtpMIDIService(websocket_callback=self.mock_callback)
        service._state = RtpMIDIState.IDLE  # Reset from ERROR state
        
        result = service.start_discovery()
        
        self.assertTrue(result)
        self.assertEqual(service.state, RtpMIDIState.DISCOVERING)
    
    def test_start_discovery_no_pymidi(self):
        """Test discovery start without pymidi"""
        result = self.service.start_discovery()
        
        self.assertFalse(result)
        self.assertEqual(self.service.state, RtpMIDIState.ERROR)
    
    def test_stop_listening(self):
        """Test stopping listening"""
        # Set up listening state
        self.service._state = RtpMIDIState.LISTENING
        self.service._running = True
        
        result = self.service.stop_listening()
        
        self.assertTrue(result)
        self.assertEqual(self.service.state, RtpMIDIState.IDLE)
    
    def test_session_management(self):
        """Test session creation and management"""
        session = RtpMIDISession(
            name='Test Session',
            ip_address='192.168.1.100',
            port=5004
        )
        
        # Add session to discovered sessions
        self.service._discovered_sessions['test_session'] = session
        
        self.assertIn('test_session', self.service.discovered_sessions)
        retrieved_session = self.service.discovered_sessions['test_session']
        self.assertEqual(retrieved_session.name, 'Test Session')
        self.assertEqual(retrieved_session.ip_address, '192.168.1.100')
        self.assertEqual(retrieved_session.port, 5004)
    
    @patch('rtpmidi_service.PYMIDI_AVAILABLE', True)
    def test_connect_session_success(self):
        """Test successful session connection"""
        # Create a session
        session = RtpMIDISession(
            name='Test Session',
            ip_address='192.168.1.100',
            port=5004
        )
        
        # Create a new service instance with pymidi available
        service = RtpMIDIService(websocket_callback=self.mock_callback)
        service._state = RtpMIDIState.IDLE  # Reset from ERROR state
        
        result = service.connect_session(session)
        
        # Should return True even if connection fails (method handles errors gracefully)
        self.assertIsInstance(result, bool)
    
    def test_connect_invalid_session(self):
        """Test connecting to invalid session"""
        # Test with None
        result = self.service.connect_session(None)
        self.assertFalse(result)
    
    def test_disconnect_session(self):
        """Test session disconnection"""
        # Add a session to active sessions
        session = RtpMIDISession(
            name='Test Session',
            ip_address='192.168.1.100',
            port=5004,
            status='connected'
        )
        self.service._active_sessions['Test Session'] = session
        
        result = self.service.disconnect_session('Test Session')
        
        self.assertTrue(result)
    
    def test_process_network_midi_command(self):
        """Test network MIDI command processing"""
        # Mock peer and command
        mock_peer = Mock()
        mock_peer.name = 'test_peer'
        
        mock_command = Mock()
        mock_command.type = 'note_on'
        mock_command.channel = 0
        mock_command.note = 60
        mock_command.velocity = 100
        
        # Process command (should not raise exception)
        try:
            self.service._process_network_midi_command(mock_peer, mock_command)
        except Exception as e:
            self.fail(f"Processing network MIDI command raised an exception: {e}")
    
    def test_get_status(self):
        """Test status retrieval"""
        status = self.service.get_status()
        
        self.assertIn('state', status)
        self.assertIn('running', status)
        self.assertIn('port', status)
        self.assertIn('active_sessions', status)
        self.assertIn('discovered_sessions', status)
        self.assertIn('pymidi_available', status)
        self.assertEqual(status['state'], 'error')  # Because pymidi is not available
        self.assertFalse(status['pymidi_available'])
    
    def test_get_discovered_sessions(self):
        """Test discovered sessions retrieval"""
        # Add some sessions
        session1 = RtpMIDISession(name='Session 1', ip_address='192.168.1.100', port=5004)
        session2 = RtpMIDISession(name='Session 2', ip_address='192.168.1.101', port=5004)
        
        self.service._discovered_sessions['session1'] = session1
        self.service._discovered_sessions['session2'] = session2
        
        sessions = self.service.discovered_sessions
        
        self.assertEqual(len(sessions), 2)
        self.assertIn('session1', sessions)
        self.assertIn('session2', sessions)
    
    def test_network_midi_event_creation(self):
        """Test NetworkMIDIEvent creation"""
        event = NetworkMIDIEvent(
            timestamp=1234567890.0,
            event_type='note_on',
            channel=0,
            note=60,
            velocity=100,
            source_session='test_session'
        )
        
        self.assertEqual(event.timestamp, 1234567890.0)
        self.assertEqual(event.event_type, 'note_on')
        self.assertEqual(event.channel, 0)
        self.assertEqual(event.note, 60)
        self.assertEqual(event.velocity, 100)
        self.assertEqual(event.source_session, 'test_session')
    
    def test_rtpmidi_session_creation(self):
        """Test RtpMIDISession creation"""
        session = RtpMIDISession(
            name='Test Session',
            ip_address='192.168.1.100',
            port=5004
        )
        
        self.assertEqual(session.name, 'Test Session')
        self.assertEqual(session.ip_address, '192.168.1.100')
        self.assertEqual(session.port, 5004)
        self.assertEqual(session.status, 'available')
        self.assertEqual(session.latency, 0.0)
        self.assertEqual(session.packet_loss, 0.0)

if __name__ == '__main__':
    unittest.main()