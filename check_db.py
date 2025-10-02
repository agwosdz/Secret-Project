#!/usr/bin/env python3
import sqlite3
import json

# Connect to the database
conn = sqlite3.connect('settings.db')
cursor = conn.cursor()

# Get all categories
cursor.execute("SELECT DISTINCT category FROM settings ORDER BY category")
categories = cursor.fetchall()
print("Categories in database:")
for cat in categories:
    print(f"  - {cat[0]}")

print("\nAll settings:")
cursor.execute("SELECT category, key, value FROM settings ORDER BY category, key")
settings = cursor.fetchall()
for setting in settings:
    category, key, value = setting
    try:
        parsed_value = json.loads(value)
        print(f"  {category}.{key} = {parsed_value}")
    except:
        print(f"  {category}.{key} = {value}")

conn.close()