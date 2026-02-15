from contextlib import contextmanager
import bcrypt
from flask import template_rendered
import pytest
import sqlite3
from app.services.users_service import create_account, create_user
from app.services.challenges import create_challenge
from app.services.actions import log_action
from app import create_app
from app.db_config import db_cursor
from datetime import datetime, timedelta


def defaultDatabase():
    # Create Users
    emma_id = create_user('Emma', 'Watson', 'e.watson@exeter.ac.uk', '1999-04-15', 'student', 'Computer Science', 'Engineering')

    james_id = create_user('James', 'Miller', 'j.miller@exeter.ac.uk', '1985-09-22', 'moderator', None, 'Mathematics')

    sarah_id = create_user('Sarah', 'Chen', 's.chen@exeter.ac.uk', '2001-11-08', 'student', 'Business Analytics', 'Business School')

    # Create Accounts
    password1 = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt())
    create_account(emma_id, 'ewatson', password1, '2024-01-15 10:30:00', '2026-02-13 09:15:00')

    password2 = bcrypt.hashpw('moderator456'.encode('utf-8'), bcrypt.gensalt())
    create_account(james_id, 'jmiller', password2, '2023-06-01 14:20:00', '2026-02-13 11:45:00', 1)

    password3 = bcrypt.hashpw('student789'.encode('utf-8'), bcrypt.gensalt())
    create_account(sarah_id, 'schen', password3, '2024-09-10 16:00:00', '2026-02-12 20:30:00')

    print(f"Created users: Emma (ID: {emma_id}), James (ID: {james_id}), Sarah (ID: {sarah_id})")

def default_actionType_data():
    sql = """INSERT INTO ActionType(actionName, category, unit, co2e_factor) VALUES (%s, %s, %s, %s)"""

    with db_cursor() as (connection, cursor):
        cursor.execute(sql, ("walk", "travel", "KM", 0.7))
        cursor.execute(sql, ("bus", "travel", "KM", 0.9))

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
