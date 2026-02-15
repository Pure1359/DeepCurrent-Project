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
james_id = 0

def defaultDatabase():
    global james_id
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



def default_actionType_data():
    sql = """INSERT INTO ActionType(actionName, category, unit, co2e_factor) VALUES (%s, %s, %s, %s)"""

    with db_cursor() as (connection, cursor):
        cursor.execute(sql, ("walk", "travel", "KM", 0.7))
        cursor.execute(sql, ("bus", "travel", "KM", 0.9))

def production_setup(james_id = 2):
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)
    challenge1_id = create_challenge(james_id, "travel", "let walk", start_date, end_date, "walk as much as you can")
    challenge2_id = create_challenge(james_id, "food", "Green Eat", start_date, end_date, "Eat vegetarian food")
    
    past_start = datetime.now() - timedelta(days=60)
    past_end = datetime.now() - timedelta(days=30)
    challenge3_id = create_challenge(james_id, "travel", "Expired Challenge", past_start, past_end, "This challenge has ended")
    
    future_start = datetime.now() + timedelta(days=30)
    future_end = datetime.now() + timedelta(days=60)
    challenge4_id = create_challenge(james_id, "food", "Future Challenge", future_start, future_end, "This challenge hasn't started yet")

    emma_actions = [
        ("walk", "travel", 2, challenge1_id, "https://www.youtube.com/"),
        ("bus", "travel", 4, challenge1_id, "url2"),
        ("walk", "travel", 10, challenge1_id, "url3"),
        ("bus", "travel", 15, challenge1_id, "url4"),
        ("walk", "travel", 5, challenge2_id, "url5"),
        ("walk", "travel", 8, None, None),
        ("bus", "travel", 12, None, None),
        ("walk", "travel", 3, None, None),
        ("walk", "travel", 7, challenge1_id, None),
        ("walk", "travel", 4, None, None),
        ("bus", "travel", 18, None, None),
    ]
    
    emma_account_id = 1
    for action_name, category, quantity, challenge_id, evidence_url in emma_actions:
        log_action(emma_account_id, action_name, category, quantity, challenge_id, evidence_url)
    
    print(f"Created {len(emma_actions)} actions for Emma")
    
    # Sarah's actions (account_id = 3)
    sarah_actions = [
        ("walk", "travel", 20, challenge1_id, "url6"),
        ("bus", "travel", 25, challenge1_id, "url7"),
        ("walk", "travel", 6, None, None),
        ("bus", "travel", 9, None, None),
        ("bus", "travel", 11, challenge2_id, None),
        ("walk", "travel", 13, None, None),
        ("bus", "travel", 22, None, None),
    ]
    
    sarah_account_id = 3
    for action_name, category, quantity, challenge_id, evidence_url in sarah_actions:
        log_action(sarah_account_id, action_name, category, quantity, challenge_id, evidence_url)

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

