import sqlite3
import os

db_path = os.path.join("resume_storage", "resumes.db")
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("Current database schema:")
    for table in tables:
        print(table[0])
        print("-" * 50)
    
    conn.close()
else:
    print("Database file not found")
