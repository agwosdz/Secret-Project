import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch
from app import app
from playback_service import PlaybackState


class TestPlaybackAPI:
    """Test cases for playback API endpoints"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Create upload directory for tests
        self.upload_dir = tempfile.mkdtemp()
        self.app.config['UPLOAD_FOLDER'] = self.upload_dir
    
    def teardown_method(self):
        """Clean up test fixtures"""
        # Clean up upload directory
        import shutil
        if os.path.exists(self.upload_dir):
            shutil.rmtree(self.upload_dir)
    
    @patch('app.playback_service')
    def test_start_playback_success(self, mock_service):
        """Test successful playback start"""
        # Create a test file
        test_file = os.path.join(self.upload_dir, 'test.mid')
        with open(test_file, 'wb') as f:
            f.write(b'fake midi data')
        
        # Mock service methods
        mock_service.load_midi_file.return_value = True
        mock_service.start_playback.return_value = True
        
        response = self.client.post('/api/play', 
                                  json={'filename': 'test.mid'},
                                  content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['filename'] == 'test.mid'
        
        # Verify service methods were called
        mock_service.load_midi_file.assert_called_once_with(test_file)
        mock_service.start_playback.assert_called_once()
    
    @patch('app.playback_service')
    def test_start_playback_no_service(self, mock_service):
        """Test playback start when service unavailable"""
        # Mock service as None
        with patch('app.playback_service', None):
            response = self.client.post('/api/play', 
                                      json={'filename': 'test.mid'},
                                      content_type='application/json')
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['error'] == 'Service Unavailable'
    
    @patch('app.playback_service')
    def test_start_playback_missing_filename(self, mock_service):
        """Test playback start without filename"""
        response = self.client.post('/api/play', 
                                  json={},
                                  content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Bad Request'
    
    @patch('app.playback_service')
    def test_start_playback_file_not_found(self, mock_service):
        """Test playback start with non-existent file"""
        response = self.client.post('/api/play', 
                                  json={'filename': 'nonexistent.mid'},
                                  content_type='application/json')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'File Not Found'
    
    @patch('app.playback_service')
    def test_pause_playback_success(self, mock_service):
        """Test successful playback pause"""
        # Mock service methods
        mock_service.pause_playback.return_value = True
        mock_status = Mock()
        mock_status.state.value = 'paused'
        mock_service.get_status.return_value = mock_status
        
        response = self.client.post('/api/pause')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['playback_state'] == 'paused'
        
        mock_service.pause_playback.assert_called_once()
    
    @patch('app.playback_service')
    def test_stop_playback_success(self, mock_service):
        """Test successful playback stop"""
        # Mock service methods
        mock_service.stop_playback.return_value = True
        
        response = self.client.post('/api/stop')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        
        mock_service.stop_playback.assert_called_once()
    
    @patch('app.playback_service')
    def test_get_playback_status_success(self, mock_service):
        """Test successful status retrieval"""
        # Mock service status
        mock_status = Mock()
        mock_status.state.value = 'playing'
        mock_status.current_time = 30.5
        mock_status.total_duration = 120.0
        mock_status.progress_percentage = 25.4
        mock_status.filename = 'test.mid'
        mock_status.error_message = None
        mock_service.get_status.return_value = mock_status
        
        response = self.client.get('/api/playback-status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['playback']['state'] == 'playing'
        assert data['playback']['current_time'] == 30.5
        assert data['playback']['total_duration'] == 120.0
        assert data['playback']['progress_percentage'] == 25.4
        assert data['playback']['filename'] == 'test.mid'
        assert data['playback']['error_message'] is None
    
    def test_health_check(self):
        """Test basic health check endpoint"""
        response = self.client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
    
    def test_invalid_json(self):
        """Test API with invalid JSON"""
        response = self.client.post('/api/play', 
                                  data='invalid json',
                                  content_type='application/json')
        
        assert response.status_code == 400
    
    @patch('app.midi_parser')
    def test_parse_midi_success(self, mock_parser):
        """Test successful MIDI file parsing"""
        # Create a test file
        test_file = os.path.join(self.upload_dir, 'test.mid')
        with open(test_file, 'wb') as f:
            f.write(b'fake midi data')
        
        # Mock parser methods
        mock_notes = [
            {'note': 60, 'led_position': 39, 'start_time': 0.0, 'end_time': 0.5, 'duration': 0.5, 'velocity': 64},
            {'note': 64, 'led_position': 43, 'start_time': 0.25, 'end_time': 0.75, 'duration': 0.5, 'velocity': 80}
        ]
        mock_parser.parse_file.return_value = mock_notes
        
        response = self.client.post('/api/parse-midi',
                                  json={'filename': 'test.mid'},
                                  content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['filename'] == 'test.mid'
        assert data['note_count'] == 2
        assert len(data['notes']) == 2
        
        # Verify parser method was called
        mock_parser.parse_file.assert_called_once_with(test_file)
    
    def test_parse_midi_no_service(self):
        """Test MIDI parsing when service unavailable"""
        # Mock midi_parser as None
        with patch('app.midi_parser', None):
            response = self.client.post('/api/parse-midi',
                                      json={'filename': 'test.mid'},
                                      content_type='application/json')
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['error'] == 'Service Unavailable'
    
    def test_parse_midi_missing_filename(self):
        """Test MIDI parsing without filename"""
        response = self.client.post('/api/parse-midi',
                                  json={},
                                  content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Bad Request'
    
    def test_parse_midi_file_not_found(self):
        """Test MIDI parsing with non-existent file"""
        response = self.client.post('/api/parse-midi',
                                  json={'filename': 'nonexistent.mid'},
                                  content_type='application/json')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'File Not Found'
    
    @patch('app.midi_parser')
    def test_parse_midi_parsing_error(self, mock_parser):
        """Test MIDI parsing with parsing error"""
        # Create a test file
        test_file = os.path.join(self.upload_dir, 'test.mid')
        with open(test_file, 'wb') as f:
            f.write(b'fake midi data')
        
        # Mock parser to raise exception
        mock_parser.parse_file.side_effect = Exception('Invalid MIDI format')
        
        response = self.client.post('/api/parse-midi',
                                  json={'filename': 'test.mid'},
                                  content_type='application/json')
        
        assert response.status_code == 422
        data = json.loads(response.data)
        assert data['error'] == 'Parse Error'