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
from set_up.database_setup import *

@pytest.fixture()
def function_scope_database():
    print("DELETION")
    deleterecord()
    #set up connection
    database_path = 'sqlite_database/mydb.sqlite'
    
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    default_actionType_data()
    defaultDatabase()
    
    yield
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


@pytest.fixture(scope = "module")
def module_scope_database():
    print("DELETION")
    deleterecord()
    #set up connection
    database_path = 'sqlite_database/mydb.sqlite'
    
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    default_actionType_data()
    defaultDatabase()
   
    yield
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

@pytest.fixture(scope="module")
def populated_database(new_client_module, module_scope_database):
    """Populates database and logs in as moderator for tests"""
    
    # Login as moderator to create challenges
    new_client_module.post("/login", data={
        "email": "j.miller@exeter.ac.uk",
        "password": "moderator456"
    }, follow_redirects=True)
    
    # Create active challenges
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    new_client_module.post("/moderator_access/create_challenge", data={
        "challenge_type": "travel",
        "title": "let walk",
        "start_date": start_date,
        "end_date": end_date,
        "rule": "walk as much as you can"
    })
    
    new_client_module.post("/moderator_access/create_challenge", data={
        "challenge_type": "food",
        "title": "Green Eat",
        "start_date": start_date,
        "end_date": end_date,
        "rule": "Eat vegetarian food"
    })
    
    # Create expired challenge (challenge_id will be 3)
    past_start = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
    past_end = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    new_client_module.post("/moderator_access/create_challenge", data={
        "challenge_type": "travel",
        "title": "Expired Challenge",
        "start_date": past_start,
        "end_date": past_end,
        "rule": "This challenge has ended"
    })
    
    # Create future challenge (challenge_id will be 4)
    future_start = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    future_end = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
    
    new_client_module.post("/moderator_access/create_challenge", data={
        "challenge_type": "food",
        "title": "Future Challenge",
        "start_date": future_start,
        "end_date": future_end,
        "rule": "This challenge hasn't started yet"
    })
    
    # Logout
    new_client_module.post("/logout")
    
    # Login as Emma to create actions
    new_client_module.post("/login", data={
        "email": "e.watson@exeter.ac.uk",
        "password": "password123"
    }, follow_redirects=True)
    
    # Emma's actions
    actions_emma = [
        {"action_name": "walk", "category": "travel", "quantity": 2, "challenge_id": 1, "evidence_url": "url1"},
        {"action_name": "bus", "category": "travel", "quantity": 4, "challenge_id": 1, "evidence_url": "url2"},
        {"action_name": "walk", "category": "travel", "quantity": 10, "challenge_id": 1, "evidence_url": "url3"},
        {"action_name": "bus", "category": "travel", "quantity": 15, "challenge_id": 1, "evidence_url": "url4"},
        {"action_name": "walk", "category": "travel", "quantity": 5, "challenge_id": 2, "evidence_url": "url5"},
        {"action_name": "walk", "category": "travel", "quantity": 8, "challenge_id": None, "evidence_url": None},
        {"action_name": "bus", "category": "travel", "quantity": 12, "challenge_id": None, "evidence_url": None},
        {"action_name": "walk", "category": "travel", "quantity": 3, "challenge_id": None, "evidence_url": None},
        {"action_name": "walk", "category": "travel", "quantity": 7, "challenge_id": 1, "evidence_url": None},
        {"action_name": "walk", "category": "travel", "quantity": 4, "challenge_id": None, "evidence_url": None},
        {"action_name": "bus", "category": "travel", "quantity": 18, "challenge_id": None, "evidence_url": None},
    ]
    
    for action in actions_emma:
        new_client_module.post("/user_access/submit_action", json=action)
    
    # Logout Emma
    new_client_module.post("/logout")
    
    # Login as Sarah
    new_client_module.post("/login", data={
        "email": "s.chen@exeter.ac.uk",
        "password": "student789"
    }, follow_redirects=True)
    
    # Sarah's actions
    actions_sarah = [
        {"action_name": "walk", "category": "travel", "quantity": 20, "challenge_id": 1, "evidence_url": "url6"},
        {"action_name": "bus", "category": "travel", "quantity": 25, "challenge_id": 1, "evidence_url": "url7"},
        {"action_name": "walk", "category": "travel", "quantity": 6, "challenge_id": None, "evidence_url": None},
        {"action_name": "bus", "category": "travel", "quantity": 9, "challenge_id": None, "evidence_url": None},
        {"action_name": "bus", "category": "travel", "quantity": 11, "challenge_id": 2, "evidence_url": None},
        {"action_name": "walk", "category": "travel", "quantity": 13, "challenge_id": None, "evidence_url": None},
        {"action_name": "bus", "category": "travel", "quantity": 22, "challenge_id": None, "evidence_url": None},
    ]
    
    for action in actions_sarah:
        new_client_module.post("/user_access/submit_action", json=action)
    
    # Logout Sarah and login as moderator for tests
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "j.miller@exeter.ac.uk",
        "password": "moderator456"
    }, follow_redirects=True)
    
    yield

#check for rendering template
@contextmanager
def captured_template(app):
    recorded_template = []
    def record_template(sender, template, context, **extra):
        recorded_template.append((template, context))
    template_rendered.connect(record_template, app)
    try:
        yield recorded_template
    finally:
        template_rendered.disconnect(record_template, app)

@pytest.fixture()
def app():
    app = create_app()
    app.config.update({"TESTING" : True})
    yield app

@pytest.fixture(scope = "module")
def app_module():
    app = create_app()
    app.config.update({"TESTING" : True})
    yield app

@pytest.fixture()
def new_client_function(app):
    return app.test_client()


@pytest.fixture(scope="module")
def new_client_module(app_module):
    return app_module.test_client()

@pytest.fixture()
def recorded_template(app):
    with captured_template(app) as recorder:
        yield recorder

@pytest.fixture(scope = "module")
def recorded_template_module(app_module):
    with captured_template(app_module) as recorder:
        yield recorder



