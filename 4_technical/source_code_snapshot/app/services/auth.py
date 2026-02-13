import bcrypt
from app.db_config import db_cursor
from flask import session
# Check if account exists via email
def get_account_by_email_for_login(email):
    sql = """
        SELECT a.account_id, a.user_id, a.username, a.password, a.is_moderator, u.email
        FROM Accounts a
        JOIN Users u ON a.user_id = u.user_id
        WHERE u.email = %s
        """
    
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (email,))
        return cursor.fetchone()

# Check if password is correct
def verify_password(plain_password, stored_password):
    if stored_password is None:
        return False
    
    # stored_password may be bytes for MySQL or string for SQLite
    if isinstance(stored_password, bytes):
        stored_password = stored_password
        return bcrypt.checkpw(plain_password.encode("utf-8"), stored_password) 
    else:
        stored_bytes = str(stored_password).encode("utf-8")
        return bcrypt.checkpw(plain_password.encode("utf-8"), stored_bytes)    

def verify_session_role(unknown_session, known_session):
    if (unknown_session == known_session):
        return True
    else:
        return False
    
# Return "moderator" or "user" based on account flags
def derive_role(account_row):
    print(f"derive_role is {account_row}")
    try:
        if int(account_row.get("is_moderator") or 0) == 1:
            return "moderator"
    except Exception:
        pass
    return "user"
