#!/usr/bin/env python3
"""
Test script for the new note positioning algorithm
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import calculate_note_position, generate_density_based_mapping

def test_basic_positioning():
    """Test basic note positioning without offsets"""
    print("=== Basic Note Positioning Test ===")
    
    # Test parameters - now leds_per_meter represents total LEDs available
    total_leds = 245  # Total LEDs available for mapping
    strip_length = 4.1  # Not used in new algorithm but kept for compatibility
    
    print(f"Total LEDs available: {total_leds}")
    print(f"Piano keys: 88")
    print(f"Density: {total_leds / 88:.2f} LEDs per key")
    
    # Test some notes
    test_notes = [21, 40, 60, 80, 108]  # A0, E2, C4, G#5, C8
    
    for note in test_notes:
        position = calculate_note_position(
            note=note,
            leds_per_meter=total_leds,  # Now represents total LEDs
            strip_length=strip_length,
            led_count=total_leds,
            debug=True
        )
        print(f"Note {note}: LED position {position}")
    
    print()

def test_with_offsets():
    """Test note positioning with offsets and global shift"""
    print("=== Note Positioning with Offsets Test ===")
    
    # Test parameters
    leds_per_meter = 60
    strip_length = 4.1
    led_count = int(leds_per_meter * strip_length)
    
    # Example offsets: shift notes above 60 by 5 positions
    note_offsets = {60: 5}
    global_shift = 2
    
    print(f"Note offsets: {note_offsets}")
    print(f"Global shift: {global_shift}")
    
    # Test some notes
    test_notes = [21, 40, 60, 61, 80, 108]
    
    for note in test_notes:
        position = calculate_note_position(
            note=note,
            leds_per_meter=leds_per_meter,
            strip_length=strip_length,
            note_offsets=note_offsets,
            global_shift=global_shift,
            led_count=led_count
        )
        print(f"Note {note}: LED position {position}")
    
    print()

def test_orientation():
    """Test note positioning with reversed orientation"""
    print("=== Orientation Test ===")
    
    # Test parameters
    leds_per_meter = 60
    strip_length = 4.1
    led_count = int(leds_per_meter * strip_length)
    
    test_note = 60  # Middle C
    
    # Normal orientation
    pos_normal = calculate_note_position(
        note=test_note,
        leds_per_meter=leds_per_meter,
        strip_length=strip_length,
        led_count=led_count,
        led_orientation="normal"
    )
    
    # Reversed orientation
    pos_reversed = calculate_note_position(
        note=test_note,
        leds_per_meter=leds_per_meter,
        strip_length=strip_length,
        led_count=led_count,
        led_orientation="reversed"
    )
    
    print(f"Note {test_note} (Middle C):")
    print(f"  Normal orientation: LED {pos_normal}")
    print(f"  Reversed orientation: LED {pos_reversed}")
    print()

def test_full_mapping():
    """Test generating a full piano mapping"""
    print("=== Full Piano Mapping Test ===")
    
    # Test parameters
    leds_per_meter = 60
    strip_length = 4.1
    
    mapping = generate_density_based_mapping(
        piano_size="88-key",
        leds_per_meter=leds_per_meter,
        strip_length=strip_length
    )
    
    print(f"Generated mapping for {len(mapping)} notes")
    print("First 10 mappings:")
    for i, (note, led) in enumerate(list(mapping.items())[:10]):
        print(f"  Note {note}: LED {led}")
    
    print("Last 10 mappings:")
    for note, led in list(mapping.items())[-10:]:
        print(f"  Note {note}: LED {led}")
    
    print()

if __name__ == "__main__":
    test_basic_positioning()
    test_with_offsets()
    test_orientation()
    test_full_mapping()
    print("✓ All tests completed!")