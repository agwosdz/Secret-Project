#!/usr/bin/env python3
"""
Fix missing required fields in settings database
"""

import sqlite3
import json

def fix_required_fields():
    conn = sqlite3.connect('settings.db')
    cursor = conn.cursor()
    
    # Check and fix audio category
    cursor.execute("SELECT value FROM settings WHERE category = 'audio' AND key = 'volume'")
    if not cursor.fetchone():
        print("Adding missing audio.volume field")
        cursor.execute("INSERT INTO settings (category, key, value) VALUES (?, ?, ?)", 
                      ('audio', 'volume', '50'))
    
    # Check and fix led category
    cursor.execute("SELECT value FROM settings WHERE category = 'led' AND key = 'count'")
    if not cursor.fetchone():
        print("Adding missing led.count field")
        cursor.execute("INSERT INTO settings (category, key, value) VALUES (?, ?, ?)", 
                      ('led', 'count', '88'))
    
    cursor.execute("SELECT value FROM settings WHERE category = 'led' AND key = 'brightness'")
    if not cursor.fetchone():
        print("Adding missing led.brightness field")
        cursor.execute("INSERT INTO settings (category, key, value) VALUES (?, ?, ?)", 
                      ('led', 'brightness', '50'))
    
    # Check and fix system category
    cursor.execute("SELECT value FROM settings WHERE category = 'system' AND key = 'theme'")
    if not cursor.fetchone():
        print("Adding missing system.theme field")
        cursor.execute("INSERT INTO settings (category, key, value) VALUES (?, ?, ?)", 
                      ('system', 'theme', 'auto'))
    
    # Check and fix user category
    cursor.execute("SELECT value FROM settings WHERE category = 'user' AND key = 'preferences'")
    if not cursor.fetchone():
        print("Adding missing user.preferences field")
        # Default preferences object
        default_preferences = json.dumps({
            "show_tooltips": True,
            "auto_connect": True,
            "remember_window_size": True
        })
        cursor.execute("INSERT INTO settings (category, key, value) VALUES (?, ?, ?)", 
                      ('user', 'preferences', default_preferences))
    
    # Commit changes
    conn.commit()
    
    # Verify all required fields are now present
    print("\nVerifying required fields:")
    
    required_fields = [
        ('audio', 'enabled'),
        ('audio', 'volume'),
        ('led', 'enabled'),
        ('led', 'count'),
        ('led', 'brightness'),
        ('system', 'debug'),
        ('system', 'theme'),
        ('user', 'name'),
        ('user', 'preferences')
    ]
    
    all_present = True
    for category, key in required_fields:
        cursor.execute("SELECT value FROM settings WHERE category = ? AND key = ?", (category, key))
        result = cursor.fetchone()
        if result:
            print(f"✓ {category}.{key} = {result[0]}")
        else:
            print(f"✗ {category}.{key} is missing")
            all_present = False
    
    conn.close()
    
    if all_present:
        print("\n✓ All required fields are now present in the database")
    else:
        print("\n✗ Some required fields are still missing")
    
    return all_present

if __name__ == "__main__":
    fix_required_fields()