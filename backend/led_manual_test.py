#!/usr/bin/env python3
"""
Manual LED Testing Tool
Interactive tool for testing individual LEDs and patterns

Usage:
    python3 led_manual_test.py
"""

import sys
import time
import logging
from typing import Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ManualLEDTester:
    """Interactive LED testing tool."""
    
    def __init__(self):
        """Initialize the manual tester."""
        self.controller = None
        self.running = True
        
        # Predefined colors
        self.colors = {
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'white': (255, 255, 255),
            'yellow': (255, 255, 0),
            'cyan': (0, 255, 255),
            'magenta': (255, 0, 255),
            'orange': (255, 165, 0),
            'purple': (128, 0, 128),
            'pink': (255, 192, 203),
            'off': (0, 0, 0)
        }
    
    def initialize_controller(self) -> bool:
        """Initialize the LED controller."""
        try:
            from led_controller import LEDController
            
            print("Initializing LED controller...")
            
            # Get configuration from user
            num_pixels = self.get_int_input("Number of LEDs", default=30, min_val=1, max_val=300)
            brightness = self.get_float_input("Brightness (0.0-1.0)", default=0.3, min_val=0.0, max_val=1.0)
            
            self.controller = LEDController(num_pixels=num_pixels, brightness=brightness)
            
            if self.controller.pixels is None:
                print("⚠ Controller initialized in simulation mode (no hardware detected)")
                print("Commands will be logged but LEDs won't actually light up.")
            else:
                print(f"✓ Controller initialized with {num_pixels} LEDs at {brightness*100:.0f}% brightness")
            
            return True
            
        except ImportError as e:
            print(f"✗ Failed to import LED controller: {e}")
            print("Make sure required packages are installed:")
            print("  pip3 install rpi_ws281x")
            return False
        except Exception as e:
            print(f"✗ Failed to initialize controller: {e}")
            return False
    
    def get_int_input(self, prompt: str, default: int, min_val: int = None, max_val: int = None) -> int:
        """Get integer input from user with validation."""
        while True:
            try:
                response = input(f"{prompt} [{default}]: ").strip()
                if not response:
                    return default
                
                value = int(response)
                
                if min_val is not None and value < min_val:
                    print(f"Value must be >= {min_val}")
                    continue
                
                if max_val is not None and value > max_val:
                    print(f"Value must be <= {max_val}")
                    continue
                
                return value
                
            except ValueError:
                print("Please enter a valid integer")
    
    def get_float_input(self, prompt: str, default: float, min_val: float = None, max_val: float = None) -> float:
        """Get float input from user with validation."""
        while True:
            try:
                response = input(f"{prompt} [{default}]: ").strip()
                if not response:
                    return default
                
                value = float(response)
                
                if min_val is not None and value < min_val:
                    print(f"Value must be >= {min_val}")
                    continue
                
                if max_val is not None and value > max_val:
                    print(f"Value must be <= {max_val}")
                    continue
                
                return value
                
            except ValueError:
                print("Please enter a valid number")
    
    def parse_color(self, color_input: str) -> Optional[Tuple[int, int, int]]:
        """Parse color input from user."""
        color_input = color_input.lower().strip()
        
        # Check predefined colors
        if color_input in self.colors:
            return self.colors[color_input]
        
        # Try to parse RGB values
        if ',' in color_input:
            try:
                parts = [int(x.strip()) for x in color_input.split(',')]
                if len(parts) == 3 and all(0 <= x <= 255 for x in parts):
                    return tuple(parts)
            except ValueError:
                pass
        
        return None
    
    def show_help(self):
        """Show available commands."""
        print("\n=== MANUAL LED TESTER COMMANDS ===")
        print("\nBasic Commands:")
        print("  on <led> [color]     - Turn on LED (e.g., 'on 5 red' or 'on 0 255,0,0')")
        print("  off <led>            - Turn off specific LED (e.g., 'off 5')")
        print("  all <color>          - Set all LEDs to color (e.g., 'all blue')")
        print("  clear                - Turn off all LEDs")
        print("\nPattern Commands:")
        print("  rainbow              - Show rainbow pattern")
        print("  chase <color>        - Color chase effect")
        print("  blink <led> <color>  - Blink specific LED")
        print("  fade <color>         - Fade in/out effect")
        print("\nUtility Commands:")
        print("  colors               - Show available colors")
        print("  status               - Show controller status")
        print("  help                 - Show this help")
        print("  quit                 - Exit the tester")
        print("\nColor Examples:")
        print("  Named colors: red, green, blue, white, yellow, cyan, magenta, orange, purple, pink")
        print("  RGB values: 255,0,0 (red), 0,255,0 (green), 0,0,255 (blue)")
        print("  Turn off: off, 0,0,0")
    
    def show_colors(self):
        """Show available predefined colors."""
        print("\nAvailable Colors:")
        for name, rgb in self.colors.items():
            print(f"  {name:10} - {rgb}")
    
    def show_status(self):
        """Show controller status."""
        if not self.controller:
            print("Controller not initialized")
            return
        
        print(f"\nController Status:")
        print(f"  Number of LEDs: {self.controller.num_pixels}")
        print(f"  Brightness: {self.controller.brightness}")
        print(f"  Hardware mode: {'Yes' if self.controller.pixels else 'No (simulation)'}")
    
    def cmd_on(self, args: list):
        """Turn on specific LED."""
        if len(args) < 1:
            print("Usage: on <led_index> [color]")
            return
        
        try:
            led_index = int(args[0])
            color = (255, 255, 255)  # Default white
            
            if len(args) > 1:
                parsed_color = self.parse_color(' '.join(args[1:]))
                if parsed_color:
                    color = parsed_color
                else:
                    print(f"Invalid color: {' '.join(args[1:])}")
                    return
            
            if self.controller.turn_on_led(led_index, color):
                print(f"✓ LED {led_index} turned on with color {color}")
            else:
                print(f"✗ Failed to turn on LED {led_index}")
                
        except ValueError:
            print("Invalid LED index")
    
    def cmd_off(self, args: list):
        """Turn off specific LED."""
        if len(args) < 1:
            print("Usage: off <led_index>")
            return
        
        try:
            led_index = int(args[0])
            
            if self.controller.turn_off_led(led_index):
                print(f"✓ LED {led_index} turned off")
            else:
                print(f"✗ Failed to turn off LED {led_index}")
                
        except ValueError:
            print("Invalid LED index")
    
    def cmd_all(self, args: list):
        """Set all LEDs to specified color."""
        if len(args) < 1:
            print("Usage: all <color>")
            return
        
        color = self.parse_color(' '.join(args))
        if not color:
            print(f"Invalid color: {' '.join(args)}")
            return
        
        led_data = {i: color for i in range(self.controller.num_pixels)}
        
        if self.controller.set_multiple_leds(led_data):
            print(f"✓ All LEDs set to color {color}")
        else:
            print("✗ Failed to set all LEDs")
    
    def cmd_clear(self, args: list):
        """Turn off all LEDs."""
        if self.controller.turn_off_all():
            print("✓ All LEDs turned off")
        else:
            print("✗ Failed to turn off all LEDs")
    
    def cmd_rainbow(self, args: list):
        """Show rainbow pattern."""
        print("Showing rainbow pattern...")
        
        try:
            import math
            
            led_data = {}
            for i in range(self.controller.num_pixels):
                hue = (i * 360 / self.controller.num_pixels) % 360
                
                # Convert HSV to RGB
                c = 1.0
                x = c * (1 - abs((hue / 60) % 2 - 1))
                
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
                
                led_data[i] = (int(r * 255), int(g * 255), int(b * 255))
            
            if self.controller.set_multiple_leds(led_data):
                print("✓ Rainbow pattern displayed")
            else:
                print("✗ Failed to display rainbow pattern")
                
        except Exception as e:
            print(f"✗ Error creating rainbow pattern: {e}")
    
    def cmd_chase(self, args: list):
        """Color chase effect."""
        if len(args) < 1:
            print("Usage: chase <color>")
            return
        
        color = self.parse_color(' '.join(args))
        if not color:
            print(f"Invalid color: {' '.join(args)}")
            return
        
        print(f"Running chase effect with color {color}... (Press Ctrl+C to stop)")
        
        try:
            while True:
                for i in range(self.controller.num_pixels):
                    # Turn off all LEDs
                    self.controller.turn_off_all()
                    # Turn on current LED
                    self.controller.turn_on_led(i, color)
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            self.controller.turn_off_all()
            print("\nChase effect stopped")
    
    def cmd_blink(self, args: list):
        """Blink specific LED."""
        if len(args) < 2:
            print("Usage: blink <led_index> <color>")
            return
        
        try:
            led_index = int(args[0])
            color = self.parse_color(' '.join(args[1:]))
            
            if not color:
                print(f"Invalid color: {' '.join(args[1:])}")
                return
            
            print(f"Blinking LED {led_index} with color {color}... (Press Ctrl+C to stop)")
            
            while True:
                self.controller.turn_on_led(led_index, color)
                time.sleep(0.5)
                self.controller.turn_off_led(led_index)
                time.sleep(0.5)
                
        except ValueError:
            print("Invalid LED index")
        except KeyboardInterrupt:
            self.controller.turn_off_led(led_index)
            print("\nBlink stopped")
    
    def process_command(self, command: str):
        """Process user command."""
        parts = command.strip().split()
        if not parts:
            return
        
        cmd = parts[0].lower()
        args = parts[1:]
        
        if cmd == 'help':
            self.show_help()
        elif cmd == 'colors':
            self.show_colors()
        elif cmd == 'status':
            self.show_status()
        elif cmd == 'quit' or cmd == 'exit':
            self.running = False
        elif cmd == 'on':
            self.cmd_on(args)
        elif cmd == 'off':
            self.cmd_off(args)
        elif cmd == 'all':
            self.cmd_all(args)
        elif cmd == 'clear':
            self.cmd_clear(args)
        elif cmd == 'rainbow':
            self.cmd_rainbow(args)
        elif cmd == 'chase':
            self.cmd_chase(args)
        elif cmd == 'blink':
            self.cmd_blink(args)
        else:
            print(f"Unknown command: {cmd}")
            print("Type 'help' for available commands")
    
    def run(self):
        """Run the interactive tester."""
        print("🔧 Manual LED Testing Tool")
        print("=========================\n")
        
        if not self.initialize_controller():
            return False
        
        print("\nManual LED tester ready!")
        print("Type 'help' for available commands, 'quit' to exit.\n")
        
        try:
            while self.running:
                try:
                    command = input("LED> ").strip()
                    if command:
                        self.process_command(command)
                except EOFError:
                    break
                except KeyboardInterrupt:
                    print("\nUse 'quit' to exit")
        
        finally:
            if self.controller:
                print("\nCleaning up...")
                self.controller.cleanup()
                print("✓ Cleanup completed")
        
        return True

def main():
    """Main function."""
    tester = ManualLEDTester()
    
    try:
        success = tester.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()