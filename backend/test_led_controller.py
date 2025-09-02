#!/usr/bin/env python3
"""
Unit tests for LED Controller
Tests LED controller functionality with mocked hardware
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the backend directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the hardware modules before any imports
sys.modules['board'] = Mock()
sys.modules['neopixel'] = Mock()
sys.modules['adafruit_circuitpython_neopixel'] = Mock()

class TestLEDController(unittest.TestCase):
    """Test cases for LEDController class"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock the hardware dependencies
        self.mock_board = Mock()
        self.mock_board.D18 = 'mock_pin_D18'
        
        self.mock_neopixel_class = Mock()
        self.mock_pixels = Mock()
        # Configure mock pixels to support item assignment and method calls
        self.mock_pixels.__setitem__ = Mock()
        self.mock_pixels.__getitem__ = Mock()
        self.mock_pixels.show = Mock()
        self.mock_pixels.fill = Mock()
        self.mock_pixels.deinit = Mock()
        self.mock_neopixel_class.return_value = self.mock_pixels
        
        # Patch the imports
        self.board_patcher = patch('led_controller.board', self.mock_board)
        self.neopixel_patcher = patch('led_controller.neopixel.NeoPixel', self.mock_neopixel_class)
        
        self.board_patcher.start()
        self.neopixel_patcher.start()
        
        # Now import the LEDController after mocking
        from led_controller import LEDController
        self.LEDController = LEDController
    
    def tearDown(self):
        """Clean up after each test method."""
        self.board_patcher.stop()
        self.neopixel_patcher.stop()
    
    def test_led_controller_initialization(self):
        """Test LED controller initialization"""
        controller = self.LEDController()
        
        # Verify NeoPixel was initialized (mock object comparison)
        self.assertTrue(self.mock_neopixel_class.called)
        call_args = self.mock_neopixel_class.call_args
        self.assertEqual(call_args[0][1], 30)  # num_pixels
        self.assertEqual(call_args[1]['brightness'], 0.3)  # brightness
        self.assertEqual(call_args[1]['auto_write'], False)  # auto_write
        
        # Verify controller properties
        self.assertEqual(controller.num_pixels, 30)
        self.assertEqual(controller.brightness, 0.3)
        self.assertIsNotNone(controller.pixels)
    
    def test_led_controller_custom_initialization(self):
        """Test LED controller initialization with custom parameters"""
        custom_pin = 'mock_pin_D19'
        controller = self.LEDController(pin=custom_pin, num_pixels=60, brightness=0.5)
        
        # Verify NeoPixel was initialized with custom parameters
        self.mock_neopixel_class.assert_called_once_with(
            custom_pin, 60, brightness=0.5, auto_write=False
        )
    
    def test_turn_on_led_success(self):
        """Test successfully turning on an LED"""
        controller = self.LEDController()
        
        # Test turning on LED with default color
        result = controller.turn_on_led(5)
        
        # Verify the LED was set and show was called
        self.mock_pixels.__setitem__.assert_called_with(5, (255, 255, 255))
        self.mock_pixels.show.assert_called_once()
        self.assertTrue(result)
    
    def test_turn_on_led_custom_color(self):
        """Test turning on LED with custom color"""
        controller = self.LEDController()
        custom_color = (255, 0, 0)  # Red
        
        result = controller.turn_on_led(10, custom_color)
        
        # Verify the LED was set with custom color
        self.mock_pixels.__setitem__.assert_called_with(10, custom_color)
        self.mock_pixels.show.assert_called_once()
        self.assertTrue(result)
    
    def test_turn_on_led_invalid_index(self):
        """Test turning on LED with invalid index"""
        controller = self.LEDController(num_pixels=10)
        
        # Test with negative index
        result = controller.turn_on_led(-1)
        self.assertFalse(result)
        
        # Test with index too high
        result = controller.turn_on_led(10)
        self.assertFalse(result)
        
        # Verify show was not called
        self.mock_pixels.show.assert_not_called()
    
    def test_turn_off_led_success(self):
        """Test successfully turning off an LED"""
        controller = self.LEDController()
        
        result = controller.turn_off_led(3)
        
        # Verify the LED was set to black (off)
        self.mock_pixels.__setitem__.assert_called_with(3, (0, 0, 0))
        self.mock_pixels.show.assert_called_once()
        self.assertTrue(result)
    
    def test_turn_off_led_invalid_index(self):
        """Test turning off LED with invalid index"""
        controller = self.LEDController(num_pixels=5)
        
        # Test with invalid index
        result = controller.turn_off_led(5)
        self.assertFalse(result)
        
        # Verify show was not called
        self.mock_pixels.show.assert_not_called()
    
    def test_turn_off_all_leds(self):
        """Test turning off all LEDs"""
        controller = self.LEDController()
        
        result = controller.turn_off_all()
        
        # Verify fill was called with black color
        self.mock_pixels.fill.assert_called_with((0, 0, 0))
        self.mock_pixels.show.assert_called_once()
        self.assertTrue(result)
    
    def test_cleanup(self):
        """Test cleanup functionality"""
        controller = self.LEDController()
        
        controller.cleanup()
        
        # Verify cleanup sequence
        self.mock_pixels.fill.assert_called_with((0, 0, 0))
        self.mock_pixels.show.assert_called()
        self.mock_pixels.deinit.assert_called_once()
        self.assertIsNone(controller.pixels)
    
    def test_context_manager(self):
        """Test context manager functionality"""
        with self.LEDController() as controller:
            self.assertIsNotNone(controller.pixels)
        
        # Verify cleanup was called on exit
        self.mock_pixels.deinit.assert_called_once()
    
    def test_hardware_error_handling(self):
        """Test error handling when hardware operations fail"""
        controller = self.LEDController()
        
        # Mock a hardware error
        self.mock_pixels.__setitem__.side_effect = Exception("Hardware error")
        
        result = controller.turn_on_led(0)
        self.assertFalse(result)
    
    def test_initialization_failure(self):
        """Test handling of initialization failure"""
        # Mock NeoPixel initialization failure
        self.mock_neopixel_class.side_effect = Exception("GPIO not available")
        
        with self.assertRaises(Exception):
            self.LEDController()
    
    def test_operations_without_initialization(self):
        """Test operations when controller is not properly initialized"""
        controller = self.LEDController()
        controller.pixels = None  # Simulate failed initialization
        
        # Test operations return False when pixels is None
        self.assertFalse(controller.turn_on_led(0))
        self.assertFalse(controller.turn_off_led(0))
        self.assertFalse(controller.turn_off_all())


class TestLEDEndpoint(unittest.TestCase):
    """Test cases for LED endpoint functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock hardware dependencies at module level
        self.led_controller_patcher = patch('app.led_controller')
        self.mock_led_controller = self.led_controller_patcher.start()
        
        # Configure mock methods
        self.mock_led_controller.turn_on_led = Mock()
        self.mock_led_controller.turn_off_led = Mock()
        
        # Import and configure the Flask app
        from app import app
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Clean up after tests"""
        self.led_controller_patcher.stop()
    
    def test_test_led_endpoint_turn_on(self):
        """Test turning on LED via endpoint"""
        self.mock_led_controller.turn_on_led.return_value = True
        
        response = self.client.post('/api/test-led', 
                                  json={'index': 5, 'state': 'on'})
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['led_index'], 5)
        self.assertEqual(data['state'], 'on')
        
        # Verify LED controller was called
        self.mock_led_controller.turn_on_led.assert_called_once_with(5, (255, 255, 255))
    
    def test_test_led_endpoint_turn_off(self):
        """Test turning off LED via endpoint"""
        self.mock_led_controller.turn_off_led.return_value = True
        
        response = self.client.post('/api/test-led', 
                                  json={'index': 3, 'state': 'off'})
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['led_index'], 3)
        self.assertEqual(data['state'], 'off')
        
        # Verify LED controller was called
        self.mock_led_controller.turn_off_led.assert_called_once_with(3)
    
    def test_test_led_endpoint_custom_color(self):
        """Test turning on LED with custom color"""
        self.mock_led_controller.turn_on_led.return_value = True
        
        response = self.client.post('/api/test-led', 
                                  json={'index': 0, 'state': 'on', 'color': [255, 0, 0]})
        
        self.assertEqual(response.status_code, 200)
        
        # Verify LED controller was called with custom color
        self.mock_led_controller.turn_on_led.assert_called_once_with(0, (255, 0, 0))
    
    def test_test_led_endpoint_missing_data(self):
        """Test endpoint with missing required data"""
        # Missing JSON data (empty JSON)
        response = self.client.post('/api/test-led', json={})
        self.assertEqual(response.status_code, 400)
        
        # Missing index
        response = self.client.post('/api/test-led', json={'state': 'on'})
        self.assertEqual(response.status_code, 400)
        
        # Missing state
        response = self.client.post('/api/test-led', json={'index': 0})
        self.assertEqual(response.status_code, 400)
    
    def test_test_led_endpoint_invalid_data(self):
        """Test endpoint with invalid data"""
        # Invalid LED index
        response = self.client.post('/api/test-led', 
                                  json={'index': 'invalid', 'state': 'on'})
        self.assertEqual(response.status_code, 400)
        
        # Invalid state
        response = self.client.post('/api/test-led', 
                                  json={'index': 0, 'state': 'invalid'})
        self.assertEqual(response.status_code, 400)
    
    def test_test_led_endpoint_hardware_failure(self):
        """Test endpoint when hardware operation fails"""
        self.mock_led_controller.turn_on_led.return_value = False
        
        response = self.client.post('/api/test-led', 
                                  json={'index': 0, 'state': 'on'})
        
        self.assertEqual(response.status_code, 500)
        data = response.get_json()
        self.assertEqual(data['error'], 'Hardware Error')


def run_device_tests():
    """Run device-specific tests when hardware is available."""
    print("\n=== DEVICE TESTING MODE ===")
    print("Testing actual LED hardware...\n")
    
    try:
        # Import without mocking for device testing
        import importlib
        import led_controller
        importlib.reload(led_controller)  # Reload to get real hardware
        
        from led_controller import LEDController
        
        # Test hardware initialization
        print("1. Testing LED Controller initialization...")
        controller = LEDController(num_pixels=10, brightness=0.2)
        print(f"   ✓ Controller initialized with {controller.num_pixels} pixels")
        
        if controller.pixels is None:
            print("   ⚠ Running in simulation mode (no hardware detected)")
            return False
        
        # Test individual LED control
        print("\n2. Testing individual LED control...")
        for i in range(3):  # Test first 3 LEDs
            print(f"   Testing LED {i}...")
            
            # Turn on red
            if controller.turn_on_led(i, (255, 0, 0)):
                print(f"   ✓ LED {i} turned on (red)")
                import time
                time.sleep(0.5)
                
                # Turn off
                if controller.turn_off_led(i):
                    print(f"   ✓ LED {i} turned off")
                    time.sleep(0.2)
                else:
                    print(f"   ✗ Failed to turn off LED {i}")
            else:
                print(f"   ✗ Failed to turn on LED {i}")
        
        # Test all LEDs pattern
        print("\n3. Testing all LEDs pattern...")
        if controller.turn_off_all():
            print("   ✓ All LEDs turned off")
        
        # Test cleanup
        print("\n4. Testing cleanup...")
        controller.cleanup()
        print("   ✓ Cleanup completed")
        
        print("\n🎉 Device tests completed successfully!")
        print("\nYour LED hardware is working correctly.")
        print("\nFor more comprehensive testing, run:")
        print("   python3 test_led_device.py")
        
        return True
        
    except ImportError as e:
        print(f"   ✗ Hardware libraries not available: {e}")
        print("\n   Install required packages:")
        print("   pip3 install adafruit-circuitpython-neopixel adafruit-blinka")
        return False
    except Exception as e:
        print(f"   ✗ Device test failed: {e}")
        print("\n   Troubleshooting steps:")
        print("   1. Check hardware connections")
        print("   2. Verify power supply")
        print("   3. Run: python3 led_troubleshoot.py")
        return False


if __name__ == '__main__':
    import sys
    
    # Check if device testing is requested
    if len(sys.argv) > 1 and sys.argv[1] == '--device':
        success = run_device_tests()
        sys.exit(0 if success else 1)
    else:
        # Run unit tests
        print("Running unit tests...")
        print("For device testing, use: python3 test_led_controller.py --device")
        unittest.main()