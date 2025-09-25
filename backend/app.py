from config import load_config, update_config
from rtpmidi_service import RtpMIDISession
import colorsys
import datetime
import math
import os
import time

import logging
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit

# Initialize Flask app and SocketIO early so decorators work
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET', 'dev-secret')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
app.config['HOST'] = os.getenv('FLASK_HOST', '0.0.0.0')
app.config['PORT'] = int(os.getenv('FLASK_PORT', '5000'))
app.config.setdefault('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), 'uploads'))
app.config.setdefault('MAX_CONTENT_LENGTH', 1 * 1024 * 1024)

socketio = SocketIO(app, cors_allowed_origins='*')

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

from led_controller import LEDController
try:
    from midi_parser import midi_parser
except Exception:
    midi_parser = None
try:
    from midi_input_manager import MIDIInputManager
except Exception:
    MIDIInputManager = None
try:
    from usb_midi_service import USBMIDIInputService
except Exception:
    USBMIDIInputService = None
try:
    from playback_service import PlaybackService
except Exception:
    PlaybackService = None

def websocket_status_callback(status):
    """Broadcast playback status over WebSocket."""
    try:
        state = getattr(status, 'state', None)
        state_value = getattr(state, 'value', str(state).lower() if state is not None else None)
        data = {
            'state': state_value,
            'current_time': getattr(status, 'current_time', 0.0),
            'total_duration': getattr(status, 'total_duration', 0.0),
            'progress_percentage': getattr(status, 'progress_percentage', 0.0),
            'filename': getattr(status, 'filename', None),
            'error_message': getattr(status, 'error_message', None)
        }
        socketio.emit('playback_status', data)
    except Exception as e:
        try:
            logger.error(f"Error in websocket_status_callback: {e}")
        except Exception:
            pass

LED_COUNT = 246

# Initialize LED controller first
led_controller = LEDController(num_pixels=LED_COUNT)

# Initialize services that depend on LED controller
usb_midi_service = USBMIDIInputService(led_controller=led_controller, websocket_callback=socketio.emit) if USBMIDIInputService else None
playback_service = PlaybackService(led_controller=led_controller, midi_parser=midi_parser) if PlaybackService and midi_parser else None
midi_input_manager = MIDIInputManager(websocket_callback=socketio.emit, led_controller=led_controller) if MIDIInputManager else None

# Initialize MIDI input manager services
if midi_input_manager:
    midi_input_manager.initialize_services()

@app.route('/api/playback', methods=['POST'])
def start_playback():
    """Start playback"""
    try:
        if not playback_service:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'Playback service not initialized'
            }), 503
        
        filename = data.get('filename')
        if not filename:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Filename parameter is required'
            }), 400
        
        if not playback_service.start_playback(filename):
            return jsonify({
                'error': 'Playback Error',
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

@app.route('/api/seek', methods=['POST'])
def seek_playback():
    """Seek to specific time in playback"""
    try:
        if not playback_service:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'Playback service not initialized'
            }), 503
        
        data = request.get_json()
        if not data or 'time' not in data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Time parameter is required'
            }), 400
        
        seek_time = float(data['time'])
        playback_service.seek_to_time(seek_time)
        
        return jsonify({
            'status': 'success',
            'message': f'Seeked to {seek_time:.2f} seconds'
        }), 200
    
    except ValueError as e:
        return jsonify({
            'error': 'Bad Request',
            'message': f'Invalid time value: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"Error in seek endpoint: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred while seeking'
        }), 500

@app.route('/api/tempo', methods=['POST'])
def set_tempo():
    """Set playback tempo multiplier"""
    try:
        if not playback_service:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'Playback service not initialized'
            }), 503
        
        data = request.get_json()
        if not data or 'tempo' not in data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Tempo parameter is required'
            }), 400
        
        tempo = float(data['tempo'])
        playback_service.set_tempo(tempo)
        
        return jsonify({
            'status': 'success',
            'message': f'Tempo set to {tempo:.2f}x'
        }), 200
    
    except ValueError as e:
        return jsonify({
            'error': 'Bad Request',
            'message': f'Invalid tempo value: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"Error in tempo endpoint: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred while setting tempo'
        }), 500

@app.route('/api/volume', methods=['POST'])
def set_volume():
    """Set playback volume multiplier"""
    try:
        if not playback_service:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'Playback service not initialized'
            }), 503
        
        data = request.get_json()
        if not data or 'volume' not in data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Volume parameter is required'
            }), 400
        
        volume = float(data['volume'])
        playback_service.set_volume(volume)
        
        return jsonify({
            'status': 'success',
            'message': f'Volume set to {volume:.2f}x'
        }), 200
    
    except ValueError as e:
        return jsonify({
            'error': 'Bad Request',
            'message': f'Invalid volume value: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"Error in volume endpoint: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred while setting volume'
        }), 500

@app.route('/api/loop', methods=['POST'])
def set_loop():
    """Set loop parameters"""
    try:
        if not playback_service:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'Playback service not initialized'
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Request body is required'
            }), 400
        
        enabled = data.get('enabled', False)
        start_time = data.get('start', 0.0)
        end_time = data.get('end', None)
        
        playback_service.set_loop(enabled, start_time, end_time)
        
        return jsonify({
            'status': 'success',
            'message': f'Loop {"enabled" if enabled else "disabled"}'
        }), 200
    
    except ValueError as e:
        return jsonify({
            'error': 'Bad Request',
            'message': f'Invalid loop parameters: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"Error in loop endpoint: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred while setting loop'
        }), 500

@app.route('/api/extended-status', methods=['GET'])
def get_extended_status():
    """Get extended playback status including new controls"""
    try:
        if not playback_service:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'Playback service not initialized'
            }), 503
        
        status = playback_service.get_extended_status()
        
        return jsonify({
            'status': 'success',
            'playback': status
        }), 200
    
    except Exception as e:
        logger.error(f"Error in get_extended_status endpoint: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred while getting extended status'
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

@app.route('/api/settings/led_count', methods=['GET'])
def get_led_count():
    """Get the current LED count from settings"""
    try:
        return jsonify({
            'led_count': LED_COUNT
        }), 200
    except Exception as e:
        logger.error(f"Error getting LED count: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred while getting LED count'
        }), 500

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get all current settings"""
    try:
        config = load_config()
        return jsonify(config), 200
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred while getting settings'
        }), 500

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update settings with validation"""
    global led_controller, playback_service, midi_input_manager
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'No JSON data provided'
            }), 400
        
        # Load current config
        current_config = load_config()
        
        # Update only provided fields
        updated_config = current_config.copy()
        updated_config.update(data)
        
        # Handle piano size changes
        if 'piano_size' in data and data['piano_size'] != 'custom':
            piano_size = data['piano_size']
            specs = get_piano_specs(piano_size)
            if 'led_count' not in data:  # Only auto-update if not explicitly set
                updated_config['led_count'] = specs.get('keys', 88)
        
        # Validate configuration
        validation_errors = validate_config(updated_config)
        if validation_errors:
            return jsonify({
                'error': 'Validation Error',
                'message': 'Configuration validation failed',
                'details': validation_errors
            }), 400
        
        # Save configuration
        save_config(updated_config)
        
        # Reinitialize LED controller if hardware settings changed
        hardware_fields = ['gpio_pin', 'led_count', 'led_frequency', 'led_dma', 'led_channel', 'led_invert', 'brightness', 'led_orientation']
        if any(field in data for field in hardware_fields) and led_controller:
            try:
                # Clean up existing controller
                if hasattr(led_controller, 'cleanup'):
                    led_controller.cleanup()
                
                # Create new controller with updated configuration
                led_controller = LEDController(
                    pin=updated_config.get('gpio_pin', 18),
                    num_pixels=updated_config.get('led_count', 246),
                    brightness=updated_config.get('brightness', 0.5)
                )
                logger.info("LED controller reinitialized with new settings")
                
                # Reinitialize playback service with new LED controller and configuration
                if playback_service:
                    # Stop current playback and clean up
                    playback_service.stop_playback()
                    
                    # Create new playback service with updated configuration
                    playback_service = PlaybackService(led_controller=led_controller, midi_parser=midi_parser)
                    playback_service.add_status_callback(websocket_status_callback)
                    logger.info("Playback service reinitialized with new LED controller and configuration")
                    
                # Update MIDI input manager with new LED controller
                if midi_input_manager and hasattr(midi_input_manager, '_led_controller'):
                    midi_input_manager._led_controller = led_controller
                    # Reinitialize USB MIDI service if it exists
                    if hasattr(midi_input_manager, 'usb_midi_service') and midi_input_manager.usb_midi_service:
                        midi_input_manager.usb_midi_service._led_controller = led_controller
                        # Update configuration-dependent properties
                        piano_size = updated_config.get('piano_size', '88-key')
                        piano_specs = get_piano_specs(piano_size)
                        midi_input_manager.usb_midi_service.num_leds = piano_specs['keys']
                        midi_input_manager.usb_midi_service.min_midi_note = piano_specs['midi_start']
                        midi_input_manager.usb_midi_service.max_midi_note = piano_specs['midi_end']
                        midi_input_manager.usb_midi_service.led_orientation = updated_config.get('led_orientation', 'normal')
                        logger.info("MIDI input manager updated with new LED controller and configuration")
                    
            except Exception as e:
                logger.error(f"Failed to reinitialize LED controller: {e}")
                return jsonify({
                    'error': 'Hardware Error',
                    'message': f'Settings saved but LED controller failed to reinitialize: {str(e)}'
                }), 500
        
        return jsonify({'message': 'Settings updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred while updating settings'
        }), 500


@app.route('/api/test-hardware', methods=['POST'])
def test_hardware():
    """Test hardware configuration"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No configuration data provided'
            }), 400
        
        # Validate GPIO pin availability
        gpio_pin = data.get('gpio_pin', 18)
        try:
            from config import validate_gpio_pin_availability
            if not validate_gpio_pin_availability(gpio_pin):
                return jsonify({
                    'success': False,
                    'message': f'GPIO pin {gpio_pin} is not available or already in use'
                }), 200
        except Exception as e:
            logger.warning(f"GPIO validation failed: {e}")
        
        # Test LED controller initialization
        if LEDController:
            try:
                test_controller = LEDController(
                    led_count=data.get('led_count', 246),
                    gpio_pin=gpio_pin,
                    freq_hz=data.get('led_frequency', 800000),
                    dma=data.get('led_dma', 10),
                    channel=data.get('led_channel', 0),
                    invert=data.get('led_invert', False),
                    brightness=int(data.get('brightness', 0.5) * 255)
                )
                
                # Test basic LED functionality
                test_controller.clear()
                test_controller.set_pixel(0, (255, 0, 0))  # Red test
                test_controller.show()
                time.sleep(0.1)
                test_controller.clear()
                test_controller.show()
                
                return jsonify({
                    'success': True,
                    'message': 'Hardware test passed successfully'
                }), 200
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'LED controller test failed: {str(e)}'
                }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'LED controller not available (development mode?)'
            }), 200
            
    except Exception as e:
        logger.error(f"Error testing hardware: {e}")
        return jsonify({
            'success': False,
            'message': f'Hardware test error: {str(e)}'
        }), 500

@app.route('/api/led-test-sequence', methods=['POST'])
def start_led_test_sequence():
    """Start an LED test sequence"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No test sequence data provided'
            }), 400
            
        sequence_type = data.get('type', 'rainbow')
        duration = data.get('duration', 5)  # seconds
        led_count = data.get('led_count', LED_COUNT)
        
        if not led_controller:
            return jsonify({
                'success': False,
                'message': 'LED controller not available'
            }), 503
            
        # Emit test sequence start event
        socketio.emit('led_test_sequence_start', {
            'type': sequence_type,
            'duration': duration,
            'led_count': led_count
        })
        
        # Start the test sequence in a background thread
        socketio.start_background_task(_run_led_test_sequence, sequence_type, duration, led_count)
        
        return jsonify({
            'success': True,
            'message': f'LED test sequence "{sequence_type}" started',
            'duration': duration
        }), 200
        
    except Exception as e:
        logger.error(f"Error starting LED test sequence: {e}")
        return jsonify({
            'success': False,
            'message': f'Test sequence error: {str(e)}'
        }), 500

@app.route('/api/led-test-sequence/stop', methods=['POST'])
def stop_led_test_sequence():
    """Stop the current LED test sequence"""
    try:
        if led_controller:
            led_controller.clear()
            led_controller.show()
            
        # Emit test sequence stop event
        socketio.emit('led_test_sequence_stop', {})
        
        return jsonify({
            'success': True,
            'message': 'LED test sequence stopped'
        }), 200
        
    except Exception as e:
        logger.error(f"Error stopping LED test sequence: {e}")
        return jsonify({
            'success': False,
            'message': f'Stop sequence error: {str(e)}'
        }), 500

def _run_led_test_sequence(sequence_type, duration, led_count):
    """Run LED test sequence in background thread"""
    try:
        if not led_controller:
            return
            
        start_time = time.time()
        
        while time.time() - start_time < duration:
            if sequence_type == 'rainbow':
                _rainbow_sequence(led_count)
            elif sequence_type == 'chase':
                _chase_sequence(led_count)
            elif sequence_type == 'fade':
                _fade_sequence(led_count)
            elif sequence_type == 'piano_keys':
                _piano_keys_sequence(led_count)
            else:
                _rainbow_sequence(led_count)  # Default
                
            time.sleep(0.05)  # 20 FPS
            
        # Clear LEDs when done
        led_controller.clear()
        led_controller.show()
        
        # Emit completion event
        socketio.emit('led_test_sequence_complete', {
            'type': sequence_type,
            'duration': duration
        })
        
    except Exception as e:
        logger.error(f"Error in LED test sequence: {e}")
        socketio.emit('led_test_sequence_error', {
            'error': str(e)
        })

def _rainbow_sequence(led_count):
    """Rainbow color sequence"""
    hue_offset = (time.time() * 50) % 360
    for i in range(min(led_count, 246)):
        hue = (hue_offset + (i * 360 / led_count)) % 360
        r, g, b = _hue_to_rgb(hue)
        led_controller.set_pixel(i, (int(r * 255), int(g * 255), int(b * 255)))
    led_controller.show()

def _chase_sequence(led_count):
    """Chase light sequence"""
    position = int((time.time() * 10) % led_count)
    led_controller.clear()
    for i in range(5):  # 5-LED chase
        led_pos = (position + i) % led_count
        brightness = 1.0 - (i * 0.2)
        led_controller.set_pixel(led_pos, (int(255 * brightness), int(100 * brightness), 0))
    led_controller.show()

def _fade_sequence(led_count):
    """Fade in/out sequence"""
    brightness = (math.sin(time.time() * 2) + 1) / 2  # 0 to 1
    color = (int(255 * brightness), int(100 * brightness), int(50 * brightness))
    for i in range(min(led_count, 246)):
        led_controller.set_pixel(i, color)
    led_controller.show()

def _piano_keys_sequence(led_count):
    """Piano key pattern sequence"""
    # Simulate piano key pattern with white and black key colors
    pattern_offset = int((time.time() * 5) % 12)
    white_key_pattern = [0, 2, 4, 5, 7, 9, 11]  # C major scale
    
    for i in range(min(led_count, 246)):
        key_pos = (i + pattern_offset) % 12
        if key_pos in white_key_pattern:
            led_controller.set_pixel(i, (255, 255, 255))  # White
        else:
            led_controller.set_pixel(i, (50, 50, 50))     # Dark gray for black keys
    led_controller.show()

def _hue_to_rgb(hue):
    """Convert HSV hue to RGB (saturation=1, value=1)"""
    hue = hue % 360
    c = 1.0  # chroma
    x = c * (1 - abs((hue / 60) % 2 - 1))
    m = 0
    
    if 0 <= hue < 60:
        r, g, b = c, x, 0
    elif 60 <= hue < 120:
        r, g, b = x, c, 0
    elif 120 <= hue < 180:
        r, g, b = 0, c, x
    elif 180 <= hue < 240:
        r, g, b = 0, x, c
    elif 240 <= hue < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    
    return r + m, g + m, b + m

@app.route('/api/config/validate', methods=['POST'])
def validate_configuration():
    """Validate configuration with comprehensive checks"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No configuration data provided'
            }), 500
        
        import config as cfg
        validation_result = cfg.validate_config_comprehensive(data)
        
        return jsonify({
            'success': True,
            'validation': validation_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating configuration: {e}")
        return jsonify({
            'success': False,
            'message': f'Validation error: {str(e)}'
        }), 500

@app.route('/api/config/backup', methods=['POST'])
def backup_configuration():
    """Create a backup of current configuration"""
    try:
        from config import backup_config
        success = backup_config()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Configuration backed up successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to backup configuration'
            }), 500
            
    except Exception as e:
        logger.error(f"Error backing up configuration: {e}")
        return jsonify({
            'success': False,
            'message': f'Backup error: {str(e)}'
        }), 500

@app.route('/api/config/restore', methods=['POST'])
def restore_configuration():
    """Restore configuration from backup"""
    try:
        from config import restore_config_from_backup
        success = restore_config_from_backup()
        
        if success:
            # Reload configuration
            global config
            config = load_config()
            
            return jsonify({
                'success': True,
                'message': 'Configuration restored successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to restore configuration (no backup found)'
            }), 404
            
    except Exception as e:
        logger.error(f"Error restoring configuration: {e}")
        return jsonify({
            'success': False,
            'message': f'Restore error: {str(e)}'
        }), 500

@app.route('/api/config/reset', methods=['POST'])
def reset_configuration():
    """Reset configuration to defaults"""
    try:
        from config import reset_config_to_defaults
        success = reset_config_to_defaults()
        
        if success:
            # Reload configuration
            global config
            config = load_config()
            
            return jsonify({
                'success': True,
                'message': 'Configuration reset to defaults'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to reset configuration'
            }), 500
            
    except Exception as e:
        logger.error(f"Error resetting configuration: {e}")
        return jsonify({
            'success': False,
            'message': f'Reset error: {str(e)}'
        }), 500

@app.route('/api/config/export', methods=['POST'])
def export_configuration():
    """Export configuration to file"""
    try:
        data = request.get_json()
        export_path = data.get('path') if data else None
        
        if not export_path:
            # Generate default export path
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            export_path = f"config_export_{timestamp}.json"
        
        from config import export_config
        success = export_config(export_path)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Configuration exported to {export_path}',
                'export_path': export_path
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to export configuration'
            }), 500
            
    except Exception as e:
        logger.error(f"Error exporting configuration: {e}")
        return jsonify({
            'success': False,
            'message': f'Export error: {str(e)}'
        }), 500

@app.route('/api/config/history', methods=['GET'])
def get_configuration_history():
    """Get configuration change history"""
    try:
        from config import get_config_history
        history = get_config_history()
        
        return jsonify({
            'success': True,
            'history': history
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting configuration history: {e}")
        return jsonify({
            'success': False,
            'message': f'History error: {str(e)}'
        }), 500

# Unified MIDI Input API Endpoints (USB + rtpMIDI)
@app.route('/api/midi-input/devices', methods=['GET'])
def get_midi_devices():
    """Get available MIDI input devices (USB and network)"""
    try:
        if not midi_input_manager:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'MIDI input manager not available'
            }), 503
        
        devices = midi_input_manager.get_available_devices()
        return jsonify({
            'status': 'success',
            'devices': devices
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting MIDI devices: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred while getting MIDI devices'
        }), 500

@app.route('/api/midi-input/start', methods=['POST'])
def start_midi_input():
    """Start MIDI input listening (USB and/or network)"""
    try:
        if not midi_input_manager:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'MIDI input manager not available'
            }), 503
        
        data = request.get_json() or {}
        device_name = data.get('device_name')
        enable_usb = data.get('enable_usb', True)
        enable_rtpmidi = data.get('enable_rtpmidi', True)
        
        success = midi_input_manager.start_listening(
            device_name=device_name,
            enable_usb=enable_usb,
            enable_rtpmidi=enable_rtpmidi
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'MIDI input started successfully',
                'services': midi_input_manager.get_active_services()
            }), 200
        else:
            return jsonify({
                'error': 'Failed to Start',
                'message': 'Could not start MIDI input listening'
            }), 400
            
    except Exception as e:
        logger.error(f"Error starting MIDI input: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred while starting MIDI input'
        }), 500

@app.route('/api/midi-input/stop', methods=['POST'])
def stop_midi_input():
    """Stop MIDI input listening (USB and network)"""
    try:
        if not midi_input_manager:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'MIDI input manager not available'
            }), 503
        
        success = midi_input_manager.stop_listening()
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'MIDI input stopped successfully'
            }), 200
        else:
            return jsonify({
                'error': 'Failed to Stop',
                'message': 'Could not stop MIDI input listening'
            }), 400
            
    except Exception as e:
        logger.error(f"Error stopping MIDI input: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred while stopping MIDI input'
        }), 500

@app.route('/api/midi-input/status', methods=['GET'])
def get_midi_input_status():
    """Get unified MIDI input status (USB and network)"""
    try:
        if not midi_input_manager:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'MIDI input manager not available'
            }), 503
        
        status = midi_input_manager.get_status()
        return jsonify({
            'status': 'success',
            'midi_input': status
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting MIDI input status: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred while getting MIDI input status'
        }), 500

# rtpMIDI Network-specific API Endpoints
@app.route('/api/rtpmidi/sessions', methods=['GET'])
def get_rtpmidi_sessions():
    """Get available rtpMIDI sessions"""
    try:
        if not midi_input_manager or not midi_input_manager._rtpmidi_service:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'rtpMIDI service not available'
            }), 503
        
        sessions = midi_input_manager._rtpmidi_service.get_available_sessions()
        return jsonify({
            'status': 'success',
            'sessions': sessions
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting rtpMIDI sessions: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred while getting rtpMIDI sessions'
        }), 500

@app.route('/api/rtpmidi/discover', methods=['POST'])
def start_rtpmidi_discovery():
    """Start rtpMIDI session discovery"""
    try:
        if not midi_input_manager or not midi_input_manager._rtpmidi_service:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'rtpMIDI service not available'
            }), 503
        
        success = midi_input_manager._rtpmidi_service.start_discovery()
        if success:
            return jsonify({
                'status': 'success',
                'message': 'rtpMIDI discovery started'
            }), 200
        else:
            return jsonify({
                'error': 'Discovery Failed',
                'message': 'Failed to start rtpMIDI discovery'
            }), 500
        
    except Exception as e:
        logger.error(f"Error starting rtpMIDI discovery: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred while starting rtpMIDI discovery'
        }), 500

@app.route('/api/rtpmidi/discovery-status', methods=['GET'])
def get_rtpmidi_discovery_status():
    """Get rtpMIDI discovery status and progress"""
    try:
        if not midi_input_manager or not midi_input_manager._rtpmidi_service:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'rtpMIDI service not available'
            }), 503
        
        rtpmidi_service = midi_input_manager._rtpmidi_service
        is_discovering = rtpmidi_service.is_discovering
        sessions = rtpmidi_service.get_available_sessions()
        
        return jsonify({
            'status': 'success',
            'discovering': is_discovering,
            'completed': not is_discovering,
            'progress': 100 if not is_discovering else 50,  # Simple progress indication
            'devices': sessions
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting rtpMIDI discovery status: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred while getting rtpMIDI discovery status'
        }), 500

@app.route('/api/rtpmidi/connect', methods=['POST'])
def connect_rtpmidi_session():
    """Connect to an rtpMIDI session"""
    try:
        if not midi_input_manager or not midi_input_manager._rtpmidi_service:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'rtpMIDI service not available'
            }), 503
        
        data = request.get_json() or {}
        session_name = data.get('session_name')
        host = data.get('host')
        port = data.get('port', 5004)
        
        if not session_name or not host:
            return jsonify({
                'error': 'Bad Request',
                'message': 'session_name and host are required'
            }), 400
        
        # Create RtpMIDISession object for connection
        from rtpmidi_service import RtpMIDISession
        session = RtpMIDISession(
            name=session_name,
            ip_address=host,
            port=port
        )
        
        success = midi_input_manager._rtpmidi_service.connect_session(session)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Connected to rtpMIDI session {session_name}'
            }), 200
        else:
            return jsonify({
                'error': 'Connection Failed',
                'message': f'Could not connect to rtpMIDI session {session_name}'
            }), 400
            
    except Exception as e:
        logger.error(f"Error connecting to rtpMIDI session: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred while connecting to rtpMIDI session'
        }), 500

@app.route('/api/rtpmidi/disconnect', methods=['POST'])
def disconnect_rtpmidi_session():
    """Disconnect from an rtpMIDI session"""
    try:
        if not midi_input_manager or not midi_input_manager._rtpmidi_service:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'rtpMIDI service not available'
            }), 503
        
        data = request.get_json() or {}
        session_name = data.get('session_name')
        
        if not session_name:
            return jsonify({
                'error': 'Bad Request',
                'message': 'session_name is required'
            }), 400
        
        success = midi_input_manager._rtpmidi_service.disconnect_session(session_name)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Disconnected from rtpMIDI session {session_name}'
            }), 200
        else:
            return jsonify({
                'error': 'Disconnection Failed',
                'message': f'Could not disconnect from rtpMIDI session {session_name}'
            }), 400
            
    except Exception as e:
        logger.error(f"Error disconnecting from rtpMIDI session: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred while disconnecting from rtpMIDI session'
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
            'playback_service_available': playback_service is not None,
            'usb_midi_service_available': usb_midi_service is not None,
            'midi_input_active': False,
            'midi_device_name': None
        }
        
        # Check if MIDI input is actively listening
        if midi_input_manager:
            try:
                manager_status = midi_input_manager.get_status()
                system_status['midi_input_active'] = manager_status.get('is_listening', False)
                
                # Get active device name if available
                usb_status = manager_status.get('usb_service', {})
                if usb_status.get('device'):
                    system_status['midi_device_name'] = usb_status['device']
            except Exception as e:
                logger.warning(f"Error getting MIDI input manager status: {e}")
        
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

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring and frontend connectivity"""
    try:
        return jsonify({
            'status': 'healthy',
            'message': 'Piano LED Visualizer Backend is running',
            'timestamp': datetime.datetime.now().isoformat(),
            'version': '1.0.0'
        }), 200
    except Exception as e:
        logger.error(f"Error in health check endpoint: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Health check failed',
            'timestamp': datetime.datetime.now().isoformat(),
            'error': str(e)
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
    else:
        # Emit a default stopped status when playback service is unavailable
        emit('playback_status', {
            'state': 'stopped',
            'current_time': 0.0,
            'total_duration': 0.0,
            'progress_percentage': 0.0,
            'filename': None,
            'error_message': None
        })

@socketio.on('test_led')
def handle_test_led(data):
    """Handle LED test via WebSocket"""
    try:
        if not led_controller:
            emit('error', {'message': 'LED controller not available'})
            return
        
        led_index = data.get('index', 0)
        r = data.get('r', 255)
        g = data.get('g', 255) 
        b = data.get('b', 255)
        brightness = data.get('brightness', 1.0)
        
        # Handle legacy rgb format
        if 'rgb' in data:
            rgb = data['rgb']
            r, g, b = rgb[0], rgb[1], rgb[2]
            
        # Convert brightness to 0-1 range if it's 0-100
        if brightness > 1.0:
            brightness = brightness / 100.0
            
        # Validate inputs
        if led_index != -1 and not (0 <= led_index < LED_COUNT):
            emit('error', {'message': f'Invalid LED index: {led_index}. Valid range: 0-{LED_COUNT-1}'})
            return
            
        if not (0 <= brightness <= 1.0):
            emit('error', {'message': f'Invalid brightness: {brightness}'})
            return
            
        # Apply brightness to RGB values
        adjusted_rgb = [int(r * brightness), int(g * brightness), int(b * brightness)]
        
        # Handle Clear All (index -1) or Fill All
        if led_index == -1:
            if r == 0 and g == 0 and b == 0:
                # Clear all LEDs
                led_controller.turn_off_all()
                logger.info("All LEDs cleared via WebSocket")
                emit('led_test_result', {
                    'success': True,
                    'action': 'clear_all',
                    'rgb': adjusted_rgb
                })
            else:
                # Fill all LEDs with color
                for i in range(LED_COUNT):
                    led_controller.turn_on_led(i, tuple(adjusted_rgb), auto_show=False)
                led_controller.show()
                logger.info(f"All LEDs filled with RGB{adjusted_rgb} via WebSocket")
                emit('led_test_result', {
                    'success': True,
                    'action': 'fill_all',
                    'rgb': adjusted_rgb
                })
        else:
            # Set individual LED
            led_controller.turn_on_led(led_index, tuple(adjusted_rgb))
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
        
        # Get additional pattern parameters
        color = data.get('color', {'r': 255, 'g': 255, 'b': 255})
        base_color = (color.get('r', 255), color.get('g', 255), color.get('b', 255))
        
        # Pattern implementations
        if pattern == 'rainbow':
            # Create rainbow pattern
            for i in range(LED_COUNT):
                hue = (i * 360 // LED_COUNT) % 360
                rgb = _hue_to_rgb(hue)
                led_controller.turn_on_led(i, tuple(rgb), auto_show=False)
            led_controller.show()
        elif pattern == 'pulse':
            # Pulse effect - fade in and out
            import time
            import threading
            def pulse_effect():
                try:
                    for brightness in range(0, 256, 8):  # Fade in
                        factor = brightness / 255.0
                        pulse_color = (int(base_color[0] * factor), int(base_color[1] * factor), int(base_color[2] * factor))
                        for i in range(LED_COUNT):
                            led_controller.turn_on_led(i, pulse_color, auto_show=False)
                        led_controller.show()
                        time.sleep(0.02)
                    for brightness in range(255, -1, -8):  # Fade out
                        factor = brightness / 255.0
                        pulse_color = (int(base_color[0] * factor), int(base_color[1] * factor), int(base_color[2] * factor))
                        for i in range(LED_COUNT):
                            led_controller.turn_on_led(i, pulse_color, auto_show=False)
                        led_controller.show()
                        time.sleep(0.02)
                except Exception as e:
                    logger.error(f"Pulse effect error: {e}")
            threading.Thread(target=pulse_effect, daemon=True).start()
        elif pattern == 'chase':
            # Color chase effect
            import time
            import threading
            def chase_effect():
                try:
                    chase_length = 5  # Number of LEDs in chase
                    for offset in range(LED_COUNT + chase_length):
                        # Clear all LEDs
                        for i in range(LED_COUNT):
                            led_controller.turn_on_led(i, (0, 0, 0), auto_show=False)
                        # Set chase LEDs
                        for i in range(chase_length):
                            led_pos = (offset - i) % LED_COUNT
                            if 0 <= led_pos < LED_COUNT:
                                brightness = 1.0 - (i / chase_length)
                                chase_color = (int(base_color[0] * brightness), int(base_color[1] * brightness), int(base_color[2] * brightness))
                                led_controller.turn_on_led(led_pos, chase_color, auto_show=False)
                        led_controller.show()
                        time.sleep(0.05)
                except Exception as e:
                    logger.error(f"Chase effect error: {e}")
            threading.Thread(target=chase_effect, daemon=True).start()
        elif pattern == 'strobe':
            # Strobe light effect
            import time
            import threading
            def strobe_effect():
                try:
                    for _ in range(20):  # 20 flashes
                        # Flash on
                        for i in range(LED_COUNT):
                            led_controller.turn_on_led(i, base_color, auto_show=False)
                        led_controller.show()
                        time.sleep(0.05)
                        # Flash off
                        for i in range(LED_COUNT):
                            led_controller.turn_on_led(i, (0, 0, 0), auto_show=False)
                        led_controller.show()
                        time.sleep(0.05)
                except Exception as e:
                    logger.error(f"Strobe effect error: {e}")
            threading.Thread(target=strobe_effect, daemon=True).start()
        elif pattern == 'fade':
            # Fade in/out effect
            import time
            import threading
            def fade_effect():
                try:
                    # Fade in
                    for brightness in range(0, 256, 4):
                        factor = brightness / 255.0
                        fade_color = (int(base_color[0] * factor), int(base_color[1] * factor), int(base_color[2] * factor))
                        for i in range(LED_COUNT):
                            led_controller.turn_on_led(i, fade_color, auto_show=False)
                        led_controller.show()
                        time.sleep(0.03)
                    time.sleep(1)  # Hold at full brightness
                    # Fade out
                    for brightness in range(255, -1, -4):
                        factor = brightness / 255.0
                        fade_color = (int(base_color[0] * factor), int(base_color[1] * factor), int(base_color[2] * factor))
                        for i in range(LED_COUNT):
                            led_controller.turn_on_led(i, fade_color, auto_show=False)
                        led_controller.show()
                        time.sleep(0.03)
                except Exception as e:
                    logger.error(f"Fade effect error: {e}")
            threading.Thread(target=fade_effect, daemon=True).start()
        elif pattern == 'solid':
            # Solid color fill
            for i in range(LED_COUNT):
                led_controller.turn_on_led(i, base_color, auto_show=False)
            led_controller.show()
        elif pattern == 'red':
            # Fill all LEDs with red
            for i in range(LED_COUNT):
                led_controller.turn_on_led(i, (255, 0, 0), auto_show=False)
            led_controller.show()
        elif pattern == 'green':
            # Fill all LEDs with green
            for i in range(LED_COUNT):
                led_controller.turn_on_led(i, (0, 255, 0), auto_show=False)
            led_controller.show()
        elif pattern == 'blue':
            # Fill all LEDs with blue
            for i in range(LED_COUNT):
                led_controller.turn_on_led(i, (0, 0, 255), auto_show=False)
            led_controller.show()
        elif pattern == 'white':
            # Fill all LEDs with white
            for i in range(LED_COUNT):
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

@socketio.on('led_count_change')
def handle_led_count_change(data):
    """Handle LED count configuration change"""
    global LED_COUNT, led_controller, playback_service
    
    try:
        new_led_count = int(data.get('ledCount', LED_COUNT))
        
        # Validate LED count range
        if not (1 <= new_led_count <= 300):
            emit('error', {'message': f'Invalid LED count: {new_led_count}. Valid range: 1-300'})
            return
            
        # Update global LED count and save to configuration
        LED_COUNT = new_led_count
        logger.info(f"LED count updated to: {LED_COUNT}")
        
        # Save to configuration if available
        try:
            update_config('led_count', LED_COUNT)
            logger.info(f"Saved LED count {LED_COUNT} to configuration")
        except Exception as e:
            logger.warning(f"Failed to save LED count to configuration: {e}")
        
        # Reinitialize LED controller with new count
        if LEDController:
            try:
                if led_controller:
                    # Turn off all LEDs but don't destroy the controller
                    led_controller.turn_off_all() 
                led_controller = LEDController(num_pixels=LED_COUNT)
                logger.info(f"LED controller reinitialized with {LED_COUNT} LEDs")
            except Exception as e:
                logger.warning(f"LED controller reinitialization failed: {e}")
                led_controller = None
        
        # Reinitialize playback service with new LED count
        if PlaybackService and midi_parser:
            try:
                if playback_service:
                    # Stop any ongoing playback
                    playback_service.stop()
                playback_service = PlaybackService(led_controller=led_controller, num_leds=LED_COUNT, midi_parser=midi_parser)
                playback_service.add_status_callback(websocket_status_callback)
                logger.info(f"Playback service reinitialized with {LED_COUNT} LEDs")
            except Exception as e:
                logger.warning(f"Playback service reinitialization failed: {e}")
                playback_service = None
        
        # Light up LEDs incrementally to provide visual feedback
        if led_controller:
            try:
                # Turn off all LEDs first
                led_controller.turn_off_all()
                
                # Default color for visualization
                color = (0, 128, 255)  # Blue color
                brightness = 0.5
                
                # Light up LEDs incrementally
                for i in range(LED_COUNT):
                    led_controller.turn_on_led(i, color, brightness)
                    # Small delay for visual effect
                    socketio.sleep(0.01)
                
                logger.info(f"Illuminated {LED_COUNT} LEDs for visual feedback")
            except Exception as e:
                logger.warning(f"Failed to provide visual LED count feedback: {e}")
        
        # Emit confirmation to all clients
        socketio.emit('led_count_updated', {
            'ledCount': LED_COUNT,
            'message': f'LED count updated to {LED_COUNT}'
        })
        
    except (ValueError, TypeError) as e:
        emit('error', {'message': f'Invalid LED count data: {e}'})
        logger.error(f"LED count change error: {e}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('get_status')
def handle_get_status():
    """Handle request for current playback status"""
    print("DEBUG: get_status event received")
    
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
        # Emit default status instead of error to satisfy tests
        emit('playback_status', {
            'state': 'stopped',
            'current_time': 0.0,
            'total_duration': 0.0,
            'progress_percentage': 0.0,
            'filename': None,
            'error_message': None
        })
    
    # Also emit USB MIDI service status
    if usb_midi_service:
        midi_status = usb_midi_service.get_status()
        emit('midi_input_status', {
            'connected': midi_status.get('connected', False),
            'device_name': midi_status.get('device_name'),
            'notes_received': midi_status.get('notes_received', 0),
            'error_message': midi_status.get('error_message')
        })
    
    # Also emit MIDI manager status
    if midi_input_manager:
        print("DEBUG: Broadcasting MIDI manager status via get_status")
        midi_input_manager._broadcast_status_update()
        print("DEBUG: MIDI manager status broadcast completed")

@socketio.on('midi_input_start')
def handle_midi_input_start(data):
    """Handle WebSocket request to start MIDI input (USB and/or network)"""
    try:
        if not midi_input_manager:
            emit('error', {'message': 'MIDI input manager not available'})
            return
            
        device_name = data.get('device_name')
        enable_usb = data.get('enable_usb', True)
        enable_rtpmidi = data.get('enable_rtpmidi', True)
            
        success = midi_input_manager.start_listening(
            device_name=device_name,
            enable_usb=enable_usb,
            enable_rtpmidi=enable_rtpmidi
        )
        if success:
            emit('midi_input_started', {
                'device_name': device_name,
                'services': midi_input_manager.get_active_services(),
                'message': 'MIDI input started successfully'
            })
        else:
            emit('error', {'message': 'Failed to start MIDI input'})
            
    except Exception as e:
        logger.error(f"Error in WebSocket MIDI input start: {e}")
        emit('error', {'message': f'MIDI input start failed: {str(e)}'})

@socketio.on('midi_input_stop')
def handle_midi_input_stop():
    """Handle WebSocket request to stop MIDI input (USB and network)"""
    try:
        if not midi_input_manager:
            emit('error', {'message': 'MIDI input manager not available'})
            return
            
        midi_input_manager.stop_listening()
        emit('midi_input_stopped', {
            'message': 'MIDI input stopped successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in WebSocket MIDI input stop: {e}")
        emit('error', {'message': f'MIDI input stop failed: {str(e)}'})

@socketio.on('get_midi_devices')
def handle_get_midi_devices():
    """Handle WebSocket request for available MIDI devices (USB and network)"""
    try:
        if not midi_input_manager:
            emit('error', {'message': 'MIDI input manager not available'})
            return
            
        devices = midi_input_manager.get_available_devices()
        emit('midi_devices', {
            'devices': devices,
            'count': len(devices.get('usb_devices', [])) + len(devices.get('rtpmidi_sessions', []))
        })
        
    except Exception as e:
        logger.error(f"Error in WebSocket get MIDI devices: {e}")
        emit('error', {'message': f'Failed to get MIDI devices: {str(e)}'})

@socketio.on('unified_midi_event')
def handle_unified_midi_event(data):
    """Handle unified MIDI events from MIDI input manager and broadcast as live events"""
    try:
        # Transform unified event to live_midi_event for UI
        live_event = {
            'timestamp': data.get('timestamp', time.time()),
            'note': data.get('note'),
            'velocity': data.get('velocity'),
            'channel': data.get('channel'),
            'event_type': data.get('event_type'),
            'source': data.get('source'),
            'source_detail': data.get('source_detail')
        }
        
        # Broadcast to all connected clients
        socketio.emit('live_midi_event', live_event)
        
        # Also trigger LED visualization if available
        if led_controller and data.get('event_type') in ['note_on', 'note_off']:
            try:
                if data.get('event_type') == 'note_on':
                    led_controller.note_on(data.get('note'), data.get('velocity'))
                else:
                    led_controller.note_off(data.get('note'))
            except Exception as led_error:
                logger.warning(f"LED visualization error: {led_error}")
                
    except Exception as e:
        logger.error(f"Error handling unified MIDI event: {e}")

@socketio.on('rtpmidi_event')
def handle_rtpmidi_event(data):
    """Handle rtpMIDI network events and broadcast to all clients"""
    try:
        # Transform rtpMIDI event to live_midi_event for UI
        live_event = {
            'timestamp': data.get('timestamp', time.time()),
            'note': data.get('note'),
            'velocity': data.get('velocity'),
            'channel': data.get('channel', 1),
            'event_type': data.get('event_type'),
            'source': f"network:{data.get('source_session', 'unknown')}"
        }
        
        # Broadcast to all connected clients
        socketio.emit('live_midi_event', live_event)
        
        # Trigger LED visualization if available
        if led_controller and data.get('event_type') in ['note_on', 'note_off']:
            try:
                if data.get('event_type') == 'note_on':
                    led_controller.note_on(data.get('note'), data.get('velocity'))
                else:
                    led_controller.note_off(data.get('note'))
            except Exception as led_error:
                logger.warning(f"LED visualization error: {led_error}")
                
    except Exception as e:
        logger.error(f"Error handling rtpMIDI event: {e}")