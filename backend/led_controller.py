import logging
import os
from typing import Optional

# Use pigpio for more reliable GPIO access
os.environ['GPIOZERO_PIN_FACTORY'] = 'pigpio'

try:
    import pigpio
    import time
    HARDWARE_AVAILABLE = True
    logging.info("Pigpio library loaded successfully")
except ImportError as e:
    logging.warning(f"Pigpio library not available: {e}")
    HARDWARE_AVAILABLE = False
    pigpio = None

class LEDController:
    """Controller for WS2812B LED strip using pigpio library."""
    
    def __init__(self, pin=18, num_pixels=30, brightness=0.3):
        """
        Initialize LED controller.
        
        Args:
            pin: GPIO pin for LED strip (default: 18)
            num_pixels: Number of LEDs in strip (default: 30)
            brightness: LED brightness 0.0-1.0 (default: 0.3)
        """
        self.logger = logging.getLogger(__name__)
        
        if not HARDWARE_AVAILABLE:
            self.logger.warning("Hardware not available - running in simulation mode")
            self.pin = pin
            self.num_pixels = num_pixels
            self.brightness = brightness
            self.pi = None
            self._led_state = [(0, 0, 0)] * num_pixels  # Track LED state for simulation
            self._pending_updates = False
            return
            
        self.pin = pin
        self.num_pixels = num_pixels
        self.brightness = brightness
        self.pi = None
        self._led_state = [(0, 0, 0)] * num_pixels  # Track current LED state
        self._pending_updates = False  # Track if updates are pending
        
        try:
            self.pi = pigpio.pi()
            if not self.pi.connected:
                raise RuntimeError("Could not connect to pigpio daemon")
            
            # Initialize WS2812B strip using pigpio's wave functionality
            self.pi.set_mode(self.pin, pigpio.OUTPUT)
            self.logger.info(f"LED controller initialized with {num_pixels} pixels on pin {pin} using pigpio")
        except Exception as e:
            self.logger.error(f"Failed to initialize LED controller: {e}")
            if self.pi:
                self.pi.stop()
            raise
    
    def turn_on_led(self, index: int, color: tuple = (255, 255, 255), auto_show: bool = True) -> bool:
        """
        Turn on a specific LED.
        
        Args:
            index: LED index (0-based)
            color: RGB color tuple (default: white)
            auto_show: Whether to immediately update the LED strip (default: True)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not 0 <= index < self.num_pixels:
                raise ValueError(f"LED index {index} out of range (0-{self.num_pixels-1})")
            
            # Check if color actually changed to avoid unnecessary updates
            if self._led_state[index] == color:
                return True
                
            self._led_state[index] = color
            
            if not HARDWARE_AVAILABLE:
                self.logger.debug(f"[SIMULATION] LED {index} set to color {color}")
                return True
                
            if not self.pi or not self.pi.connected:
                raise RuntimeError("LED controller not initialized")
            
            self._pending_updates = True
            
            if auto_show:
                self.show()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to turn on LED {index}: {e}")
            return False
    
    def turn_off_led(self, index: int, auto_show: bool = True) -> bool:
        """
        Turn off a specific LED.
        
        Args:
            index: LED index (0-based)
            auto_show: Whether to immediately update the LED strip (default: True)
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.turn_on_led(index, (0, 0, 0), auto_show)
    
    def show(self) -> bool:
        """
        Update the LED strip with pending changes.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not HARDWARE_AVAILABLE:
                return True
                
            if not self.pi or not self.pi.connected:
                raise RuntimeError("LED controller not initialized")
            
            if self._pending_updates:
                self._send_ws2812b_data()
                self._pending_updates = False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update LED strip: {e}")
            return False
    
    def _send_ws2812b_data(self):
        """Send WS2812B data using pigpio waves."""
        if not self.pi or not self.pi.connected:
            return
            
        # WS2812B timing (in microseconds)
        # 0 bit: 0.4us high, 0.85us low
        # 1 bit: 0.8us high, 0.45us low
        # Reset: >50us low
        
        waves = []
        
        for i in range(self.num_pixels):
            color = self._led_state[i]
            # Apply brightness
            r, g, b = [int(c * self.brightness) for c in color]
            
            # WS2812B expects GRB order
            for byte_val in [g, r, b]:
                for bit in range(7, -1, -1):
                    if (byte_val >> bit) & 1:
                        # Send '1' bit: 0.8us high, 0.45us low
                        waves.extend([
                            pigpio.pulse(1 << self.pin, 0, 800),   # 0.8us high
                            pigpio.pulse(0, 1 << self.pin, 450)    # 0.45us low
                        ])
                    else:
                        # Send '0' bit: 0.4us high, 0.85us low
                        waves.extend([
                            pigpio.pulse(1 << self.pin, 0, 400),   # 0.4us high
                            pigpio.pulse(0, 1 << self.pin, 850)    # 0.85us low
                        ])
        
        # Add reset pulse (>50us low)
        waves.append(pigpio.pulse(0, 1 << self.pin, 60000))  # 60us low
        
        # Clear any existing waves and add new ones
        self.pi.wave_clear()
        self.pi.wave_add_generic(waves)
        wave_id = self.pi.wave_create()
        
        if wave_id >= 0:
            self.pi.wave_send_once(wave_id)
            # Wait for transmission to complete
            while self.pi.wave_tx_busy():
                time.sleep(0.001)
            self.pi.wave_delete(wave_id)
    
    def turn_off_all(self) -> bool:
        """
        Turn off all LEDs.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update state tracking
            self._led_state = [(0, 0, 0)] * self.num_pixels
            
            if not HARDWARE_AVAILABLE:
                self.logger.debug("[SIMULATION] All LEDs turned off")
                return True
                
            if not self.pi or not self.pi.connected:
                raise RuntimeError("LED controller not initialized")
            
            self._pending_updates = True
            self.show()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to turn off all LEDs: {e}")
            return False
    
    def set_multiple_leds(self, led_data: dict, auto_show: bool = True) -> bool:
        """
        Set multiple LEDs at once for better performance.
        
        Args:
            led_data: Dictionary mapping LED index to color tuple
            auto_show: Whether to immediately update the LED strip (default: True)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            success = True
            for index, color in led_data.items():
                if not self.turn_on_led(index, color, auto_show=False):
                    success = False
            
            if auto_show and success:
                self.show()
                
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to set multiple LEDs: {e}")
            return False
    
    def cleanup(self):
        """
        Clean up GPIO resources.
        """
        try:
            if not HARDWARE_AVAILABLE:
                self.logger.info("[SIMULATION] LED controller cleaned up successfully")
                return
                
            if self.pi and self.pi.connected:
                # Turn off all LEDs before cleanup
                self._led_state = [(0, 0, 0)] * self.num_pixels
                self._pending_updates = True
                self.show()
                
                # Stop pigpio connection
                self.pi.stop()
                self.pi = None
                self.logger.info("LED controller cleaned up successfully")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()