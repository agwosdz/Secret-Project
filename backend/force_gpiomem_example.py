#!/usr/bin/env python3
"""
Example: Using rpi_ws281x with proper GPIO permissions

This script demonstrates how to use rpi_ws281x library for LED control,
which provides better performance and more reliable GPIO access.
"""

import os
import sys

print("Testing rpi_ws281x library for LED control...")

# Now import the hardware libraries
try:
    from rpi_ws281x import PixelStrip, Color
    import RPi.GPIO as GPIO
    print("✓ Hardware libraries imported successfully")
    
    # Test GPIO access
    print("\nTesting GPIO access...")
    
    # LED strip configuration
    LED_COUNT = 10        # Number of LED pixels
    LED_PIN = 19          # GPIO pin connected to the pixels (19 uses PWM!)
    LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
    LED_DMA = 10          # DMA channel to use for generating signal (try 10)
    LED_BRIGHTNESS = 25   # Set to 0 for darkest and 255 for brightest (10% = 25)
    LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
    LED_CHANNEL = 1       # set to '1' for GPIOs 13, 19, 41, 45 or 53
    
    # Create a PixelStrip instance
    pixels = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    pixels.begin()
    print("✓ PixelStrip initialized successfully")
    
    # Test setting a pixel
    pixels.setPixelColor(0, Color(255, 0, 0))  # Red
    pixels.show()
    print("✓ LED control test successful")
    
    # Cleanup
    for i in range(LED_COUNT):
        pixels.setPixelColor(i, Color(0, 0, 0))
    pixels.show()
    print("✓ Cleanup completed")
    
except ImportError as e:
    print(f"✗ Failed to import hardware libraries: {e}")
    print("Make sure you're running on a Raspberry Pi with required packages installed")
    print("Install with: pip3 install rpi_ws281x")
except Exception as e:
    print(f"✗ Error during GPIO access: {e}")
    print("This might indicate permission issues or hardware problems")
    print("Try running with sudo or check GPIO permissions")

print("\n" + "="*60)
print("RPI_WS281X LIBRARY - IMPLEMENTATION OPTIONS")
print("="*60)

print("""
1. INSTALLATION:
   Install the rpi_ws281x library:
   
   pip3 install rpi_ws281x
   
   This library provides better performance and more reliable
   GPIO access compared to CircuitPython libraries.

2. PERMISSIONS:
   The rpi_ws281x library typically requires root privileges
   for direct hardware access:
   
   sudo python3 your_script.py
   
   Or add your user to the gpio group:
   sudo usermod -a -G gpio $USER

3. GPIO PIN CONFIGURATION:
   Pin 19 (PWM1) is recommended for best performance:
   - Uses hardware PWM for precise timing
   - Supports higher LED counts
   - More stable signal generation

4. ALTERNATIVE PINS:
   Other PWM-capable pins can be used:
   - Pin 12 (PWM0 alt)
   - Pin 13 (PWM1)
   - Pin 19 (PWM1 alt)

5. TROUBLESHOOTING:
   If you encounter permission issues:
   
   ls -la /dev/gpiomem
   sudo chmod 666 /dev/gpiomem
   
   Check if PWM is available:
   ls -la /sys/class/pwm/
""")

print("\n" + "="*60)
print("IMPLEMENTATION IN YOUR PROJECT")
print("="*60)

print("""
To implement rpi_ws281x in your LED controller:

1. Update led_controller.py imports:

   from rpi_ws281x import PixelStrip, Color
   import RPi.GPIO as GPIO

2. Replace NeoPixel initialization with PixelStrip:

   # Old neopixel code:
   # pixels = neopixel.NeoPixel(board.D18, num_pixels, brightness=0.1)
   
   # New rpi_ws281x code:
   pixels = PixelStrip(num_pixels, 18, 800000, 10, False, 255, 0)
   pixels.begin()

3. Update LED control methods:

   # Old: pixels[i] = (r, g, b)
   # New: pixels.setPixelColor(i, Color(r, g, b))
   
   # Old: pixels.fill((r, g, b))
   # New: for i in range(num_pixels): pixels.setPixelColor(i, Color(r, g, b))

4. Test with this script to verify it works before implementing.

5. Monitor system logs for any GPIO-related errors:
   
   sudo dmesg | grep -i gpio
   sudo journalctl -f | grep -i gpio

Note: rpi_ws281x provides better performance and more reliable
hardware control compared to CircuitPython libraries.
""")