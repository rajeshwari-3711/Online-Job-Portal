import sqlite3

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Add missing columns
try:
    cursor.execute("ALTER TABLE users ADD COLUMN dob TEXT")
except sqlite3.OperationalError:
    pass  # Column already exists

try:
    cursor.execute("ALTER TABLE users ADD COLUMN age INTEGER")
except sqlite3.OperationalError:
    pass  # Column already exists

conn.commit()
conn.close()
print("Schema updated.")
