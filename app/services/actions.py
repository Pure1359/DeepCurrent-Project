from app.db_config import db_cursor
from flask import session
from datetime import datetime
from flask import abort
from pymysql.cursors import DictCursor

# Placeholder for now
# Create functions that have to do with actions
# Follow templates in users.py and auth.py
# Some Ideas:
# log_action
# get_action_logs
# get_account_totals

#Log action into database
def log_action(name, category, quantity, evidence_url = None):
    current_time = datetime.now()
    if not name or not category or quantity is None:
        raise ValueError("name, category and quantity is required")
    
    account_id = session.get("account_id")
    if not account_id:
        abort(400, description = "User is not login")

    #implement this later
    co2e_saved = 0
 
    #Get what type an action being logged is. e.g. Is it (cycle, travel)?
    sqlActionType = """SELECT actionType_id FROM ActionTYPE
                       WHERE name = %s AND category = %s
                    """

    sqlActionLog = """INSERT INTO ActionLog(submitted_by, actionType_id, log_date, quantity, co2e_saved) VALUES (%s, %s, %s, %s, %s)"""
    with db_cursor() as (connection, cursor):
        cursor.execute(sqlActionType, (name, category))
        return_record = cursor.fetchone()
        if return_record is None:
            raise ValueError(f"Action type does not exists: {name}, {category}")
        
        actionType_id = return_record["actionType_id"]
        cursor.execute(sqlActionLog, (account_id, actionType_id, current_time, quantity, co2e_saved))
        action_log_id = cursor.lastrowid
    
        if evidence_url is not None:
            inserted_evidence_id = insert_evidence_record(cursor, action_log_id, None, evidence_url, current_time)
            inserted_decision_id = insert_decision_record(cursor,inserted_evidence_id, None, "pending", None, None)
            apply_to_challenge(cursor, account_id, name, category, action_log_id,current_time)
        return action_log_id
    

def insert_evidence_record(cursor:DictCursor, action_log_id, evidence_type, evidence_url, evidence_date):
    insert_evidence = """INSERT INTO Evidence(action_log_id, evidence_type, evidence_url, evidence_date) VALUES (%s, %s, %s, %s)"""
    cursor.execute(insert_evidence, (action_log_id, evidence_type, evidence_url, evidence_date))

    return cursor.lastrowid

def insert_decision_record(cursor:DictCursor, evidence_id, reviewer_id, decision_status, decision_date, reason):
    insert_decision = """INSERT Decision(evidence_id, reviewer_id, decision_status, decision_date, reason) VALUES(%s, %s, %s, %s, %s)"""
    cursor.execute(insert_decision, (evidence_id, reviewer_id, decision_status, decision_date, reason))
    return cursor.lastrowid


#Find the challenge that is eligible to be applied to
def apply_to_challenge(cursor:DictCursor, account_id, name, category, action_log_id, current_time):

    #Search the challenge that the user is participating
    sql = """SELECT challenge_id FROM IndividualParticipation JOIN Challenge ON IndividualParticipation.challenge_id = Challenge.challenge_id WHERE account_id = %s AND name = %s AND category = %s AND start_date <= %s AND end_date >= %s"""

    cursor.execute(sql, (account_id, name, category, current_time, current_time))
    #Even if there is no challenge eligible we still want the user to have evidence recorded in the database, so we can give them point separately from the challenge
    for challenge_id_tuple in cursor.fetchall():
        challenge_id = challenge_id_tuple["challenge_id"]

        insertion = """INSERT INTO ChallengeAction(challenge_id, group_id, log_id, points_awarded) VALUES (%s, %s, %s, %s)"""

        #implement this later
        points_awarded = 0
        
        #Prototype support individual only no need for group now
        group_id = None

        cursor.execute(insertion, (challenge_id, None, action_log_id, points_awarded))



        
    
    



        
        

