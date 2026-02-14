from app.db_config import db_cursor
from flask import Response, jsonify, session
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
def log_action(account_id, name, category, quantity, challenge_id = None, evidence_url = None):
    current_time = datetime.now()
    #implement this later
    co2e_saved = 0
 
    #Get what type an action being logged is. e.g. Is it (cycle, travel)?
    sqlActionType = """SELECT * FROM ActionTYPE
                       WHERE actionName = %s AND category = %s
                    """

    sqlActionLog = """INSERT INTO ActionLog(submitted_by, actionType_id, log_date, quantity, co2e_saved) VALUES (%s, %s, %s, %s, %s)"""
    with db_cursor() as (connection, cursor):
        cursor.execute(sqlActionType, (name, category))
        return_record = cursor.fetchone()
        if return_record is None:
            raise ValueError(f"Action type does not exists: {name}, {category}")
        
        actionType_id = return_record["actionType_id"]
        co2e_factor = return_record["co2e_factor"]
        co2e_saved = co2e_factor * quantity

        cursor.execute(sqlActionLog, (account_id, actionType_id, current_time, quantity, co2e_saved))

        action_log_id = cursor.lastrowid

        inserted_decision_id = None
        inserted_evidence_id = None
    
        if evidence_url is not None:
            inserted_evidence_id = insert_evidence_record(cursor, action_log_id, None, evidence_url, current_time)
            inserted_decision_id = insert_decision_record(cursor,inserted_evidence_id, None, "pending", None, None)
        #For prototype only, in the final project the apply_to_challenge() will only be called when there is evidence_url
        if challenge_id is not None:
            challenge_id = apply_to_challenge(cursor, challenge_id, action_log_id, co2e_saved)

        return {"action_log_id" : action_log_id, "evidence_id" : inserted_evidence_id, "decision_id" : inserted_decision_id, "challenge_id" : challenge_id, "co2e_factor" : co2e_factor, "co2e_saved" : co2e_saved}
    
        

def insert_evidence_record(cursor:DictCursor, action_log_id, evidence_type, evidence_url, evidence_date):
    insert_evidence = """INSERT INTO Evidence(log_id, evidence_type, evidence_url, evidence_date) VALUES (%s, %s, %s, %s)"""
    cursor.execute(insert_evidence, (action_log_id, evidence_type, evidence_url, evidence_date))
    return cursor.lastrowid

def insert_decision_record(cursor:DictCursor, evidence_id, reviewer_id, decision_status, decision_date, reason):
    insert_decision = """INSERT INTO Decision(evidence_id, reviewer_id, decision_status, decision_date, reason) VALUES(%s, %s, %s, %s, %s)"""
    cursor.execute(insert_decision, (evidence_id, reviewer_id, decision_status, decision_date, reason))
    return cursor.lastrowid


#Find the challenge that is eligible to be applied to
def apply_to_challenge(cursor:DictCursor, challenge_id, action_log_id, co2e_saved):

    insertion = """INSERT INTO ChallengeAction(challenge_id, group_id, log_id, point_awarded) VALUES (%s, %s, %s, %s)"""

    points_awarded = co2e_saved
    
    #Prototype support individual only no need for group now
    group_id = None

    cursor.execute(insertion, (challenge_id, group_id, action_log_id, points_awarded))
    return cursor.lastrowid

def get_action_history(account_id, limit, offset):
    sql = """SELECT 
                actionName,
                category,
                quantity,
                evidence_url,
                evidence_type,
                evidence_date,
                decision_status,
                unit
            FROM ActionLog
            LEFT JOIN Evidence 
                ON ActionLog.log_id = Evidence.log_id
            LEFT JOIN Decision 
                ON Evidence.evidence_id = Decision.evidence_id
            LEFT JOIN ActionType 
                ON ActionType.actionType_id = ActionLog.actionType_id
            WHERE submitted_by = %s
            ORDER BY evidence_date DESC
            LIMIT %s OFFSET %s
         """
     
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (account_id, limit, offset))
        action_list = cursor.fetchall()
        return jsonify(action_list)
    
def personal_dashboard(account_id):
    totals_sql = """
        SELECT
            COALESCE(SUM(ca.point_awarded), 0) AS total_points,
            COALESCE(SUM(al.co2e_saved), 0) AS total_co2e_saved,
            COUNT(al.log_id) AS actions_count
        FROM ActionLog al
        LEFT JOIN ChallengeAction ca ON ca.log_id = al.log_id
        WHERE al.submitted_by = %s
    """
    recent_sql = """
        SELECT al.log_id, at.actionName, at.category, al.quantity, at.unit, al.co2e_saved, al.log_date
        FROM ActionLog al
        JOIN ActionType at ON at.actionType_id = al.actionType_id
        WHERE al.submitted_by = %s
        ORDER BY al.log_date DESC
        LIMIT 10
    """
    with db_cursor() as (connection, cursor):
        cursor.execute(totals_sql, (account_id,))
        totals = cursor.fetchone() or {"total_points": 0, "total_co2e_saved": 0, "actions_count": 0}
        cursor.execute(recent_sql, (account_id,))
        recent = cursor.fetchall()
    return {"totals": totals, "recent_actions": recent}

def leaderboard(limit):
    sql = """
        SELECT
            a.account_id,
            u.first_name,
            u.last_name,
            COALESCE(SUM(ca.point_awarded), 0) AS points
        FROM Accounts a
        JOIN Users u ON u.user_id = a.user_id
        LEFT JOIN ActionLog al ON al.submitted_by = a.account_id
        LEFT JOIN ChallengeAction ca ON ca.log_id = al.log_id
        GROUP BY a.account_id, u.first_name, u.last_name
        ORDER BY points DESC
        LIMIT %s
    """
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (limit,))
        return cursor.fetchall()



        
    
    



        
        

