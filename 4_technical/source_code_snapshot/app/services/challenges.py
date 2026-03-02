import sqlite3
from typing import Any

from app.db_config import db_cursor
from app.services.auth import verify_session_role
from flask import abort
from custom_error.Challenge_Exception import InvalidChallengeDate, ChallengeIdNotFound, UserAlreadyJoinChallenge, GroupAlreadyJoinChallenge
from custom_error.Group_Exception import *
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
            start_date = check_challenge["start_date"]
            end_date = check_challenge["end_date"]
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

            if (start_date > current_time or end_date < current_time):
                raise InvalidChallengeDate("The challenge is currently not active")
        
        cursor.execute(sql, (challenge_id, group_id, current_time))
            
    
#ignore specific challenge conflict with category type, we will check this later
def challenge_leaderboard_individual(start_date :str, end_date:str, challenge_category_type:str = "All", specific_challenge:int|None = None) -> list[dict]:
    """
    Give the ranking and leaderboard of individuals and groups based on parameter given

    Args:
        start_date (string): The start date to filter rankings from
        end_date (string): The end date to filter ranking to
        challenge_category_type(string): What type of challenge to be consider for ranking ("Travel", "Energy", "Food", "Waste", "All")
        specific_challenge(int): Use to show leaderboard only for 1 particular challenge, by using challenge id. 

    Returns:
        list[dict] : list of dictionary, each dictionary represent each record , each key in dictionary represent each field
    """

    if specific_challenge is not None and challenge_category_type != "All":
        raise ValueError("Invalid argument type : if specific_challenge is given, challenge_category_type must be \"All\"")
    
    
    query = """SELECT Accounts.account_id, username, SUM(ChallengeAction.point_awarded) AS Total_Points FROM Accounts INNER JOIN ActionLog ON Accounts.account_id = ActionLog.submitted_by INNER JOIN ActionType ON ActionLog.actionType_id = ActionType.actionType_id INNER JOIN ChallengeAction ON ActionLog.log_id = ChallengeAction.log_id INNER JOIN Evidence ON Evidence.log_id = ActionLog.log_id INNER JOIN Decision ON Evidence.evidence_id = Decision.evidence_id WHERE ActionLog.log_date BETWEEN %s AND %s AND Decision.decision_status = 'Approved'"""

    parameter: list[str|int] = [start_date, end_date]


    if specific_challenge is not None:
        query += """ AND ChallengeAction.challenge_id = %s"""
        parameter.append(specific_challenge)

    if challenge_category_type != "All":
        query += """ AND ActionType.category = %s"""
        parameter.append(challenge_category_type)

    #Group by operation
    query += """ GROUP BY Accounts.account_id , username"""


    with db_cursor() as (connection, cursor):
        cursor.execute(query, parameter)
        query_result = cursor.fetchall()
    

    return query_result


def challenge_leaderboard_group():
    pass
