import sqlite3
def deleterecord():
    print("DELETION")
    #set up connection
    database_path = 'sqlite_database/mydb.sqlite'
    
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    #turn off the foreign key to make dropping table easier and get all table name
    cursor.execute("PRAGMA foreign_keys = OFF")
    cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'")

    #for all table name , drop entire table structure
    for schema in cursor.fetchall():
        table_name = schema['name']
        sql = f"DELETE FROM {table_name}"
        cursor.execute(sql)
    cursor.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    #close connection
    conn.close()
