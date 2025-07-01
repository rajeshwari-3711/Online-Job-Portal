import sqlite3

# Connect to (or create) the database file
conn = sqlite3.connect('user.db')

# Create a cursor object to execute SQL commands
cursor = conn.cursor()

# Create the users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    dob TEXT NOT NULL,
    age INTEGER NOT NULL,
    college TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    profile_pic TEXT,
    is_admin INTEGER DEFAULT 0
)
''')

# Commit changes and close connection
conn.commit()
conn.close()

print("Database and users table created successfully.")
