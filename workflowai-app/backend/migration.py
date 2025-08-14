import sqlite3
import os

# Connect to the database
conn = sqlite3.connect('workflowai.db')
cursor = conn.cursor()

# Add token column to users table
try:
    cursor.execute("ALTER TABLE users ADD COLUMN token TEXT")
    conn.commit()
    print("Successfully added token column to users table")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("Token column already exists in users table")
    else:
        print(f"Error adding token column: {e}")

# Close the connection
conn.close()
