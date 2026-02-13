from contextlib import contextmanager
import bcrypt
from flask import template_rendered
import pytest
import sqlite3
from app.services.users_service import create_account, create_user
from app import create_app

@pytest.fixture()
def function_scope_database():
    print("DELETION")
    #set up connection
    database_path = 'sqlite_database/mydb.sqlite'
    
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
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
    #set up connection
    database_path = 'sqlite_database/mydb.sqlite'
    
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

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

    