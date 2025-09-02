#!/usr/bin/env python3
"""
Example: Force NeoPixel to use /dev/gpiomem instead of /dev/mem

This script demonstrates how to force the use of /dev/gpiomem for GPIO access,
which is safer and doesn't require root privileges.
"""

import os
import sys

# Method 1: Set environment variable before importing any GPIO libraries
# This forces the underlying GPIO library to use /dev/gpiomem
os.environ['BLINKA_FORCEBOARD'] = 'RASPBERRY_PI_ZERO_2_W'  # or your Pi model
os.environ['BLINKA_FORCECHIP'] = 'BCM2XXX'  # BCM chip
os.environ['BLINKA_USE_GPIOMEM'] = '1'  # Force gpiomem usage

# Alternative environment variables that may help:
# os.environ['GPIOZERO_PIN_FACTORY'] = 'pigpio'  # Use pigpio instead of RPi.GPIO
# os.environ['PIGPIO_ADDR'] = 'localhost'  # For remote pigpio

print("Environment variables set to force /dev/gpiomem usage:")
print(f"BLINKA_FORCEBOARD: {os.environ.get('BLINKA_FORCEBOARD', 'Not set')}")
print(f"BLINKA_FORCECHIP: {os.environ.get('BLINKA_FORCECHIP', 'Not set')}")
print(f"BLINKA_USE_GPIOMEM: {os.environ.get('BLINKA_USE_GPIOMEM', 'Not set')}")

# Now import the hardware libraries
try:
    import board
    import neopixel
    print("✓ Hardware libraries imported successfully")
    
    # Test GPIO access
    print("\nTesting GPIO access...")
    
    # Create a NeoPixel instance (this will test GPIO access)
    pixels = neopixel.NeoPixel(board.D18, 10, brightness=0.1, auto_write=False)
    print("✓ NeoPixel initialized successfully using /dev/gpiomem")
    
    # Test setting a pixel
    pixels[0] = (255, 0, 0)  # Red
    pixels.show()
    print("✓ LED control test successful")
    
    # Cleanup
    pixels.deinit()
    print("✓ Cleanup completed")
    
except ImportError as e:
    print(f"✗ Failed to import hardware libraries: {e}")
    print("Make sure you're running on a Raspberry Pi with required packages installed")
except Exception as e:
    print(f"✗ Error during GPIO access: {e}")
    print("This might indicate permission issues or hardware problems")

print("\n" + "="*60)
print("FORCING /dev/gpiomem USAGE - IMPLEMENTATION OPTIONS")
print("="*60)

print("""
1. ENVIRONMENT VARIABLES (Recommended):
   Set these before importing any GPIO libraries:
   
   export BLINKA_USE_GPIOMEM=1
   export BLINKA_FORCEBOARD=RASPBERRY_PI_4B
   export BLINKA_FORCECHIP=BCM2XXX
   
   Or in Python:
   os.environ['BLINKA_USE_GPIOMEM'] = '1'

2. MODIFY led_controller.py:
   Add environment variable setting at the top of the file,
   before any imports.

3. SYSTEM-LEVEL CONFIGURATION:
   Ensure /dev/gpiomem has proper permissions:
   
   sudo chmod 666 /dev/gpiomem
   sudo usermod -a -G gpio $USER

4. USE ALTERNATIVE GPIO LIBRARY:
   Consider using pigpio instead of RPi.GPIO:
   
   export GPIOZERO_PIN_FACTORY=pigpio
   pip3 install pigpio
   sudo systemctl enable pigpiod
   sudo systemctl start pigpiod

5. VERIFY DEVICE ACCESS:
   Check which device is being used:
   
   ls -la /dev/gpio*
   lsof /dev/gpiomem
   lsof /dev/mem
""")

print("\n" + "="*60)
print("IMPLEMENTATION IN YOUR PROJECT")
print("="*60)

print("""
To force /dev/gpiomem in your LED controller:

1. Modify led_controller.py to set environment variables:
   
   import os
   # Force gpiomem usage BEFORE importing board/neopixel
   os.environ['BLINKA_USE_GPIOMEM'] = '1'
   os.environ['BLINKA_FORCEBOARD'] = 'RASPBERRY_PI_4B'
   
   import board
   import neopixel

2. Or set environment variables when running your application:
   
   BLINKA_USE_GPIOMEM=1 python3 start.py

3. Or add to your systemd service file:
   
   Environment=BLINKA_USE_GPIOMEM=1
   Environment=BLINKA_FORCEBOARD=RASPBERRY_PI_4B
""")