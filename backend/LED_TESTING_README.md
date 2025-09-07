# LED Hardware Testing Guide

This guide provides comprehensive tools and instructions for testing WS281x LED strips on Raspberry Pi using the rpi_ws281x library.

## Quick Start

If your LEDs aren't lighting up, follow these steps in order:

1. **Run the troubleshooting tool first:**
   ```bash
   cd /path/to/backend
   sudo python3 led_troubleshoot.py
   ```

2. **If troubleshooting passes, run a quick hardware test:**
   ```bash
   sudo python3 test_led_device.py --quick
   ```

3. **If quick test passes, run comprehensive tests:**
   ```bash
   sudo python3 test_led_device.py
   ```

## Testing Tools Overview

### 1. `led_troubleshoot.py` - Diagnostic Tool

**Purpose:** Diagnoses common hardware and software issues

**Usage:**
```bash
sudo python3 led_troubleshoot.py
```

**What it checks:**
- System information and permissions
- Required Python packages (rpi_ws281x, RPi.GPIO)
- GPIO configuration
- Hardware connection guidance
- Basic GPIO and rpi_ws281x functionality

**When to use:** First step when LEDs don't work at all

### 2. `test_led_device.py` - Hardware Testing

**Purpose:** Comprehensive testing of LED hardware functionality

**Usage:**
```bash
# Quick test (3 LEDs only)
sudo python3 test_led_device.py --quick

# Full test suite
sudo python3 test_led_device.py

# Verbose output
sudo python3 test_led_device.py --verbose
```

**What it tests:**
- Individual LED control
- Color patterns (red, green, blue, white)
- Rainbow effects
- Performance benchmarks
- Error handling

**When to use:** After troubleshooting passes, to verify full functionality

### 3. `test_led_controller.py` - Unit and Device Tests

**Purpose:** Both unit tests (with mocks) and device tests

**Usage:**
```bash
# Unit tests (default)
python3 test_led_controller.py

# Device tests (requires hardware)
sudo python3 test_led_controller.py --device
```

**When to use:** 
- Unit tests: During development
- Device tests: Quick hardware verification

## Hardware Setup Requirements

### Standard Connections

| LED Strip Pin | Raspberry Pi Pin | Description |
|---------------|------------------|-------------|
| VCC/5V        | Pin 2 or 4 (5V)  | Power supply |
| GND           | Pin 6 (GND)      | Ground |
| DIN/Data      | Pin 35 (GPIO19)  | Data signal |

### Power Considerations

- **≤10 LEDs:** Can be powered from Pi's 5V pin
- **>10 LEDs:** Requires external 5V power supply
- **Always:** Connect LED strip GND to Pi GND
- **Recommended:** Add 330Ω resistor between Pi GPIO and LED data pin
- **Recommended:** Add 1000µF capacitor between power +5V and GND

### Alternative GPIO Pins

If GPIO19 doesn't work, try these alternatives:
- GPIO12 (Pin 32)
- GPIO13 (Pin 33) 
- GPIO19 (Pin 35)

Update your code:
```python
# In led_controller.py, change LED_PIN
LED_PIN = 12  # For GPIO12
LED_PIN = 13  # For GPIO13
LED_PIN = 19  # For GPIO19
```

## Software Requirements

### Required Packages

```bash
# Install required packages for rpi_ws281x
pip3 install rpi_ws281x RPi.GPIO

# Or install individually
pip3 install rpi_ws281x
pip3 install RPi.GPIO
```

### System Configuration

1. **Enable GPIO access:**
   ```bash
   sudo usermod -a -G gpio $USER
   # Logout and login again
   ```

2. **Check SPI settings (if issues persist):**
   ```bash
   sudo nano /boot/config.txt
   # Ensure SPI is disabled: dtparam=spi=off
   ```

## Common Issues and Solutions

### Issue: "Permission denied" or "GPIO not accessible"

**Solutions:**
1. Run with sudo: `sudo python3 script.py`
2. Add user to gpio group: `sudo usermod -a -G gpio $USER`
3. Set proper permissions on gpiomem device: `sudo chmod 666 /dev/gpiomem`
4. Logout and login again

### Force /dev/gpiomem Usage

This project automatically forces the use of `/dev/gpiomem` instead of `/dev/mem` for safer GPIO access. See `FORCE_GPIOMEM_GUIDE.md` for detailed information.

**Key Benefits:**
- No root privileges required
- Safer GPIO access (only GPIO registers, not full system memory)
- Reduced security risks

**Verification:**
```bash
# Check which device is being used
sudo lsof /dev/gpiomem  # Should show your LED processes
sudo lsof /dev/mem      # Should be empty or system processes only

# Test with environment variables
BLINKA_USE_GPIOMEM=1 python3 test_led_device.py --quick
```

### Issue: "No module named 'board'" or "No module named 'neopixel'"

**Solutions:**
1. Install packages: `pip3 install adafruit-circuitpython-neopixel adafruit-blinka`
2. If using virtual environment, activate it first
3. Try with sudo: `sudo pip3 install ...`

### Issue: LEDs don't light up but no errors

**Check:**
1. **Power supply:** Sufficient current for your LED count
2. **Connections:** Verify wiring matches the pin diagram
3. **LED strip type:** Ensure it's WS2812B compatible
4. **GPIO pin:** Try different pins (GPIO12, GPIO13, GPIO19)
5. **Ground connection:** LED strip GND must connect to Pi GND

### Issue: Only some LEDs work

**Possible causes:**
1. **Insufficient power:** Use external power supply
2. **Data signal integrity:** Add 330Ω resistor
3. **Damaged LEDs:** LEDs are daisy-chained, one bad LED breaks the chain
4. **Loose connections:** Check all wire connections

### Issue: LEDs flicker or show wrong colors

**Solutions:**
1. **Power supply:** Use adequate current rating
2. **Add capacitor:** 1000µF between power +5V and GND
3. **Shorter wires:** Minimize wire length for data signal
4. **Lower brightness:** Reduce power consumption

## Testing Workflow

### For New Setup

1. **Hardware check:**
   ```bash
   sudo python3 led_troubleshoot.py
   ```

2. **Quick functionality test:**
   ```bash
   sudo python3 test_led_device.py --quick
   ```

3. **Full testing:**
   ```bash
   sudo python3 test_led_device.py
   ```

### For Debugging Issues

1. **Start with troubleshooting:**
   ```bash
   sudo python3 led_troubleshoot.py
   ```

2. **If packages/permissions OK, test basic device functionality:**
   ```bash
   sudo python3 test_led_controller.py --device
   ```

3. **For comprehensive testing:**
   ```bash
   sudo python3 test_led_device.py --verbose
   ```

### For Development

1. **Unit tests (no hardware needed):**
   ```bash
   python3 test_led_controller.py
   ```

2. **Integration testing:**
   ```bash
   sudo python3 test_led_device.py
   ```

## Expected Output

### Successful Test Output

```
=== COMPREHENSIVE LED HARDWARE TEST ===
2024-01-XX XX:XX:XX - INFO - Testing hardware library availability...
2024-01-XX XX:XX:XX - INFO - ✓ board module imported successfully
2024-01-XX XX:XX:XX - INFO - ✓ neopixel module imported successfully
2024-01-XX XX:XX:XX - INFO - ✓ GPIO pin D19 available

2024-01-XX XX:XX:XX - INFO - Testing LED controller initialization...
2024-01-XX XX:XX:XX - INFO - ✓ LED controller initialized with 30 pixels
2024-01-XX XX:XX:XX - INFO - ✓ NeoPixel object created successfully

=== TEST RESULTS ===
Individual LEDs: PASS
LED Patterns: PASS
Rainbow Effect: PASS
Performance: PASS

Overall: 4/4 tests passed (100.0%)
🎉 ALL TESTS PASSED - LED hardware is fully functional!
```

### Troubleshooting Output

```
🔧 LED HARDWARE TROUBLESHOOTING TOOL
====================================

=== SYSTEM INFORMATION ===
Operating System: Raspberry Pi OS Lite (64-bit)
Python Version: 3.9.2
✓ Running with root privileges

=== GPIO PERMISSIONS ===
✓ User is in 'gpio' group
GPIO device /dev/gpiomem: permissions 664

=== PYTHON PACKAGES ===
✓ adafruit-circuitpython-neopixel is installed
✓ adafruit-blinka is installed
✓ rpi-ws281x is installed

✅ ALL BASIC TESTS PASSED!
Your LED hardware setup appears to be working correctly.
```

## Integration with Main Application

These testing tools work alongside your main LED controller:

```python
# In your main application
from led_controller import LEDController

# Initialize controller
controller = LEDController(num_pixels=30, brightness=0.3)

# Use controller methods
controller.turn_on_led(0, (255, 0, 0))  # Red
controller.turn_off_all()
controller.cleanup()
```

## Support

If you're still having issues after following this guide:

1. **Check hardware connections** against the wiring diagram
2. **Verify power supply** can handle your LED count
3. **Try different GPIO pins** if GPIO19 doesn't work
4. **Test with minimal setup** (1-3 LEDs only)
5. **Check LED strip compatibility** (must be WS2812B/NeoPixel compatible)

For additional help, run the troubleshooting tool with verbose output and check the detailed error messages.