import pytest
import os
import tempfile
from unittest.mock import Mock, patch
from playback_service import PlaybackService, PlaybackState, NoteEvent


class TestPlaybackService:
    """Test cases for PlaybackService"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_led_controller = Mock()
        self.mock_midi_parser = Mock()
        self.service = PlaybackService(led_controller=self.mock_led_controller, midi_parser=self.mock_midi_parser)
    
    def test_initialization(self):
        """Test service initialization"""
        assert self.service.led_controller == self.mock_led_controller
        assert self.service.state == PlaybackState.IDLE
        assert self.service.current_time == 0.0
        assert self.service.total_duration == 0.0
        assert self.service.notes == []
        assert self.service.filename is None
    
    def test_load_midi_file_success(self):
        """Test successful MIDI file loading"""
        # Create a temporary file to simulate MIDI file
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as temp_file:
            temp_file.write(b'fake midi data')
            temp_path = temp_file.name
        
        # Mock the MIDI parser to return parsed data
        mock_parsed_data = {
            'notes': [
                {'time': 0.0, 'note': 60, 'velocity': 80, 'duration': 0.5, 'channel': 0},
                {'time': 0.5, 'note': 64, 'velocity': 80, 'duration': 0.5, 'channel': 0}
            ]
        }
        self.mock_midi_parser.parse_file.return_value = mock_parsed_data
        
        try:
            result = self.service.load_midi_file(temp_path)
            assert result is True
            assert self.service.filename == temp_path  # Full path is stored
            assert self.service.total_duration > 0  # Should have simulated duration
            assert len(self.service.notes) > 0  # Should have parsed notes
            self.mock_midi_parser.parse_file.assert_called_once_with(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_load_midi_file_not_found(self):
        """Test loading non-existent MIDI file"""
        result = self.service.load_midi_file('/nonexistent/file.mid')
        assert result is False
        assert self.service.filename is None
    
    def test_start_playback_without_file(self):
        """Test starting playback without loaded file"""
        result = self.service.start_playback()
        assert result is False
        assert self.service.state == PlaybackState.IDLE
    
    def test_start_playback_with_file(self):
        """Test starting playback with loaded file"""
        # Load a file first
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as temp_file:
            temp_file.write(b'fake midi data')
            temp_path = temp_file.name
        
        try:
            self.service.load_midi_file(temp_path)
            result = self.service.start_playback()
            assert result is True
            assert self.service.state == PlaybackState.PLAYING
        finally:
            os.unlink(temp_path)
    
    def test_pause_playback(self):
        """Test pause/resume functionality"""
        # Load and start playback first
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as temp_file:
            temp_file.write(b'fake midi data')
            temp_path = temp_file.name
        
        try:
            self.service.load_midi_file(temp_path)
            self.service.start_playback()
            
            # Test pause
            result = self.service.pause_playback()
            assert result is True
            assert self.service.state == PlaybackState.PAUSED
            
            # Test resume
            result = self.service.pause_playback()
            assert result is True
            assert self.service.state == PlaybackState.PLAYING
        finally:
            os.unlink(temp_path)
    
    def test_stop_playback(self):
        """Test stop functionality"""
        # Load and start playback first
        with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as temp_file:
            temp_file.write(b'fake midi data')
            temp_path = temp_file.name
        
        try:
            self.service.load_midi_file(temp_path)
            self.service.start_playback()
            
            # Test stop
            result = self.service.stop_playback()
            assert result is True
            assert self.service.state == PlaybackState.STOPPED
            assert self.service.current_time == 0.0
        finally:
            os.unlink(temp_path)
    
    def test_get_status(self):
        """Test status retrieval"""
        status = self.service.get_status()
        assert status.state == PlaybackState.IDLE
        assert status.current_time == 0.0
        assert status.total_duration == 0.0
        assert status.progress_percentage == 0.0
        assert status.filename is None
        assert status.error_message is None
    
    def test_note_to_led_mapping(self):
        """Test MIDI note to LED index mapping"""
        # Test various MIDI notes
        led_index_60 = self.service._map_note_to_led(60)  # Middle C
        led_index_72 = self.service._map_note_to_led(72)  # C5
        led_index_21 = self.service._map_note_to_led(21)  # A0 (lowest piano key)
        led_index_108 = self.service._map_note_to_led(108)  # C8 (highest piano key)
        
        # Verify mapping is within LED range
        assert 0 <= led_index_60 < 30
        assert 0 <= led_index_72 < 30
        assert led_index_21 == 0  # Lowest note maps to LED 0
        assert led_index_108 == 29  # Highest note maps to LED 29
    
    def test_note_to_color_mapping(self):
        """Test MIDI note to color mapping"""
        color = self.service._get_note_color(60)  # Middle C
        assert isinstance(color, tuple)
        assert len(color) == 3
        assert all(0 <= c <= 255 for c in color)
    
    def test_update_leds_with_active_notes(self):
        """Test LED updates with active notes"""
        # Add some active notes to the service
        self.service._active_notes = {60: 1.0, 64: 0.8}
        
        self.service._update_leds()
        
        # Verify LED controller was called
        assert self.mock_led_controller.turn_off_all.called
        assert self.mock_led_controller.turn_on_led.called