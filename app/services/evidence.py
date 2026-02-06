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
def create_decision():
    pass
#Does it need to required login? perhaps the route URL of page that contain submit button, already validate it?
def submit_evidence(some_param):
    pass

def list_pending_evidence(limit, offset):
    sql = """SELECT evidence_id, evidence_type, evidence_url, evidence_date
             FROM Evidence
             ORDER BY evidence_date DESC
             LIMIT %s
             OFFSET %s
          """
    
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (limit, offset))
        submission_list = cursor.fetchall()

        json_list = []
        for record_tuple in submission_list:
            new_dict = {"evidence_id" : record_tuple[0], "evidence_type" : record_tuple[1], "evidence_url" : record_tuple[2], "evidence_date" : record_tuple[3]}
            json_list.append(new_dict)
        
        return jsonify(json_list)
    
    
#Something to do with fetching database
def get_evidence_decision():
    pass

