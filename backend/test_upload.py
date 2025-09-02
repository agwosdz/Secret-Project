#!/usr/bin/env python3
"""
Tests for MIDI file upload functionality
"""

import pytest
import os
import tempfile
import json
from unittest.mock import patch, mock_open
from io import BytesIO
from werkzeug.datastructures import FileStorage

# Mock hardware modules before importing app
from unittest.mock import MagicMock
import sys

# Create mock modules
mock_rpi_ws281x = MagicMock()
mock_rpi_gpio = MagicMock()

# Add to sys.modules
sys.modules['rpi_ws281x'] = mock_rpi_ws281x
sys.modules['RPi.GPIO'] = mock_rpi_gpio

from app import app

class TestMidiUpload:
    """Test cases for MIDI file upload endpoint"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def valid_midi_file(self):
        """Create a mock valid MIDI file"""
        # Simple MIDI file header (MThd chunk)
        midi_data = b'MThd\x00\x00\x00\x06\x00\x00\x00\x01\x00\x60'
        return FileStorage(
            stream=BytesIO(midi_data),
            filename='test.mid',
            content_type='audio/midi'
        )
    
    @pytest.fixture
    def large_midi_file(self):
        """Create a mock MIDI file that's too large"""
        # Create file larger than 1MB
        large_data = b'MThd' + b'\x00' * (1024 * 1024 + 1)
        return FileStorage(
            stream=BytesIO(large_data),
            filename='large.mid',
            content_type='audio/midi'
        )
    
    @pytest.fixture
    def invalid_file(self):
        """Create a mock invalid file (not MIDI)"""
        return FileStorage(
            stream=BytesIO(b'Not a MIDI file'),
            filename='test.txt',
            content_type='text/plain'
        )
    
    def test_upload_valid_midi_file(self, client, valid_midi_file):
        """Test uploading a valid MIDI file"""
        with patch('os.path.exists', return_value=True):
            response = client.post('/api/upload-midi', 
                                 data={'file': valid_midi_file},
                                 content_type='multipart/form-data')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'filename' in data
        assert 'original_filename' in data
        assert data['original_filename'] == 'test.mid'
        assert 'size' in data
        assert 'upload_path' in data
    
    def test_upload_no_file(self, client):
        """Test upload request without file"""
        response = client.post('/api/upload-midi', 
                             data={},
                             content_type='multipart/form-data')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Bad Request'
        assert 'No file provided' in data['message']
    
    def test_upload_empty_filename(self, client):
        """Test upload with empty filename"""
        empty_file = FileStorage(
            stream=BytesIO(b'test'),
            filename='',
            content_type='audio/midi'
        )
        
        response = client.post('/api/upload-midi', 
                             data={'file': empty_file},
                             content_type='multipart/form-data')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Bad Request'
        assert 'No file selected' in data['message']
    
    def test_upload_invalid_file_extension(self, client, invalid_file):
        """Test upload with invalid file extension"""
        response = client.post('/api/upload-midi', 
                             data={'file': invalid_file},
                             content_type='multipart/form-data')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Invalid File Type'
        assert 'Only MIDI files' in data['message']
    
    def test_upload_large_file(self, client, large_midi_file):
        """Test upload with file too large"""
        response = client.post('/api/upload-midi', 
                             data={'file': large_midi_file},
                             content_type='multipart/form-data')
        
        assert response.status_code == 413
        data = json.loads(response.data)
        assert data['error'] == 'File Too Large'
    
    def test_upload_midi_extension_case_insensitive(self, client):
        """Test that MIDI file extensions are case insensitive"""
        midi_file = FileStorage(
            stream=BytesIO(b'MThd\x00\x00\x00\x06\x00\x00\x00\x01\x00\x60'),
            filename='test.MIDI',
            content_type='audio/midi'
        )
        
        with patch('os.path.exists', return_value=True):
            response = client.post('/api/upload-midi', 
                                 data={'file': midi_file},
                                 content_type='multipart/form-data')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
    
    def test_upload_file_save_failure(self, client, valid_midi_file):
        """Test handling of file save failure"""
        with patch('os.path.exists', return_value=False):
            response = client.post('/api/upload-midi', 
                                 data={'file': valid_midi_file},
                                 content_type='multipart/form-data')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['error'] == 'Upload Failed'
        assert 'could not be saved' in data['message']
    
    def test_upload_generates_unique_filename(self, client):
        """Test that uploaded files get unique filenames"""
        midi_file1 = FileStorage(
            stream=BytesIO(b'MThd\x00\x00\x00\x06\x00\x00\x00\x01\x00\x60'),
            filename='test.mid',
            content_type='audio/midi'
        )
        midi_file2 = FileStorage(
            stream=BytesIO(b'MThd\x00\x00\x00\x06\x00\x00\x00\x01\x00\x60'),
            filename='test.mid',
            content_type='audio/midi'
        )
        
        with patch('os.path.exists', return_value=True):
            response1 = client.post('/api/upload-midi', 
                                  data={'file': midi_file1},
                                  content_type='multipart/form-data')
            response2 = client.post('/api/upload-midi', 
                                  data={'file': midi_file2},
                                  content_type='multipart/form-data')
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = json.loads(response1.data)
        data2 = json.loads(response2.data)
        
        # Filenames should be different (unique)
        assert data1['filename'] != data2['filename']
        # But original filenames should be the same
        assert data1['original_filename'] == data2['original_filename'] == 'test.mid'
    
    def test_upload_invalid_characters_in_filename(self, client):
        """Test handling of invalid characters in filename"""
        midi_file = FileStorage(
            stream=BytesIO(b'MThd\x00\x00\x00\x06\x00\x00\x00\x01\x00\x60'),
            filename='../../../etc/passwd.mid',
            content_type='audio/midi'
        )
        
        with patch('os.path.exists', return_value=True):
            response = client.post('/api/upload-midi', 
                                 data={'file': midi_file},
                                 content_type='multipart/form-data')
        
        # Should still work because secure_filename will clean it
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        # Filename should be sanitized
        assert '../' not in data['filename']

class TestUploadErrorHandlers:
    """Test error handlers for upload functionality"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_413_error_handler(self, client):
        """Test 413 error handler for file too large"""
        # Simulate RequestEntityTooLarge by setting a very small MAX_CONTENT_LENGTH
        original_max_size = app.config.get('MAX_CONTENT_LENGTH')
        app.config['MAX_CONTENT_LENGTH'] = 1  # 1 byte limit
        
        try:
            large_file = FileStorage(
                stream=BytesIO(b'This is definitely larger than 1 byte'),
                filename='test.mid',
                content_type='audio/midi'
            )
            
            response = client.post('/api/upload-midi', 
                                 data={'file': large_file},
                                 content_type='multipart/form-data')
            
            assert response.status_code == 413
            data = json.loads(response.data)
            assert data['error'] == 'File Too Large'
        finally:
            # Restore original config
            if original_max_size:
                app.config['MAX_CONTENT_LENGTH'] = original_max_size
            else:
                app.config.pop('MAX_CONTENT_LENGTH', None)