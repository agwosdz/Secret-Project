#!/usr/bin/env python3
"""
MIDI Diagnostics Tool
Helps diagnose MIDI device detection issues on Windows
"""

import sys
import subprocess

def check_midi_libraries():
    """Check if MIDI libraries are properly installed"""
    print("=== MIDI Library Check ===")
    
    try:
        import mido
        print("✓ mido library installed")
        print(f"  Backend: {mido.backend}")
        
        # Check available backends
        try:
            backends = mido.backend.module.get_api_names()
            print(f"  Available backends: {backends}")
        except Exception as e:
            print(f"  Could not get backends: {e}")
            
    except ImportError:
        print("✗ mido library not found")
        return False
    
    try:
        import rtmidi
        print("✓ python-rtmidi library installed")
    except ImportError:
        print("✗ python-rtmidi library not found")
        return False
        
    return True

def check_midi_devices():
    """Check for MIDI devices using different methods"""
    print("\n=== MIDI Device Detection ===")
    
    # Method 1: Using mido
    try:
        import mido
        inputs = mido.get_input_names()
        outputs = mido.get_output_names()
        print(f"mido - Input devices: {inputs}")
        print(f"mido - Output devices: {outputs}")
    except Exception as e:
        print(f"mido detection failed: {e}")
    
    # Method 2: Using rtmidi directly
    try:
        import rtmidi
        midiin = rtmidi.MidiIn()
        midiout = rtmidi.MidiOut()
        
        input_ports = midiin.get_ports()
        output_ports = midiout.get_ports()
        
        print(f"rtmidi - Input ports: {input_ports}")
        print(f"rtmidi - Output ports: {output_ports}")
        
        midiin.close_port()
        midiout.close_port()
        
    except Exception as e:
        print(f"rtmidi detection failed: {e}")

def check_windows_devices():
    """Check Windows device manager for MIDI devices"""
    print("\n=== Windows Device Check ===")
    
    try:
        # Check for MIDI devices in Device Manager
        result = subprocess.run([
            'powershell', '-Command',
            "Get-PnpDevice | Where-Object {$_.FriendlyName -like '*MIDI*' -or $_.FriendlyName -like '*Casio*'} | Select-Object FriendlyName, Status, Class | Format-Table -AutoSize"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("Windows detected MIDI devices:")
            print(result.stdout)
        else:
            print(f"Failed to query Windows devices: {result.stderr}")
            
    except Exception as e:
        print(f"Windows device check failed: {e}")

def provide_solutions():
    """Provide potential solutions for MIDI issues"""
    print("\n=== Potential Solutions ===")
    print("\n1. CASIO USB-MIDI Driver Issues:")
    print("   - The CASIO devices show 'Unknown' status in Device Manager")
    print("   - This indicates missing or incorrect drivers")
    print("   - Try these steps:")
    print("     a) Unplug and reconnect the CASIO device")
    print("     b) Check Windows Update for driver updates")
    print("     c) Download latest CASIO USB-MIDI drivers from CASIO website")
    print("     d) Try a different USB port or cable")
    
    print("\n2. Windows MIDI Service:")
    print("   - Ensure Windows Audio service is running")
    print("   - Run: services.msc and check 'Windows Audio' service")
    
    print("\n3. Alternative MIDI Solutions:")
    print("   - Use loopMIDI or similar virtual MIDI driver")
    print("   - Try MIDI-OX to test MIDI connectivity")
    print("   - Consider using ASIO drivers if available")
    
    print("\n4. Python MIDI Library Issues:")
    print("   - Try reinstalling python-rtmidi: pip uninstall python-rtmidi && pip install python-rtmidi")
    print("   - Try different mido backend: mido.set_backend('mido.backends.rtmidi')")

def main():
    """Run complete MIDI diagnostics"""
    print("MIDI Diagnostics Tool")
    print("=" * 50)
    
    if not check_midi_libraries():
        print("\n❌ MIDI libraries not properly installed")
        return
    
    check_midi_devices()
    check_windows_devices()
    provide_solutions()
    
    print("\n=== Summary ===")
    print("The main issue appears to be that Windows detects the CASIO USB-MIDI")
    print("devices but they have 'Unknown' status, indicating driver problems.")
    print("\nRecommended next steps:")
    print("1. Install proper CASIO USB-MIDI drivers")
    print("2. Restart the application after driver installation")
    print("3. Test with MIDI-OX or similar tool to verify MIDI connectivity")

if __name__ == "__main__":
    main()