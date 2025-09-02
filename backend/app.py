#!/usr/bin/env python3
"""
Piano LED Visualizer - Flask Backend
Basic Flask application with health check endpoint
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import logging
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge, BadRequest
import mimetypes

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import LED controller and playback service
try:
    from led_controller import LEDController
except ImportError as e:
    logger.warning(f"LED controller import failed: {e}")
    LEDController = None

try:
    from playback_service import PlaybackService
except ImportError as e:
    logger.warning(f"Playback service import failed: {e}")
    PlaybackService = None

try:
    from midi_parser import MIDIParser
except ImportError as e:
    logger.warning(f"MIDI parser import failed: {e}")
    MIDIParser = None

# Configuration
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
app.config['HOST'] = os.environ.get('FLASK_HOST', '0.0.0.0')
app.config['PORT'] = int(os.environ.get('FLASK_PORT', 5000))
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024  # 1MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize LED controller (with error handling for development without hardware)
if LEDController:
    try:
        led_controller = LEDController()
        logger.info("LED controller initialized successfully")
    except Exception as e:
        logger.warning(f"LED controller initialization failed (development mode?): {e}")
        led_controller = None
else:
    logger.info("LED controller not available (import failed)")
    led_controller = None

# Initialize MIDI parser
if MIDIParser:
    try:
        midi_parser = MIDIParser()
        logger.info("MIDI parser initialized successfully")
    except Exception as e:
        logger.warning(f"MIDI parser initialization failed: {e}")
        midi_parser = None
else:
    logger.info("MIDI parser not available (import failed)")
    midi_parser = None

# WebSocket status callback function
def websocket_status_callback(status):
    """Callback to emit playback status updates via WebSocket"""
    try:
        socketio.emit('playback_status', {
            'state': status.state.value,
            'current_time': status.current_time,
            'total_duration': status.total_duration,
            'progress_percentage': status.progress_percentage,
            'filename': status.filename,
            'error_message': status.error_message
        })
    except Exception as e:
        logger.error(f"Error emitting WebSocket status: {e}")

# Initialize playback service
if PlaybackService:
    try:
        playback_service = PlaybackService(led_controller=led_controller, midi_parser=midi_parser)
        # Register WebSocket callback for real-time updates
        playback_service.add_status_callback(websocket_status_callback)
        logger.info("Playback service initialized successfully")
    except Exception as e:
        logger.warning(f"Playback service initialization failed: {e}")
        playback_service = None
else:
    logger.info("Playback service not available (import failed)")
    playback_service = None

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
        'timestamp': '2025-08-31T10:34:00Z',
        'led_controller_available': led_controller is not None
    }), 200

@app.route('/api/test-led', methods=['POST'])
def test_led():
    """Test LED endpoint to turn a single LED on or off"""
    try:
        # Check if LED controller is available
        if not led_controller:
            return jsonify({
                'error': 'Hardware Not Available',
                'message': 'LED controller not initialized (development mode or hardware issue)'
            }), 503
        
        # Get request data
        try:
            data = request.get_json(force=True)
        except BadRequest as json_error:
            logger.warning(f"Invalid JSON received: {json_error}")
            return jsonify({
                'error': 'Bad Request',
                'message': 'Invalid JSON format'
            }), 400
            
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'JSON data required'
            }), 400
        
        # Validate required parameters
        led_index = data.get('index')
        state = data.get('state')
        
        if led_index is None:
            return jsonify({
                'error': 'Bad Request',
                'message': 'LED index is required'
            }), 400
        
        if state is None:
            return jsonify({
                'error': 'Bad Request',
                'message': 'LED state (on/off) is required'
            }), 400
        
        # Validate LED index
        try:
            led_index = int(led_index)
        except (ValueError, TypeError):
            return jsonify({
                'error': 'Bad Request',
                'message': 'LED index must be a valid integer'
            }), 400
        
        # Validate state
        if state not in ['on', 'off']:
            return jsonify({
                'error': 'Bad Request',
                'message': 'LED state must be "on" or "off"'
            }), 400
        
        # Control the LED
        if state == 'on':
            color = data.get('color', [255, 255, 255])  # Default to white
            if isinstance(color, list) and len(color) == 3:
                color = tuple(color)
            else:
                color = (255, 255, 255)
            
            success = led_controller.turn_on_led(led_index, color)
        else:
            success = led_controller.turn_off_led(led_index)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'LED {led_index} turned {state}',
                'led_index': led_index,
                'state': state
            }), 200
        else:
            return jsonify({
                'error': 'Hardware Error',
                'message': f'Failed to turn LED {led_index} {state}'
            }), 500
    
    except Exception as e:
        logger.error(f"Error in test_led endpoint: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500

@app.route('/api/upload-midi', methods=['POST'])
def upload_midi():
    """Upload MIDI file endpoint with validation and secure storage"""
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({
                'error': 'Bad Request',
                'message': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({
                'error': 'Bad Request',
                'message': 'No file selected'
            }), 400
        
        # Validate file extension
        if not file.filename:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Invalid filename'
            }), 400
        
        filename_lower = file.filename.lower()
        allowed_extensions = ['.mid', '.midi']
        
        if not any(filename_lower.endswith(ext) for ext in allowed_extensions):
            return jsonify({
                'error': 'Invalid File Type',
                'message': 'Only MIDI files (.mid, .midi) are allowed'
            }), 400
        
        # Validate MIME type (additional security)
        mime_type, _ = mimetypes.guess_type(file.filename)
        allowed_mime_types = ['audio/midi', 'audio/x-midi', 'application/x-midi']
        
        # Note: Some MIDI files might not have a recognized MIME type, so we'll be lenient
        if mime_type and mime_type not in allowed_mime_types:
            logger.warning(f"Unexpected MIME type for MIDI file: {mime_type}")
        
        # Secure the filename
        filename = secure_filename(file.filename)
        if not filename:
            return jsonify({
                'error': 'Invalid Filename',
                'message': 'Filename contains invalid characters'
            }), 400
        
        # Check file size (Flask's MAX_CONTENT_LENGTH should handle this, but double-check)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        max_size = app.config.get('MAX_CONTENT_LENGTH', 1024 * 1024)
        if file_size > max_size:
            return jsonify({
                'error': 'File Too Large',
                'message': f'File size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)'
            }), 413
        
        # Generate unique filename to prevent conflicts
        import time
        import uuid
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}_{unique_id}{ext}"
        
        # Save the file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Verify file was saved successfully
        if not os.path.exists(file_path):
            return jsonify({
                'error': 'Upload Failed',
                'message': 'File could not be saved'
            }), 500
        
        # Log successful upload
        logger.info(f"MIDI file uploaded successfully: {unique_filename} ({file_size} bytes)")
        
        return jsonify({
            'status': 'success',
            'message': 'MIDI file uploaded successfully',
            'filename': unique_filename,
            'original_filename': file.filename,
            'size': file_size,
            'upload_path': '/uploads/' + unique_filename
        }), 200
    
    except RequestEntityTooLarge:
        return jsonify({
            'error': 'File Too Large',
            'message': 'File size exceeds maximum allowed size (1MB)'
        }), 413
    
    except Exception as e:
            logger.error(f"Error in upload_midi endpoint: {e}")
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred during upload'
            }), 500

@app.route('/api/parse-midi', methods=['POST'])
def parse_midi():
    """Parse MIDI file and return note sequence for LED visualization"""
    try:
        # Check if MIDI parser is available
        if not midi_parser:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'MIDI parser service is not available'
            }), 503
        
        # Get JSON data from request
        try:
            data = request.get_json(force=True)
        except BadRequest:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Invalid JSON in request body'
            }), 400
        
        if not data or 'filename' not in data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Missing filename in request body'
            }), 400
        
        filename = data['filename']
        if not filename:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Filename cannot be empty'
            }), 400
        
        # Construct file path
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({
                'error': 'File Not Found',
                'message': f'MIDI file "{filename}" not found'
            }), 404
        
        # Parse the MIDI file
        try:
            note_sequence = midi_parser.parse_file(file_path)
            
            # Log successful parsing
            logger.info(f"MIDI file parsed successfully: {filename} ({len(note_sequence)} notes)")
            
            return jsonify({
                'status': 'success',
                'message': 'MIDI file parsed successfully',
                'filename': filename,
                'note_count': len(note_sequence),
                'notes': note_sequence
            }), 200
            
        except Exception as e:
            logger.error(f"Error parsing MIDI file {filename}: {e}")
            return jsonify({
                'error': 'Parse Error',
                'message': f'Failed to parse MIDI file: {str(e)}'
            }), 422
    
    except Exception as e:
        logger.error(f"Error in parse_midi endpoint: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred during MIDI parsing'
        }), 500

@app.route('/api/play', methods=['POST'])
def start_playback():
    """Start playback of uploaded MIDI file"""
    try:
        # Check if playback service is available
        if not playback_service:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'Playback service not initialized'
            }), 503
        
        # Get request data
        try:
            data = request.get_json(force=True)
        except BadRequest as json_error:
            logger.warning(f"Invalid JSON received: {json_error}")
            return jsonify({
                'error': 'Bad Request',
                'message': 'Invalid JSON format'
            }), 400
        
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'JSON data required'
            }), 400
        
        filename = data.get('filename')
        if not filename:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Filename is required'
            }), 400
        
        # Construct full file path
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({
                'error': 'File Not Found',
                'message': f'MIDI file {filename} not found'
            }), 404
        
        # Load and start playback
        if not playback_service.load_midi_file(file_path):
            return jsonify({
                'error': 'Playback Error',
                'message': 'Failed to load MIDI file for playback'
            }), 500
        
        if not playback_service.start_playback():
            return jsonify({
                'error': 'Playback Error',
                'message': 'Failed to start playback'
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': 'Playback started successfully',
            'filename': filename
        }), 200
    
    except Exception as e:
        logger.error(f"Error in start_playback endpoint: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred during playback start'
        }), 500

@app.route('/api/pause', methods=['POST'])
def pause_playback():
    """Pause or resume playback"""
    try:
        if not playback_service:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'Playback service not initialized'
            }), 503
        
        if not playback_service.pause_playback():
            return jsonify({
                'error': 'Playback Error',
                'message': 'Failed to pause/resume playback'
            }), 500
        
        status = playback_service.get_status()
        return jsonify({
            'status': 'success',
            'message': f'Playback {status.state.value}',
            'playback_state': status.state.value
        }), 200
    
    except Exception as e:
        logger.error(f"Error in pause_playback endpoint: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred during pause/resume'
        }), 500

@app.route('/api/stop', methods=['POST'])
def stop_playback():
    """Stop playback"""
    try:
        if not playback_service:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'Playback service not initialized'
            }), 503
        
        if not playback_service.stop_playback():
            return jsonify({
                'error': 'Playback Error',
                'message': 'Failed to stop playback'
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': 'Playback stopped successfully'
        }), 200
    
    except Exception as e:
        logger.error(f"Error in stop_playback endpoint: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred during stop'
        }), 500

@app.route('/api/playback-status', methods=['GET'])
def get_playback_status():
    """Get current playback status"""
    try:
        if not playback_service:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'Playback service not initialized'
            }), 503
        
        status = playback_service.get_status()
        return jsonify({
            'status': 'success',
            'playback': {
                'state': status.state.value,
                'current_time': status.current_time,
                'total_duration': status.total_duration,
                'progress_percentage': status.progress_percentage,
                'filename': status.filename,
                'error_message': status.error_message
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error in get_playback_status endpoint: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred while getting status'
        }), 500

@app.route('/api/performance', methods=['GET'])
def get_performance_metrics():
    """Get performance metrics"""
    try:
        if not playback_service:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'Playback service not initialized'
            }), 503
        
        if not hasattr(playback_service, 'performance_monitor') or not playback_service.performance_monitor:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'Performance monitoring not available'
            }), 503
        
        current_metrics = playback_service.performance_monitor.get_current_metrics()
        summary = playback_service.performance_monitor.get_metrics_summary()
        
        return jsonify({
            'status': 'success',
            'performance': {
                'current': current_metrics.__dict__ if current_metrics else None,
                'summary': summary
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred while getting performance metrics'
        }), 500

@app.route('/api/dashboard', methods=['GET'])
def api_dashboard():
    """API endpoint providing dashboard data for frontend"""
    try:
        # Get system status
        system_status = {
            'backend_status': 'running',
            'led_controller_available': led_controller is not None,
            'midi_parser_available': midi_parser is not None,
            'playback_service_available': playback_service is not None
        }
        
        # Get playback status if available
        playback_status = None
        if playback_service:
            try:
                status = playback_service.get_status()
                playback_status = {
                    'state': status.state.value,
                    'current_time': status.current_time,
                    'total_duration': status.total_duration,
                    'progress_percentage': status.progress_percentage,
                    'filename': status.filename,
                    'error_message': status.error_message
                }
            except Exception as e:
                logger.warning(f"Error getting playback status for dashboard: {e}")
        
        # Get uploaded files count
        uploaded_files_count = 0
        try:
            upload_folder = app.config['UPLOAD_FOLDER']
            if os.path.exists(upload_folder):
                uploaded_files_count = len([f for f in os.listdir(upload_folder) 
                                          if f.lower().endswith(('.mid', '.midi'))])
        except Exception as e:
            logger.warning(f"Error counting uploaded files: {e}")
        
        return jsonify({
            'status': 'success',
            'message': 'Piano LED Visualizer Dashboard Data',
            'version': '1.0.0',
            'system_status': system_status,
            'playback_status': playback_status,
            'uploaded_files_count': uploaded_files_count
        }), 200
    
    except Exception as e:
        logger.error(f"Error in api_dashboard endpoint: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred while loading dashboard data'
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large errors"""
    return jsonify({
        'error': 'File Too Large',
        'message': 'File size exceeds maximum allowed size (1MB)'
    }), 413

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    # Send current playback status to newly connected client
    if playback_service:
        status = playback_service.get_status()
        emit('playback_status', {
            'state': status.state.value,
            'current_time': status.current_time,
            'total_duration': status.total_duration,
            'progress_percentage': status.progress_percentage,
            'filename': status.filename,
            'error_message': status.error_message
        })

@socketio.on('test_led')
def handle_test_led(data):
    """Handle LED test via WebSocket"""
    try:
        if not led_controller:
            emit('error', {'message': 'LED controller not available'})
            return
        
        led_index = data.get('index', 0)
        rgb = data.get('rgb', [255, 255, 255])
        brightness = data.get('brightness', 100)
        
        # Validate inputs
        if not (0 <= led_index < 150):
            emit('error', {'message': f'Invalid LED index: {led_index}'})
            return
            
        if not (0 <= brightness <= 100):
            emit('error', {'message': f'Invalid brightness: {brightness}'})
            return
            
        # Apply brightness to RGB values
        brightness_factor = brightness / 100.0
        adjusted_rgb = [int(c * brightness_factor) for c in rgb]
        
        # Set the LED
        led_controller.turn_on_led(led_index, tuple(adjusted_rgb))
        # show() is called automatically by turn_on_led with auto_show=True
        
        logger.info(f"LED {led_index} set to RGB{adjusted_rgb} via WebSocket")
        emit('led_test_result', {
            'success': True,
            'index': led_index,
            'rgb': adjusted_rgb,
            'brightness': brightness
        })
        
    except Exception as e:
        logger.error(f"Error in WebSocket LED test: {e}")
        emit('error', {'message': f'LED test failed: {str(e)}'})

@socketio.on('test_pattern')
def handle_test_pattern(data):
    """Handle pattern test via WebSocket"""
    try:
        if not led_controller:
            emit('error', {'message': 'LED controller not available'})
            return
            
        pattern = data.get('pattern', 'rainbow')
        duration_ms = data.get('duration_ms', 1000)
        
        logger.info(f"Testing pattern '{pattern}' for {duration_ms}ms via WebSocket")
        
        # Simple pattern implementations
        if pattern == 'rainbow':
            # Create rainbow pattern
            for i in range(min(150, led_controller.num_pixels)):
                hue = (i * 360 // 150) % 360
                rgb = _hue_to_rgb(hue)
                led_controller.turn_on_led(i, tuple(rgb), auto_show=False)
            led_controller.show()
        elif pattern == 'red':
            # Fill all LEDs with red
            for i in range(led_controller.num_pixels):
                led_controller.turn_on_led(i, (255, 0, 0), auto_show=False)
            led_controller.show()
        elif pattern == 'green':
            # Fill all LEDs with green
            for i in range(led_controller.num_pixels):
                led_controller.turn_on_led(i, (0, 255, 0), auto_show=False)
            led_controller.show()
        elif pattern == 'blue':
            # Fill all LEDs with blue
            for i in range(led_controller.num_pixels):
                led_controller.turn_on_led(i, (0, 0, 255), auto_show=False)
            led_controller.show()
        elif pattern == 'white':
            # Fill all LEDs with white
            for i in range(led_controller.num_pixels):
                led_controller.turn_on_led(i, (255, 255, 255), auto_show=False)
            led_controller.show()
        else:
            emit('error', {'message': f'Unknown pattern: {pattern}'})
            return
            
        led_controller.show()
        
        emit('pattern_test_result', {
            'success': True,
            'pattern': pattern,
            'duration_ms': duration_ms
        })
        
    except Exception as e:
        logger.error(f"Error in WebSocket pattern test: {e}")
        emit('error', {'message': f'Pattern test failed: {str(e)}'})

def _hue_to_rgb(hue):
    """Convert hue (0-360) to RGB values"""
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(hue / 360.0, 1.0, 1.0)
    return [int(r * 255), int(g * 255), int(b * 255)]

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('get_status')
def handle_get_status():
    """Handle request for current playback status"""
    if playback_service:
        status = playback_service.get_status()
        emit('playback_status', {
            'state': status.state.value,
            'current_time': status.current_time,
            'total_duration': status.total_duration,
            'progress_percentage': status.progress_percentage,
            'filename': status.filename,
            'error_message': status.error_message
        })
    else:
        emit('error', {'message': 'Playback service not available'})

if __name__ == '__main__':
    print(f"Starting Piano LED Visualizer Backend...")
    print(f"Debug mode: {app.config['DEBUG']}")
    print(f"Host: {app.config['HOST']}")
    print(f"Port: {app.config['PORT']}")

    socketio.run(
        app,
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )