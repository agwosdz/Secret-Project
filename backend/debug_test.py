#!/usr/bin/env python3

import sys
sys.path.append('.')

from unittest.mock import Mock, patch
from usb_midi_service import USBMIDIInputService

# Create mocks
mock_led_controller = Mock()
mock_websocket_callback = Mock()

# Create service
service = USBMIDIInputService(
    led_controller=mock_led_controller,
    websocket_callback=mock_websocket_callback
)

# Create mock MIDI message
mock_msg = Mock()
mock_msg.type = 'note_on'
mock_msg.note = 60
mock_msg.velocity = 64
mock_msg.channel = 0

print("Before processing:")
print(f"LED controller calls: {mock_led_controller.method_calls}")

# Process the message
with patch('usb_midi_service.mido'):
    service.start_listening('Test Device')
    service._process_midi_message(mock_msg)

print("\nAfter processing:")
print(f"LED controller calls: {mock_led_controller.method_calls}")
print(f"Turn on LED calls: {mock_led_controller.turn_on_led.call_args_list}")

# Check what color and brightness methods return
print(f"\nNote color for 60: {service._get_note_color(60)}")
print(f"Velocity brightness for 64: {service._velocity_to_brightness(64)}")

# Calculate expected color
base_color = service._get_note_color(60)
brightness = service._velocity_to_brightness(64)
expected_color = tuple(int(c * brightness) for c in base_color)
print(f"Expected final color: {expected_color}")