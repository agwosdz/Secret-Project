#!/usr/bin/env python3
"""
Hardware Test API endpoints for Piano LED Visualizer
Provides comprehensive hardware testing and validation capabilities
"""

import logging
import threading
import time
import json
from typing import Dict, Any, Optional, List
from flask import Blueprint, request, jsonify
from flask_socketio import emit

logger = logging.getLogger(__name__)

# Import hardware components
try:
    from led_controller import LEDController
except ImportError:
    LEDController = None

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

# Global test state
active_tests = {}
test_lock = threading.Lock()

# Create the blueprint
hardware_test_bp = Blueprint('hardware_test_api', __name__, url_prefix='/api/hardware-test')

def get_socketio():
    """Get the global SocketIO instance with proper error handling"""
    from app import socketio
    if not socketio:
        raise RuntimeError("SocketIO instance not available - check application initialization")
    return socketio

def emit_test_event(event_type: str, data: Dict[str, Any]):
    """Emit a test event via WebSocket"""
    try:
        socketio = get_socketio()
        socketio.emit(event_type, data)
    except Exception as e:
        logger.error(f"Error emitting test event: {e}")

@hardware_test_bp.route('/led/individual', methods=['POST'])
def test_individual_led():
    """Test individual LED functionality"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No test data provided'
            }), 400
        
        led_index = data.get('led_index', 0)
        color = data.get('color', [255, 255, 255])
        brightness = data.get('brightness', 1.0)
        duration = data.get('duration', 1.0)
        gpio_pin = data.get('gpio_pin', 18)
        led_count = data.get('led_count', 246)
        
        # Validate parameters
        if not (0 <= led_index < led_count):
            return jsonify({
                'success': False,
                'error': f'LED index {led_index} out of range (0-{led_count-1})'
            }), 400
        
        if not LEDController:
            return jsonify({
                'success': False,
                'error': 'LED controller not available (hardware dependencies missing)'
            }), 503
        
        # Initialize LED controller
        try:
            controller = LEDController(num_pixels=led_count, pin=gpio_pin)
            
            # Turn on the specific LED
            controller.turn_on_led(led_index, tuple(color), brightness)
            
            # Emit real-time update
            emit_test_event('led_test_update', {
                'type': 'individual',
                'led_index': led_index,
                'color': color,
                'brightness': brightness,
                'status': 'active'
            })
            
            # Schedule LED turn-off after duration
            def turn_off_led():
                time.sleep(duration)
                try:
                    controller.turn_off_led(led_index)
                    emit_test_event('led_test_update', {
                        'type': 'individual',
                        'led_index': led_index,
                        'status': 'off'
                    })
                except Exception as e:
                    logger.error(f"Error turning off LED: {e}")
            
            threading.Thread(target=turn_off_led, daemon=True).start()
            
            return jsonify({
                'success': True,
                'message': f'LED {led_index} activated',
                'led_index': led_index,
                'color': color,
                'brightness': brightness,
                'duration': duration
            })
            
        except Exception as e:
            logger.error(f"LED controller error: {e}")
            return jsonify({
                'success': False,
                'error': f'LED controller initialization failed: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in individual LED test: {e}")
        return jsonify({
            'success': False,
            'error': f'Test failed: {str(e)}'
        }), 500

@hardware_test_bp.route('/led/sequence', methods=['POST'])
def start_led_sequence():
    """Start an LED test sequence"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No sequence data provided'
            }), 400
        
        sequence_type = data.get('sequence_type', 'rainbow')
        duration = data.get('duration', 5.0)
        led_count = data.get('led_count', 246)
        gpio_pin = data.get('gpio_pin', 18)
        speed = data.get('speed', 1.0)
        brightness = data.get('brightness', 1.0)
        colors = data.get('colors', [[255, 0, 0], [0, 255, 0], [0, 0, 255]])
        
        if not LEDController:
            return jsonify({
                'success': False,
                'error': 'LED controller not available'
            }), 503
        
        # Generate unique test ID
        test_id = f"seq_{int(time.time() * 1000)}"
        
        with test_lock:
            if test_id in active_tests:
                return jsonify({
                    'success': False,
                    'error': 'Test already running'
                }), 409
            
            active_tests[test_id] = {
                'type': 'sequence',
                'sequence_type': sequence_type,
                'status': 'starting',
                'start_time': time.time()
            }
        
        # Start sequence in background thread
        def run_sequence():
            try:
                # Check if we can run as root or have proper permissions
                try:
                    controller = LEDController(num_pixels=led_count, pin=gpio_pin)
                except Exception as init_error:
                    logger.error(f"LED controller initialization failed: {init_error}")
                    emit_test_event('led_sequence_error', {
                        'test_id': test_id,
                        'error': f'Hardware initialization failed: {str(init_error)}. Try running with sudo or check GPIO permissions.'
                    })
                    with test_lock:
                        if test_id in active_tests:
                            active_tests[test_id]['status'] = 'error'
                            active_tests[test_id]['error'] = str(init_error)
                    return
                
                # Update test status
                with test_lock:
                    active_tests[test_id]['status'] = 'running'
                    active_tests[test_id]['controller'] = controller
                
                emit_test_event('led_sequence_start', {
                    'test_id': test_id,
                    'sequence_type': sequence_type,
                    'duration': duration,
                    'led_count': led_count
                })
                
                # Run the appropriate sequence
                if sequence_type == 'rainbow':
                    _run_rainbow_sequence(controller, led_count, duration, speed, brightness, test_id)
                elif sequence_type == 'chase':
                    _run_chase_sequence(controller, led_count, duration, speed, brightness, colors, test_id)
                elif sequence_type == 'fade':
                    _run_fade_sequence(controller, led_count, duration, speed, brightness, colors, test_id)
                elif sequence_type == 'piano_keys':
                    _run_piano_keys_sequence(controller, led_count, duration, brightness, test_id)
                elif sequence_type == 'custom':
                    pattern = data.get('pattern', [])
                    _run_custom_sequence(controller, led_count, duration, pattern, test_id)
                else:
                    raise ValueError(f"Unknown sequence type: {sequence_type}")
                
                # Clean up
                controller.turn_off_all()
                
                with test_lock:
                    if test_id in active_tests:
                        active_tests[test_id]['status'] = 'completed'
                
                emit_test_event('led_sequence_complete', {
                    'test_id': test_id,
                    'sequence_type': sequence_type
                })
                
            except Exception as e:
                logger.error(f"Sequence error: {e}")
                with test_lock:
                    if test_id in active_tests:
                        active_tests[test_id]['status'] = 'error'
                        active_tests[test_id]['error'] = str(e)
                
                emit_test_event('led_sequence_error', {
                    'test_id': test_id,
                    'error': str(e)
                })
            finally:
                # Clean up test record after delay
                def cleanup():
                    time.sleep(30)  # Keep record for 30 seconds
                    with test_lock:
                        active_tests.pop(test_id, None)
                
                threading.Thread(target=cleanup, daemon=True).start()
        
        threading.Thread(target=run_sequence, daemon=True).start()
        
        return jsonify({
            'success': True,
            'message': f'{sequence_type.title()} sequence started',
            'test_id': test_id,
            'sequence_type': sequence_type,
            'duration': duration
        })
        
    except Exception as e:
        logger.error(f"Error starting LED sequence: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to start sequence: {str(e)}'
        }), 500

@hardware_test_bp.route('/led/sequence/<test_id>/stop', methods=['POST'])
def stop_led_sequence(test_id):
    """Stop a running LED sequence"""
    try:
        with test_lock:
            if test_id not in active_tests:
                return jsonify({
                    'success': False,
                    'error': 'Test not found'
                }), 404
            
            test = active_tests[test_id]
            if test['status'] not in ['running', 'starting']:
                return jsonify({
                    'success': False,
                    'error': f'Test is {test["status"]}, cannot stop'
                }), 400
            
            # Mark for stopping
            test['status'] = 'stopping'
            
            # Turn off all LEDs if controller available
            if 'controller' in test:
                try:
                    test['controller'].turn_off_all()
                except Exception as e:
                    logger.error(f"Error turning off LEDs: {e}")
        
        emit_test_event('led_sequence_stop', {
            'test_id': test_id
        })
        
        return jsonify({
            'success': True,
            'message': 'Sequence stopped'
        })
        
    except Exception as e:
        logger.error(f"Error stopping sequence: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to stop sequence: {str(e)}'
        }), 500

@hardware_test_bp.route('/led/sequence/status', methods=['GET'])
def get_sequence_status():
    """Get status of all active sequences"""
    try:
        with test_lock:
            status = {}
            for test_id, test in active_tests.items():
                status[test_id] = {
                    'type': test['type'],
                    'sequence_type': test.get('sequence_type'),
                    'status': test['status'],
                    'start_time': test['start_time'],
                    'duration': time.time() - test['start_time'],
                    'error': test.get('error')
                }
        
        return jsonify({
            'success': True,
            'active_tests': status
        })
        
    except Exception as e:
        logger.error(f"Error getting sequence status: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get status: {str(e)}'
        }), 500

@hardware_test_bp.route('/gpio/validate', methods=['POST'])
def validate_gpio():
    """Validate GPIO pin configuration"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No GPIO data provided'
            }), 400
        
        pins_to_test = data.get('pins', [18])
        test_mode = data.get('mode', 'output')  # output, input, pwm
        
        if not GPIO:
            return jsonify({
                'success': False,
                'error': 'GPIO not available (not running on Raspberry Pi)'
            }), 503
        
        results = {}
        
        try:
            GPIO.setmode(GPIO.BCM)
            
            for pin in pins_to_test:
                try:
                    # Test pin availability
                    if test_mode == 'output':
                        GPIO.setup(pin, GPIO.OUT)
                        GPIO.output(pin, GPIO.HIGH)
                        time.sleep(0.1)
                        GPIO.output(pin, GPIO.LOW)
                        results[pin] = {'status': 'ok', 'mode': 'output'}
                    
                    elif test_mode == 'input':
                        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                        value = GPIO.input(pin)
                        results[pin] = {'status': 'ok', 'mode': 'input', 'value': value}
                    
                    elif test_mode == 'pwm':
                        GPIO.setup(pin, GPIO.OUT)
                        pwm = GPIO.PWM(pin, 1000)  # 1kHz
                        pwm.start(50)  # 50% duty cycle
                        time.sleep(0.1)
                        pwm.stop()
                        results[pin] = {'status': 'ok', 'mode': 'pwm'}
                    
                except Exception as e:
                    results[pin] = {'status': 'error', 'error': str(e)}
                finally:
                    try:
                        GPIO.cleanup(pin)
                    except:
                        pass
        
        finally:
            try:
                GPIO.cleanup()
            except:
                pass
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error validating GPIO: {e}")
        return jsonify({
            'success': False,
            'error': f'GPIO validation failed: {str(e)}'
        }), 500

@hardware_test_bp.route('/system/capabilities', methods=['GET'])
def get_system_capabilities():
    """Get system hardware capabilities"""
    try:
        capabilities = {
            'led_controller': LEDController is not None,
            'gpio': GPIO is not None,
            'platform': 'unknown'
        }
        
        # Detect platform
        try:
            import platform
            system = platform.system().lower()
            if system == 'linux':
                # Check if running on Raspberry Pi
                try:
                    with open('/proc/cpuinfo', 'r') as f:
                        cpuinfo = f.read()
                        if 'raspberry pi' in cpuinfo.lower():
                            capabilities['platform'] = 'raspberry_pi'
                        else:
                            capabilities['platform'] = 'linux'
                except:
                    capabilities['platform'] = 'linux'
            else:
                capabilities['platform'] = system
        except:
            pass
        
        # Test LED controller availability
        if LEDController:
            try:
                # Try to create a minimal controller to test
                test_controller = LEDController(num_pixels=1, pin=18)
                capabilities['led_controller_functional'] = True
            except Exception as e:
                capabilities['led_controller_functional'] = False
                capabilities['led_controller_error'] = str(e)
        
        # Test GPIO availability
        if GPIO:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.cleanup()
                capabilities['gpio_functional'] = True
            except Exception as e:
                capabilities['gpio_functional'] = False
                capabilities['gpio_error'] = str(e)
        
        return jsonify({
            'success': True,
            'capabilities': capabilities
        })
        
    except Exception as e:
        logger.error(f"Error getting system capabilities: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get capabilities: {str(e)}'
        }), 500

# Sequence implementation functions
def _run_rainbow_sequence(controller, led_count, duration, speed, brightness, test_id):
    """Run rainbow sequence"""
    start_time = time.time()
    hue_step = 360.0 / led_count
    
    while time.time() - start_time < duration:
        with test_lock:
            if test_id in active_tests and active_tests[test_id]['status'] == 'stopping':
                break
        
        for i in range(led_count):
            hue = (i * hue_step + (time.time() - start_time) * speed * 60) % 360
            color = _hue_to_rgb(hue)
            controller.turn_on_led(i, color, brightness, auto_show=False)
        
        controller.show()
        
        # Emit progress update
        progress = min(100, (time.time() - start_time) / duration * 100)
        emit_test_event('led_sequence_progress', {
            'test_id': test_id,
            'progress': progress,
            'current_step': int(progress * led_count / 100)
        })
        
        time.sleep(0.05)  # 20 FPS

def _run_chase_sequence(controller, led_count, duration, speed, brightness, colors, test_id):
    """Run chase sequence"""
    start_time = time.time()
    chase_length = 5
    color_index = 0
    
    while time.time() - start_time < duration:
        with test_lock:
            if test_id in active_tests and active_tests[test_id]['status'] == 'stopping':
                break
        
        controller.turn_off_all(auto_show=False)
        
        position = int((time.time() - start_time) * speed * 10) % led_count
        color = colors[color_index % len(colors)]
        
        for i in range(chase_length):
            led_pos = (position + i) % led_count
            fade_brightness = brightness * (1.0 - i / chase_length)
            controller.turn_on_led(led_pos, tuple(color), fade_brightness, auto_show=False)
        
        controller.show()
        
        # Change color every few seconds
        if int(time.time() - start_time) % 3 == 0:
            color_index += 1
        
        progress = min(100, (time.time() - start_time) / duration * 100)
        emit_test_event('led_sequence_progress', {
            'test_id': test_id,
            'progress': progress,
            'current_step': position
        })
        
        time.sleep(0.1)

def _run_fade_sequence(controller, led_count, duration, speed, brightness, colors, test_id):
    """Run fade sequence"""
    start_time = time.time()
    color_index = 0
    
    while time.time() - start_time < duration:
        with test_lock:
            if test_id in active_tests and active_tests[test_id]['status'] == 'stopping':
                break
        
        # Calculate fade brightness using sine wave
        fade_factor = (math.sin((time.time() - start_time) * speed * 2) + 1) / 2
        current_brightness = brightness * fade_factor
        
        color = colors[color_index % len(colors)]
        
        for i in range(led_count):
            controller.turn_on_led(i, tuple(color), current_brightness, auto_show=False)
        
        controller.show()
        
        # Change color every cycle
        cycle_duration = 2.0 / speed
        if int((time.time() - start_time) / cycle_duration) > color_index:
            color_index += 1
        
        progress = min(100, (time.time() - start_time) / duration * 100)
        emit_test_event('led_sequence_progress', {
            'test_id': test_id,
            'progress': progress,
            'fade_factor': fade_factor
        })
        
        time.sleep(0.05)

def _run_piano_keys_sequence(controller, led_count, duration, brightness, test_id):
    """Run piano keys sequence (white and black key pattern)"""
    start_time = time.time()
    
    # Standard piano pattern (simplified)
    white_key_pattern = [0, 2, 4, 5, 7, 9, 11]  # C major scale
    
    while time.time() - start_time < duration:
        with test_lock:
            if test_id in active_tests and active_tests[test_id]['status'] == 'stopping':
                break
        
        controller.turn_off_all(auto_show=False)
        
        # Animate through the pattern
        animation_step = int((time.time() - start_time) * 2) % len(white_key_pattern)
        
        for i in range(led_count):
            key_position = i % 12  # 12-tone chromatic scale
            
            if key_position in white_key_pattern:
                # White key
                if key_position == white_key_pattern[animation_step]:
                    color = (255, 255, 0)  # Yellow for active white key
                else:
                    color = (255, 255, 255)  # White for inactive white keys
                controller.turn_on_led(i, color, brightness * 0.8, auto_show=False)
            else:
                # Black key
                color = (64, 64, 64)  # Dark gray for black keys
                controller.turn_on_led(i, color, brightness * 0.3, auto_show=False)
        
        controller.show()
        
        progress = min(100, (time.time() - start_time) / duration * 100)
        emit_test_event('led_sequence_progress', {
            'test_id': test_id,
            'progress': progress,
            'current_key': animation_step
        })
        
        time.sleep(0.5)

def _run_custom_sequence(controller, led_count, duration, pattern, test_id):
    """Run custom sequence from pattern data"""
    start_time = time.time()
    
    if not pattern:
        pattern = [{'leds': list(range(led_count)), 'color': [255, 255, 255], 'duration': 1.0}]
    
    while time.time() - start_time < duration:
        with test_lock:
            if test_id in active_tests and active_tests[test_id]['status'] == 'stopping':
                break
        
        for step_index, step in enumerate(pattern):
            step_start = time.time()
            step_duration = step.get('duration', 1.0)
            leds = step.get('leds', [])
            color = step.get('color', [255, 255, 255])
            step_brightness = step.get('brightness', 1.0)
            
            controller.turn_off_all(auto_show=False)
            
            for led_index in leds:
                if 0 <= led_index < led_count:
                    controller.turn_on_led(led_index, tuple(color), step_brightness, auto_show=False)
            
            controller.show()
            
            progress = min(100, (time.time() - start_time) / duration * 100)
            emit_test_event('led_sequence_progress', {
                'test_id': test_id,
                'progress': progress,
                'current_step': step_index,
                'total_steps': len(pattern)
            })
            
            # Wait for step duration or until sequence should stop
            while time.time() - step_start < step_duration:
                with test_lock:
                    if test_id in active_tests and active_tests[test_id]['status'] == 'stopping':
                        return
                time.sleep(0.1)

def _hue_to_rgb(hue):
    """Convert hue (0-360) to RGB tuple"""
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(hue / 360.0, 1.0, 1.0)
    return (int(r * 255), int(g * 255), int(b * 255))

# Import math for fade sequence
import math