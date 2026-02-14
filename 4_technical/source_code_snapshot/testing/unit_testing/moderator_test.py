from datetime import datetime, timedelta
import pytest
from database_fixture import *
from app.db_config import db_cursor

def test_login_moderator(new_client_module, recorded_template_module, module_scope_database, populated_database):
    response = new_client_module.post("/login", data = {
        "email" : "j.miller@exeter.ac.uk",
        "password" : "moderator456" 
    }, follow_redirects = True)

    assert len(recorded_template_module) >= 1
    template, context = recorded_template_module[-1]
    assert response.request.path == "/dashboard"
    assert template.name == "dashboard.html"

    with new_client_module.session_transaction() as session:
        assert session.get("account_role") == "moderator"

def test_moderator_make_challenge(new_client_module, recorded_template_module, module_scope_database, populated_database):
    start_date = datetime.now()
    end_date = datetime.now() + timedelta(days = 30)
    response = new_client_module.post("/moderator_access/create_challenge", data = {
        "challenge_type" : "travel",
        "title" : "Let Walk",
        "start_date" : start_date,
        "end_date" : end_date,
        "rule" : "Walk in a park"
    })
    response = response.get_json()
    challenge_id = response["challenge_id"]

    with db_cursor() as (connection, cursor):
        sql = """SELECT * FROM Challenge WHERE challenge_id = %s"""
        cursor.execute(sql, (challenge_id,))
        response = cursor.fetchone()

        assert response["created_by"] == 2
        assert response["challenge_type"] == "travel"
        assert response["title"] == "Let Walk"
        assert response["start_date"] == str(start_date)
        assert response["end_date"] == str(end_date)
        assert response["rules"] == "Walk in a park"

        sql = "SELECT * FROM Accounts"
        cursor.execute(sql)
        accounts = cursor.fetchall()

def test_moderator_view_pending_evidence(new_client_module, recorded_template_module, module_scope_database, populated_database):
    response = new_client_module.post("/moderator_access/view_pending_submission", json = {
        "offset" : 0,
        "limit" : 100
    }, follow_redirects = True)
    response = response.get_json()
    assert len(response) == 7

    print(response)
    
def test_moderator_accept_pending_evidence(new_client_module, recorded_template_module, module_scope_database, populated_database):
    response = new_client_module.post("/moderator_access/approve_submission", json = {
        "evidence_id" : 1,
        "result" : "accepted",
        "reason" : "Evidence is accepted"
    }, follow_redirects = True)

    response = response.get_json()
    decision_list = response["decision_list"]
    assert len(decision_list) == 1
    
    sql = """SELECT * FROM Decision WHERE decision_id = %s"""
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (decision_list[-1],))
        result = cursor.fetchall()
        assert result[0]["decision_status"] == "accepted"


def test_moderator_reject_pending_evidence(new_client_module, recorded_template_module, module_scope_database, populated_database):
    response = new_client_module.post("/moderator_access/approve_submission", json = {
        "evidence_id" : 2,
        "result" : "rejected",
        "reason" : "Wrong Challenge"
    }, follow_redirects = True)

    response = response.get_json()
    decision_list = response["decision_list"]
    assert len(decision_list) == 1
    
    sql = """SELECT * FROM Decision WHERE decision_id = %s"""
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (decision_list[-1],))
        result = cursor.fetchall()
        assert result[0]["decision_status"] == "rejected"

    response = new_client_module.post("/moderator_access/view_pending_submission", json = {
        "offset" : 0,
        "limit" : 100,
    })

    response = response.get_json()
    assert len(response) == 5

def test_check_db_after(new_client_module, recorded_template_module, module_scope_database, populated_database):
    #check if evidence record and decision record is generated when in case of evidence is submitted by user
    sqlActionLog = """SELECT * FROM ActionLog"""
    sqlEvidence = """SELECT * FROM Evidence"""
    sqlDecision = """SELECT * FROM Decision"""
    sqlChallengeAction = """SELECT * FROM ChallengeAction"""
    with db_cursor() as (connection, cursor):
        # Check ActionLog
        cursor.execute(sqlActionLog)
        result = cursor.fetchall()

        assert len(result) == 18
        assert result[0]["log_id"] == 1
        assert result[0]["submitted_by"] == 1
        assert result[0]["actionType_id"] == 1
        assert result[0]["quantity"] == 2
        assert result[0]["co2e_saved"] == 1.4

        assert result[1]["log_id"] == 2
        assert result[1]["submitted_by"] == 1
        assert result[1]["actionType_id"] == 2
        assert result[1]["quantity"] == 4
        assert result[1]["co2e_saved"] == 3.6

        # Check Evidence
        cursor.execute(sqlEvidence)
        result = cursor.fetchall()

        assert len(result) == 7
        assert result[0]["evidence_id"] == 1
        assert result[0]["log_id"] == 1
        assert result[0]["evidence_type"] is None
        assert result[0]["evidence_url"] == "url1"
        
        assert result[1]["evidence_id"] == 2
        assert result[1]["log_id"] == 2
        assert result[1]["evidence_type"] is None
        assert result[1]["evidence_url"] == "url2"

        # Check Decision
        cursor.execute(sqlDecision)
        result = cursor.fetchall()

        assert len(result) == 7
        # First decision (Accepted)
        assert result[0]["decision_id"] == 1
        assert result[0]["evidence_id"] == 1
        assert result[0]["reviewer_id"] == 2  # James (moderator)
        assert result[0]["decision_status"] == "accepted"
        assert result[0]["reason"] == "Evidence is accepted"
        assert result[0]["decision_date"] is not None
        
        # Second decision (Rejected)
        assert result[1]["decision_id"] == 2
        assert result[1]["evidence_id"] == 2
        assert result[1]["reviewer_id"] == 2  # James (moderator)
        assert result[1]["decision_status"] == "rejected"
        assert result[1]["reason"] == "Wrong Challenge"
        assert result[1]["decision_date"] is not None

        # Check ChallengeAction
        cursor.execute(sqlChallengeAction)
        result = cursor.fetchall()

        assert len(result) == 9
        assert result[0]["challenge_id"] == 1
        assert result[0]["group_id"] is None
        assert result[0]["log_id"] == 1
        assert result[0]["point_awarded"] == 1.4

        assert result[1]["challenge_id"] == 1
        assert result[1]["group_id"] is None
        assert result[1]["log_id"] == 2
        assert result[1]["point_awarded"] == 3.6

    
    

        
        



