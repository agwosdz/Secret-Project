#!/usr/bin/env python3
"""Test script to check MIDI devices API endpoint after fix"""

import requests
import json

try:
    response = requests.get('http://localhost:5001/api/midi-input/devices')
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")