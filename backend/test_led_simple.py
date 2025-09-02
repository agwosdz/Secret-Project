#!/usr/bin/env python3
import os
import time

# Set environment variables for Pi Zero 2 W
os.environ['BLINKA_FORCEBOARD'] = 'RASPBERRY_PI_ZERO_2_W'
os.environ['BLINKA_USE_GPIOMEM'] = '1'

print(f"BLINKA_FORCEBOARD: {os.environ.get('BLINKA_FORCEBOARD')}")
print(f"BLINKA_USE_GPIOMEM: {os.environ.get('BLINKA_USE_GPIOMEM')}")

try:
    import board
    print(f"Board detected: {board.board_id}")
    
    import neopixel
    print("Creating NeoPixel object...")
    pixels = neopixel.NeoPixel(board.D18, 10)
    
    print("Testing LED - Red")
    pixels[0] = (255, 0, 0)
    pixels.show()
    time.sleep(1)
    
    print("Testing LED - Green")
    pixels[0] = (0, 255, 0)
    pixels.show()
    time.sleep(1)
    
    print("Testing LED - Blue")
    pixels[0] = (0, 0, 255)
    pixels.show()
    time.sleep(1)
    
    print("Turning off LED")
    pixels.fill((0, 0, 0))
    pixels.show()
    
    print("✓ LED test completed successfully!")
    
except Exception as e:
    print(f"✗ LED test failed: {e}")
    import traceback
    traceback.print_exc()