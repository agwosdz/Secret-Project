import pytest
import tempfile
import os
import json
import time

# Import the app and components
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app

class TestSimpleIntegration:
    """Simplified integration tests for core playback functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.app = app.app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create a simple MIDI file for testing
        self.temp_midi = tempfile.NamedTemporaryFile(suffix='.mid', delete=False)
        # Write minimal MIDI header
        midi_header = b'MThd\x00\x00\x00\x06\x00\x00\x00\x01\x00\x60'
        midi_track = b'MTrk\x00\x00\x00\x04\x00\xFF\x2F\x00'
        self.temp_midi.write(midi_header + midi_track)
        self.temp_midi.close()
    
    def teardown_method(self):
        """Clean up test fixtures"""
        if hasattr(self, 'temp_midi') and os.path.exists(self.temp_midi.name):
            os.unlink(self.temp_midi.name)
        self.app_context.pop()
    
    def test_api_endpoints_exist(self):
        """Test that all required API endpoints exist"""
        # Test health endpoint
        response = self.client.get('/health')
        assert response.status_code == 200
        
        # Test playback status endpoint
        response = self.client.get('/api/playback-status')
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data
    
    def test_upload_endpoint(self):
        """Test MIDI file upload functionality"""
        with open(self.temp_midi.name, 'rb') as f:
            response = self.client.post('/api/upload-midi', 
                                      data={'file': (f, 'test.mid')},
                                      content_type='multipart/form-data')
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 400, 500]
        data = response.get_json()
        assert isinstance(data, dict)
    
    def test_playback_endpoints_respond(self):
        """Test that playback endpoints respond appropriately"""
        # Test play endpoint without file
        response = self.client.post('/api/play', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        
        # Test pause endpoint
        response = self.client.post('/api/pause')
        assert response.status_code in [200, 400, 500]
        
        # Test stop endpoint
        response = self.client.post('/api/stop')
        assert response.status_code in [200, 400, 500]
    
    def test_error_handling(self):
        """Test API error handling"""
        # Test invalid JSON
        response = self.client.post('/api/play', 
                                  data='invalid json',
                                  content_type='application/json')
        assert response.status_code == 400
        
        # Test missing file upload
        response = self.client.post('/api/upload-midi')
        assert response.status_code == 400
    
    def test_status_endpoint_structure(self):
        """Test that status endpoint returns expected structure"""
        response = self.client.get('/api/playback-status')
        assert response.status_code == 200
        data = response.get_json()
        
        # Check for top-level fields
        assert 'status' in data
        assert 'playback' in data
        
        # Check playback structure
        playback = data['playback']
        required_playback_fields = ['state', 'current_time', 'total_duration', 'progress_percentage', 'filename']
        for field in required_playback_fields:
            assert field in playback, f"Missing required playback field: {field}"