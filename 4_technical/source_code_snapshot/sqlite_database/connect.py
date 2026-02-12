import sqlite3

# Connect to your database file
conn = sqlite3.connect('mydb.sqlite')
conn.row_factory = sqlite3.Row
# Create a cursor object to execute SQL commands
cursor = conn.cursor()

cursor.execute(f"SELECT * FROM sqlite_master WHERE type='table'")

for schema in cursor.fetchall():
    print(f"table name is {schema['name']}")
    sql = f"""SELECT * FROM {schema['name']}"""
    cursor.execute(sql)
    for record in cursor.fetchall():
        print(f"record is : {record}")
    print(schema['sql'])
    print("\n")


# Close the connection when done
conn.close()

