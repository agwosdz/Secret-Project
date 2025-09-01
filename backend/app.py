#!/usr/bin/env python3
"""
Piano LED Visualizer - Flask Backend
Basic Flask application with health check endpoint
"""

from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configuration
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
app.config['HOST'] = os.environ.get('FLASK_HOST', '0.0.0.0')
app.config['PORT'] = int(os.environ.get('FLASK_PORT', 5000))

@app.route('/')
def hello_world():
    """Basic Hello World endpoint"""
    return jsonify({
        'message': 'Hello World from Piano LED Visualizer Backend!',
        'status': 'running',
        'version': '1.0.0'
    })

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring and frontend integration"""
    return jsonify({
        'status': 'healthy',
        'message': 'Backend is running successfully',
        'timestamp': '2025-08-31T10:34:00Z'
    }), 200

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    print(f"Starting Piano LED Visualizer Backend...")
    print(f"Debug mode: {app.config['DEBUG']}")
    print(f"Host: {app.config['HOST']}")
    print(f"Port: {app.config['PORT']}")
    
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )