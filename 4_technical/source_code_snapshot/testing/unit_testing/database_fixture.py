import pytest
import sqlite3

@pytest.fixture
def function_scope_database():
    #set up connection
    database_path = '4_technical/source_code_snapshot/sqlite_database/mydb.sqlite'
    schema_path  = '4_technical/source_code_snapshot/sqlite_database/schema.sql'
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    #turn off the foreign key to make dropping table easier and get all table name
    cursor.execute("PRAGMA foreign_keys = OFF")
    cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'")

    #for all table name , drop entire table structure
    for schema in cursor.fetchall():
        table_name = schema['name']
        sql = f"DROP TABLE IF EXISTS {table_name}"
        cursor.execute(sql)
    
    conn.commit()

    #recreate table and enable the foreign key again
    with open(schema_path) as create_script:
        table_schema = create_script.read()
    cursor.executescript(table_schema)
    cursor.execute("PRAGMA foreign_keys = ON")
    conn.commit()

    #return connection
    yield conn
    #close connection
    conn.close()


