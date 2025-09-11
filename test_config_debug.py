#!/usr/bin/env python3
import sys
sys.path.append('/home/pi/Secret-Project/backend')

import config
print("Testing config module...")
current = config.load_config()
print("Current config:", current)
current["brightness"] = 0.9
result = config.save_config(current)
print("Save result:", result)
new_config = config.load_config()
print("New config:", new_config)