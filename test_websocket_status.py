#!/usr/bin/env python3
"""
Test script to verify WebSocket MIDI status updates
"""

import socketio
import time
import json

def test_websocket_status():
    # Create Socket.IO client
    sio = socketio.Client()
    
    @sio.event
    def connect():
        print("Connected to WebSocket")
        print("Requesting current status...")
        # Request status update
        sio.emit('get_status')
        print("Waiting for status updates... (Press Ctrl+C to exit)")
    
    @sio.event
    def disconnect():
        print("Disconnected from WebSocket")
    
    @sio.event
    def midi_manager_status(data):
        print("\n=== MIDI Manager Status Update ===")
        print(json.dumps(data, indent=2))
        
        # Check if the new structure is present
        if 'sources' in data:
            if 'USB' in data['sources']:
                usb = data['sources']['USB']
                print(f"\nUSB Status:")
                print(f"  Connected: {usb.get('connected', 'MISSING')}")
                print(f"  Device Name: {usb.get('device_name', 'MISSING')}")
                print(f"  Listening: {usb.get('listening', 'MISSING')}")
                print(f"  Available: {usb.get('available', 'MISSING')}")
            
            if 'RTP_MIDI' in data['sources']:
                rtp = data['sources']['RTP_MIDI']
                print(f"\nRTP MIDI Status:")
                print(f"  Connected: {rtp.get('connected', 'MISSING')}")
                print(f"  Active Sessions: {len(rtp.get('active_sessions', []))}")
                print(f"  Listening: {rtp.get('listening', 'MISSING')}")
                print(f"  Available: {rtp.get('available', 'MISSING')}")
        else:
            print("ERROR: 'sources' field missing from status update!")
    
    @sio.event
    def device_status(data):
        print("\n=== Device Status Update ===")
        print(json.dumps(data, indent=2))
    
    @sio.event
    def rtpmidi_status(data):
        print("\n=== RTP MIDI Status Update ===")
        print(json.dumps(data, indent=2))
    
    try:
        # Connect to the backend
        sio.connect('http://localhost:5001')
        
        # Wait for status updates
        print("Waiting for status updates... (Press Ctrl+C to exit)")
        time.sleep(10)
        
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sio.disconnect()

if __name__ == '__main__':
    test_websocket_status()