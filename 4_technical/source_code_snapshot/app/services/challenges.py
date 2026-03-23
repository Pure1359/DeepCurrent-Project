from app.db_config import db_cursor
from app.services.auth import verify_session_role
from flask import abort
from custom_error.Challenge_Exception import InvalidChallengeDate, ChallengeIdNotFound, UserAlreadyJoinChallenge, GroupAlreadyJoinChallenge
from custom_error.Group_Exception import *
from datetime import datetime

def _parse_date(value):
    if not isinstance(value, str):
        return value
    value = value.split(".")[0]
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


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

            start_date = _parse_date(start_date)
            end_date = _parse_date(end_date)

            if (start_date > current_time or end_date < current_time):
                raise InvalidChallengeDate("The challenge is currently not active")


        #if this is reached then user is not already in the challenge and the challenge exists and is still active
        cursor.execute(sql, (challenge_id, account_id, current_time))
    
#Add group and challenge to the GroupParticipation table
def join_challenge_group(challenge_id, group_id, account_id):
    
    current_time = datetime.now()
    #check if you are the group owner
    check_owner = """SELECT * FROM UserGroup WHERE group_id = %s AND group_creator_id = %s"""
    #check if challenge exists
    check_challenge = """SELECT start_date, end_date FROM Challenge WHERE challenge_id = %s"""
    #check if group already join a challenge
    check_duplicate_join = """SELECT * FROM GroupParticipation WHERE challenge_id = %s AND group_id = %s"""
    sql = """INSERT INTO GroupParticipation(challenge_id, group_id, joined_date) VALUES(%s, %s, %s)"""
    with db_cursor() as (connection, cursor):

        cursor.execute(check_owner, (group_id, account_id))
        result = cursor.fetchone()
        if result is None:
            raise GroupPermissionError("Normal member can not tell which challenge the group can join")
        
        cursor.execute(check_challenge, (challenge_id,))
        check_challenge = cursor.fetchone()
        if check_challenge is None:
            raise ChallengeIdNotFound(f"The Challenge with ID: {challenge_id} does not exists in database")
        
        cursor.execute(check_duplicate_join, (challenge_id, group_id))
        check_duplicate_join = cursor.fetchone()
        if check_duplicate_join is not None:
            raise GroupAlreadyJoinChallenge("The group already participate in this challenge")
    
        if check_challenge is not None:
            #check if challenge is active or not
            start_date = _parse_date(check_challenge["start_date"])
            end_date = _parse_date(check_challenge["end_date"])

            if (start_date > current_time or end_date < current_time):
                raise InvalidChallengeDate("The challenge is currently not active")
        
        cursor.execute(sql, (challenge_id, group_id, current_time))
            

def get_all_active_challenges():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = """SELECT c.challenge_id, c.challenge_type, c.title, c.start_date, c.end_date, c.rules, c.created_by
             FROM Challenge c
             WHERE c.start_date <= %s AND c.end_date >= %s
             ORDER BY c.end_date ASC"""
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (now, now))
        return cursor.fetchall()

def get_challenge_for_user(account_id):
    sql = """SELECT challenge_id FROM IndividualParticipation WHERE account_id = %s"""
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (account_id,))
        return cursor.fetchall()

def get_user_active_challenges_by_category(account_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = """SELECT Challenge.challenge_id, Challenge.title, Challenge.challenge_type, Challenge.start_date, Challenge.end_date
             FROM Challenge
             JOIN IndividualParticipation ON IndividualParticipation.challenge_id = Challenge.challenge_id
             WHERE IndividualParticipation.account_id = %s
               AND Challenge.start_date <= %s
               AND Challenge.end_date >= %s
             UNION
             SELECT Challenge.challenge_id, Challenge.title, Challenge.challenge_type, Challenge.start_date, Challenge.end_date
             FROM Challenge
             JOIN GroupParticipation ON GroupParticipation.challenge_id = Challenge.challenge_id
             JOIN AccountGroup ON AccountGroup.group_id = GroupParticipation.group_id
             WHERE AccountGroup.account_id = %s
               AND Challenge.start_date <= %s
               AND Challenge.end_date >= %s
             ORDER BY end_date ASC"""
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (account_id, now, now, account_id, now, now))
        return cursor.fetchall()

def challenge_leaderboard_individual():
    pass

def challenge_leaderboard_group():
    pass

