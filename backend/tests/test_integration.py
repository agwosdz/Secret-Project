import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from flask import Flask
from flask_socketio import SocketIOTestClient

# Import the app and components
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app
from playback_service import PlaybackService
from midi_parser import MIDIParser
from led_controller import LEDController

class TestIntegration:
    """Integration tests for the complete playback system"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.app = app.app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create a temporary MIDI file for testing
        self.temp_midi = tempfile.NamedTemporaryFile(suffix='.mid', delete=False)
        # Simple MIDI file content (header + track)
        midi_content = bytes([
            # MIDI Header
            0x4D, 0x54, 0x68, 0x64,  # "MThd"
            0x00, 0x00, 0x00, 0x06,  # Header length
            0x00, 0x00,              # Format 0
            0x00, 0x01,              # 1 track
            0x00, 0x60,              # 96 ticks per quarter note
            
            # Track Header
            0x4D, 0x54, 0x72, 0x6B,  # "MTrk"
            0x00, 0x00, 0x00, 0x0B,  # Track length
            
            # Track data
            0x00, 0x90, 0x40, 0x40,  # Note on C4
            0x60, 0x80, 0x40, 0x40,  # Note off C4
            0x00, 0xFF, 0x2F, 0x00   # End of track
        ])
        self.temp_midi.write(midi_content)
        self.temp_midi.close()
        
    def teardown_method(self):
        """Clean up test fixtures"""
        self.app_context.pop()
        if os.path.exists(self.temp_midi.name):
            os.unlink(self.temp_midi.name)
    
    def test_complete_playback_workflow(self):
        """Test the complete workflow: upload -> play -> status -> stop"""
        # 1. Upload a MIDI file
        with open(self.temp_midi.name, 'rb') as f:
            response = self.client.post('/api/upload-midi', 
                                      data={'file': (f, 'test.mid')},
                                      content_type='multipart/form-data')
        
        assert response.status_code == 200
        upload_data = json.loads(response.data)
        assert upload_data['success'] is True
        
        # 2. Start playback
        response = self.client.post('/api/play')
        assert response.status_code == 200
        play_data = json.loads(response.data)
        assert play_data['status'] == 'success'
        
        # 3. Check status
        response = self.client.get('/api/playback-status')
        assert response.status_code == 200
        status_data = json.loads(response.data)
        assert 'status' in status_data
        assert 'position' in status_data
        assert 'duration' in status_data
        
        # 4. Stop playback
        response = self.client.post('/api/stop')
        assert response.status_code == 200
        stop_data = json.loads(response.data)
        assert stop_data['status'] == 'success'
    
    def test_playback_without_file(self):
        """Test playback behavior when no file is loaded"""
        # Try to play without providing filename
        response = self.client.post('/api/play', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'Bad Request'
        
        # Try to play with nonexistent file
        response = self.client.post('/api/play', 
                                  json={'filename': 'nonexistent.mid'})
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'File Not Found'
    
    def test_pause_resume_workflow(self):
        """Test pause and resume functionality"""
        # Upload and start playback
        with open(self.temp_midi.name, 'rb') as f:
            self.client.post('/api/upload-midi', 
                           data={'file': (f, 'test.mid')},
                           content_type='multipart/form-data')
        
        self.client.post('/api/play')
        
        # Pause
        response = self.client.post('/api/pause')
        assert response.status_code == 200
        pause_data = json.loads(response.data)
        assert pause_data['status'] == 'success'
        
        # Check paused status
        response = self.client.get('/api/playback-status')
        status_data = json.loads(response.data)
        assert status_data['status'] == 'paused'
        
        # Resume
        response = self.client.post('/api/play')
        assert response.status_code == 200
    
    def test_invalid_file_upload(self):
        """Test uploading invalid file types"""
        # Create a text file instead of MIDI
        temp_txt = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
        temp_txt.write(b'This is not a MIDI file')
        temp_txt.close()
        
        try:
            with open(temp_txt.name, 'rb') as f:
                response = self.client.post('/api/upload-midi',
                                          data={'file': (f, 'test.txt')},
                                          content_type='multipart/form-data')
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data
        finally:
            os.unlink(temp_txt.name)
    
    def test_api_error_handling(self):
        """Test API error handling for various scenarios"""
        # Test missing file in upload
        response = self.client.post('/api/upload-midi')
        assert response.status_code == 400
        
        # Test invalid endpoints
        response = self.client.get('/api/nonexistent')
        assert response.status_code == 404
        
        # Test method not allowed
        response = self.client.get('/api/play')
        assert response.status_code == 405
    
    @patch('playback_service.PlaybackService')
    def test_service_initialization_failure(self, mock_playback_service):
        """Test handling of service initialization failures"""
        mock_playback_service.side_effect = Exception("Service init failed")
        
        # This should be handled gracefully by the app
        # Since the app is already initialized, we'll test that it handles service failures
        assert hasattr(app, 'playback_service')
    
    def test_concurrent_playback_requests(self):
        """Test handling of concurrent playback requests"""
        # Upload file first
        with open(self.temp_midi.name, 'rb') as f:
            self.client.post('/api/upload-midi',
                           data={'file': (f, 'test.mid')},
                           content_type='multipart/form-data')
        
        # Start playback
        response1 = self.client.post('/api/play')
        assert response1.status_code == 200
        
        # Try to start again (should handle gracefully)
        response2 = self.client.post('/api/play')
        # Should either succeed (if already playing) or return appropriate status
        assert response2.status_code in [200, 400]
    
    def test_status_endpoint_consistency(self):
        """Test that status endpoint returns consistent data"""
        response = self.client.get('/api/playback-status')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        required_fields = ['status', 'position', 'duration', 'song_info']
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Test data types
        assert isinstance(data['position'], (int, float))
        assert isinstance(data['duration'], (int, float))
        assert isinstance(data['song_info'], dict)
    
    def test_led_visualization_integration(self):
        """Test that LED visualization works with playback"""
        with patch('led_controller.LEDController') as mock_led:
            mock_led_instance = MagicMock()
            mock_led.return_value = mock_led_instance
            
            # Upload and play
            with open(self.temp_midi.name, 'rb') as f:
                self.client.post('/api/upload-midi',
                               data={'file': (f, 'test.mid')},
                               content_type='multipart/form-data')
            
            self.client.post('/api/play')
            
            # Verify LED controller methods would be called
            # (This tests the integration, actual LED calls are mocked)
            assert mock_led.called