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

    John_id = create_user('John', 'Doe', 'jdsiki@fakemail.com','1997-11-15', 'student', 'Biology', 'ScienceDepartment')

    jack_id = create_user('Jack', 'Mike', 'jamike@goodmail.com', '2004-07-22', 'student', 'architecture', 'DesignDepartment')

    rosy_id = create_user('rosy', 'Winthrop', 'rw@mail.com', '1996', 'moderator')

    # Create Accounts
    password1 = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt())
    create_account(emma_id, 'ewatson', password1, '2024-01-15 10:30:00', '2026-02-13 09:15:00')

    password2 = bcrypt.hashpw('moderator456'.encode('utf-8'), bcrypt.gensalt())
    create_account(james_id, 'jmiller', password2, '2023-06-01 14:20:00', '2026-02-13 11:45:00', 1)

    password3 = bcrypt.hashpw('student789'.encode('utf-8'), bcrypt.gensalt())
    create_account(sarah_id, 'schen', password3, '2024-09-10 16:00:00', '2026-02-12 20:30:00')

    password4 = bcrypt.hashpw('johndoe123'.encode('utf-8'), bcrypt.gensalt())
    create_account(John_id, 'johndoe', password4, '2024-09-10 12:00:00', '2026-02-12 20:30:00')

    password5 = bcrypt.hashpw('jackmike123'.encode('utf-8'), bcrypt.gensalt())
    create_account(jack_id, 'jackmike', password5, '2024-09-10 12:00:00', '2026-02-12 20:30:00')

    password6 = bcrypt.hashpw('rosy123'.encode('utf-8'), bcrypt.gensalt())
    create_account(rosy_id, 'rose', password6, '2024-09-10 12:00:00', '2026-02-12 20:30:00', 1)

def default_actionType_data():
    sql = """INSERT INTO ActionType(actionName, category, unit, co2e_factor) VALUES (%s, %s, %s, %s)"""

    with db_cursor() as (connection, cursor):
        cursor.execute(sql, ("walk", "travel", "KM", 0.7))
        cursor.execute(sql, ("bus", "travel", "KM", 0.9))
        cursor.execute(sql, ("bike", "travel", "KM", 0.8))
        cursor.execute(sql, ("train", "travel", "KM", 0.5))
        cursor.execute(sql, ("car", "travel", "KM", 0.4))

        # Food ingredients (co2e in kg per kg of food)
        cursor.execute(sql, ("Alternative Meat", "food", "KG", 4.100))
        cursor.execute(sql, ("Apples", "food", "KG", 0.318))
        cursor.execute(sql, ("Apricots", "food", "KG", 0.430))
        cursor.execute(sql, ("Artichoke Plants", "food", "KG", 1.511))
        cursor.execute(sql, ("Artichokes", "food", "KG", 0.480))
        cursor.execute(sql, ("Asparagus", "food", "KG", 2.947))
        cursor.execute(sql, ("Aubergines", "food", "KG", 2.377))
        cursor.execute(sql, ("Baking/Cooking Supplies", "food", "KG", 1.797))
        cursor.execute(sql, ("Beef", "food", "KG", 34.237))
        cursor.execute(sql, ("Beer", "food", "KG", 1.034))
        cursor.execute(sql, ("Beetroot", "food", "KG", 1.707))
        cursor.execute(sql, ("Biscuits/Cookies", "food", "KG", 2.233))
        cursor.execute(sql, ("Bison/Buffalo", "food", "KG", 62.590))
        cursor.execute(sql, ("Black Eyed Peas", "food", "KG", 0.480))
        cursor.execute(sql, ("Blackberries", "food", "KG", 0.747))
        cursor.execute(sql, ("Blueberries", "food", "KG", 1.519))
        cursor.execute(sql, ("Bread", "food", "KG", 1.052))
        cursor.execute(sql, ("Breakfast Cereal", "food", "KG", 1.640))
        cursor.execute(sql, ("Broccoli", "food", "KG", 0.726))
        cursor.execute(sql, ("Brussel Sprouts", "food", "KG", 0.711))
        cursor.execute(sql, ("Butter", "food", "KG", 8.214))
        cursor.execute(sql, ("Carrots", "food", "KG", 1.084))
        cursor.execute(sql, ("Cassava", "food", "KG", 0.948))
        cursor.execute(sql, ("Cauliflower", "food", "KG", 0.611))
        cursor.execute(sql, ("Celery", "food", "KG", 0.388))
        cursor.execute(sql, ("Cheese", "food", "KG", 6.264))
        cursor.execute(sql, ("Chicken", "food", "KG", 4.963))
        cursor.execute(sql, ("Chicken (Processed)", "food", "KG", 5.607))
        cursor.execute(sql, ("Chickpeas", "food", "KG", 0.670))
        cursor.execute(sql, ("Chocolate/Confectionery", "food", "KG", 15.912))
        cursor.execute(sql, ("Chutneys/Relishes", "food", "KG", 2.784))
        cursor.execute(sql, ("Coffee", "food", "KG", 16.948))
        cursor.execute(sql, ("Condiments/Sauces", "food", "KG", 2.553))
        cursor.execute(sql, ("Cooking Oil", "food", "KG", 3.200))
        cursor.execute(sql, ("Cooking Sauces (Fresh)", "food", "KG", 3.584))
        cursor.execute(sql, ("Cooking Sauces (Shelf Stable)", "food", "KG", 2.849))
        cursor.execute(sql, ("Courgettes", "food", "KG", 0.777))
        cursor.execute(sql, ("Cranberries", "food", "KG", 1.018))
        cursor.execute(sql, ("Cream", "food", "KG", 4.034))
        cursor.execute(sql, ("Cucumbers", "food", "KG", 2.023))
        cursor.execute(sql, ("Dates", "food", "KG", 0.320))
        cursor.execute(sql, ("Dessert Sauces/Toppings", "food", "KG", 3.823))
        cursor.execute(sql, ("Dressings/Dips", "food", "KG", 2.941))
        cursor.execute(sql, ("Egg Products", "food", "KG", 3.060))
        cursor.execute(sql, ("Eggs", "food", "KG", 2.792))
        cursor.execute(sql, ("Fennel", "food", "KG", 0.480))
        cursor.execute(sql, ("Figs", "food", "KG", 0.430))
        cursor.execute(sql, ("Fish", "food", "KG", 3.200))
        cursor.execute(sql, ("Fish (Processed)", "food", "KG", 6.189))
        cursor.execute(sql, ("Flavoured Drinks", "food", "KG", 0.430))
        cursor.execute(sql, ("Fruit Juice", "food", "KG", 0.794))
        cursor.execute(sql, ("Garlic", "food", "KG", 0.461))
        cursor.execute(sql, ("Ginger", "food", "KG", 0.880))
        cursor.execute(sql, ("Gooseberries", "food", "KG", 1.402))
        cursor.execute(sql, ("Grains/Flour", "food", "KG", 0.850))
        cursor.execute(sql, ("Grapes", "food", "KG", 0.410))
        cursor.execute(sql, ("Ice Cream", "food", "KG", 5.031))
        cursor.execute(sql, ("Kiwifruits", "food", "KG", 0.572))
        cursor.execute(sql, ("Lamb", "food", "KG", 35.506))
        cursor.execute(sql, ("Lemons", "food", "KG", 0.541))
        cursor.execute(sql, ("Lentils", "food", "KG", 1.294))
        cursor.execute(sql, ("Limes", "food", "KG", 0.398))
        cursor.execute(sql, ("Mandarins", "food", "KG", 0.453))
        cursor.execute(sql, ("Margarine", "food", "KG", 0.743))
        cursor.execute(sql, ("Meat Substitutes", "food", "KG", 3.092))
        cursor.execute(sql, ("Milk", "food", "KG", 1.811))
        cursor.execute(sql, ("Mushrooms", "food", "KG", 0.350))
        cursor.execute(sql, ("Nuts/Seeds", "food", "KG", 1.311))
        cursor.execute(sql, ("Olives", "food", "KG", 1.918))
        cursor.execute(sql, ("Onions", "food", "KG", 1.006))
        cursor.execute(sql, ("Oranges", "food", "KG", 0.418))
        cursor.execute(sql, ("Pears", "food", "KG", 0.330))
        cursor.execute(sql, ("Peas", "food", "KG", 2.329))
        cursor.execute(sql, ("Pineapples", "food", "KG", 0.484))
        cursor.execute(sql, ("Plant-Based Milk", "food", "KG", 0.580))
        cursor.execute(sql, ("Pork", "food", "KG", 7.935))
        cursor.execute(sql, ("Pork (Processed)", "food", "KG", 10.450))
        cursor.execute(sql, ("Potatoes", "food", "KG", 1.390))
        cursor.execute(sql, ("Pumpkin/Squash", "food", "KG", 0.388))
        cursor.execute(sql, ("Quinces", "food", "KG", 0.310))
        cursor.execute(sql, ("Raspberries", "food", "KG", 0.978))
        cursor.execute(sql, ("Sparkling Wine", "food", "KG", 1.121))
        cursor.execute(sql, ("Strawberries", "food", "KG", 1.184))
        cursor.execute(sql, ("Swede/Rutabaga", "food", "KG", 0.290))
        cursor.execute(sql, ("Sweetcorn", "food", "KG", 1.308))
        cursor.execute(sql, ("Tomato Ketchup", "food", "KG", 4.090))
        cursor.execute(sql, ("Tomatoes", "food", "KG", 1.700))
        cursor.execute(sql, ("Turkey", "food", "KG", 11.950))
        cursor.execute(sql, ("Vegetables (Processed)", "food", "KG", 1.204))
        cursor.execute(sql, ("Watermelons", "food", "KG", 0.320))
        cursor.execute(sql, ("Wine", "food", "KG", 1.319))
        cursor.execute(sql, ("Yogurt", "food", "KG", 1.469))
        cursor.execute(sql, ("Yogurt Substitutes", "food", "KG", 0.948))

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

    challenge5_id = create_challenge(james_id, "food", "Low Carbon Meals", start_date, end_date, "Log your meals and try to keep CO2e low")

    emma_actions = [
        ("walk", "travel", 2, challenge1_id, "https://www.youtube.com/"),
        ("bus", "travel", 4, challenge1_id, "https://www.strava.com/"),
        ("walk", "travel", 10, challenge1_id, "https://runkeeper.com/cms/"),
        ("bus", "travel", 15, challenge1_id, "https://runkeeper.com/cms/"),
        ("walk", "travel", 5, challenge2_id, "https://www.runtastic.com/"),
        ("walk", "travel", 8, None, None),
        ("bus", "travel", 12, None, None),
        ("walk", "travel", 3, None, None),
        ("walk", "travel", 7, challenge1_id, None),
        ("walk", "travel", 4, None, None),
        ("bus", "travel", 18, None, None),
        ("food", "food", [("Broccoli", 0.3), ("Chicken", 0.5), ("Potatoes", 0.4)], challenge5_id, "https://www.youtube.com/"),
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

