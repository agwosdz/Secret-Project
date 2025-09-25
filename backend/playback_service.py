#!/usr/bin/env python3
"""
Playback Service - Coordinates MIDI playback with LED visualization
Integrates MIDI parsing and LED control for real-time playback
"""

import logging
import threading
import time
import json
import os
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

try:
    from led_controller import LEDController
except ImportError:
    LEDController = None

try:
    from midi_parser import MIDIParser
except ImportError:
    MIDIParser = None

try:
    from .performance_monitor import PerformanceMonitor
except ImportError:
    PerformanceMonitor = None

try:
    from config import get_config, get_piano_specs
except ImportError:
    logging.warning("Config module not available, using defaults")
    def get_config(key, default):
        return default
    def get_piano_specs(piano_size):
        return {'keys': 88, 'midi_start': 21, 'midi_end': 108}

class PlaybackState(Enum):
    """Playback state enumeration"""
    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"

@dataclass
class NoteEvent:
    """Represents a single note event in the MIDI sequence"""
    time: float  # Time in seconds from start
    note: int    # MIDI note number (0-127)
    velocity: int  # Note velocity (0-127)
    duration: float  # Note duration in seconds
    channel: int = 0  # MIDI channel

@dataclass
class PlaybackStatus:
    """Current playback status information"""
    state: PlaybackState
    current_time: float
    total_duration: float
    filename: Optional[str]
    progress_percentage: float
    error_message: Optional[str] = None

class PlaybackService:
    """Service for coordinating MIDI playback with LED visualization"""
    
    def __init__(self, led_controller: Optional[LEDController] = None, num_leds: int = None, midi_parser: Optional[MIDIParser] = None):
        """
        Initialize playback service with configurable piano specifications.
        
        Args:
            led_controller: LED controller instance
            num_leds: Number of LEDs in the strip (optional, loaded from config if not provided)
            midi_parser: MIDI parser instance for file parsing
        """
        self.logger = logging.getLogger(__name__)
        self._led_controller = led_controller
        
        # Load configuration
        piano_size = get_config('piano_size', '88-key')
        piano_specs = get_piano_specs(piano_size)
        
        self.num_leds = num_leds or piano_specs['keys']
        self.min_midi_note = piano_specs['midi_start']
        self.max_midi_note = piano_specs['midi_end']
        self.led_orientation = get_config('led_orientation', 'normal')
        
        # Load multi-LED mapping configuration
        self.mapping_mode = get_config('mapping_mode', 'auto')
        self.leds_per_key = get_config('leds_per_key', 3)
        self.mapping_base_offset = get_config('mapping_base_offset', 0)
        self.key_mapping = get_config('key_mapping', {})
        
        # Precompute key-to-LED mapping for performance
        self._precomputed_mapping = self._generate_key_mapping()
        self._midi_parser = midi_parser or (MIDIParser() if MIDIParser else None)
        
        # Playback state
        self._state = PlaybackState.IDLE
        self._current_time = 0.0
        self._total_duration = 0.0
        self._filename = None
        self._note_events: List[NoteEvent] = []
        self._active_notes: Dict[int, float] = {}  # note -> end_time
        
        # Threading
        self._playback_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        
        # Callbacks for real-time updates
        self._status_callbacks: List[Callable[[PlaybackStatus], None]] = []
        
        # Timing precision
        self._start_time = 0.0
        self._pause_time = 0.0
        
        # New Story 1.8 features
        self._tempo_multiplier = 1.0  # 1.0 = normal speed, 0.5 = half speed, 2.0 = double speed
        self._volume_multiplier = 1.0  # 0.0 = mute, 1.0 = full volume
        self._loop_enabled = False
        self._loop_start = 0.0
        self._loop_end = 0.0
        
        # Performance monitoring
        self.performance_monitor = PerformanceMonitor() if PerformanceMonitor else None
        
        self.logger.info(f"PlaybackService initialized with {num_leds} LEDs")
    
    @property
    def state(self) -> PlaybackState:
        """Get current playback state"""
        return self._state
    
    @property
    def current_time(self) -> float:
        """Get current playback time"""
        return self._current_time
    
    @property
    def filename(self) -> Optional[str]:
        """Get current filename"""
        return self._filename
    
    @property
    def total_duration(self) -> float:
        """Get total duration"""
        return self._total_duration
    
    @property
    def notes(self) -> List[NoteEvent]:
        """Get loaded note events"""
        return self._note_events
    
    @property
    def led_controller(self):
        """Get LED controller instance"""
        return self._led_controller

    @led_controller.setter
    def led_controller(self, value):
        """Set LED controller"""
        self._led_controller = value
    
    @property
    def tempo_multiplier(self) -> float:
        """Get current tempo multiplier"""
        return self._tempo_multiplier
    
    @property
    def volume_multiplier(self) -> float:
        """Get current volume multiplier"""
        return self._volume_multiplier
    
    @property
    def loop_enabled(self) -> bool:
        """Get loop enabled status"""
        return self._loop_enabled
    
    @property
    def loop_start(self) -> float:
        """Get loop start time"""
        return self._loop_start
    
    @property
    def loop_end(self) -> float:
        """Get loop end time"""
        return self._loop_end
    
    def add_status_callback(self, callback: Callable[[PlaybackStatus], None]):
        """Add a callback for status changes"""
        self._status_callbacks.append(callback)
    
    def remove_status_callback(self, callback: Callable[[PlaybackStatus], None]):
        """Remove a status callback"""
        if callback in self._status_callbacks:
            self._status_callbacks.remove(callback)
    
    def _notify_status_change(self):
        """Notify all callbacks of status change"""
        status = self.get_status()
        for callback in self._status_callbacks:
            try:
                callback(status)
            except Exception as e:
                self.logger.error(f"Error in status callback: {e}")
    
    def seek_to_time(self, time_seconds: float) -> bool:
        """Seek to a specific time in the playback"""
        try:
            if not self._note_events:
                self.logger.error("No MIDI file loaded for seeking")
                return False
            
            # Clamp time to valid range
            time_seconds = max(0.0, min(time_seconds, self._total_duration))
            
            # Update current time
            self._current_time = time_seconds
            
            # If playing, adjust start time to maintain sync
            if self._state == PlaybackState.PLAYING:
                self._start_time = time.time() - self._current_time / self._tempo_multiplier
            
            # Clear active notes and update LEDs
            self._active_notes.clear()
            if self._led_controller:
                self._led_controller.turn_off_all()
            
            self.logger.info(f"Seeked to {time_seconds:.2f}s")
            self._notify_status_change()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to seek: {e}")
            return False
    
    def set_tempo(self, multiplier: float) -> bool:
        """Set tempo multiplier (1.0 = normal, 0.5 = half speed, 2.0 = double speed)"""
        try:
            # Clamp tempo to reasonable range
            multiplier = max(0.1, min(multiplier, 4.0))
            
            # If playing, adjust start time to maintain current position
            if self._state == PlaybackState.PLAYING:
                current_real_time = time.time()
                elapsed_playback_time = (current_real_time - self._start_time) * self._tempo_multiplier
                self._start_time = current_real_time - elapsed_playback_time / multiplier
            
            self._tempo_multiplier = multiplier
            self.logger.info(f"Tempo set to {multiplier:.2f}x")
            self._notify_status_change()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set tempo: {e}")
            return False
    
    def set_volume(self, multiplier: float) -> bool:
        """Set volume multiplier (0.0 = mute, 1.0 = full volume)"""
        try:
            # Clamp volume to valid range
            multiplier = max(0.0, min(multiplier, 1.0))
            self._volume_multiplier = multiplier
            self.logger.info(f"Volume set to {multiplier:.2f}")
            self._notify_status_change()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set volume: {e}")
            return False
    
    def set_loop(self, enabled: bool, start_time: float = 0.0, end_time: float = 0.0) -> bool:
        """Set loop parameters"""
        try:
            self._loop_enabled = enabled
            if enabled:
                # Validate and set loop points
                start_time = max(0.0, min(start_time, self._total_duration))
                end_time = max(start_time + 1.0, min(end_time, self._total_duration))
                self._loop_start = start_time
                self._loop_end = end_time
                self.logger.info(f"Loop enabled: {start_time:.2f}s - {end_time:.2f}s")
            else:
                self.logger.info("Loop disabled")
            
            self._notify_status_change()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set loop: {e}")
            return False
    
    def load_midi_file(self, filename: str) -> bool:
        """
        Load and parse MIDI file for playback.
        
        Args:
            filename: Path to MIDI file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(filename):
                self.logger.error(f"MIDI file not found: {filename}")
                self._state = PlaybackState.ERROR
                self._notify_status_change()
                return False
            
            # Use MIDI parser if available, otherwise fall back to demo notes
            self._filename = filename
            
            if self._midi_parser:
                # Parse actual MIDI file
                parsed_data = self._midi_parser.parse_file(filename)
                if parsed_data:
                    self._note_events = self._convert_parsed_notes(parsed_data)
                else:
                    self.logger.warning(f"Failed to parse MIDI file {filename}, using demo notes")
                    self._note_events = self._generate_demo_notes()
            else:
                self.logger.warning("No MIDI parser available, using demo notes")
                self._note_events = self._generate_demo_notes()
            
            self._total_duration = max(event.time + event.duration for event in self._note_events) if self._note_events else 0
            
            self._state = PlaybackState.IDLE
            self._current_time = 0.0
            
            self.logger.info(f"Loaded MIDI file: {filename} ({len(self._note_events)} notes, {self._total_duration:.1f}s)")
            self._notify_status_change()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load MIDI file {filename}: {e}")
            self._state = PlaybackState.ERROR
            self._notify_status_change()
            return False
    
    def _generate_demo_notes(self) -> List[NoteEvent]:
        """Generate demo note events for testing"""
        notes = []
        
        # Generate a simple scale pattern
        scale_notes = [60, 62, 64, 65, 67, 69, 71, 72]  # C major scale
        
        for i, note in enumerate(scale_notes):
            # Each note plays for 0.5 seconds, starting every 0.6 seconds
            notes.append(NoteEvent(
                time=i * 0.6,
                note=note,
                velocity=80,
                duration=0.5
            ))
        
        # Add some harmony
        for i in range(4):
            notes.append(NoteEvent(
                time=i * 1.2 + 0.3,
                note=scale_notes[i] + 12,  # Octave higher
                velocity=60,
                duration=0.8
            ))
        
        return sorted(notes, key=lambda x: x.time)
    
    def _convert_parsed_notes(self, parsed_data: Dict[str, Any]) -> List[NoteEvent]:
        """
        Convert parsed MIDI data to NoteEvent objects.
        
        Args:
            parsed_data: Dictionary containing parsed MIDI data
            
        Returns:
            List[NoteEvent]: Converted note events
        """
        notes = []
        
        try:
            # Extract events from parsed data
            # The MIDI parser returns structure: {'events': [{'time': int, 'note': int, 'velocity': int, 'type': str, 'led_index': int}]}
            if 'events' in parsed_data:
                # Group note_on and note_off events to calculate durations
                active_notes = {}  # note -> (start_time, velocity)
                
                for event_data in parsed_data['events']:
                    note_num = event_data.get('note', 60)
                    time_ms = event_data.get('time', 0)
                    time_sec = time_ms / 1000.0  # Convert milliseconds to seconds
                    velocity = event_data.get('velocity', 80)
                    event_type = event_data.get('type', 'on')
                    
                    if event_type == 'on' and velocity > 0:
                        # Note starts
                        active_notes[note_num] = (time_sec, velocity)
                    elif event_type == 'off' or (event_type == 'on' and velocity == 0):
                        # Note ends
                        if note_num in active_notes:
                            start_time, note_velocity = active_notes[note_num]
                            duration = max(0.1, time_sec - start_time)  # Minimum duration of 0.1s
                            
                            notes.append(NoteEvent(
                                time=start_time,
                                note=note_num,
                                velocity=note_velocity,
                                duration=duration,
                                channel=0
                            ))
                            
                            del active_notes[note_num]
                
                # Handle any remaining active notes (notes that never got a note_off)
                max_time = max([event['time'] / 1000.0 for event in parsed_data['events']], default=0)
                for note_num, (start_time, velocity) in active_notes.items():
                    duration = max(0.5, max_time - start_time)  # Default duration
                    notes.append(NoteEvent(
                        time=start_time,
                        note=note_num,
                        velocity=velocity,
                        duration=duration,
                        channel=0
                    ))
            
            self.logger.info(f"Converted {len(notes)} notes from parsed MIDI data")
            
        except Exception as e:
            self.logger.error(f"Error converting parsed MIDI data: {e}")
            # Fall back to demo notes on error
            notes = self._generate_demo_notes()
        
        return sorted(notes, key=lambda x: x.time)
    
    def start_playback(self) -> bool:
        """
        Start playback of loaded MIDI file.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            if self._state == PlaybackState.PLAYING:
                self.logger.warning("Playback already in progress")
                return True
            
            if not self._note_events:
                self.logger.error("No MIDI file loaded")
                return False
            
            # Reset events
            self._stop_event.clear()
            self._pause_event.clear()
            
            # Start performance monitoring
            if self.performance_monitor:
                self.performance_monitor.reset_metrics()
                self.performance_monitor.start_monitoring()
            
            # Start playback thread
            self._playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
            self._playback_thread.start()
            
            self._state = PlaybackState.PLAYING
            self._start_time = time.time() - self._current_time / self._tempo_multiplier  # Account for resume and tempo
            
            self.logger.info("Playback started")
            self._notify_status_change()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start playback: {e}")
            self._state = PlaybackState.ERROR
            self._notify_status_change()
            return False
    
    def pause_playback(self) -> bool:
        """
        Pause or resume playback.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self._state == PlaybackState.PLAYING:
                self._pause_event.set()
                self._state = PlaybackState.PAUSED
                self._pause_time = time.time()
                self.logger.info("Playback paused")
            elif self._state == PlaybackState.PAUSED:
                self._pause_event.clear()
                self._state = PlaybackState.PLAYING
                # Adjust start time to account for pause duration
                pause_duration = time.time() - self._pause_time
                self._start_time += pause_duration
                self.logger.info("Playback resumed")
            else:
                self.logger.warning(f"Cannot pause/resume from state: {self._state}")
                return False
            
            self._notify_status_change()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to pause/resume playback: {e}")
            return False
    
    def stop_playback(self) -> bool:
        """
        Stop playback and reset position.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._stop_event.set()
            self._pause_event.clear()
            
            # Wait for playback thread to finish
            if self._playback_thread and self._playback_thread.is_alive():
                self._playback_thread.join(timeout=1.0)
            
            # Stop performance monitoring
            if self.performance_monitor:
                self.performance_monitor.stop_monitoring()
            
            # Turn off all LEDs
            if self._led_controller:
                self._led_controller.turn_off_all()
            
            self._state = PlaybackState.STOPPED
            self._current_time = 0.0
            self._active_notes.clear()
            
            self.logger.info("Playback stopped")
            self._notify_status_change()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop playback: {e}")
            return False
    
    def _playback_loop(self):
        """Main playback loop running in separate thread"""
        try:
            self.logger.info("Playback loop started")
            last_status_update = 0
            last_led_update = 0
            
            while not self._stop_event.is_set():
                current_loop_time = time.time()
                
                # Handle pause
                if self._pause_event.is_set():
                    time.sleep(0.05)  # Reduced pause check interval
                    continue
                
                # Update current time with tempo adjustment
                self._current_time = (current_loop_time - self._start_time) * self._tempo_multiplier
                
                # Handle loop functionality
                if self._loop_enabled and self._current_time >= self._loop_end:
                    self.logger.info(f"Loop: jumping from {self._current_time:.2f}s to {self._loop_start:.2f}s")
                    self._current_time = self._loop_start
                    self._start_time = current_loop_time - self._current_time / self._tempo_multiplier
                    self._active_notes.clear()
                    if self._led_controller:
                        self._led_controller.turn_off_all()
                
                # Check if playback is complete (only if not looping)
                elif self._current_time >= self._total_duration:
                    self.logger.info("Playback completed")
                    break
                
                # Process note events
                note_processing_start = time.time()
                self._process_note_events()
                
                # Track note processing performance
                if self.performance_monitor:
                    note_processing_time = time.time() - note_processing_start
                    self.performance_monitor.record_note_processing_time(note_processing_time)
                
                # Update LED display (limit to 60 FPS max)
                if current_loop_time - last_led_update >= 0.0167:  # ~60 FPS
                    self._update_leds()
                    
                    # Track LED update
                    if self.performance_monitor:
                        self.performance_monitor.record_led_update()
                    
                    last_led_update = current_loop_time
                
                # Notify status update (limit to 4 Hz)
                if current_loop_time - last_status_update >= 0.25:  # Every 0.25 seconds
                    self._notify_status_change()
                    last_status_update = current_loop_time
                
                # Sleep for timing precision (reduced for better responsiveness)
                time.sleep(0.005)  # 5ms resolution
            
            # Playback finished
            if not self._stop_event.is_set():
                # Natural completion
                self._state = PlaybackState.STOPPED
                self._current_time = self._total_duration
                if self._led_controller:
                    self._led_controller.turn_off_all()
                self._notify_status_change()
            
        except Exception as e:
            self.logger.error(f"Error in playback loop: {e}")
            self._state = PlaybackState.ERROR
            self._notify_status_change()
    
    def _process_note_events(self):
        """Process note events at current time"""
        current_time = self._current_time
        
        # Find notes that should start now
        for event in self._note_events:
            if abs(event.time - current_time) < 0.02:  # 20ms tolerance
                if event.note not in self._active_notes:
                    self._active_notes[event.note] = current_time + event.duration
                    self.logger.debug(f"Note ON: {event.note} at {current_time:.2f}s")
        
        # Remove notes that should end
        notes_to_remove = []
        for note, end_time in self._active_notes.items():
            if current_time >= end_time:
                notes_to_remove.append(note)
                self.logger.debug(f"Note OFF: {note} at {current_time:.2f}s")
        
        for note in notes_to_remove:
            del self._active_notes[note]
    
    def _update_leds(self):
        """Update LED display based on active notes"""
        if not self._led_controller:
            return
        
        try:
            # Prepare LED data for batch update
            led_data = {}
            
            # Map active notes to LEDs using multi-LED mapping
            for note in self._active_notes.keys():
                led_indices = self._map_note_to_leds(note)
                color = self._get_note_color(note)
                # Apply volume multiplier to brightness
                adjusted_color = tuple(int(c * self._volume_multiplier) for c in color)
                
                # Set color for all LEDs mapped to this note
                for led_index in led_indices:
                    if 0 <= led_index < self.num_leds:
                        led_data[led_index] = adjusted_color
            
            # Turn off all LEDs first, then set active ones
            self._led_controller.turn_off_all()
            
            # Use batch update for better performance
            if led_data:
                self._led_controller.set_multiple_leds(led_data, auto_show=True)
        
        except Exception as e:
            self.logger.error(f"Error updating LEDs: {e}")
    
    def _map_note_to_led(self, note: int) -> int:
        """
        Map MIDI note to LED index with configuration and orientation support.
        
        Args:
            note: MIDI note number (0-127)
            
        Returns:
            int: LED index
        """
        # Use configured piano range
        if note < self.min_midi_note:
            note = self.min_midi_note
        elif note > self.max_midi_note:
            note = self.max_midi_note
        
        # Map to logical LED range
        piano_range = self.max_midi_note - self.min_midi_note
        logical_index = int((note - self.min_midi_note) * (self.num_leds - 1) / piano_range)
        
        # Apply orientation mapping
        if self.led_orientation == 'reversed':
            return self.num_leds - 1 - logical_index
        else:
            return logical_index
    
    def _map_note_to_leds(self, note: int) -> List[int]:
        """
        Map MIDI note to multiple LED indices based on configuration.
        
        Args:
            note: MIDI note number (0-127)
            
        Returns:
            List[int]: List of LED indices for this note
        """
        # Use precomputed mapping if available
        if note in self._precomputed_mapping:
            return self._precomputed_mapping[note]
        
        # Fallback to single LED mapping for backward compatibility
        single_led = self._map_note_to_led(note)
        return [single_led] if 0 <= single_led < self.num_leds else []
    
    def _generate_key_mapping(self) -> Dict[int, List[int]]:
        """
        Generate key-to-LED mapping based on configuration.
        
        Returns:
            Dict[int, List[int]]: Mapping of MIDI note to list of LED indices
        """
        try:
            from config import generate_auto_key_mapping
            
            if self.mapping_mode == 'manual' and self.key_mapping:
                # Use manual mapping from configuration
                mapping = {}
                for note_str, led_indices in self.key_mapping.items():
                    try:
                        note = int(note_str)
                        if isinstance(led_indices, int):
                            mapping[note] = [led_indices]
                        elif isinstance(led_indices, list):
                            mapping[note] = led_indices
                    except (ValueError, TypeError):
                        continue
                return mapping
            
            elif self.mapping_mode in ['auto', 'proportional']:
                # Use auto-generated mapping
                piano_size = get_config('piano_size', '88-key')
                auto_mapping = generate_auto_key_mapping(
                    piano_size=piano_size,
                    led_count=self.num_leds,
                    led_orientation=self.led_orientation,
                    leds_per_key=self.leds_per_key,
                    mapping_base_offset=self.mapping_base_offset
                )
                return auto_mapping
            
            else:
                # Fallback to single LED mapping
                mapping = {}
                for note in range(self.min_midi_note, self.max_midi_note + 1):
                    single_led = self._map_note_to_led(note)
                    if 0 <= single_led < self.num_leds:
                        mapping[note] = [single_led]
                return mapping
                
        except Exception as e:
            self.logger.error(f"Error generating key mapping: {e}")
            # Fallback to single LED mapping
            mapping = {}
            for note in range(self.min_midi_note, self.max_midi_note + 1):
                single_led = self._map_note_to_led(note)
                if 0 <= single_led < self.num_leds:
                    mapping[note] = [single_led]
            return mapping
    
    def _get_note_color(self, note: int) -> tuple:
        """
        Get color for a note based on its pitch.
        
        Args:
            note: MIDI note number
            
        Returns:
            tuple: RGB color tuple
        """
        # Color mapping based on note position in octave
        note_in_octave = note % 12
        colors = [
            (255, 0, 0),    # C - Red
            (255, 127, 0),  # C# - Orange
            (255, 255, 0),  # D - Yellow
            (127, 255, 0),  # D# - Yellow-Green
            (0, 255, 0),    # E - Green
            (0, 255, 127),  # F - Green-Cyan
            (0, 255, 255),  # F# - Cyan
            (0, 127, 255),  # G - Cyan-Blue
            (0, 0, 255),    # G# - Blue
            (127, 0, 255),  # A - Blue-Purple
            (255, 0, 255),  # A# - Purple
            (255, 0, 127),  # B - Purple-Red
        ]
        
        return colors[note_in_octave]
    
    def get_status(self) -> PlaybackStatus:
        """Get current playback status"""
        progress = 0.0
        if self._total_duration > 0:
            progress = min(100.0, (self._current_time / self._total_duration) * 100)
        
        return PlaybackStatus(
            state=self._state,
            current_time=self._current_time,
            total_duration=self._total_duration,
            filename=self._filename,
            progress_percentage=progress,
            error_message=None if self._state != PlaybackState.ERROR else "Playback error occurred"
        )
    
    def get_extended_status(self) -> Dict[str, Any]:
        """Get extended playback status including new controls"""
        basic_status = self.get_status()
        return {
            'state': basic_status.state.value,
            'current_time': basic_status.current_time,
            'total_duration': basic_status.total_duration,
            'filename': basic_status.filename,
            'progress_percentage': basic_status.progress_percentage,
            'error_message': basic_status.error_message,
            'tempo_multiplier': self._tempo_multiplier,
            'volume_multiplier': self._volume_multiplier,
            'loop_enabled': self._loop_enabled,
            'loop_start': self._loop_start,
            'loop_end': self._loop_end
        }
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.stop_playback()
            self._status_callbacks.clear()
            self.logger.info("PlaybackService cleaned up")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self.cleanup()