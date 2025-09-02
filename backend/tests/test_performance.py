import pytest
import time
import threading
import os
import tempfile
import json
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import the app and components
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app
from playback_service import PlaybackService
from midi_parser import MIDIParser
from led_controller import LEDController

class TestPerformance:
    """Performance and stress tests for the playback system"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.app = app.app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create a larger MIDI file for performance testing
        self.temp_midi = tempfile.NamedTemporaryFile(suffix='.mid', delete=False)
        # Create a more complex MIDI file with multiple notes
        midi_content = self._create_complex_midi()
        self.temp_midi.write(midi_content)
        self.temp_midi.close()
        
    def teardown_method(self):
        """Clean up test fixtures"""
        self.app_context.pop()
        if os.path.exists(self.temp_midi.name):
            os.unlink(self.temp_midi.name)
    
    def _create_complex_midi(self):
        """Create a more complex MIDI file for testing"""
        # MIDI Header
        header = bytes([
            0x4D, 0x54, 0x68, 0x64,  # "MThd"
            0x00, 0x00, 0x00, 0x06,  # Header length
            0x00, 0x00,              # Format 0
            0x00, 0x01,              # 1 track
            0x00, 0x60,              # 96 ticks per quarter note
        ])
        
        # Create track with multiple notes
        track_data = []
        # Add multiple note on/off events
        for note in range(60, 72):  # C4 to B4
            track_data.extend([
                0x00, 0x90, note, 0x40,  # Note on
                0x30, 0x80, note, 0x40,  # Note off after 48 ticks
            ])
        
        # End of track
        track_data.extend([0x00, 0xFF, 0x2F, 0x00])
        
        # Track header
        track_header = bytes([
            0x4D, 0x54, 0x72, 0x6B,  # "MTrk"
            0x00, 0x00, 0x00, len(track_data)  # Track length
        ])
        
        return header + track_header + bytes(track_data)
    
    def test_api_response_time(self):
        """Test API response times are within acceptable limits"""
        # Upload file first
        with open(self.temp_midi.name, 'rb') as f:
            self.client.post('/api/upload-midi',
                           data={'file': (f, 'test.mid')},
                           content_type='multipart/form-data')
        
        # Test play endpoint response time
        start_time = time.time()
        response = self.client.post('/api/play')
        play_time = time.time() - start_time
        
        assert response.status_code == 200
        assert play_time < 1.0, f"Play endpoint took {play_time:.3f}s, should be < 1.0s"
        
        # Test status endpoint response time
        start_time = time.time()
        response = self.client.get('/api/playback-status')
        status_time = time.time() - start_time
        
        assert response.status_code == 200
        assert status_time < 0.1, f"Status endpoint took {status_time:.3f}s, should be < 0.1s"
        
        # Test stop endpoint response time
        start_time = time.time()
        response = self.client.post('/api/stop')
        stop_time = time.time() - start_time
        
        assert response.status_code == 200
        assert stop_time < 0.5, f"Stop endpoint took {stop_time:.3f}s, should be < 0.5s"
    
    def test_concurrent_status_requests(self):
        """Test handling of multiple concurrent status requests"""
        num_requests = 20
        
        def make_status_request():
            response = self.client.get('/api/playback-status')
            return response.status_code, time.time()
        
        # Make concurrent requests
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_status_request) for _ in range(num_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # All requests should succeed
        for status_code, _ in results:
            assert status_code == 200
        
        # Should handle all requests reasonably quickly
        assert total_time < 5.0, f"Concurrent requests took {total_time:.3f}s, should be < 5.0s"
    
    def test_memory_usage_during_playback(self):
        """Test that memory usage doesn't grow excessively during playback"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Upload and start playback
        with open(self.temp_midi.name, 'rb') as f:
            self.client.post('/api/upload-midi',
                           data={'file': (f, 'test.mid')},
                           content_type='multipart/form-data')
        
        self.client.post('/api/play')
        
        # Let it run for a bit
        time.sleep(2)
        
        # Check memory usage
        current_memory = process.memory_info().rss
        memory_increase = current_memory - initial_memory
        
        # Stop playback
        self.client.post('/api/stop')
        
        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024, f"Memory increased by {memory_increase / 1024 / 1024:.1f}MB"
    
    def test_rapid_play_stop_cycles(self):
        """Test rapid play/stop cycles for stability"""
        # Upload file first
        with open(self.temp_midi.name, 'rb') as f:
            self.client.post('/api/upload-midi',
                           data={'file': (f, 'test.mid')},
                           content_type='multipart/form-data')
        
        # Perform rapid play/stop cycles
        for i in range(10):
            play_response = self.client.post('/api/play')
            assert play_response.status_code == 200
            
            # Brief pause
            time.sleep(0.1)
            
            stop_response = self.client.post('/api/stop')
            assert stop_response.status_code == 200
            
            # Brief pause
            time.sleep(0.1)
    
    def test_large_file_handling(self):
        """Test handling of larger MIDI files"""
        # Create a larger MIDI file
        large_midi = tempfile.NamedTemporaryFile(suffix='.mid', delete=False)
        
        try:
            # Create MIDI with many more notes
            header = bytes([
                0x4D, 0x54, 0x68, 0x64,  # "MThd"
                0x00, 0x00, 0x00, 0x06,  # Header length
                0x00, 0x00,              # Format 0
                0x00, 0x01,              # 1 track
                0x00, 0x60,              # 96 ticks per quarter note
            ])
            
            # Create track with many notes (simulate a longer song)
            track_data = []
            for measure in range(100):  # 100 measures
                for note in range(60, 72):  # C4 to B4
                    track_data.extend([
                        0x00, 0x90, note, 0x40,  # Note on
                        0x10, 0x80, note, 0x40,  # Note off
                    ])
            
            track_data.extend([0x00, 0xFF, 0x2F, 0x00])  # End of track
            
            track_header = bytes([
                0x4D, 0x54, 0x72, 0x6B,  # "MTrk"
                0x00, 0x00, 0x00, len(track_data)  # Track length
            ])
            
            large_midi.write(header + track_header + bytes(track_data))
            large_midi.close()
            
            # Test upload and parsing
            start_time = time.time()
            with open(large_midi.name, 'rb') as f:
                response = self.client.post('/api/upload-midi',
                                          data={'file': (f, 'large_test.mid')},
                                          content_type='multipart/form-data')
            upload_time = time.time() - start_time
            
            assert response.status_code == 200
            assert upload_time < 5.0, f"Large file upload took {upload_time:.3f}s, should be < 5.0s"
            
            # Test playback initialization
            start_time = time.time()
            response = self.client.post('/api/play')
            play_time = time.time() - start_time
            
            assert response.status_code == 200
            assert play_time < 2.0, f"Large file playback start took {play_time:.3f}s, should be < 2.0s"
            
            # Stop playback
            self.client.post('/api/stop')
            
        finally:
            if os.path.exists(large_midi.name):
                os.unlink(large_midi.name)
    
    def test_websocket_performance(self):
        """Test WebSocket performance under load"""
        from flask_socketio import SocketIOTestClient
        
        # Get the socketio instance from the app
        socketio = self.app.extensions.get('socketio')
        if not socketio:
            pytest.skip("SocketIO not available")
        
        # Create multiple WebSocket clients
        clients = []
        try:
            for i in range(5):
                client = socketio.test_client(self.app)
                clients.append(client)
            
            # Upload and start playback
            with open(self.temp_midi.name, 'rb') as f:
                self.client.post('/api/upload-midi',
                               data={'file': (f, 'test.mid')},
                               content_type='multipart/form-data')
            
            self.client.post('/api/play')
            
            # Let it run briefly to generate WebSocket messages
            time.sleep(1)
            
            # All clients should receive messages
            for i, client in enumerate(clients):
                received = client.get_received()
                assert len(received) > 0, f"Client {i} received no messages"
            
            self.client.post('/api/stop')
            
        finally:
            # Clean up clients
            for client in clients:
                client.disconnect()
    
    @patch('led_controller.LEDController')
    def test_led_update_performance(self, mock_led_controller):
        """Test LED update performance during playback"""
        mock_led_instance = MagicMock()
        mock_led_controller.return_value = mock_led_instance
        
        # Upload and start playback
        with open(self.temp_midi.name, 'rb') as f:
            self.client.post('/api/upload-midi',
                           data={'file': (f, 'test.mid')},
                           content_type='multipart/form-data')
        
        start_time = time.time()
        self.client.post('/api/play')
        
        # Let it run for a bit
        time.sleep(2)
        
        self.client.post('/api/stop')
        total_time = time.time() - start_time
        
        # Verify LED updates were called
        assert mock_led_instance.update_leds.called
        
        # Check that LED updates don't cause significant performance issues
        call_count = mock_led_instance.update_leds.call_count
        if call_count > 0:
            avg_time_per_call = total_time / call_count
            assert avg_time_per_call < 0.1, f"LED updates too slow: {avg_time_per_call:.3f}s per call"