import os
from contextlib import contextmanager
import pymysql
from flask import g, has_app_context
from typing import Any, Iterable, Optional
import sqlite3

# Sets the Flask app name from an environment variable to "DeepCurrent" - Uses os module to get environment variable
DeepCurrent = os.getenv('FLASK_APP', 'DeepCurrent') 

GLOBAL_CONN = None
GLOBAL_CONN_KEY = None

# Helper function to check if we are using MySQL or SQLite
def db_engine():
    return (os.getenv('DB_ENGINE') or "mysql") # Set to mysql by default

# Create SQLite Class to handle automatic code conversion in testing
class SQLiteDictCursor:
    def __init__(self, cursor: sqlite3.Cursor):
        self.cursor = cursor

    @property
    def lastrowid(self):
        return int(self.cursor.lastrowid)
    
    def execute(self, sql, params: Optional[Iterable[Any]] = None):
        # Replace %s placeholders with ?
        sql = sql.replace("%s", "?")
        if params is None:
            return self.cursor.execute(sql)
        return self.cursor.execute(sql, tuple(params))
    
    def execturemany(self, sql, sequence_of_params: Iterable[Iterable[Any]]):
        sql = sql.replace("%s", "?")
        return self.cursor.executemany(sql, [tuple(p) for p in sequence_of_params])

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        if isinstance(row, sqlite3.Row):
            return dict(row)
        return row
    
    def fetchall(self):
        rows = self.cursor.fetchall()
        if rows and isinstance(rows[0], sqlite3.Row):
            return [dict(row) for row in rows]
        return rows
    
    def close(self):
        self.cursor.close()

# Creates one connection per request to the database
def get_connection():
    global GLOBAL_CONN, GLOBAL_CONN_KEY

    # Simple check for automatic tests, the Flask server will not be running
    # so, if the server is not running, still run the automatic tests
    if has_app_context():
        if "db_connection" in g:
            return g.db_connection
    else:
        key = (db_engine(), os.getenv("SQLITE_PATH"), os.getenv("MYSQL_HOST"), os.getenv("MYSQL_DB"))
        if GLOBAL_CONN is not None and GLOBAL_CONN_KEY == key:
            return GLOBAL_CONN
    
    engine = db_engine()
    # SQLite (Testing)
    if engine == "sqlite":
        path = os.getenv("SQLITE_PATH")
        conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        if has_app_context():
            g.db_connection = conn
        else:
            GLOBAL_CONN = conn
            GLOBAL_CONN_KEY = (db_engine(), os.getenv("SQLITE_PATH"), os.getenv("MYSQL_HOST"), os.getenv("MYSQL_DB"))
        return conn
    
    # MySQL (Default)
    conn = pymysql.connect(
        host=os.getenv('MYSQL_HOST'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'), # type: ignore
        db=os.getenv('MYSQL_DB'),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    ) # type: ignore

    if has_app_context():
        g.db_connection = conn
    else:
        GLOBAL_CONN = conn
        GLOBAL_CONN_KEY = (db_engine(), os.getenv("SQLITE_PATH"), os.getenv("MYSQL_HOST"), os.getenv("MYSQL_DB"))
    return conn

# Closes the database connection
def close_connection():
    global GLOBAL_CONN, GLOBAL_CONN_KEY
    if has_app_context():
        connection = g.pop("db_connection", None)
        if connection is not None:
            connection.close()
    else:
        if GLOBAL_CONN is not None:
            GLOBAL_CONN.close()
            GLOBAL_CONN = None
            GLOBAL_CONN_KEY = None

# Create the cursor and establish connection
@contextmanager
def db_cursor():
    connection = get_connection()
    engine = db_engine()

    if engine == "sqlite":
        raw_cursor = connection.cursor()
        cursor = SQLiteDictCursor(raw_cursor)
        try:
            yield connection, cursor
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
        return

    cursor = connection.cursor()
    # Automaticallty commit changes to the database
    try: # Try to commit
        yield connection, cursor
        connection.commit()
    except Exception: # If error occurs, rollback changes, raise error
        connection.rollback()
        raise
    finally: # Close connection
        cursor.close()
