from app.db_config import db_cursor
from app.services.challenges import join_challenge_individual
from custom_error.Challenge_Exception import *
from datetime import datetime, timedelta
from calendar import monthrange

# Create a user in the database
def create_user(first_name, last_name, email, dob, user_type, course=None, department=None):
    sql = "INSERT INTO Users (first_name, last_name, email, dob, user_type, course, department) VALUES (%s, %s, %s, %s, %s, %s, %s)"

    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (first_name, last_name, email, dob, user_type, course, department))
        return cursor.lastrowid # Return user_id

# Create an account in the database
def create_account(user_id, username, password, date_created, last_active):
    sql = "INSERT INTO Accounts (user_id, username, password, date_created, last_active) VALUES (%s, %s, %s, %s, %s)"

    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (user_id, username, password, date_created, last_active))
        return cursor.lastrowid # Return account_id

# Update Last Active
def update_last_active(account_id, last_active):
    sql = "UPDATE Accounts SET last_active = %s WHERE account_id = %s"

    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (last_active, account_id))

def get_user_role(user_id):
    sql = "SELECT user_type FROM Users WHERE user_id = %s"

    with db_cursor() as (connection, cursor):
        cursor.execute(sql,user_id)
        return cursor.fetchone()

def get_weekly_saved(account_id):
    today = datetime.now()
    start_of_week = today - timedelta(days = today.weekday()) #Monday
    end_of_week = start_of_week + timedelta(days = 6) #Sunday

    sql = """SELECT SUM(co2e_saved) FROM ActionLog WHERE submitted_by = %s AND log_date BETWEEN %s AND %s"""
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (account_id, start_of_week, end_of_week))
        result = cursor.fetchone()
        if result is not None:
            return result["SUM(co2e_saved)"]
        else:
            return 0

def get_monthly_saved(account_id):
    temp_today = datetime.now()
    start_of_month = temp_today.replace(day = 1)
    last_date_of_month = monthrange(temp_today.year, temp_today.month)[1]
    end_of_month = datetime(temp_today.year, temp_today.month, last_date_of_month)

    sql = """SELECT SUM(co2e_saved) FROM ActionLog WHERE submitted_by = %s AND log_date BETWEEN %s AND %s"""

    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (account_id, start_of_month, end_of_month))
        result = cursor.fetchone()
        if result is not None:
            return result["SUM(co2e_saved)"]
        else:
            return 0

def get_yearly_saved(account_id):
    temp_today = datetime.now()
    start_of_year = temp_today.replace(day = 1, month=1)
    end_of_year = datetime(day = 31 , month=12, year = temp_today.year)

    sql = """SELECT SUM(co2e_saved) FROM ActionLog WHERE submitted_by = %s AND log_date BETWEEN %s AND %s"""

    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (account_id, start_of_year, end_of_year))
        result = cursor.fetchone()
        if result is not None:
            return result["SUM(co2e_saved)"]
        else:
            return 0





    