#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/pi/Secret-Project/backend')

try:
    from midi_input_manager import MIDIInputManager
    print("MIDIInputManager imported successfully")
    
    m = MIDIInputManager()
    print("MIDIInputManager created")
    
    print("Initializing services...")
    result = m.initialize_services()
    print(f"Initialize result: {result}")
    
    print(f"USB service: {m._usb_service}")
    print(f"RTP service: {m._rtpmidi_service}")
    
    if m._usb_service:
        print("Testing USB service start_listening...")
        usb_result = m._usb_service.start_listening()
        print(f"USB start_listening result: {usb_result}")
        
        if usb_result:
            print("USB service started successfully, stopping...")
            m._usb_service.stop_listening()
    
    print("Testing manager start_listening...")
    manager_result = m.start_listening(enable_usb=True, enable_rtpmidi=False)
    print(f"Manager start_listening result: {manager_result}")
    
    if manager_result:
        print("Manager started successfully, stopping...")
        m.stop_listening()
        
except Exception as e:
    import traceback
    print(f"Error: {e}")
    print(f"Traceback: {traceback.format_exc()}")