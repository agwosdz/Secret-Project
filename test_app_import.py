#!/usr/bin/env python3
import sys
sys.path.append('/home/pi/Secret-Project/backend')

try:
    import app
    print('App imported successfully')
    print('Flask app object:', app.app)
except Exception as e:
    print('Error importing app:', str(e))
    import traceback
    traceback.print_exc()