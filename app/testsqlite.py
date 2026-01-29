import sqlite3

try:
    with sqlite3.connect("sqlite_database/fake_database") as conn:
        print(f"Opened SQLite database with version {sqlite3.sqlite_version} successfully.")
        cursor = conn.cursor()
        cursor.execute("""
    CREATE TABLE GEEK (
        Email VARCHAR(255) NOT NULL,
        First_Name CHAR(25) NOT NULL,
        Last_Name CHAR(25),
        Score INT
    );
""")
        
except sqlite3.OperationalError as e:
    print("Failed to open database:", e)