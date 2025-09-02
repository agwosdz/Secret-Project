import mido
import os
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MIDIParser:
    """Service for parsing MIDI files into timed note sequences for LED visualization."""
    
    def __init__(self, led_count: int = 88):
        """
        Initialize MIDI parser.
        
        Args:
            led_count: Number of LEDs in the strip (default 88 for piano keys)
        """
        self.led_count = led_count
        # Map MIDI note range (21-108, A0-C8) to LED positions
        self.min_midi_note = 21  # A0
        self.max_midi_note = 108  # C8
        
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a MIDI file into a timed sequence of note events.
        
        Args:
            file_path: Path to the MIDI file
            
        Returns:
            Dictionary containing parsed note sequence and metadata
            
        Raises:
            FileNotFoundError: If MIDI file doesn't exist
            ValueError: If file is not a valid MIDI file
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"MIDI file not found: {file_path}")
            
        try:
            # Load MIDI file
            midi_file = mido.MidiFile(file_path)
            logger.info(f"Loaded MIDI file: {file_path} with {len(midi_file.tracks)} tracks")
            
            # Extract all note events from all tracks
            all_events = self._extract_note_events(midi_file)
            
            # Convert to timed sequence
            note_sequence = self._create_note_sequence(all_events, midi_file)
            
            # Calculate total duration
            duration = max([event['time'] for event in note_sequence], default=0)
            
            # Extract metadata
            metadata = self._extract_metadata(midi_file)
            
            return {
                'duration': duration,
                'events': note_sequence,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error parsing MIDI file {file_path}: {str(e)}")
            raise ValueError(f"Invalid MIDI file: {str(e)}")
    
    def _extract_note_events(self, midi_file: mido.MidiFile) -> List[Dict[str, Any]]:
        """
        Extract note on/off events from all tracks in the MIDI file.
        
        Args:
            midi_file: Loaded MIDI file object
            
        Returns:
            List of note events with timing information
        """
        events = []
        
        for track_idx, track in enumerate(midi_file.tracks):
            current_time = 0
            
            for msg in track:
                current_time += msg.time
                
                # Process note on events
                if msg.type == 'note_on' and msg.velocity > 0:
                    events.append({
                        'time_ticks': current_time,
                        'note': msg.note,
                        'velocity': msg.velocity,
                        'type': 'on',
                        'track': track_idx
                    })
                
                # Process note off events (including note_on with velocity 0)
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    events.append({
                        'time_ticks': current_time,
                        'note': msg.note,
                        'velocity': 0,
                        'type': 'off',
                        'track': track_idx
                    })
        
        logger.info(f"Extracted {len(events)} note events from {len(midi_file.tracks)} tracks")
        return events
    
    def _create_note_sequence(self, events: List[Dict[str, Any]], midi_file: mido.MidiFile) -> List[Dict[str, Any]]:
        """
        Convert MIDI events to a time-ordered sequence with absolute timing.
        
        Args:
            events: List of note events with tick timing
            midi_file: MIDI file object for timing calculations
            
        Returns:
            Time-ordered list of note events with millisecond timing
        """
        # Calculate ticks per second for timing conversion
        ticks_per_beat = midi_file.ticks_per_beat
        tempo = 500000  # Default tempo (120 BPM) in microseconds per beat
        
        # Convert events to absolute time and map to LEDs
        timed_events = []
        
        for event in events:
            # Convert ticks to milliseconds
            time_ms = self._ticks_to_milliseconds(event['time_ticks'], ticks_per_beat, tempo)
            
            # Map MIDI note to LED position
            led_index = self._map_note_to_led(event['note'])
            
            # Only include notes that map to valid LED positions
            if led_index is not None:
                timed_events.append({
                    'time': time_ms,
                    'note': event['note'],
                    'velocity': event['velocity'],
                    'type': event['type'],
                    'led_index': led_index
                })
        
        # Sort events by time
        timed_events.sort(key=lambda x: x['time'])
        
        logger.info(f"Created sequence with {len(timed_events)} timed events")
        return timed_events
    
    def _ticks_to_milliseconds(self, ticks: int, ticks_per_beat: int, tempo: int) -> int:
        """
        Convert MIDI ticks to milliseconds.
        
        Args:
            ticks: MIDI ticks
            ticks_per_beat: Ticks per quarter note
            tempo: Microseconds per beat
            
        Returns:
            Time in milliseconds
        """
        # Calculate seconds per tick
        seconds_per_tick = (tempo / 1_000_000) / ticks_per_beat
        
        # Convert to milliseconds
        return int(ticks * seconds_per_tick * 1000)
    
    def _map_note_to_led(self, midi_note: int) -> Optional[int]:
        """
        Map MIDI note number to LED strip position.
        
        Args:
            midi_note: MIDI note number (0-127)
            
        Returns:
            LED index (0-based) or None if note is outside range
        """
        # Only map notes within piano range
        if midi_note < self.min_midi_note or midi_note > self.max_midi_note:
            return None
            
        # Map to LED position (0-based)
        led_index = midi_note - self.min_midi_note
        
        # Ensure within LED strip bounds
        if led_index >= self.led_count:
            return None
            
        return led_index
    
    def _extract_metadata(self, midi_file: mido.MidiFile) -> Dict[str, Any]:
        """
        Extract metadata from MIDI file.
        
        Args:
            midi_file: Loaded MIDI file object
            
        Returns:
            Dictionary containing metadata
        """
        metadata = {
            'tracks': len(midi_file.tracks),
            'ticks_per_beat': midi_file.ticks_per_beat,
            'type': midi_file.type,
            'title': None,
            'tempo': 120  # Default BPM
        }
        
        # Extract title and tempo from meta messages
        for track in midi_file.tracks:
            for msg in track:
                if msg.type == 'track_name' and not metadata['title']:
                    metadata['title'] = msg.name
                elif msg.type == 'set_tempo':
                    # Convert microseconds per beat to BPM
                    metadata['tempo'] = int(60_000_000 / msg.tempo)
                    break
        
        return metadata
    
    def validate_file(self, file_path: str) -> bool:
        """
        Validate if a file is a proper MIDI file.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if valid MIDI file, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                return False
                
            # Try to load the file
            midi_file = mido.MidiFile(file_path)
            
            # Check if it has at least one track
            if len(midi_file.tracks) == 0:
                return False
                
            return True
            
        except Exception as e:
            logger.warning(f"MIDI validation failed for {file_path}: {str(e)}")
            return False