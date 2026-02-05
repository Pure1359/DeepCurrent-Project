from app.db_config import db_cursor
from app.services.auth import verify_session_role
from flask import abort
# Placeholder for now
# Create functions that have to do with challenges
# Follow templates in users.py and auth.py
# Some Ideas:
# create_challenge
# join_challenge_individual
# join_challenge_group
# challenge_leaderboard_individual
# challenge_leaderboard_group
#Required role : Who can create the challenge? Parameter : Role -> {Admin, Locally Group Leader , etc}
def create_challenge(created_by, challenge_type, is_official, title, start_date, end_date, rules, session_role):
    if verify_session_role(session_role, "moderator"):
        sql = """INSERT INTO Challenge (created_by, challenge_type, is_official, title, start_date, end_date, rules) 
              VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        with db_cursor as (connection, cursor):
            cursor.execute(sql, (created_by, challenge_type, is_official, title, start_date, end_date, rules))
    else:
        abort(404)
#Add user and challenge to the individualParticipation table
def join_challenge_individual(challenge_id, account_id, join_date):
    sql = """INSERT INTO IndividualParticipation (challenge_id, account_id, join_date) VALUES(%s, %s, %s)"""

    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (challenge_id, account_id, join_date))
    
#Add group and challenge to the GroupParticipation table
def join_challenge_group(challenge_id, group_id, join_date):
    sql = """INSERT INTO GroupParticipation (challenge_id, group_id, join_date) VALUES(%s, %s, %s)"""

    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (challenge_id, group_id, join_date))

def challenge_leaderboard_individual():
    pass

def challenge_leaderboard_group():
    pass

