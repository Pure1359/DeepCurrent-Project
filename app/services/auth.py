import bcrypt
from app.db_config import db_cursor

# Check if account exists via email
def get_account_by_email_for_login(email):
    sql = """
        SELECT a.account_id, a.user_id, a.username, a.password, u.email
        FROM account a
        JOIN user u ON a.user_id = u.user_id
        WHERE u.email = %s
        """
    
    with db_cursor() as cursor:
        cursor.execute(sql, (email))
        return cursor.fetchone()

# Check if password is correct
def verify_password(plain_password, stored_password):
    if stored_password is None:
        return False
    
    # Hash password and check against stored password
    return bcrypt.checkpw(plain_password.encode("utf-8"), stored_password.encode("utf-8"))