from app.db_config import db_cursor
from app.services.auth import verify_session_role
from flask import abort
from custom_error.Challenge_Exception import InvalidChallengeDate, ChallengeIdNotFound, UserAlreadyJoinChallenge
from datetime import datetime
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
def create_challenge(created_by, challenge_type, title, start_date, end_date, rules):
    sql = """INSERT INTO Challenge (created_by, challenge_type, title, start_date, end_date, rules) 
            VALUES (%s, %s, %s, %s, %s, %s)"""
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (created_by, challenge_type, title, start_date, end_date, rules))
        return cursor.lastrowid

#Add user and challenge to the individualParticipation table
def join_challenge_individual(challenge_id, account_id):
    current_time = datetime.now()
    #check to see if the challenge is expired or not
    check_challenge = """SELECT start_date, end_date FROM Challenge WHERE challenge_id = %s"""
    check_duplicate_join = """SELECT challenge_id, account_id FROM IndividualParticipation WHERE challenge_id = %s AND account_id = %s"""
    sql = """INSERT INTO IndividualParticipation (challenge_id, account_id, joined_date) VALUES(%s, %s, %s)"""

    with db_cursor() as (connection, cursor):
        #check to see if the user already joined
        cursor.execute(check_duplicate_join, (challenge_id, account_id))
        if (cursor.fetchone() is not None):
            raise UserAlreadyJoinChallenge("The user already participate in this challenge")

        cursor.execute(check_challenge, (challenge_id,))
        check_challenge_result = cursor.fetchone()
        if (check_challenge_result is None):
            raise ChallengeIdNotFound(f"The Challenge with ID: {challenge_id} does not exists in database" )
        elif(check_challenge_result is not None):
            start_date = check_challenge_result["start_date"]
            end_date = check_challenge_result["end_date"]

            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, "%Y-%m-%d")
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, "%Y-%m-%d")

            if (start_date > current_time or end_date < current_time):
                raise InvalidChallengeDate("The challenge is currently not active")
            
            
        #if this is reached then user is not already in the challenge and the challenge exists and is still active
        cursor.execute(sql, (challenge_id, account_id, current_time))
    
#Add group and challenge to the GroupParticipation table
def join_challenge_group(challenge_id, group_id, join_date):
    sql = """INSERT INTO GroupParticipation (challenge_id, group_id, join_date) VALUES(%s, %s, %s)"""

    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (challenge_id, group_id, join_date))

def challenge_leaderboard_individual():
    pass

def challenge_leaderboard_group():
    pass

