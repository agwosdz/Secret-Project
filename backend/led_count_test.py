#!/usr/bin/env python3
"""
LED Count Test Script
Tests individual LEDs to identify hardware issues
"""

import time
import logging
from rpi_ws281x import PixelStrip, Color

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# LED strip configuration
LED_COUNT = 30  # Start with a small count to test
LED_PIN = 19
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 76  # 30% brightness
LED_INVERT = False
LED_CHANNEL = 1

def test_individual_leds(strip, count=30):
    """Test individual LEDs one by one"""
    logger.info(f"Testing individual LEDs (0-{count-1})...")
    
    # Clear all LEDs first
    for i in range(count):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()
    time.sleep(0.5)
    
    # Test each LED individually
    for i in range(count):
        logger.info(f"Testing LED {i}...")
        
        # Turn on current LED (blue)
        strip.setPixelColor(i, Color(0, 0, 255))
        strip.show()
        time.sleep(0.5)
        
        # Turn off current LED
        strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
        time.sleep(0.2)

def test_led_24_specifically(strip):
    """Test LED 24 specifically since that's the one working"""
    logger.info("Testing LED 24 specifically...")
    
    # Clear all
    for i in range(50):  # Clear more than needed
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()
    time.sleep(1)
    
    # Test LED 24 with different colors
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Yellow
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Cyan
        (255, 255, 255) # White
    ]
    
    for color in colors:
        r, g, b = color
        logger.info(f"LED 24: Setting color to RGB({r}, {g}, {b})")
        strip.setPixelColor(24, Color(r, g, b))
        strip.show()
        time.sleep(1)
    
    # Turn off
    strip.setPixelColor(24, Color(0, 0, 0))
    strip.show()

def test_surrounding_leds(strip):
    """Test LEDs around position 24"""
    logger.info("Testing LEDs around position 24...")
    
    # Clear all
    for i in range(50):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()
    time.sleep(0.5)
    
    # Test LEDs 20-29
    for i in range(20, 30):
        logger.info(f"Testing LED {i}...")
        strip.setPixelColor(i, Color(255, 0, 0))  # Red
        strip.show()
        time.sleep(0.8)
        strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
        time.sleep(0.2)

def main():
    """Main test function"""
    logger.info("Starting LED count test...")
    
    try:
        # Create PixelStrip object
        strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        strip.begin()
        
        logger.info(f"LED strip initialized with {LED_COUNT} pixels")
        
        # Run tests
        test_led_24_specifically(strip)
        time.sleep(2)
        
        test_surrounding_leds(strip)
        time.sleep(2)
        
        test_individual_leds(strip, 30)
        
        # Final cleanup
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
        
        logger.info("LED count test completed")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())