import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import time
import threading
from flask import Flask, request
from flask_socketio import SocketIO, SocketIOTestClient
from usb_midi_service import USBMIDIInputService

class TestMIDIIntegration(unittest.TestCase):
    """Integration tests for MIDI input service with Flask app"""
    
    def setUp(self):
        """Set up test Flask app and components"""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Mock components
        self.mock_led_controller = Mock()
        self.mock_led_controller.num_pixels = 88
        
        # Store WebSocket events for testing
        self.websocket_events = []
        
        # Create USB MIDI service
        self.usb_midi_service = USBMIDIInputService(
            led_controller=self.mock_led_controller,
            websocket_callback=lambda event_type, data: self.websocket_events.append({'name': event_type, 'args': [data]})
        )
        
        # Set up routes and WebSocket handlers
        self._setup_routes()
        self._setup_websocket_handlers()
        
        # Create test client
        self.client = self.app.test_client()
        self.socketio_client = self.socketio.test_client(self.app)
    
    def _setup_routes(self):
        """Set up API routes for testing"""
        @self.app.route('/api/midi-input/devices', methods=['GET'])
        def get_midi_devices():
            try:
                devices = self.usb_midi_service.get_available_devices()
                return {
                    'success': True,
                    'devices': devices,
                    'count': len(devices)
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}, 500
        
        @self.app.route('/api/midi-input/start', methods=['POST'])
        def start_midi_input():
            try:
                data = json.loads(request.data) if request.data else {}
                device_name = data.get('device_name')
                
                if not device_name:
                    return {'success': False, 'error': 'Device name is required'}, 400
                
                success = self.usb_midi_service.start_listening(device_name)
                if success:
                    return {
                        'success': True,
                        'message': f'MIDI input started on {device_name}',
                        'device_name': device_name
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Failed to start MIDI input on {device_name}'
                    }, 500
            except Exception as e:
                return {'success': False, 'error': str(e)}, 500
        
        @self.app.route('/api/midi-input/stop', methods=['POST'])
        def stop_midi_input():
            try:
                self.usb_midi_service.stop_listening()
                return {
                    'success': True,
                    'message': 'MIDI input stopped successfully'
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}, 500
        
        @self.app.route('/api/midi-input/status', methods=['GET'])
        def get_midi_input_status():
            try:
                status = self.usb_midi_service.get_status()
                return {
                    'success': True,
                    'status': status
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}, 500
    
    def _setup_websocket_handlers(self):
        """Set up WebSocket handlers for testing"""
        @self.socketio.on('midi_input_start')
        def handle_midi_input_start(data):
            try:
                device_name = data.get('device_name')
                if not device_name:
                    self.socketio.emit('error', {'message': 'Device name is required'})
                    return
                
                success = self.usb_midi_service.start_listening(device_name)
                if success:
                    self.socketio.emit('midi_input_started', {
                        'device_name': device_name,
                        'message': f'MIDI input started on {device_name}'
                    })
                else:
                    self.socketio.emit('error', {
                        'message': f'Failed to start MIDI input on {device_name}'
                    })
            except Exception as e:
                self.socketio.emit('error', {
                    'message': f'MIDI input start failed: {str(e)}'
                })
        
        @self.socketio.on('midi_input_stop')
        def handle_midi_input_stop():
            try:
                self.usb_midi_service.stop_listening()
                self.socketio.emit('midi_input_stopped', {
                    'message': 'MIDI input stopped successfully'
                })
            except Exception as e:
                self.socketio.emit('error', {
                    'message': f'MIDI input stop failed: {str(e)}'
                })
        
        @self.socketio.on('get_midi_devices')
        def handle_get_midi_devices():
            try:
                devices = self.usb_midi_service.get_available_devices()
                device_list = [{'id': d.id, 'name': d.name, 'status': d.status, 'type': d.type} for d in devices]
                self.socketio.emit('midi_devices', {
                    'devices': device_list,
                    'count': len(device_list)
                })
            except Exception as e:
                self.socketio.emit('error', {
                    'message': f'Failed to get MIDI devices: {str(e)}'
                })
    
    def tearDown(self):
        """Clean up after tests"""
        if self.usb_midi_service.is_listening:
            self.usb_midi_service.stop_listening()
    
    @patch('usb_midi_service.mido')
    def test_api_get_devices(self, mock_mido):
        """Test API endpoint for getting MIDI devices"""
        mock_mido.get_input_names.return_value = ['Piano', 'Keyboard', 'Synth']
        
        response = self.client.get('/api/midi-input/devices')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        expected_devices = [
            {'id': 0, 'name': 'Piano', 'status': 'available', 'type': 'usb'},
            {'id': 1, 'name': 'Keyboard', 'status': 'available', 'type': 'usb'},
            {'id': 2, 'name': 'Synth', 'status': 'available', 'type': 'usb'}
        ]
        self.assertEqual(data['devices'], expected_devices)
        self.assertEqual(data['count'], 3)
    
    @patch('usb_midi_service.mido')
    def test_api_start_stop_midi_input(self, mock_mido):
        """Test API endpoints for starting and stopping MIDI input"""
        mock_port = Mock()
        mock_mido.open_input.return_value = mock_port
        
        # Test start
        start_data = {'device_name': 'Test Piano'}
        response = self.client.post(
            '/api/midi-input/start',
            data=json.dumps(start_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['device_name'], 'Test Piano')
        
        # Verify service is active
        self.assertTrue(self.usb_midi_service.is_listening)
        
        # Test stop
        response = self.client.post('/api/midi-input/stop')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify service is inactive
        self.assertFalse(self.usb_midi_service.is_listening)
    
    def test_api_get_status(self):
        """Test API endpoint for getting MIDI input status"""
        response = self.client.get('/api/midi-input/status')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        self.assertIn('status', data)
        
        status = data['status']
        self.assertIn('state', status)
        self.assertIn('device', status)
        self.assertIn('is_listening', status)
        self.assertIn('active_notes', status)
        self.assertIn('event_count', status)
    
    @patch('usb_midi_service.mido')
    def test_websocket_midi_devices(self, mock_mido):
        """Test WebSocket handler for getting MIDI devices"""
        mock_mido.get_input_names.return_value = ['Device1', 'Device2']
        
        # Connect and emit request
        self.socketio_client.emit('get_midi_devices')
        
        # Check received events
        received = self.socketio_client.get_received()
        
        # Find the midi_devices event
        midi_devices_event = None
        for event in received:
            if event['name'] == 'midi_devices':
                midi_devices_event = event
                break
        
        self.assertIsNotNone(midi_devices_event)
        devices = midi_devices_event['args'][0]['devices']
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0]['name'], 'Device1')
        self.assertEqual(devices[1]['name'], 'Device2')
        self.assertEqual(midi_devices_event['args'][0]['count'], 2)
    
    @patch('usb_midi_service.mido')
    def test_websocket_start_stop_midi(self, mock_mido):
        """Test WebSocket handlers for starting and stopping MIDI input"""
        mock_port = Mock()
        mock_mido.open_input.return_value = mock_port
        
        # Test start via WebSocket
        self.socketio_client.emit('midi_input_start', {'device_name': 'Test Device'})
        
        received = self.socketio_client.get_received()
        
        # Find the midi_input_started event
        start_event = None
        for event in received:
            if event['name'] == 'midi_input_started':
                start_event = event
                break
        
        self.assertIsNotNone(start_event)
        self.assertEqual(start_event['args'][0]['device_name'], 'Test Device')
        
        # Verify service is active
        self.assertTrue(self.usb_midi_service.is_listening)
        
        # Test stop via WebSocket
        self.socketio_client.emit('midi_input_stop')
        
        received = self.socketio_client.get_received()
        
        # Find the midi_input_stopped event
        stop_event = None
        for event in received:
            if event['name'] == 'midi_input_stopped':
                stop_event = event
                break
        
        self.assertIsNotNone(stop_event)
        
        # Verify service is stopped
        self.assertFalse(self.usb_midi_service.is_listening)
    
    @patch('usb_midi_service.mido')
    def test_end_to_end_midi_to_led_flow(self, mock_mido):
        """Test complete MIDI input to LED output flow"""
        mock_port = Mock()
        mock_mido.open_input.return_value = mock_port
        
        # Start MIDI input
        success = self.usb_midi_service.start_listening('Test Device')
        self.assertTrue(success)
        
        # Simulate MIDI note_on message
        mock_msg = Mock()
        mock_msg.type = 'note_on'
        mock_msg.note = 60  # Middle C
        mock_msg.velocity = 100
        
        # Process the message
        self.usb_midi_service._process_midi_message(mock_msg)
        
        # Verify LED was turned on
        expected_led_index = 39  # Middle C maps to LED 39
        base_color = self.usb_midi_service._get_note_color(60)
        brightness = self.usb_midi_service._velocity_to_brightness(100)
        expected_color = tuple(int(c * brightness) for c in base_color)
        
        self.mock_led_controller.turn_on_led.assert_called_with(
            expected_led_index, expected_color, auto_show=True
        )
        
        # Verify note is tracked
        self.assertIn(60, self.usb_midi_service.active_notes)
        
        # Simulate MIDI note_off message
        mock_msg_off = Mock()
        mock_msg_off.type = 'note_off'
        mock_msg_off.note = 60
        mock_msg_off.velocity = 0
        
        # Process the note_off message
        self.usb_midi_service._process_midi_message(mock_msg_off)
        
        # Verify LED was turned off
        self.mock_led_controller.turn_off_led.assert_called_with(
            expected_led_index, auto_show=True
        )
        
        # Verify note is no longer tracked
        self.assertNotIn(60, self.usb_midi_service.active_notes)
    
    @patch('usb_midi_service.mido')
    def test_websocket_midi_events_broadcast(self, mock_mido):
        """Test that MIDI events are properly broadcast via WebSocket"""
        mock_port = Mock()
        mock_mido.open_input.return_value = mock_port
        
        # Start MIDI input
        self.usb_midi_service.start_listening('Test Device')
        
        # Clear any previous events
        self.socketio_client.get_received()
        
        # Simulate MIDI note_on message
        mock_msg = Mock()
        mock_msg.type = 'note_on'
        mock_msg.note = 64  # E4
        mock_msg.velocity = 80
        mock_msg.channel = 0  # Set proper channel value
        
        # Process the message
        self.usb_midi_service._process_midi_message(mock_msg)
        
        # Give a small delay for WebSocket emission
        time.sleep(0.1)
        
        # Check for WebSocket events
        received = self.websocket_events
        
        # Find the midi_input event
        note_event = None
        for event in received:
            if event['name'] == 'midi_input':
                note_event = event
                break
        
        self.assertIsNotNone(note_event, "MIDI note event should be broadcast via WebSocket")
        
        event_data = note_event['args'][0]
        self.assertEqual(event_data['event_type'], 'note_on')
        self.assertEqual(event_data['note'], 64)
        self.assertEqual(event_data['velocity'], 80)
        self.assertEqual(event_data['type'], 'midi_input_event')
    
    @patch('usb_midi_service.mido')
    def test_error_handling_invalid_device(self, mock_mido):
        """Test error handling for invalid MIDI device"""
        mock_mido.open_input.side_effect = Exception("Device not found")
        
        # Test API error handling
        start_data = {'device_name': 'Invalid Device'}
        response = self.client.post(
            '/api/midi-input/start',
            data=json.dumps(start_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        
        # Test WebSocket error handling
        self.socketio_client.emit('midi_input_start', {'device_name': 'Invalid Device'})
        
        received = self.socketio_client.get_received()
        
        # Find the error event
        error_event = None
        for event in received:
            if event['name'] == 'error':
                error_event = event
                break
        
        self.assertIsNotNone(error_event)
        self.assertIn('message', error_event['args'][0])
    
    def test_concurrent_websocket_connections(self):
        """Test handling multiple WebSocket connections"""
        # Create multiple test clients
        client1 = self.socketio.test_client(self.app)
        client2 = self.socketio.test_client(self.app)
        
        with patch('usb_midi_service.mido') as mock_mido:
            mock_mido.get_input_names.return_value = ['Device1', 'Device2']
            
            # Both clients request device list
            client1.emit('get_midi_devices')
            client2.emit('get_midi_devices')
            
            # Both should receive the response
            received1 = client1.get_received()
            received2 = client2.get_received()
            
            self.assertTrue(len(received1) > 0)
            self.assertTrue(len(received2) > 0)
            
            # Find midi_devices events
            devices_event1 = next((e for e in received1 if e['name'] == 'midi_devices'), None)
            devices_event2 = next((e for e in received2 if e['name'] == 'midi_devices'), None)
            
            self.assertIsNotNone(devices_event1)
            self.assertIsNotNone(devices_event2)
            
            # Both should have the same device list
            self.assertEqual(
                devices_event1['args'][0]['devices'],
                devices_event2['args'][0]['devices']
            )

if __name__ == '__main__':
    unittest.main()