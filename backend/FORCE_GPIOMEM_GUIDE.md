# GPIO Access and Permissions Guide for rpi_ws281x

This guide explains GPIO access methods and permission requirements for the rpi_ws281x library on Raspberry Pi.

## rpi_ws281x Library Overview

The `rpi_ws281x` library provides direct hardware access for WS281x LED strips with better performance than CircuitPython alternatives.

## Permission Requirements

- **Root Access**: rpi_ws281x typically requires root privileges for direct hardware access
- **GPIO Group**: Alternative to root - add user to gpio group
- **Hardware PWM**: Uses hardware PWM for precise timing control
- **DMA Access**: Requires DMA channel access for efficient data transfer

## Setup Methods

### Method 1: Run with sudo (Recommended for testing)

```bash
sudo python3 your_led_script.py
```

### Method 2: Add User to GPIO Group

```bash
sudo usermod -a -G gpio $USER
# Log out and back in for changes to take effect
```

### Method 3: Set GPIO Permissions

```bash
# Check current permissions
ls -la /dev/gpiomem

# Set permissions (temporary)
sudo chmod 666 /dev/gpiomem
```

### Method 4: Systemd Service Configuration

For production deployment, configure your systemd service to run with appropriate permissions:

```ini
[Unit]
Description=LED Controller Service
After=network.target

[Service]
Type=simple
User=pi
Group=gpio
WorkingDirectory=/home/pi/your-project
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Method 5: Shell Script Wrapper

Create a wrapper script for easier execution:

```bash
#!/bin/bash
# Check if running as root or in gpio group
if [ "$EUID" -ne 0 ] && ! groups | grep -q gpio; then
    echo "Running with sudo for GPIO access..."
    sudo python3 "$@"
else
    python3 "$@"
fi
```

## Implementation in This Project

### 1. LED Controller with rpi_ws281x

The `led_controller.py` uses the rpi_ws281x library for direct hardware access:

```python
from rpi_ws281x import PixelStrip, Color
import RPi.GPIO as GPIO

# LED strip configuration
LED_COUNT = 144
LED_PIN = 19          # GPIO pin (19 uses PWM!)
LED_FREQ_HZ = 800000  # LED signal frequency
LED_DMA = 10          # DMA channel
LED_BRIGHTNESS = 255  # Brightness (0-255)
LED_INVERT = False    # Signal inversion
LED_CHANNEL = 1       # PWM channel

# Initialize the LED strip
pixels = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
pixels.begin()
```

### 2. Permission Handling

The application checks for proper permissions and provides helpful error messages:

```python
try:
    pixels = PixelStrip(...)
    pixels.begin()
except Exception as e:
    if "Permission denied" in str(e):
        print("GPIO permission denied. Try running with sudo or add user to gpio group.")
    raise
```

### 3. Testing Scripts

All testing scripts include proper error handling for permission issues and provide guidance for resolution.

## Verification

### Check Which Device is Being Used

```bash
# List GPIO devices
ls -la /dev/gpio*

# Check permissions
ls -la /dev/gpiomem /dev/mem

# See which processes are using the devices
sudo lsof /dev/gpiomem
sudo lsof /dev/mem
```

### Test GPIO Access

```bash
# Run the force gpiomem example
python3 force_gpiomem_example.py

# Run LED troubleshoot to check permissions
python3 led_troubleshoot.py

# Test device functionality
python3 test_led_device.py --quick
```

## Troubleshooting

### Permission Denied Errors

```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Set proper permissions on gpiomem
sudo chmod 666 /dev/gpiomem

# Logout and login again
```

### Environment Variables Not Working

1. **Check if variables are set**:
   ```bash
   echo $BLINKA_USE_GPIOMEM
   ```

2. **Set variables in the right place**:
   - For systemd services: in the service file
   - For shell scripts: before running Python
   - For Python scripts: before importing GPIO libraries

3. **Restart services after changes**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart piano-led-visualizer
   ```

### Still Using /dev/mem

1. **Check library versions**:
   ```bash
   pip3 list | grep -E "adafruit|blinka|neopixel"
   ```

2. **Update libraries**:
   ```bash
   pip3 install --upgrade adafruit-blinka adafruit-circuitpython-neopixel
   ```

3. **Try alternative approach**:
   ```bash
   # Use pigpio instead
   export GPIOZERO_PIN_FACTORY=pigpio
   sudo systemctl start pigpiod
   ```

## Raspberry Pi Model Configuration

Adjust `BLINKA_FORCEBOARD` for your specific Pi model:

- **Pi 4**: `RASPBERRY_PI_4B`
- **Pi 3**: `RASPBERRY_PI_3B_PLUS` or `RASPBERRY_PI_3B`
- **Pi Zero**: `RASPBERRY_PI_ZERO` or `RASPBERRY_PI_ZERO_W`
- **Pi 2**: `RASPBERRY_PI_2B`
- **Pi 1**: `RASPBERRY_PI_B_PLUS` or `RASPBERRY_PI_B_REV2`

## Security Benefits

| Device | Access Level | Root Required | Risk Level |
|--------|-------------|---------------|------------|
| `/dev/mem` | Full system memory | Yes | High |
| `/dev/gpiomem` | GPIO registers only | No | Low |

## Testing the Implementation

After implementing these changes:

1. **Deploy to Pi**:
   ```bash
   ./scripts/deploy-to-pi.sh
   ```

2. **Check service status**:
   ```bash
   sudo systemctl status piano-led-visualizer
   ```

3. **Test LED functionality**:
   ```bash
   python3 backend/led_manual_test.py
   ```

4. **Verify device usage**:
   ```bash
   sudo lsof /dev/gpiomem  # Should show your process
   sudo lsof /dev/mem      # Should be empty or show system processes only
   ```

The implementation ensures that your LED controller will always use the safer `/dev/gpiomem` device for GPIO access.