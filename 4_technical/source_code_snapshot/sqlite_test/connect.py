import sqlite3

# Connect to your database file
conn = sqlite3.connect('mydb.sqlite')

# Create a cursor object to execute SQL commands
cursor = conn.cursor()

cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table'")

for schema in cursor.fetchall():
    print(schema[0])
    print("\n")

# Close the connection when done
conn.close()

