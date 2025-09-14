#!/usr/bin/env python3
"""
USB MIDI Input Service - Real-time MIDI input processing
Handles USB MIDI device detection, input processing, and LED visualization
"""

import logging
import threading
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

try:
    import mido
    MIDO_AVAILABLE = True
except ImportError:
    MIDO_AVAILABLE = False
    mido = None

try:
    from led_controller import LEDController
except ImportError:
    LEDController = None

# Configuration imports with fallbacks
try:
    from config import get_config, get_piano_specs
except ImportError:
    def get_config(key, default=None):
        return default
    def get_piano_specs(piano_size):
        return {'min_midi_note': 21, 'max_midi_note': 108, 'num_keys': 88}

class MIDIInputState(Enum):
    """MIDI input service state enumeration"""
    IDLE = "idle"
    LISTENING = "listening"
    ERROR = "error"

@dataclass
class MIDIDevice:
    """Represents a MIDI input device"""
    name: str
    id: int
    type: str = "usb"
    status: str = "available"

@dataclass
class MIDIInputEvent:
    """Represents a real-time MIDI input event"""
    timestamp: float
    note: int
    velocity: int
    channel: int
    event_type: str  # 'note_on' or 'note_off'

class USBMIDIInputService:
    """Service for real-time USB MIDI input processing and LED visualization"""
    
    def __init__(self, led_controller: Optional[LEDController] = None, 
                 websocket_callback: Optional[Callable] = None):
        """
        Initialize USB MIDI input service.
        
        Args:
            led_controller: LED controller instance for real-time visualization
            websocket_callback: Callback function for WebSocket event broadcasting
        """
        self.logger = logging.getLogger(__name__)
        self._led_controller = led_controller
        self._websocket_callback = websocket_callback
        
        # Load configuration
        piano_size = get_config('piano_size', '88-key')
        piano_specs = get_piano_specs(piano_size)
        self.num_leds = piano_specs['num_keys']
        self.min_midi_note = piano_specs['min_midi_note']
        self.max_midi_note = piano_specs['max_midi_note']
        self.led_orientation = get_config('led_orientation', 'normal')
        
        # Service state
        self._state = MIDIInputState.IDLE
        self._current_device: Optional[str] = None
        self._input_port: Optional[mido.ports.BaseInput] = None
        
        # Active notes tracking for sustain and LED management
        self._active_notes: Dict[int, Dict[str, Any]] = {}  # note -> {velocity, timestamp, led_index}
        
        # Threading for real-time input processing
        self._input_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
        
        # Performance tracking
        self._event_count = 0
        self._last_event_time = 0.0
        
        # Check MIDI availability
        if not MIDO_AVAILABLE:
            self.logger.warning("mido library not available - MIDI input disabled")
            self._state = MIDIInputState.ERROR
    
    @property
    def state(self) -> MIDIInputState:
        """Get current service state"""
        return self._state
    
    @property
    def current_device(self) -> Optional[str]:
        """Get currently selected MIDI device"""
        return self._current_device
    
    @property
    def active_notes(self) -> Dict[int, Dict[str, Any]]:
        """Get currently active notes"""
        return self._active_notes.copy()
    
    @property
    def is_listening(self) -> bool:
        """Check if service is actively listening for MIDI input"""
        return self._state == MIDIInputState.LISTENING and self._running
    
    def get_available_devices(self) -> List[MIDIDevice]:
        """
        Get list of available MIDI input devices.
        
        Returns:
            List of MIDIDevice objects representing available devices
        """
        if not MIDO_AVAILABLE:
            self.logger.warning("mido not available - no MIDI devices")
            return []
        
        try:
            device_names = mido.get_input_names()
            devices = []
            
            for idx, name in enumerate(device_names):
                devices.append(MIDIDevice(
                    name=name,
                    id=idx,
                    type="usb",
                    status="available"
                ))
            
            self.logger.info(f"Found {len(devices)} MIDI input devices")
            return devices
            
        except Exception as e:
            self.logger.error(f"Error getting MIDI devices: {e}")
            return []
    
    def start_listening(self, device_name: Optional[str] = None) -> bool:
        """
        Start listening for MIDI input from specified device.
        
        Args:
            device_name: Name of MIDI device to use (auto-select if None)
            
        Returns:
            True if listening started successfully, False otherwise
        """
        if not MIDO_AVAILABLE:
            self.logger.error("Cannot start listening - mido not available")
            return False
        
        if self._running:
            self.logger.warning("Already listening for MIDI input")
            return True
        
        try:
            # Auto-select device if none specified
            if device_name is None:
                available_devices = self.get_available_devices()
                if not available_devices:
                    self.logger.error("No MIDI devices available")
                    self._state = MIDIInputState.ERROR
                    return False
                device_name = available_devices[0].name
                self.logger.info(f"Auto-selected MIDI device: {device_name}")
            
            # Open MIDI input port
            self._input_port = mido.open_input(device_name)
            self._current_device = device_name
            
            # Start input processing thread
            self._stop_event.clear()
            self._running = True
            self._input_thread = threading.Thread(
                target=self._input_processing_loop,
                name="USBMIDIInput",
                daemon=True
            )
            self._input_thread.start()
            
            self._state = MIDIInputState.LISTENING
            self.logger.info(f"Started MIDI input listening on device: {device_name}")
            
            # Notify via WebSocket
            self._broadcast_status_update()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start MIDI listening: {e}")
            self._state = MIDIInputState.ERROR
            self._cleanup_input_port()
            return False
    
    def stop_listening(self) -> bool:
        """
        Stop listening for MIDI input.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self._running:
            self.logger.info("MIDI input not currently running")
            return True
        
        try:
            # Signal stop and wait for thread
            self._running = False
            self._stop_event.set()
            
            if self._input_thread and self._input_thread.is_alive():
                self._input_thread.join(timeout=2.0)
                if self._input_thread.is_alive():
                    self.logger.warning("MIDI input thread did not stop gracefully")
            
            # Clean up resources
            self._cleanup_input_port()
            self._clear_all_leds()
            
            self._state = MIDIInputState.IDLE
            self._current_device = None
            
            self.logger.info("Stopped MIDI input listening")
            
            # Notify via WebSocket
            self._broadcast_status_update()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping MIDI input: {e}")
            return False
    
    def _input_processing_loop(self):
        """
        Main loop for processing MIDI input messages.
        Runs in separate thread for real-time processing.
        """
        self.logger.info("MIDI input processing loop started")
        
        try:
            while self._running and not self._stop_event.is_set():
                try:
                    # Check for MIDI messages with timeout
                    if self._input_port:
                        # Use polling to allow for clean shutdown
                        msg = self._input_port.poll()
                        if msg:
                            self._process_midi_message(msg)
                        else:
                            # Small sleep to prevent busy waiting
                            time.sleep(0.001)  # 1ms
                    else:
                        break
                        
                except Exception as e:
                    self.logger.error(f"Error in MIDI input loop: {e}")
                    # Continue processing unless it's a critical error
                    if "device" in str(e).lower() or "port" in str(e).lower():
                        break
                    time.sleep(0.01)  # Brief pause before retry
                    
        except Exception as e:
            self.logger.error(f"Critical error in MIDI input processing: {e}")
            self._state = MIDIInputState.ERROR
        
        finally:
            self.logger.info("MIDI input processing loop ended")
    
    def _process_midi_message(self, msg):
        """
        Process a single MIDI message and update LEDs accordingly.
        
        Args:
            msg: MIDI message from mido
        """
        try:
            # DEBUG: Log all incoming MIDI messages
            self.logger.info(f"MIDI DEBUG: Received message: {msg} (type={msg.type}, channel={getattr(msg, 'channel', 'N/A')})")
            
            current_time = time.time()
            self._event_count += 1
            self._last_event_time = current_time
            
            # Process note on events
            if msg.type == 'note_on' and msg.velocity > 0:
                self.logger.info(f"MIDI DEBUG: Note ON - {msg.note}, velocity={msg.velocity}, active notes: {sorted(self._active_notes.keys())}")
                self._handle_note_on(msg.note, msg.velocity, msg.channel, current_time)
            
            # Process note off events (including note_on with velocity 0)
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                self.logger.info(f"MIDI DEBUG: Note OFF - {msg.note}, active notes: {sorted(self._active_notes.keys())}")
                self._handle_note_off(msg.note, msg.channel, current_time)
            
            # Log other MIDI events for debugging
            elif msg.type in ['control_change', 'program_change', 'pitchwheel']:
                self.logger.info(f"MIDI DEBUG: {msg.type}: {msg}")
            else:
                self.logger.info(f"MIDI DEBUG: Other message type: {msg}")
                
        except Exception as e:
            self.logger.error(f"Error processing MIDI message {msg}: {e}")
    
    def _handle_note_on(self, note: int, velocity: int, channel: int, timestamp: float):
        """
        Handle MIDI note on event.
        
        Args:
            note: MIDI note number (0-127)
            velocity: Note velocity (1-127)
            channel: MIDI channel (0-15)
            timestamp: Event timestamp
        """
        try:
            # Map MIDI note to LED index
            led_index = self._map_note_to_led(note)
            if led_index is None:
                return  # Note outside LED range
            
            # Calculate LED color and brightness based on velocity
            color = self._get_note_color(note)
            brightness = self._velocity_to_brightness(velocity)
            
            # Apply brightness to color
            final_color = tuple(int(c * brightness) for c in color)
            
            # Update LED
            if self._led_controller:
                self._led_controller.turn_on_led(led_index, final_color, auto_show=True)
            
            # Track active note
            self._active_notes[note] = {
                'velocity': velocity,
                'timestamp': timestamp,
                'led_index': led_index,
                'channel': channel,
                'color': final_color
            }
            
            # Create event for WebSocket broadcast
            event = MIDIInputEvent(
                timestamp=timestamp,
                note=note,
                velocity=velocity,
                channel=channel,
                event_type='note_on'
            )
            
            # Broadcast event
            self._broadcast_midi_event(event)
            
            self.logger.debug(f"Note ON: {note} (LED {led_index}) velocity {velocity}")
            
        except Exception as e:
            self.logger.error(f"Error handling note on {note}: {e}")
    
    def _handle_note_off(self, note: int, channel: int, timestamp: float):
        """
        Handle MIDI note off event.
        
        Args:
            note: MIDI note number (0-127)
            channel: MIDI channel (0-15)
            timestamp: Event timestamp
        """
        try:
            # Check if note was active
            if note not in self._active_notes:
                return  # Note wasn't active
            
            note_info = self._active_notes[note]
            led_index = note_info['led_index']
            
            # Turn off LED
            if self._led_controller:
                self._led_controller.turn_off_led(led_index, auto_show=True)
            
            # Remove from active notes
            del self._active_notes[note]
            
            # Create event for WebSocket broadcast
            event = MIDIInputEvent(
                timestamp=timestamp,
                note=note,
                velocity=0,
                channel=channel,
                event_type='note_off'
            )
            
            # Broadcast event
            self._broadcast_midi_event(event)
            
            self.logger.debug(f"Note OFF: {note} (LED {led_index})")
            
        except Exception as e:
            self.logger.error(f"Error handling note off {note}: {e}")
    
    def _map_note_to_led(self, midi_note: int) -> Optional[int]:
        """
        Map MIDI note number to LED strip position with orientation support.
        
        Args:
            midi_note: MIDI note number (0-127)
            
        Returns:
            Physical LED index (0-based) or None if note is outside range
        """
        if midi_note < self.min_midi_note or midi_note > self.max_midi_note:
            return None
        
        # Calculate logical LED index (0 to num_leds-1)
        note_range = self.max_midi_note - self.min_midi_note
        logical_index = int((midi_note - self.min_midi_note) * (self.num_leds - 1) / note_range)
        logical_index = max(0, min(logical_index, self.num_leds - 1))
        
        # Apply LED orientation mapping
        if self.led_orientation == 'reversed':
            physical_index = (self.num_leds - 1) - logical_index
        else:
            physical_index = logical_index
            
        return physical_index
    
    def _get_note_color(self, note: int) -> tuple:
        """
        Get RGB color for a MIDI note based on pitch.
        
        Args:
            note: MIDI note number
            
        Returns:
            RGB color tuple (0-255)
        """
        # Color mapping based on chromatic scale
        note_in_octave = note % 12
        
        # Color wheel mapping for chromatic notes
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
            (127, 0, 255),  # A - Blue-Magenta
            (255, 0, 255),  # A# - Magenta
            (255, 0, 127),  # B - Magenta-Red
        ]
        
        return colors[note_in_octave]
    
    def _velocity_to_brightness(self, velocity: int) -> float:
        """
        Convert MIDI velocity to LED brightness factor.
        
        Args:
            velocity: MIDI velocity (0-127)
            
        Returns:
            Brightness factor (0.0-1.0)
        """
        # Map velocity to brightness with minimum threshold
        min_brightness = 0.1
        max_brightness = 1.0
        
        normalized_velocity = velocity / 127.0
        return min_brightness + (normalized_velocity * (max_brightness - min_brightness))
    
    def _clear_all_leds(self):
        """Clear all LEDs and reset active notes."""
        try:
            if self._led_controller:
                self._led_controller.turn_off_all()
            
            self._active_notes.clear()
            self.logger.debug("Cleared all LEDs and active notes")
            
        except Exception as e:
            self.logger.error(f"Error clearing LEDs: {e}")
    
    def _cleanup_input_port(self):
        """Clean up MIDI input port resources."""
        try:
            if self._input_port:
                self._input_port.close()
                self._input_port = None
                self.logger.debug("Closed MIDI input port")
        except Exception as e:
            self.logger.error(f"Error closing MIDI input port: {e}")
    
    def _broadcast_midi_event(self, event: MIDIInputEvent):
        """Broadcast MIDI event via WebSocket."""
        if self._websocket_callback:
            try:
                # Send event to unified manager (which will broadcast unified_midi_event)
                event_data = {
                    'timestamp': event.timestamp,
                    'note': event.note,
                    'velocity': event.velocity,
                    'channel': event.channel,
                    'event_type': event.event_type,
                    'source': f"USB:{self._current_device or 'unknown'}"
                }
                self._websocket_callback(event.event_type, event_data)
                
                # Also broadcast direct midi_input event for backward compatibility
                legacy_event_data = {
                    'type': 'midi_input_event',
                    'timestamp': event.timestamp,
                    'note': event.note,
                    'velocity': event.velocity,
                    'channel': event.channel,
                    'event_type': event.event_type,
                    'active_notes': len(self._active_notes)
                }
                self._websocket_callback('midi_input', legacy_event_data)
            except Exception as e:
                self.logger.error(f"Error broadcasting MIDI event: {e}")
    
    def _broadcast_status_update(self):
        """Broadcast service status update via WebSocket."""
        if self._websocket_callback:
            try:
                status_data = {
                    'type': 'midi_input_status',
                    'state': self._state.value,
                    'device': self._current_device,
                    'active_notes': len(self._active_notes),
                    'event_count': self._event_count,
                    'last_event_time': self._last_event_time
                }
                self._websocket_callback('midi_input_status', status_data)
                
                # Also notify the manager about device status changes
                self._websocket_callback('device_status', {
                    'device': self._current_device,
                    'state': self._state.value,
                    'is_listening': self.is_listening,
                    'devices': [d.__dict__ for d in self.get_available_devices()]
                })
            except Exception as e:
                self.logger.error(f"Error broadcasting status update: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current service status information.
        
        Returns:
            Dictionary containing service status
        """
        return {
            'state': self._state.value,
            'device': self._current_device,
            'is_listening': self.is_listening,
            'active_notes': len(self._active_notes),
            'event_count': self._event_count,
            'last_event_time': self._last_event_time,
            'available_devices': [d.__dict__ for d in self.get_available_devices()]
        }
    
    def cleanup(self):
        """Clean up service resources."""
        self.logger.info("Cleaning up USB MIDI input service")
        self.stop_listening()
        self._clear_all_leds()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()