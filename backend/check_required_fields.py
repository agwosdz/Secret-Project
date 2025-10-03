#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('settings.db')
cursor = conn.execute('''
    SELECT category, key, value 
    FROM settings 
    WHERE (category = ? AND key = ?) 
       OR (category = ? AND key = ?) 
       OR (category = ? AND key = ?) 
       OR (category = ? AND key = ?)
''', ('audio', 'enabled', 'led', 'enabled', 'system', 'debug', 'user', 'name'))

results = [(row[0], row[1], row[2]) for row in cursor.fetchall()]
print("Required fields found:")
for category, key, value in results:
    print(f"  {category}.{key} = {value}")

# Check what categories exist
cursor = conn.execute('SELECT DISTINCT category FROM settings ORDER BY category')
categories = [row[0] for row in cursor.fetchall()]
print(f"\nAll categories: {categories}")

# Check all settings in each category
for category in ['audio', 'led', 'system', 'user']:
    cursor = conn.execute('SELECT key, value FROM settings WHERE category = ?', (category,))
    settings = [(row[0], row[1]) for row in cursor.fetchall()]
    print(f"\n{category} settings:")
    for key, value in settings:
        print(f"  {key} = {value}")

conn.close()