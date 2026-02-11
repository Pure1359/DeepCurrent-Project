import pytest
import sqlite3

@pytest.fixture
def function_scope_database():
    #set up connection
    conn = sqlite3.connect('mydb.sqlite')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'")

    for schema in cursor.fetchall():
        table_name = schema['name']

        sql = f"DELETE FROM {table_name}"
        cursor.execute(sql)
    
    conn.commit()

    #return connection
    yield conn
    #close connection
    conn.close()


