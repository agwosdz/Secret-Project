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
    port = app.config.get('PORT', 5001)
    host = app.config.get('HOST', '0.0.0.0')
    debug = app.config.get('DEBUG', True)
    print(f"Starting Flask on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()