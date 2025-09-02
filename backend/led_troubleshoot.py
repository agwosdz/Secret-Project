#!/usr/bin/env python3
"""
LED Hardware Troubleshooting Script
Diagnoses common issues with WS2812B LED strips on Raspberry Pi using rpi_ws281x

Usage:
    python3 led_troubleshoot.py
"""

import sys
import os
import subprocess
import logging
from typing import List, Dict, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_system_info():
    """Check basic system information."""
    logger.info("=== SYSTEM INFORMATION ===")
    
    try:
        # Check OS
        with open('/etc/os-release', 'r') as f:
            os_info = f.read()
            for line in os_info.split('\n'):
                if line.startswith('PRETTY_NAME='):
                    os_name = line.split('=')[1].strip('"')
                    logger.info(f"Operating System: {os_name}")
                    break
    except Exception as e:
        logger.warning(f"Could not read OS info: {e}")
    
    try:
        # Check Python version
        python_version = sys.version.split()[0]
        logger.info(f"Python Version: {python_version}")
        
        # Check if running as root/sudo
        if os.geteuid() == 0:
            logger.info("✓ Running with root privileges")
        else:
            logger.warning("⚠ Not running as root - GPIO access may be limited")
            logger.info("  Try running with: sudo python3 led_troubleshoot.py")
    
    except Exception as e:
        logger.error(f"Error checking system info: {e}")

def check_gpio_permissions():
    """Check GPIO permissions and groups."""
    logger.info("\n=== GPIO PERMISSIONS ===")
    
    try:
        # Check if user is in gpio group
        result = subprocess.run(['groups'], capture_output=True, text=True)
        groups = result.stdout.strip()
        
        if 'gpio' in groups:
            logger.info("✓ User is in 'gpio' group")
        else:
            logger.warning("⚠ User is NOT in 'gpio' group")
            logger.info("  Fix: sudo usermod -a -G gpio $USER")
            logger.info("  Then logout and login again")
        
        # Check GPIO device permissions
        gpio_devices = ['/dev/gpiomem', '/dev/mem']
        for device in gpio_devices:
            if os.path.exists(device):
                stat = os.stat(device)
                permissions = oct(stat.st_mode)[-3:]
                logger.info(f"GPIO device {device}: permissions {permissions}")
            else:
                logger.warning(f"GPIO device {device} not found")
    
    except Exception as e:
        logger.error(f"Error checking GPIO permissions: {e}")

def check_required_packages():
    """Check if required Python packages are installed."""
    logger.info("\n=== PYTHON PACKAGES ===")
    
    required_packages = [
        ('rpi_ws281x', 'rpi_ws281x'),
        ('RPi.GPIO', 'RPi.GPIO'),
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            logger.info(f"✓ {package_name} is installed")
        except ImportError:
            logger.error(f"✗ {package_name} is NOT installed")
            missing_packages.append(package_name)
    
    if missing_packages:
        logger.info("\nTo install missing packages:")
        for package in missing_packages:
            logger.info(f"  pip3 install {package}")
        logger.info("Or install all at once:")
        logger.info(f"  pip3 install {' '.join(missing_packages)}")
    
    return len(missing_packages) == 0

def check_gpio_configuration():
    """Check GPIO configuration and SPI settings."""
    logger.info("\n=== GPIO CONFIGURATION ===")
    
    try:
        # Check if SPI is enabled (sometimes interferes with GPIO)
        config_files = ['/boot/config.txt', '/boot/firmware/config.txt']
        config_found = False
        
        for config_file in config_files:
            if os.path.exists(config_file):
                config_found = True
                logger.info(f"Checking {config_file}...")
                
                with open(config_file, 'r') as f:
                    config_content = f.read()
                
                # Check SPI settings
                if 'dtparam=spi=on' in config_content:
                    logger.warning("⚠ SPI is enabled - may interfere with GPIO")
                    logger.info("  Consider disabling SPI if not needed")
                else:
                    logger.info("✓ SPI is disabled")
                
                # Check GPIO settings
                if 'gpio=' in config_content:
                    logger.info("GPIO configuration found in config.txt")
                
                break
        
        if not config_found:
            logger.warning("Could not find boot config file")
    
    except Exception as e:
        logger.error(f"Error checking GPIO configuration: {e}")

def check_hardware_connections():
    """Provide guidance on hardware connections."""
    logger.info("\n=== HARDWARE CONNECTION GUIDE ===")
    
    logger.info("Standard WS2812B LED strip connections:")
    logger.info("  LED Strip    ->  Raspberry Pi")
    logger.info("  VCC/5V       ->  5V (Pin 2 or 4)")
    logger.info("  GND          ->  GND (Pin 6, 9, 14, 20, 25, 30, 34, or 39)")
    logger.info("  DIN/Data     ->  GPIO18 (Pin 12) - Default")
    logger.info("")
    logger.info("Alternative GPIO pins for data:")
    logger.info("  GPIO12 (Pin 32), GPIO13 (Pin 33), GPIO19 (Pin 35)")
    logger.info("")
    logger.info("Power considerations:")
    logger.info("  - For >10 LEDs, use external 5V power supply")
    logger.info("  - Connect LED strip GND to both Pi GND and power supply GND")
    logger.info("  - Add 330Ω resistor between Pi GPIO and LED data pin (optional but recommended)")
    logger.info("  - Add 1000µF capacitor between power supply +5V and GND (recommended)")

def test_gpio_basic():
    """Test basic GPIO functionality."""
    logger.info("\n=== BASIC GPIO TEST ===")
    
    try:
        import board
        logger.info("✓ board module imported successfully")
        
        # Test GPIO pin access
        pin = board.D18
        logger.info(f"✓ GPIO18 (D18) accessible: {pin}")
        
        # List available pins
        available_pins = [attr for attr in dir(board) if attr.startswith('D')]
        logger.info(f"Available GPIO pins: {', '.join(available_pins)}")
        
        return True
        
    except ImportError as e:
        logger.error(f"✗ Cannot import board module: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ GPIO test failed: {e}")
        return False

def test_led_basic():
    """Test basic LED functionality using rpi_ws281x."""
    logger.info("\n=== LED BASIC TEST (rpi_ws281x) ===")
    
    try:
        from rpi_ws281x import PixelStrip, Color
        import RPi.GPIO as GPIO
        
        logger.info("✓ rpi_ws281x module imported successfully")
        
        # Try to create a PixelStrip object (this will fail if hardware issues exist)
        logger.info("Attempting to create PixelStrip object...")
        
        # LED strip configuration
        LED_COUNT = 1         # Number of LED pixels
        LED_PIN = 18          # GPIO pin connected to the pixels (18 uses PWM!)
        LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
        LED_DMA = 10          # DMA channel to use for generating signal (try 10)
        LED_BRIGHTNESS = 25   # Set to 0 for darkest and 255 for brightest (10% = 25)
        LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
        LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
        
        pixels = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        pixels.begin()
        logger.info("✓ PixelStrip object created successfully")
        
        # Try to set a pixel
        pixels.setPixelColor(0, Color(255, 0, 0))  # Red
        pixels.show()
        logger.info("✓ Pixel set and show() called successfully")
        
        # Turn off
        pixels.setPixelColor(0, Color(0, 0, 0))
        pixels.show()
        
        logger.info("✓ LED test completed successfully")
        
        return True
        
    except ImportError as e:
        logger.error(f"✗ Cannot import required modules: {e}")
        logger.info("Install with: pip3 install rpi_ws281x")
        return False
    except Exception as e:
        logger.error(f"✗ LED test failed: {e}")
        logger.info("Common causes:")
        logger.info("  - Incorrect wiring")
        logger.info("  - Insufficient power supply")
        logger.info("  - Wrong GPIO pin")
        logger.info("  - Permission issues (try running with sudo)")
        logger.info("  - LED strip not compatible with WS2812B protocol")
        return False

def run_diagnostics():
    """Run comprehensive diagnostics."""
    logger.info("🔧 LED HARDWARE TROUBLESHOOTING TOOL")
    logger.info("====================================\n")
    
    # System checks
    check_system_info()
    check_gpio_permissions()
    
    # Package checks
    packages_ok = check_required_packages()
    if not packages_ok:
        logger.error("\n❌ Missing required packages - install them first!")
        return False
    
    # Configuration checks
    check_gpio_configuration()
    
    # Hardware connection guide
    check_hardware_connections()
    
    # Basic functionality tests
    gpio_ok = test_gpio_basic()
    if not gpio_ok:
        logger.error("\n❌ Basic GPIO test failed - check permissions and packages")
        return False
    
    led_ok = test_led_basic()
    if not led_ok:
        logger.error("\n❌ LED test failed - check hardware connections")
        return False
    
    logger.info("\n✅ ALL BASIC TESTS PASSED!")
    logger.info("Your LED hardware setup appears to be working correctly.")
    logger.info("\nNext steps:")
    logger.info("  1. Run: python3 test_led_device.py --quick")
    logger.info("  2. If that works, run: python3 test_led_device.py")
    
    return True

def main():
    """Main function."""
    try:
        success = run_diagnostics()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\nDiagnostics interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()