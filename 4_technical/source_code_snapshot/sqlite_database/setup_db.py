import sqlite3

conn = sqlite3.connect('mydb.sqlite')
cursor = conn.cursor()

with open('schema.sql', 'r') as f:
    schema_script = f.read()
    cursor.executescript(schema_script)
conn.commit()
conn.close()

print("Schema executed successfully!")