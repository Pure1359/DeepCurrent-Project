from app.db_config import db_cursor
from flask import jsonify
# Placeholder for now
# Create functions that have to do with evidence
# Follow templates in users.py and auth.py
# Some Ideas:
# submit_evidence
# create_decision (admin deciding to approve or not)
# list_pending_evidence (list evidence that is awaiting admin approval)
# get_evidence_decisions



#Return Boolean? : Approve -> True, Disapprove -> False
def create_decision(reviewer_id, status, date, reason, evidence_id):
    sql = """UPDATE Decision SET reviewer_id = %s ,decision_status = %s, decision_date = %s, decision_reason = %s WHERE evidence_id = %s"""

    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (reviewer_id, status, date, reason, evidence_id))

#Ignore this function for now
def submit_evidence(some_param):
    pass

def list_pending_decision(limit, offset):
    sql = """SELECT 
                actionName,
                category,
                quantity,
                evidence_url,
                evidence_type,
                evidence_date,
                unit
            FROM Decision
            JOIN Evidence 
                ON Decision.evidence_id = Evidence.evidence_id
            JOIN ActionLog 
                ON Evidence.log_id = ActionLog.log_id
            JOIN ActionType 
                ON ActionType.actionType_id = ActionLog.actionType_id
            ORDER BY evidence_date DESC
            LIMIT %s OFFSET %s
         """
    
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (limit, offset))
        submission_list = cursor.fetchall()
        return jsonify(submission_list)
    
    
#Something to do with fetching database
def get_evidence_decision():
    pass
