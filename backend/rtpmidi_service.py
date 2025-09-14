#!/usr/bin/env python3
"""
rtpMIDI Network Listener Service - Real-time network MIDI input processing
Handles rtpMIDI session discovery, connection management, and network MIDI input
"""

import logging
import threading
import time
import socket
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

try:
    import pymidi
    from pymidi import server
    PYMIDI_AVAILABLE = True
except ImportError:
    pymidi = None
    server = None
    PYMIDI_AVAILABLE = False
    print("Warning: pymidi not available. rtpMIDI functionality will be limited.")

# Configuration imports with fallbacks
try:
    from config import get_config
except ImportError:
    def get_config(key, default=None):
        return default

class RtpMIDIState(Enum):
    """rtpMIDI service state enumeration"""
    IDLE = "idle"
    DISCOVERING = "discovering"
    LISTENING = "listening"
    ERROR = "error"

@dataclass
class RtpMIDISession:
    """Represents an rtpMIDI session"""
    name: str
    ip_address: str
    port: int
    status: str = "available"
    latency: float = 0.0
    packet_loss: float = 0.0
    connected_at: Optional[float] = None

@dataclass
class NetworkMIDIEvent:
    """Represents a network MIDI input event"""
    timestamp: float
    note: int
    velocity: int
    channel: int
    event_type: str  # 'note_on' or 'note_off'
    source_session: str

if PYMIDI_AVAILABLE:
    class RtpMIDIHandler(server.Handler):
        """Handler for rtpMIDI events"""
        
        def __init__(self, rtpmidi_service):
            super().__init__()
            self.rtpmidi_service = rtpmidi_service
            self.logger = logging.getLogger(__name__ + '.Handler')
            
        def on_peer_connected(self, peer):
            """Handle peer connection"""
            self.logger.info(f'rtpMIDI peer connected: {peer}')
            self.rtpmidi_service._handle_peer_connected(peer)
            
        def on_peer_disconnected(self, peer):
            """Handle peer disconnection"""
            self.logger.info(f'rtpMIDI peer disconnected: {peer}')
            self.rtpmidi_service._handle_peer_disconnected(peer)
            
        def on_midi_commands(self, peer, command_list):
            """Handle incoming MIDI commands from network"""
            for command in command_list:
                self.rtpmidi_service._process_network_midi_command(peer, command)
else:
    class RtpMIDIHandler:
        """Dummy handler when pymidi is not available"""
        
        def __init__(self, rtpmidi_service):
            self.rtpmidi_service = rtpmidi_service
            self.logger = logging.getLogger(__name__ + '.Handler')
            
        def on_peer_connected(self, peer):
            pass
            
        def on_peer_disconnected(self, peer):
            pass
            
        def on_midi_commands(self, peer, command_list):
            pass

class RtpMIDIService:
    """Service for real-time rtpMIDI network input processing"""
    
    def __init__(self, midi_input_manager=None, websocket_callback: Optional[Callable] = None):
        """
        Initialize rtpMIDI service.
        
        Args:
            midi_input_manager: Unified MIDI input manager for event forwarding
            websocket_callback: Callback function for WebSocket event broadcasting
        """
        self.logger = logging.getLogger(__name__)
        self._midi_input_manager = midi_input_manager
        self._websocket_callback = websocket_callback
        
        # Load configuration
        self.rtpmidi_port = get_config('rtpmidi_port', 5051)
        self.max_connections = get_config('rtpmidi_max_connections', 3)
        self.discovery_timeout = get_config('rtpmidi_discovery_timeout', 30.0)
        
        # Service state
        self._state = RtpMIDIState.IDLE
        self._server: Optional[server.Server] = None
        self._handler: Optional[RtpMIDIHandler] = None
        
        # Session management
        self._active_sessions: Dict[str, RtpMIDISession] = {}
        self._discovered_sessions: Dict[str, RtpMIDISession] = {}
        
        # Threading for service management
        self._server_thread: Optional[threading.Thread] = None
        self._discovery_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
        
        # Performance tracking
        self._event_count = 0
        self._last_event_time = 0.0
        self._connection_quality: Dict[str, Dict[str, float]] = {}
        
        # Check pymidi availability
        if not PYMIDI_AVAILABLE:
            self.logger.error("pymidi library not available - rtpMIDI functionality disabled")
            self._state = RtpMIDIState.ERROR
    
    @property
    def state(self) -> RtpMIDIState:
        """Get current service state"""
        return self._state
    
    @property
    def active_sessions(self) -> Dict[str, RtpMIDISession]:
        """Get active rtpMIDI sessions"""
        return self._active_sessions.copy()
    
    @property
    def discovered_sessions(self) -> Dict[str, RtpMIDISession]:
        """Get discovered rtpMIDI sessions"""
        return self._discovered_sessions.copy()
    
    @property
    def is_listening(self) -> bool:
        """Check if service is actively listening for rtpMIDI connections"""
        return self._state == RtpMIDIState.LISTENING
    
    @property
    def is_discovering(self) -> bool:
        """Check if service is actively discovering rtpMIDI sessions"""
        return self._state == RtpMIDIState.DISCOVERING
    
    def start_discovery(self) -> bool:
        """
        Start rtpMIDI session discovery using Bonjour/mDNS.
        
        Returns:
            bool: True if discovery started successfully
        """
        if not PYMIDI_AVAILABLE:
            self.logger.error("Cannot start discovery - pymidi not available")
            return False
            
        if self._state == RtpMIDIState.DISCOVERING:
            self.logger.warning("Discovery already running")
            return True
            
        try:
            self._state = RtpMIDIState.DISCOVERING
            self._stop_event.clear()
            
            # Start discovery thread
            self._discovery_thread = threading.Thread(
                target=self._discovery_loop,
                name="RtpMIDI-Discovery",
                daemon=True
            )
            self._discovery_thread.start()
            
            self.logger.info("rtpMIDI session discovery started")
            self._broadcast_status_update()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start rtpMIDI discovery: {e}")
            self._state = RtpMIDIState.ERROR
            return False
    
    def start_listening(self, port: Optional[int] = None) -> bool:
        """
        Start rtpMIDI server to listen for incoming connections.
        
        Args:
            port: Port to listen on (defaults to configured port)
            
        Returns:
            bool: True if listening started successfully
        """
        if not PYMIDI_AVAILABLE:
            self.logger.error("Cannot start listening - pymidi not available")
            return False
            
        if self._state == RtpMIDIState.LISTENING:
            self.logger.warning("Already listening for rtpMIDI connections")
            return True
            
        listen_port = port or self.rtpmidi_port
        
        try:
            # Create pymidi server
            self._server = server.Server([('0.0.0.0', listen_port)])
            self._handler = RtpMIDIHandler(self)
            self._server.add_handler(self._handler)
            
            # Start server in separate thread
            self._server_thread = threading.Thread(
                target=self._server_loop,
                name="RtpMIDI-Server",
                daemon=True
            )
            self._server_thread.start()
            
            self._state = RtpMIDIState.LISTENING
            self._running = True
            
            self.logger.info(f"rtpMIDI server listening on port {listen_port}")
            self._broadcast_status_update()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start rtpMIDI server: {e}")
            self._state = RtpMIDIState.ERROR
            return False
    
    def stop_listening(self) -> bool:
        """
        Stop rtpMIDI server and close all connections.
        
        Returns:
            bool: True if stopped successfully
        """
        if self._state == RtpMIDIState.IDLE:
            return True
            
        try:
            self._running = False
            self._stop_event.set()
            
            # Stop server
            if self._server:
                # pymidi server doesn't have a direct stop method
                # We'll need to handle this through thread management
                pass
                
            # Wait for threads to finish
            if self._server_thread and self._server_thread.is_alive():
                self._server_thread.join(timeout=5.0)
                
            if self._discovery_thread and self._discovery_thread.is_alive():
                self._discovery_thread.join(timeout=5.0)
            
            # Clear sessions
            self._active_sessions.clear()
            self._discovered_sessions.clear()
            
            self._state = RtpMIDIState.IDLE
            self.logger.info("rtpMIDI service stopped")
            self._broadcast_status_update()
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping rtpMIDI service: {e}")
            return False
    
    def connect_session(self, session_info: RtpMIDISession) -> bool:
        """
        Connect to a specific rtpMIDI session.
        
        Args:
            session_info: Session information for connection
            
        Returns:
            bool: True if connection successful
        """
        if not PYMIDI_AVAILABLE:
            self.logger.error("Cannot connect to rtpMIDI session: pymidi not available")
            return False
            
        if session_info is None:
            self.logger.error("Cannot connect to session: session_info is None")
            return False
            
        if len(self._active_sessions) >= self.max_connections:
            self.logger.warning(f"Maximum connections ({self.max_connections}) reached")
            return False
            
        try:
            # For pymidi, connections are handled automatically when peers connect
            # We'll track the session as "connecting"
            session_info.status = "connecting"
            session_info.connected_at = time.time()
            
            self._active_sessions[session_info.name] = session_info
            
            self.logger.info(f"Attempting to connect to rtpMIDI session: {session_info.name}")
            self._broadcast_status_update()
            return True
            
        except Exception as e:
            session_name = session_info.name if session_info else "unknown"
            self.logger.error(f"Failed to connect to session {session_name}: {e}")
            return False
    
    def disconnect_session(self, session_name: str) -> bool:
        """
        Disconnect from a specific rtpMIDI session.
        
        Args:
            session_name: Name of session to disconnect
            
        Returns:
            bool: True if disconnection successful
        """
        if session_name not in self._active_sessions:
            self.logger.warning(f"Session {session_name} not found in active sessions")
            return False
            
        try:
            # Remove from active sessions
            del self._active_sessions[session_name]
            
            # Clean up connection quality tracking
            if session_name in self._connection_quality:
                del self._connection_quality[session_name]
            
            self.logger.info(f"Disconnected from rtpMIDI session: {session_name}")
            self._broadcast_status_update()
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from session {session_name}: {e}")
            return False
    
    def _discovery_loop(self):
        """Main discovery loop for finding rtpMIDI sessions"""
        self.logger.info("Starting rtpMIDI session discovery loop")
        
        while not self._stop_event.is_set():
            try:
                # Simple discovery implementation
                # In a full implementation, this would use Bonjour/mDNS
                # For now, we'll simulate discovery by checking common ports
                self._discover_sessions_on_network()
                
                # Wait before next discovery cycle
                if self._stop_event.wait(timeout=10.0):
                    break
                    
            except Exception as e:
                self.logger.error(f"Error in discovery loop: {e}")
                time.sleep(5.0)
        
        self.logger.info("rtpMIDI discovery loop stopped")
    
    def _server_loop(self):
        """Main server loop for handling rtpMIDI connections"""
        self.logger.info("Starting rtpMIDI server loop")
        
        try:
            if self._server:
                # This will block until server is stopped
                self._server.serve_forever()
        except Exception as e:
            self.logger.error(f"Error in server loop: {e}")
        
        self.logger.info("rtpMIDI server loop stopped")
    
    def _discover_sessions_on_network(self):
        """Discover rtpMIDI sessions on local network"""
        # Simplified discovery - scan common rtpMIDI ports on local network
        # In production, this should use proper Bonjour/mDNS discovery
        
        try:
            # Get local network range (simplified)
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            # For demo purposes, we'll just log that discovery is running
            self.logger.debug(f"Scanning for rtpMIDI sessions from {local_ip}")
            
            # TODO: Implement proper mDNS/Bonjour discovery
            # This would involve:
            # 1. Broadcasting mDNS queries for _apple-midi._udp services
            # 2. Parsing responses to find available sessions
            # 3. Updating self._discovered_sessions
            
        except Exception as e:
            self.logger.error(f"Error during session discovery: {e}")
    
    def _handle_peer_connected(self, peer):
        """Handle when a peer connects to our rtpMIDI server"""
        try:
            peer_name = str(peer)
            
            # Create session info for connected peer
            session = RtpMIDISession(
                name=peer_name,
                ip_address=getattr(peer, 'address', 'unknown')[0] if hasattr(peer, 'address') else 'unknown',
                port=getattr(peer, 'address', ('unknown', 0))[1] if hasattr(peer, 'address') else 0,
                status="connected",
                connected_at=time.time()
            )
            
            self._active_sessions[peer_name] = session
            
            # Initialize connection quality tracking
            self._connection_quality[peer_name] = {
                'latency': 0.0,
                'packet_loss': 0.0,
                'last_update': time.time()
            }
            
            self.logger.info(f"rtpMIDI peer connected: {peer_name}")
            self._broadcast_status_update()
            
        except Exception as e:
            self.logger.error(f"Error handling peer connection: {e}")
    
    def _handle_peer_disconnected(self, peer):
        """Handle when a peer disconnects from our rtpMIDI server"""
        try:
            peer_name = str(peer)
            
            if peer_name in self._active_sessions:
                del self._active_sessions[peer_name]
            
            if peer_name in self._connection_quality:
                del self._connection_quality[peer_name]
            
            self.logger.info(f"rtpMIDI peer disconnected: {peer_name}")
            self._broadcast_status_update()
            
        except Exception as e:
            self.logger.error(f"Error handling peer disconnection: {e}")
    
    def _process_network_midi_command(self, peer, command):
        """Process incoming MIDI command from network peer"""
        try:
            peer_name = str(peer)
            timestamp = time.time()
            
            # Parse MIDI command
            if hasattr(command, 'command') and hasattr(command, 'params'):
                if command.command == 'note_on':
                    event = NetworkMIDIEvent(
                        timestamp=timestamp,
                        note=command.params.key,
                        velocity=command.params.velocity,
                        channel=getattr(command.params, 'channel', 0),
                        event_type='note_on',
                        source_session=peer_name
                    )
                    self._forward_midi_event(event)
                    
                elif command.command == 'note_off':
                    event = NetworkMIDIEvent(
                        timestamp=timestamp,
                        note=command.params.key,
                        velocity=0,
                        channel=getattr(command.params, 'channel', 0),
                        event_type='note_off',
                        source_session=peer_name
                    )
                    self._forward_midi_event(event)
            
            # Update performance tracking
            self._event_count += 1
            self._last_event_time = timestamp
            
            # Update connection quality
            self._update_connection_quality(peer_name, timestamp)
            
        except Exception as e:
            self.logger.error(f"Error processing network MIDI command: {e}")
    
    def _forward_midi_event(self, event: NetworkMIDIEvent):
        """Forward network MIDI event to unified input manager"""
        try:
            if self._midi_input_manager:
                # Convert to format expected by unified manager
                self._midi_input_manager.process_midi_event('rtpmidi', {
                    'timestamp': event.timestamp,
                    'note': event.note,
                    'velocity': event.velocity,
                    'channel': event.channel,
                    'event_type': event.event_type,
                    'source': f"rtpMIDI:{event.source_session}"
                })
            
            # Broadcast via WebSocket
            self._broadcast_midi_event(event)
            
        except Exception as e:
            self.logger.error(f"Error forwarding MIDI event: {e}")
    
    def _update_connection_quality(self, peer_name: str, timestamp: float):
        """Update connection quality metrics for a peer"""
        if peer_name in self._connection_quality:
            quality = self._connection_quality[peer_name]
            
            # Simple latency estimation (would need proper implementation)
            quality['latency'] = 0.0  # Placeholder
            quality['packet_loss'] = 0.0  # Placeholder
            quality['last_update'] = timestamp
    
    def _broadcast_midi_event(self, event: NetworkMIDIEvent):
        """Broadcast MIDI event via WebSocket"""
        if self._websocket_callback:
            try:
                self._websocket_callback('rtpmidi_event', {
                    'timestamp': event.timestamp,
                    'note': event.note,
                    'velocity': event.velocity,
                    'channel': event.channel,
                    'event_type': event.event_type,
                    'source_session': event.source_session
                })
            except Exception as e:
                self.logger.error(f"Error broadcasting MIDI event: {e}")
    
    def _broadcast_status_update(self):
        """Broadcast service status update via WebSocket"""
        if self._websocket_callback:
            try:
                # Send detailed status for manager consumption
                self._websocket_callback('rtpmidi_status', {
                    'state': self._state.value,
                    'running': self._running,
                    'active_sessions': {
                        name: {
                            'name': session.name,
                            'ip_address': session.ip_address,
                            'port': session.port,
                            'status': session.status,
                            'latency': session.latency,
                            'packet_loss': session.packet_loss,
                            'connected_at': session.connected_at
                        } for name, session in self._active_sessions.items()
                    },
                    'discovered_sessions': {
                        name: {
                            'name': session.name,
                            'ip_address': session.ip_address,
                            'port': session.port,
                            'status': session.status
                        } for name, session in self._discovered_sessions.items()
                    },
                    'event_count': self._event_count,
                    'last_event_time': self._last_event_time
                })
            except Exception as e:
                self.logger.error(f"Error broadcasting status update: {e}")
    
    def get_available_sessions(self) -> List[Dict[str, Any]]:
        """Get list of available rtpMIDI sessions (both active and discovered)"""
        sessions = []
        
        # Add active sessions
        for name, session in self._active_sessions.items():
            sessions.append({
                'name': session.name,
                'ip_address': session.ip_address,
                'port': session.port,
                'status': 'active',
                'latency': session.latency,
                'packet_loss': session.packet_loss,
                'connected_at': session.connected_at
            })
        
        # Add discovered sessions that are not already active
        for name, session in self._discovered_sessions.items():
            if name not in self._active_sessions:
                sessions.append({
                    'name': session.name,
                    'ip_address': session.ip_address,
                    'port': session.port,
                    'status': 'discovered',
                    'latency': 0.0,
                    'packet_loss': 0.0,
                    'connected_at': None
                })
        
        return sessions
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive service status"""
        return {
            'state': self._state.value,
            'running': self._running,
            'port': self.rtpmidi_port,
            'max_connections': self.max_connections,
            'active_sessions': {
                name: {
                    'name': session.name,
                    'ip_address': session.ip_address,
                    'port': session.port,
                    'status': session.status,
                    'latency': session.latency,
                    'packet_loss': session.packet_loss,
                    'connected_at': session.connected_at
                } for name, session in self._active_sessions.items()
            },
            'discovered_sessions': {
                name: {
                    'name': session.name,
                    'ip_address': session.ip_address,
                    'port': session.port,
                    'status': session.status
                } for name, session in self._discovered_sessions.items()
            },
            'performance': {
                'event_count': self._event_count,
                'last_event_time': self._last_event_time
            },
            'pymidi_available': PYMIDI_AVAILABLE
        }
    
    def cleanup(self):
        """Clean up service resources"""
        self.logger.info("Cleaning up rtpMIDI service")
        self.stop_listening()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()