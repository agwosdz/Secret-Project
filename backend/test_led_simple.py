#!/usr/bin/env python3
import os
import time

print("Simple LED test using rpi_ws281x library")

try:
    from rpi_ws281x import PixelStrip, Color
    
    # LED strip configuration
    LED_COUNT = 10        # Number of LED pixels
    LED_PIN = 19          # GPIO pin connected to the pixels (19 uses PWM!)
    LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
    LED_DMA = 10          # DMA channel to use for generating signal (try 10)
    LED_BRIGHTNESS = 76   # Set to 0 for darkest and 255 for brightest (30% = 76)
    LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
    LED_CHANNEL = 1       # set to '1' for GPIOs 13, 19, 41, 45 or 53
    
    print("Creating PixelStrip object...")
    pixels = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    pixels.begin()
    
    print("Testing LED - Red")
    pixels.setPixelColor(0, Color(255, 0, 0))
    pixels.show()
    time.sleep(1)
    
    print("Testing LED - Green")
    pixels.setPixelColor(0, Color(0, 255, 0))
    pixels.show()
    time.sleep(1)
    
    print("Testing LED - Blue")
    pixels.setPixelColor(0, Color(0, 0, 255))
    pixels.show()
    time.sleep(1)
    
    print("Turning off LED")
    for i in range(LED_COUNT):
        pixels.setPixelColor(i, Color(0, 0, 0))
    pixels.show()
    
    print("✓ LED test completed successfully!")
    
except Exception as e:
    print(f"✗ LED test failed: {e}")
    import traceback
    traceback.print_exc()