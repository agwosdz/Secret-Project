#!/usr/bin/env python3
import sys
sys.path.append('/home/pi/Secret-Project/backend')

import config
test_config = {'piano_size': '61-key', 'brightness': 0.7, 'gpio_pin': 18}
print('Test config:', test_config)
errors = config.validate_config(test_config)
print('Validation errors:', errors)
specs = config.get_piano_specs('61-key')
print('Piano specs:', specs)

# Test the full update process
current = config.load_config()
print('Current config:', current)
updated = current.copy()
updated.update(test_config)
print('Updated config:', updated)
validation_errors = config.validate_config(updated)
print('Final validation errors:', validation_errors)