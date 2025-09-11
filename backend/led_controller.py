import logging
from typing import Optional

try:
    from rpi_ws281x import PixelStrip, Color
    import RPi.GPIO as GPIO
    HARDWARE_AVAILABLE = True
    logging.info("rpi_ws281x library loaded successfully")
except ImportError as e:
    logging.warning(f"rpi_ws281x library not available: {e}")
    HARDWARE_AVAILABLE = False
    PixelStrip = None
    Color = None
    GPIO = None

try:
    from config import get_config
except ImportError:
    logging.warning("Config module not available, using defaults")
    def get_config(key, default):
        return default

class LEDController:
    """Controller for WS2812B LED strip using rpi_ws281x library."""
    
    def __init__(self, pin=None, num_pixels=None, brightness=None):
        """
        Initialize LED controller.
        
        Args:
            pin: GPIO pin for LED strip (uses config if None)
            num_pixels: Number of LEDs in strip (uses config if None)
            brightness: LED brightness 0.0-1.0 (uses config if None)
        """
        self.logger = logging.getLogger(__name__)
        
        # Load configuration values if not provided
        self.pin = pin if pin is not None else get_config('gpio_pin', 19)
        self.num_pixels = num_pixels if num_pixels is not None else get_config('led_count', 30)
        self.brightness = brightness if brightness is not None else get_config('brightness', 0.3)
        
        # Get LED orientation setting
        self.led_orientation = get_config('led_orientation', 'normal')
        
        if not HARDWARE_AVAILABLE:
            self.logger.warning("Hardware not available - running in simulation mode")
            self.pixels = None
            self._led_state = [(0, 0, 0)] * self.num_pixels  # Track LED state for simulation
            return
            
        self._led_state = [(0, 0, 0)] * self.num_pixels  # Track current LED state
        
        try:
            # rpi_ws281x configuration
            LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
            LED_DMA = 10          # DMA channel to use for generating signal (try 10)
            LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
            LED_CHANNEL = 1       # set to '1' for GPIOs 13, 19, 41, 45 or 53
            
            # Initialize rpi_ws281x strip
            self.pixels = PixelStrip(
                self.num_pixels,
                self.pin,
                LED_FREQ_HZ,
                LED_DMA,
                LED_INVERT,
                int(self.brightness * 255),  # Convert brightness to 0-255 range
                LED_CHANNEL
            )
            
            # Initialize the library (must be called once before other functions)
            self.pixels.begin()
            
            self.logger.info(f"LED controller initialized with {self.num_pixels} pixels on pin {self.pin} using rpi_ws281x")
        except Exception as e:
            self.logger.error(f"Failed to initialize LED controller: {e}")
            raise
    
    def _map_led_index(self, index: int) -> int:
        """
        Map logical LED index to physical LED index based on orientation.
        
        Args:
            index: Logical LED index (0-based)
            
        Returns:
            int: Physical LED index
        """
        if self.led_orientation == 'reversed':
            return self.num_pixels - 1 - index
        return index
    
    def turn_on_led(self, index: int, color: tuple = (255, 255, 255), auto_show: bool = True) -> bool:
        """
        Turn on a specific LED.
        
        Args:
            index: Logical LED index (0-based)
            color: RGB color tuple (default: white)
            auto_show: Whether to immediately update the LED strip (default: True)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not 0 <= index < self.num_pixels:
                raise ValueError(f"LED index {index} out of range (0-{self.num_pixels-1})")
            
            # Map logical index to physical index based on orientation
            physical_index = self._map_led_index(index)
            
            # Check if color actually changed to avoid unnecessary updates
            if self._led_state[index] == color:
                return True
                
            self._led_state[index] = color
            
            if not HARDWARE_AVAILABLE:
                self.logger.debug(f"[SIMULATION] LED {index} (physical: {physical_index}) set to color {color}")
                return True
                
            if not self.pixels:
                raise RuntimeError("LED controller not initialized")
            
            # Set the pixel color using rpi_ws281x Color function
            # Convert RGB tuple to rpi_ws281x Color format
            r, g, b = color
            self.pixels.setPixelColor(physical_index, Color(r, g, b))
            
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
            
            # Update the LED strip
            self.pixels.show()
                
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
            
            # Turn off all pixels using rpi_ws281x
            for i in range(self.num_pixels):
                self.pixels.setPixelColor(i, Color(0, 0, 0))
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
                
            if self.pixels:
                # Turn off all LEDs before cleanup
                self._led_state = [(0, 0, 0)] * self.num_pixels
                for i in range(self.num_pixels):
                    self.pixels.setPixelColor(i, Color(0, 0, 0))
                self.pixels.show()
                
                # Clean up rpi_ws281x resources
                # Note: rpi_ws281x doesn't have explicit cleanup, but we set to None
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