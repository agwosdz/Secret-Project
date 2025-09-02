# Force /dev/gpiomem Usage Guide

This guide explains how to force the use of `/dev/gpiomem` instead of `/dev/mem` for GPIO access on Raspberry Pi. Using `/dev/gpiomem` is safer and doesn't require root privileges.

## Why Force /dev/gpiomem?

- **Security**: `/dev/gpiomem` provides access only to GPIO registers, not entire system memory
- **No Root Required**: Regular users can access `/dev/gpiomem` with proper permissions
- **Safer**: Reduces risk of accidentally accessing system memory
- **Recommended**: This is the preferred method for GPIO access

## Methods to Force /dev/gpiomem Usage

### Method 1: Environment Variables (Recommended)

Set these environment variables before importing any GPIO libraries:

```bash
export BLINKA_USE_GPIOMEM=1
export BLINKA_FORCEBOARD=RASPBERRY_PI_ZERO_2_W  # Adjust for your Pi model
export BLINKA_FORCECHIP=BCM2XXX
```

Or in Python (before any imports):

```python
import os
os.environ['BLINKA_USE_GPIOMEM'] = '1'
os.environ['BLINKA_FORCEBOARD'] = 'RASPBERRY_PI_4B'
os.environ['BLINKA_FORCECHIP'] = 'BCM2XXX'

# Now import GPIO libraries
import board
import neopixel
```

### Method 2: Systemd Service Configuration

Add environment variables to your systemd service file:

```ini
[Service]
Environment=BLINKA_USE_GPIOMEM=1
Environment=BLINKA_FORCEBOARD=RASPBERRY_PI_4B
Environment=BLINKA_FORCECHIP=BCM2XXX
```

### Method 3: Shell Script Wrapper

Create a wrapper script that sets environment variables:

```bash
#!/bin/bash
export BLINKA_USE_GPIOMEM=1
export BLINKA_FORCEBOARD=RASPBERRY_PI_4B
export BLINKA_FORCECHIP=BCM2XXX
python3 your_script.py
```

### Method 4: Alternative GPIO Library (pigpio)

Use pigpio instead of the default GPIO library:

```bash
# Install pigpio
sudo apt-get install pigpio python3-pigpio

# Enable pigpio daemon
sudo systemctl enable pigpiod
sudo systemctl start pigpiod

# Set environment variable
export GPIOZERO_PIN_FACTORY=pigpio
```

## Implementation in This Project

### 1. LED Controller Modified

The `led_controller.py` has been updated to automatically force `/dev/gpiomem` usage:

```python
# Force the use of /dev/gpiomem instead of /dev/mem for safer GPIO access
# This must be set BEFORE importing any GPIO libraries
os.environ['BLINKA_USE_GPIOMEM'] = '1'
os.environ['BLINKA_FORCEBOARD'] = 'RASPBERRY_PI_4B'
os.environ['BLINKA_FORCECHIP'] = 'BCM2XXX'
```

### 2. Deployment Scripts Updated

Both `deploy-to-pi.ps1` and `deploy-to-pi.sh` now include the environment variables in the systemd service configuration.

### 3. Testing Scripts

All testing scripts (`test_led_device.py`, `led_manual_test.py`, etc.) will automatically use the forced settings when importing `led_controller.py`.

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