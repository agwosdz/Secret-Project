#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))
os.chdir(str(backend_dir))

# Set environment for Flask - use port 5001
os.environ['FLASK_DEBUG'] = 'True'
os.environ['FLASK_HOST'] = '0.0.0.0'
os.environ['FLASK_PORT'] = '5001'

try:
    from app import app
    print("Flask app imported successfully")
    print("Starting Flask on 0.0.0.0:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()