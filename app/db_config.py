import os
from contextlib import contextmanager
import pymysql
from flask import g

# Sets the Flask app name from an environment variable to "DeepCurrent" - Uses os module to get environment variable
DeepCurrent = os.getenv('FLASK_APP', 'DeepCurrent') 

# Creates one connection per request to the database
def get_connection():
    if "db_connection" not in g:
        g.db_connection = pymysql.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            db=os.getenv('MYSQL_DB'),
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False
        )
    
    return g.db_connection

# Closes the database connection
def close_connection():
    connection = g.pop("db_connection", None)
    if connection is not None:
        connection.close()

# Create the cursor and establish connection
@contextmanager
def db_cursor():
    connection = get_connection()
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


