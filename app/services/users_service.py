from app.db_config import db_cursor

# Create a user in the database
def create_user(first_name, last_name, email, dob, user_type, course=None, department=None):
    sql = "INSERT INTO user (first_name, last_name, email, dob, user_type, course, department) VALUES (%s, %s, %s, %s, %s, %s, %s)"

    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (first_name, last_name, email, dob, user_type, course, department))
        return cursor.lastrowid # Return user_id

# Create an account in the database
def create_account(user_id, username, password, date_created, last_active):
    sql = "INSERT INTO account (user_id, username, password, date_created, last_active) VALUES (%s, %s, %s, %s, %s)"

    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (user_id, username, password, date_created, last_active))
        return cursor.lastrowid # Return account_id

# Update Last Active
def update_last_active(account_id, last_active):
    sql = "UPDATE account SET last_active = %s WHERE account_id = %s"

    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (last_active, account_id))

def get_user_role(user_id):
    sql = "SELECT user_type FROM USER WHERE user_id = %s"

    with db_cursor() as (connection, cursor):
        cursor.execute(sql,user_id)
        return cursor.fetchone()
    
