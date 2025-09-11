#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))
os.chdir(str(backend_dir))

try:
    from app import app
    print("Flask app imported successfully")
    print(f"Starting Flask on 0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()