#!/usr/bin/env python3
from config import save_config, load_config

print("Current config:", load_config())
result = save_config({'brightness': 0.8, 'led_count': 245, 'gpio_pin': 19, 'piano_size': '88-key', 'led_orientation': 'normal'})
print("Save result:", result)
print("Updated config:", load_config())