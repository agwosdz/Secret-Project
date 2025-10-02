#!/usr/bin/env python3
import sqlite3

# Connect to the database
conn = sqlite3.connect('settings.db')
cursor = conn.cursor()

# Delete all entries with category 'settings'
cursor.execute("DELETE FROM settings WHERE category = 'settings'")
rows_deleted = cursor.rowcount
conn.commit()

print(f"Deleted {rows_deleted} entries from 'settings' category")

# Verify the deletion
cursor.execute("SELECT DISTINCT category FROM settings ORDER BY category")
categories = cursor.fetchall()
print("Remaining categories in database:")
for cat in categories:
    print(f"  - {cat[0]}")

conn.close()