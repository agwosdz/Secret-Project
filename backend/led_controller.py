import logging
import os
from typing import Optional

# Force the use of /dev/gpiomem instead of /dev/mem for safer GPIO access
# This must be set BEFORE importing any GPIO libraries
os.environ['BLINKA_USE_GPIOMEM'] = '1'
os.environ['BLINKA_FORCEBOARD'] = 'RASPBERRY_PI_ZERO_2_W'  # Pi Zero 2 W model
os.environ['BLINKA_FORCECHIP'] = 'BCM2XXX'

try:
    import board
    import neopixel
    HARDWARE_AVAILABLE = True
    logging.info("Hardware libraries loaded with forced /dev/gpiomem usage")
except (ImportError, NotImplementedError) as e:
    logging.warning(f"Hardware libraries not available: {e}")
    HARDWARE_AVAILABLE = False
    board = None
    neopixel = None

class LEDController:
    """Controller for WS2812B LED strip using Adafruit NeoPixel library."""
    
    def __init__(self, pin=None, num_pixels=30, brightness=0.3):
        """
        Initialize LED controller.
        
        Args:
            pin: GPIO pin for LED strip (default: D18 if available)
            num_pixels: Number of LEDs in strip (default: 30)
            brightness: LED brightness 0.0-1.0 (default: 0.3)
        """
        self.logger = logging.getLogger(__name__)
        
        if not HARDWARE_AVAILABLE:
            self.logger.warning("Hardware not available - running in simulation mode")
            self.pin = None
            self.num_pixels = num_pixels
            self.brightness = brightness
            self.pixels = None
            self._led_state = [(0, 0, 0)] * num_pixels  # Track LED state for simulation
            return
            
        if pin is None:
            pin = board.D18
            
        self.pin = pin
        self.num_pixels = num_pixels
        self.brightness = brightness
        self.pixels: Optional[neopixel.NeoPixel] = None
        self._led_state = [(0, 0, 0)] * num_pixels  # Track current LED state
        self._pending_updates = False  # Track if updates are pending
        
        try:
            self.pixels = neopixel.NeoPixel(
                pin, num_pixels, brightness=brightness, auto_write=False
            )
            self.logger.info(f"LED controller initialized with {num_pixels} pixels on pin {pin}")
        except Exception as e:
            self.logger.error(f"Failed to initialize LED controller: {e}")
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
                
            if not self.pixels:
                raise RuntimeError("LED controller not initialized")
            
            self.pixels[index] = color
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
                
            if not self.pixels:
                raise RuntimeError("LED controller not initialized")
            
            if self._pending_updates:
                self.pixels.show()
                self._pending_updates = False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update LED strip: {e}")
            return False
    
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
                
            if not self.pixels:
                raise RuntimeError("LED controller not initialized")
            
            self.pixels.fill((0, 0, 0))
            self.pixels.show()
            self._pending_updates = False
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
                
            if self.pixels:
                # Turn off all LEDs before cleanup
                self.pixels.fill((0, 0, 0))
                self.pixels.show()
                self.pixels.deinit()
                self.pixels = None
                self.logger.info("LED controller cleaned up successfully")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()