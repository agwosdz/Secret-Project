import logging
from typing import Optional

try:
    import board
    import neopixel
    HARDWARE_AVAILABLE = True
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
            return
            
        if pin is None:
            pin = board.D18
            
        self.pin = pin
        self.num_pixels = num_pixels
        self.brightness = brightness
        self.pixels: Optional[neopixel.NeoPixel] = None
        
        try:
            self.pixels = neopixel.NeoPixel(
                pin, num_pixels, brightness=brightness, auto_write=False
            )
            self.logger.info(f"LED controller initialized with {num_pixels} pixels on pin {pin}")
        except Exception as e:
            self.logger.error(f"Failed to initialize LED controller: {e}")
            raise
    
    def turn_on_led(self, index: int, color: tuple = (255, 255, 255)) -> bool:
        """
        Turn on a specific LED.
        
        Args:
            index: LED index (0-based)
            color: RGB color tuple (default: white)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not HARDWARE_AVAILABLE:
                self.logger.info(f"[SIMULATION] LED {index} turned on with color {color}")
                return True
                
            if not self.pixels:
                raise RuntimeError("LED controller not initialized")
                
            if not 0 <= index < self.num_pixels:
                raise ValueError(f"LED index {index} out of range (0-{self.num_pixels-1})")
            
            self.pixels[index] = color
            self.pixels.show()
            self.logger.info(f"LED {index} turned on with color {color}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to turn on LED {index}: {e}")
            return False
    
    def turn_off_led(self, index: int) -> bool:
        """
        Turn off a specific LED.
        
        Args:
            index: LED index (0-based)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not HARDWARE_AVAILABLE:
                self.logger.info(f"[SIMULATION] LED {index} turned off")
                return True
                
            if not self.pixels:
                raise RuntimeError("LED controller not initialized")
                
            if not 0 <= index < self.num_pixels:
                raise ValueError(f"LED index {index} out of range (0-{self.num_pixels-1})")
            
            self.pixels[index] = (0, 0, 0)  # Turn off (black)
            self.pixels.show()
            self.logger.info(f"LED {index} turned off")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to turn off LED {index}: {e}")
            return False
    
    def turn_off_all(self) -> bool:
        """
        Turn off all LEDs.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not HARDWARE_AVAILABLE:
                self.logger.info("[SIMULATION] All LEDs turned off")
                return True
                
            if not self.pixels:
                raise RuntimeError("LED controller not initialized")
            
            self.pixels.fill((0, 0, 0))
            self.pixels.show()
            self.logger.info("All LEDs turned off")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to turn off all LEDs: {e}")
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