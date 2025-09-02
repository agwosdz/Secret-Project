import pytest
import json
from unittest.mock import Mock, patch
from flask_socketio import SocketIOTestClient
from flask import Flask

# Import the app and socketio instance
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, socketio, playback_service

class TestWebSocket:
    """Test WebSocket functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.app = app
        self.app.config['TESTING'] = True
        # Create test client with proper Flask-SocketIO configuration
        self.client = socketio.test_client(self.app)
    
    def teardown_method(self):
        """Clean up after tests"""
        if hasattr(self, 'client') and self.client.is_connected():
            self.client.disconnect()
    
    def test_websocket_connect(self):
        """Test WebSocket connection"""
        # Client is already connected, check for initial status message
        received = self.client.get_received()
        
        # Should receive initial playback status
        assert len(received) >= 1
        status_event = received[0]
        assert status_event['name'] == 'playback_status'
        assert 'args' in status_event
        
        status_data = status_event['args'][0]
        assert 'state' in status_data
        assert 'current_time' in status_data
        assert 'total_duration' in status_data
        assert 'progress_percentage' in status_data
    
    def test_get_status_event(self):
        """Test get_status WebSocket event"""
        # Clear any initial messages
        self.client.get_received()
        
        # Emit get_status event
        self.client.emit('get_status')
        
        # Should receive playback status
        received = self.client.get_received()
        assert len(received) >= 1
        
        status_event = received[0]
        assert status_event['name'] == 'playback_status'
        
        status_data = status_event['args'][0]
        assert 'state' in status_data
        assert 'current_time' in status_data
        assert 'total_duration' in status_data
        assert 'progress_percentage' in status_data
    
    def test_websocket_status_callback(self):
        """Test WebSocket status callback function"""
        from app import websocket_status_callback
        from playback_service import PlaybackStatus, PlaybackState
        
        # Create mock status
        mock_status = PlaybackStatus(
            state=PlaybackState.PLAYING,
            current_time=10.5,
            total_duration=60.0,
            filename='test.mid',
            progress_percentage=17.5,
            error_message=None
        )
        
        # Clear any initial messages
        self.client.get_received()
        
        # Call the callback function with the test client context
        with self.app.test_request_context():
            websocket_status_callback(mock_status)
        
        # Should receive the status update
        received = self.client.get_received()
        assert len(received) >= 1
        
        status_event = received[0]
        assert status_event['name'] == 'playback_status'
        
        status_data = status_event['args'][0]
        assert status_data['state'] == 'playing'
        assert status_data['current_time'] == 10.5
        assert status_data['total_duration'] == 60.0
        assert status_data['filename'] == 'test.mid'
        assert status_data['progress_percentage'] == 17.5
        assert status_data['error_message'] is None
    
    def test_websocket_disconnect(self):
        """Test WebSocket disconnection"""
        # Disconnect should not raise any errors
        if self.client.is_connected():
            self.client.disconnect()
        
        # Reconnect should work
        self.client = socketio.test_client(self.app)
        received = self.client.get_received()
        assert len(received) >= 1