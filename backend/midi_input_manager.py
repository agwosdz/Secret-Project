#!/usr/bin/env python3
"""
Unified MIDI Input Manager - Coordinates USB and rtpMIDI inputs
Provides shared processing pipeline and event coordination
"""

import logging
import threading
import time
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass
from enum import Enum

# Import MIDI services
try:
    from usb_midi_service import USBMIDIInputService
except ImportError:
    USBMIDIInputService = None

try:
    from rtpmidi_service import RtpMIDIService
except ImportError:
    RtpMIDIService = None

# Configuration imports with fallbacks
try:
    from config import get_config
except ImportError:
    def get_config(key, default=None):
        return default

class MIDIInputSource(Enum):
    """MIDI input source types"""
    USB = "usb"
    RTPMIDI = "rtpmidi"
    UNKNOWN = "unknown"

@dataclass
class UnifiedMIDIEvent:
    """Unified MIDI event structure"""
    timestamp: float
    note: int
    velocity: int
    channel: int
    event_type: str  # 'note_on' or 'note_off'
    source: MIDIInputSource
    source_detail: str  # Device name or session name
    processed: bool = False
    
    def get_event_key(self) -> tuple:
        """Generate a key for duplicate detection based on event properties"""
        return (self.event_type, self.channel, self.note, self.velocity)

class MIDIInputManager:
    """Unified manager for coordinating USB and rtpMIDI inputs"""
    
    def __init__(self, websocket_callback: Optional[Callable] = None, led_controller: Optional['LEDController'] = None):
        """
        Initialize unified MIDI input manager.
        
        Args:
            websocket_callback: Callback function for WebSocket event broadcasting
            led_controller: LED controller instance for real-time visualization
        """
        self.logger = logging.getLogger(__name__)
        self._websocket_callback = websocket_callback
        self._led_controller = led_controller
        
        # Load configuration
        self.enable_usb = get_config('midi_enable_usb', True)
        self.enable_rtpmidi = get_config('midi_enable_rtpmidi', True)
        self.event_buffer_size = get_config('midi_event_buffer_size', 1000)
        self.duplicate_filter_window = get_config('midi_duplicate_filter_ms', 50)
        
        # Initialize MIDI services
        self._usb_service: Optional[USBMIDIInputService] = None
        self._rtpmidi_service: Optional[RtpMIDIService] = None
        
        # Event processing
        self._event_buffer: List[UnifiedMIDIEvent] = []
        self._buffer_lock = threading.Lock()
        self._processing_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
        
        # Active notes tracking (unified across all sources)
        self._active_notes: Dict[int, Dict[str, Any]] = {}  # note -> {source, timestamp, velocity, channel}
        self._notes_lock = threading.Lock()
        self.active_notes: Set[tuple] = set()  # Public set for (channel, note) tuples
        
        # Duplicate detection tracking
        self._recent_events: Dict[tuple, float] = {}  # event_key -> timestamp
        self._recent_events_lock = threading.Lock()
        
        # Performance tracking
        self._event_count_by_source: Dict[MIDIInputSource, int] = {
            MIDIInputSource.USB: 0,
            MIDIInputSource.RTPMIDI: 0
        }
        self._last_event_time = 0.0
        self._duplicate_events_filtered = 0
        
        # Source status tracking
        self._source_status: Dict[MIDIInputSource, Dict[str, Any]] = {
            MIDIInputSource.USB: {'available': False, 'listening': False, 'devices': []},
            MIDIInputSource.RTPMIDI: {'available': False, 'listening': False, 'sessions': []}
        }
        
        self.logger.info("Unified MIDI Input Manager initialized")
        # Send initial status broadcast
        self.logger.info("Broadcasting initial status update...")
        self._broadcast_status_update()
        self.logger.info("Initial status broadcast completed")
    
    @property
    def is_listening(self) -> bool:
        """Check if manager is actively listening for MIDI input"""
        return self._running
    

    
    def initialize_services(self) -> bool:
        """
        Initialize USB and rtpMIDI services.
        
        Returns:
            bool: True if at least one service initialized successfully
        """
        success_count = 0
        
        # Initialize USB MIDI service
        if self.enable_usb and USBMIDIInputService:
            try:
                self._usb_service = USBMIDIInputService(
                    led_controller=self._led_controller,
                    websocket_callback=self._handle_usb_event
                )
                self._source_status[MIDIInputSource.USB]['available'] = True
                success_count += 1
                self.logger.info("USB MIDI service initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize USB MIDI service: {e}")
        
        # Initialize rtpMIDI service
        if self.enable_rtpmidi and RtpMIDIService:
            try:
                self._rtpmidi_service = RtpMIDIService(
                    midi_input_manager=self,
                    websocket_callback=self._handle_rtpmidi_event
                )
                self._source_status[MIDIInputSource.RTPMIDI]['available'] = True
                success_count += 1
                self.logger.info("rtpMIDI service initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize rtpMIDI service: {e}")
        
        if success_count == 0:
            self.logger.error("No MIDI input services could be initialized")
            return False
        
        self.logger.info(f"Initialized {success_count} MIDI input service(s)")
        return True
    
    def start_listening(self, device_name: Optional[str] = None, enable_usb: bool = True, enable_rtpmidi: bool = True) -> bool:
        """
        Start listening on specified MIDI input sources.
        
        Args:
            device_name: Specific USB device name to use (optional)
            enable_usb: Whether to enable USB MIDI input
            enable_rtpmidi: Whether to enable rtpMIDI input
        
        Returns:
            bool: True if at least one source started successfully
        """
        if self._running:
            self.logger.warning("MIDI input manager already running")
            return True
        
        # Initialize services if not already done
        if not self._usb_service and not self._rtpmidi_service:
            self.initialize_services()
        
        success_count = 0
        
        # Start event processing thread
        self._stop_event.clear()
        self._processing_thread = threading.Thread(
            target=self._event_processing_loop,
            name="MIDI-EventProcessor",
            daemon=True
        )
        self._processing_thread.start()
        
        # Start USB MIDI listening
        if enable_usb and self._usb_service:
            try:
                if self._usb_service.start_listening(device_name):
                    self._source_status[MIDIInputSource.USB]['listening'] = True
                    success_count += 1
                    self.logger.info("USB MIDI listening started")
            except Exception as e:
                self.logger.error(f"Failed to start USB MIDI listening: {e}")
        
        # Start rtpMIDI listening
        if enable_rtpmidi and self._rtpmidi_service:
            try:
                if self._rtpmidi_service.start_listening():
                    self._source_status[MIDIInputSource.RTPMIDI]['listening'] = True
                    success_count += 1
                    self.logger.info("rtpMIDI listening started")
            except Exception as e:
                self.logger.error(f"Failed to start rtpMIDI listening: {e}")
        
        if success_count == 0:
            self.logger.error("No MIDI input sources could be started")
            self._stop_event.set()
            return False
        
        self._running = True
        self.logger.info(f"MIDI input manager started with {success_count} source(s)")
        self._broadcast_status_update()
        return True
    
    def stop_listening(self) -> bool:
        """
        Stop listening on all MIDI input sources.
        
        Returns:
            bool: True if stopped successfully
        """
        if not self._running:
            return True
        
        self._running = False
        self._stop_event.set()
        
        # Stop USB MIDI service
        if self._usb_service:
            try:
                self._usb_service.stop_listening()
                self._source_status[MIDIInputSource.USB]['listening'] = False
                self.logger.info("USB MIDI listening stopped")
            except Exception as e:
                self.logger.error(f"Error stopping USB MIDI: {e}")
        
        # Stop rtpMIDI service
        if self._rtpmidi_service:
            try:
                self._rtpmidi_service.stop_listening()
                self._source_status[MIDIInputSource.RTPMIDI]['listening'] = False
                self.logger.info("rtpMIDI listening stopped")
            except Exception as e:
                self.logger.error(f"Error stopping rtpMIDI: {e}")
        
        # Wait for processing thread to finish
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=5.0)
        
        # Clear active notes
        with self._notes_lock:
            self._active_notes.clear()
            self.active_notes.clear()
        
        self.logger.info("MIDI input manager stopped")
        self._broadcast_status_update()
        return True
    
    def process_midi_event(self, source_type: str, event_data: Dict[str, Any]):
        """
        Process MIDI event from any source (called by individual services).
        
        Args:
            source_type: Source type ('usb' or 'rtpmidi')
            event_data: Event data dictionary
        """
        try:
            # Determine source enum
            if source_type == 'usb':
                source = MIDIInputSource.USB
            elif source_type == 'rtpmidi':
                source = MIDIInputSource.RTPMIDI
            else:
                source = MIDIInputSource.UNKNOWN
            
            # Create unified event
            unified_event = UnifiedMIDIEvent(
                timestamp=event_data.get('timestamp', time.time()),
                note=event_data.get('note', 0),
                velocity=event_data.get('velocity', 0),
                channel=event_data.get('channel', 0),
                event_type=event_data.get('event_type', 'unknown'),
                source=source,
                source_detail=event_data.get('source', 'unknown')
            )
            
            # Add to event buffer for processing
            with self._buffer_lock:
                if len(self._event_buffer) >= self.event_buffer_size:
                    # Remove oldest event if buffer is full
                    self._event_buffer.pop(0)
                    self.logger.warning("MIDI event buffer overflow - dropping oldest event")
                
                self._event_buffer.append(unified_event)
            
            # Update performance tracking
            self._event_count_by_source[source] += 1
            self._last_event_time = unified_event.timestamp
            
        except Exception as e:
            self.logger.error(f"Error processing MIDI event from {source_type}: {e}")
    
    def _event_processing_loop(self):
        """Main event processing loop"""
        self.logger.info("Starting MIDI event processing loop")
        
        while not self._stop_event.is_set():
            try:
                # Process events from buffer
                events_to_process = []
                
                with self._buffer_lock:
                    if self._event_buffer:
                        events_to_process = self._event_buffer.copy()
                        self._event_buffer.clear()
                
                # Process each event
                for event in events_to_process:
                    self._process_unified_event(event)
                
                # Small delay to prevent excessive CPU usage
                if not events_to_process:
                    time.sleep(0.001)  # 1ms
                
            except Exception as e:
                self.logger.error(f"Error in event processing loop: {e}")
                time.sleep(0.1)
        
        self.logger.info("MIDI event processing loop stopped")
    
    def _process_unified_event(self, event: UnifiedMIDIEvent):
        """Process a unified MIDI event"""
        try:
            # Filter duplicate events
            if self._is_duplicate_event(event):
                self._duplicate_events_filtered += 1
                return
            
            # Update active notes tracking
            self._update_active_notes(event)
            
            # Broadcast unified event
            self._broadcast_unified_event(event)
            
            # Mark as processed
            event.processed = True
            
        except Exception as e:
            self.logger.error(f"Error processing unified event: {e}")
    
    def _is_duplicate_event(self, event: UnifiedMIDIEvent) -> bool:
        """
        Check if event is a duplicate within the filter window.
        
        Args:
            event: Event to check
            
        Returns:
            bool: True if event is considered a duplicate
        """
        current_time = time.time()
        filter_window_seconds = self.duplicate_filter_window / 1000.0
        event_key = event.get_event_key()
        
        with self._recent_events_lock:
            # Clean up old events first
            keys_to_remove = []
            for key, timestamp in self._recent_events.items():
                if current_time - timestamp > filter_window_seconds:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._recent_events[key]
            
            # Check if this event is a duplicate
            if event_key in self._recent_events:
                return True
            
            # Record this event
            self._recent_events[event_key] = current_time
            
        return False
    
    def _update_active_notes(self, event: UnifiedMIDIEvent):
        """Update active notes tracking"""
        with self._notes_lock:
            if event.event_type == 'note_on' and event.velocity > 0:
                self._active_notes[event.note] = {
                    'source': event.source,
                    'source_detail': event.source_detail,
                    'timestamp': event.timestamp,
                    'velocity': event.velocity,
                    'channel': event.channel,
                    'event_type': event.event_type
                }
                # Also update the public set
                self.active_notes.add((event.channel, event.note))
            elif event.event_type == 'note_off' or (event.event_type == 'note_on' and event.velocity == 0):
                if event.note in self._active_notes:
                    del self._active_notes[event.note]
                # Also update the public set
                self.active_notes.discard((event.channel, event.note))
    
    def _broadcast_unified_event(self, event: UnifiedMIDIEvent):
        """Broadcast unified MIDI event via WebSocket"""
        if self._websocket_callback:
            try:
                self._websocket_callback('unified_midi_event', {
                    'timestamp': event.timestamp,
                    'note': event.note,
                    'velocity': event.velocity,
                    'channel': event.channel,
                    'event_type': event.event_type,
                    'source': event.source.value,
                    'source_detail': event.source_detail
                })
            except Exception as e:
                self.logger.error(f"Error broadcasting unified MIDI event: {e}")
    
    def _handle_usb_event(self, event_type: str, event_data: Dict[str, Any]):
        """Handle events from USB MIDI service"""
        try:
            if event_type in ['note_on', 'note_off']:
                # Convert USB event to unified format
                self.process_midi_event('usb', {
                    'timestamp': time.time(),
                    'note': event_data.get('note', 0),
                    'velocity': event_data.get('velocity', 0),
                    'channel': event_data.get('channel', 0),
                    'event_type': event_type,
                    'source': f"USB:{event_data.get('device', 'unknown')}"
                })
            elif event_type == 'device_status':
                # Update USB device status
                self._source_status[MIDIInputSource.USB]['devices'] = event_data.get('devices', [])
                self._broadcast_status_update()
        except Exception as e:
            self.logger.error(f"Error handling USB event: {e}")
    
    def _handle_rtpmidi_event(self, event_type: str, event_data: Dict[str, Any]):
        """Handle events from rtpMIDI service"""
        try:
            if event_type == 'rtpmidi_event':
                # Event already processed by rtpMIDI service via process_midi_event
                pass
            elif event_type == 'rtpmidi_status':
                # Update rtpMIDI status
                self._source_status[MIDIInputSource.RTPMIDI]['sessions'] = event_data.get('active_sessions', 0)
                self._broadcast_status_update()
        except Exception as e:
            self.logger.error(f"Error handling rtpMIDI event: {e}")
    
    def _broadcast_status_update(self):
        """Broadcast unified status update via WebSocket"""
        if self._websocket_callback:
            try:
                self.logger.info("Broadcasting MIDI manager status update...")
                # Get detailed status from services
                usb_status = {}
                rtpmidi_status = {}
                
                if self._usb_service:
                    usb_service_status = self._usb_service.get_status()
                    usb_status = {
                        'connected': usb_service_status.get('is_listening', False),
                        'device_name': usb_service_status.get('device'),
                        'listening': usb_service_status.get('is_listening', False),
                        'available': self._source_status[MIDIInputSource.USB].get('available', False)
                    }
                    self.logger.info(f"USB status: {usb_status}")
                
                if self._rtpmidi_service:
                    rtpmidi_service_status = self._rtpmidi_service.get_status()
                    active_sessions = rtpmidi_service_status.get('active_sessions', {})
                    rtpmidi_status = {
                        'connected': len(active_sessions) > 0,
                        'active_sessions': list(active_sessions.values()) if active_sessions else [],
                        'listening': rtpmidi_service_status.get('running', False),
                        'available': self._source_status[MIDIInputSource.RTPMIDI].get('available', False)
                    }
                
                status_data = {
                    'running': self._running,
                    'sources': {
                        'USB': usb_status,
                        'RTP_MIDI': rtpmidi_status
                    },
                    'active_notes': len(self._active_notes),
                    'event_counts': {
                        source.value: count for source, count in self._event_count_by_source.items()
                    },
                    'performance': {
                        'last_event_time': self._last_event_time,
                        'duplicate_events_filtered': self._duplicate_events_filtered,
                        'buffer_size': len(self._event_buffer)
                    }
                }
                self.logger.info(f"Sending midi_manager_status: {status_data}")
                self._websocket_callback('midi_manager_status', status_data)
                self.logger.info("WebSocket callback completed")
            except Exception as e:
                self.logger.error(f"Error broadcasting status update: {e}")
    
    def get_active_notes(self) -> Dict[int, Dict[str, Any]]:
        """Get currently active notes across all sources"""
        with self._notes_lock:
            return self._active_notes.copy()
    
    def get_source_status(self, source: MIDIInputSource) -> Dict[str, Any]:
        """Get status for a specific MIDI input source"""
        return self._source_status.get(source, {}).copy()
    
    def get_available_devices(self) -> Dict[str, Any]:
        """Get available MIDI input devices from all sources"""
        devices = {
            'usb_devices': [],
            'rtpmidi_sessions': []
        }
        
        # Get USB devices
        if self._usb_service:
            try:
                usb_devices = self._usb_service.get_available_devices()
                devices['usb_devices'] = [{
                    'name': device.name,
                    'id': device.id,
                    'type': device.type,
                    'status': device.status
                } for device in usb_devices]
            except Exception as e:
                self.logger.error(f"Error getting USB devices: {e}")
        
        # Get rtpMIDI sessions
        if self._rtpmidi_service:
            try:
                rtpmidi_sessions = self._rtpmidi_service.get_available_sessions()
                devices['rtpmidi_sessions'] = rtpmidi_sessions
            except Exception as e:
                self.logger.error(f"Error getting rtpMIDI sessions: {e}")
        
        return devices
    
    def get_status(self) -> Dict[str, Any]:
        """Get unified status of MIDI input manager"""
        status = {
            'is_listening': self._running,
            'active_notes_count': len(self.active_notes),
            'usb_service': {},
            'rtpmidi_service': {}
        }
        
        # Get USB service status
        if self._usb_service:
            try:
                status['usb_service'] = self._usb_service.get_status()
            except Exception as e:
                self.logger.error(f"Error getting USB service status: {e}")
        
        # Get rtpMIDI service status
        if self._rtpmidi_service:
            try:
                status['rtpmidi_service'] = self._rtpmidi_service.get_status()
            except Exception as e:
                self.logger.error(f"Error getting rtpMIDI service status: {e}")
        
        return status
    
    def get_active_services(self) -> Dict[str, Any]:
        """Get information about active MIDI input services"""
        services = {
            'usb': False,
            'rtpmidi': False
        }
        
        # Check USB service
        if self._usb_service:
            try:
                services['usb'] = self._usb_service.is_listening
            except Exception as e:
                self.logger.error(f"Error checking USB service status: {e}")
        
        # Check rtpMIDI service
        if self._rtpmidi_service:
            try:
                services['rtpmidi'] = hasattr(self._rtpmidi_service, 'state') and \
                                   self._rtpmidi_service.state.value in ['discovering', 'listening']
            except Exception as e:
                self.logger.error(f"Error checking rtpMIDI service status: {e}")
        
        return services
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all MIDI inputs"""
        status = {
            'manager': {
                'running': self._running,
                'sources_available': len([s for s in self._source_status.values() if s.get('available', False)]),
                'sources_listening': len([s for s in self._source_status.values() if s.get('listening', False)])
            },
            'sources': {},
            'performance': {
                'total_events': sum(self._event_count_by_source.values()),
                'events_by_source': {source.value: count for source, count in self._event_count_by_source.items()},
                'last_event_time': self._last_event_time,
                'duplicate_events_filtered': self._duplicate_events_filtered,
                'active_notes': len(self._active_notes),
                'buffer_size': len(self._event_buffer)
            }
        }
        
        # Add individual service status
        if self._usb_service:
            status['sources']['usb'] = self._usb_service.get_status()
        
        if self._rtpmidi_service:
            status['sources']['rtpmidi'] = self._rtpmidi_service.get_status()
        
        return status
    
    def cleanup(self):
        """Clean up manager resources"""
        self.logger.info("Cleaning up MIDI input manager")
        self.stop_listening()
        
        if self._usb_service:
            self._usb_service.cleanup()
        
        if self._rtpmidi_service:
            self._rtpmidi_service.cleanup()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()