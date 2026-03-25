from datetime import datetime, timedelta
import pytest
from database_fixture import *
from app.db_config import db_cursor

def test_login_moderator(new_client_module, recorded_template_module, module_scope_database, populated_database):
    response = new_client_module.post("/login", data = {
        "email" : "j.miller@exeter.ac.uk",
        "password" : "moderator456" 
    }, follow_redirects = True)

    #check to see if we can login as the moderator and have access to the dashboard, and check the session
    assert len(recorded_template_module) >= 1
    template, context = recorded_template_module[-1]
    assert response.request.path == "/dashboard"
    assert template.name == "dashboard.html"

    with new_client_module.session_transaction() as session:
        assert session.get("account_role") == "moderator"

def test_moderator_make_challenge(new_client_module, recorded_template_module, module_scope_database, populated_database):
    #check if when the moderator make a challenge, the challenge record is inserted into the database
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days = 30)).strftime("%Y-%m-%d")
    response = new_client_module.post("/moderator_access/create_challenge", data = {
        "challenge_type" : "Personal",
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
        assert response["challenge_type"] == "Personal"
        assert response["title"] == "Let Walk"
        assert response["start_date"] == start_date + " 00:00:00"
        assert response["end_date"] == end_date + " 23:59:59"
        assert response["rules"] == "Walk in a park"

def test_moderator_view_pending_evidence(new_client_module, recorded_template_module, module_scope_database, populated_database):
    response = new_client_module.post("/moderator_access/view_pending_submission", json = {
        "offset" : 0,
        "limit" : 100
    }, follow_redirects = True)
    response = response.get_json()
    assert len(response) == 7

    print(response)

def test_moderator_accept_pending_evidence(new_client_module, recorded_template_module, module_scope_database, populated_database):
    response = new_client_module.post("/moderator_access/make_decision", json = {
        "evidence_id" : 1,
        "result" : "accepted",
        "reason" : "Evidence is accepted"
    }, follow_redirects = True)
    #We used to assume that evidence can have multiple decision, because evidence can be applied to many actionlog, but we won't need that for the prototype right now
    #This still work:
    response = response.get_json()
    decision_list = response["decision_list"]
    assert len(decision_list) == 1
    
    sql = """SELECT * FROM Decision WHERE decision_id = %s"""
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (decision_list[-1],))
        result = cursor.fetchall()
        assert result[0]["decision_status"] == "accepted"


def test_moderator_reject_pending_evidence(new_client_module, recorded_template_module, module_scope_database, populated_database):
    response = new_client_module.post("/moderator_access/make_decision", json = {
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
    assert len(response) == 6

def test_moderator_view_all_submission_again(new_client_module, recorded_template_module, module_scope_database, populated_database):
    response = new_client_module.post("/moderator_access/view_all_submission", json = {
        "offset" : 0,
        "limit" : 100
    }, follow_redirects = True)
    response = response.get_json()
    assert len(response) == 10

def test_check_db_after(new_client_module, recorded_template_module, module_scope_database, populated_database):
    with db_cursor() as (connection, cursor):
        # Check total counts
        cursor.execute("SELECT COUNT(*) AS count FROM ActionLog")
        assert cursor.fetchone()["count"] == 19

        cursor.execute("SELECT COUNT(*) AS count FROM Evidence")
        assert cursor.fetchone()["count"] == 10

        cursor.execute("SELECT COUNT(*) AS count FROM Decision")
        assert cursor.fetchone()["count"] == 10

        cursor.execute("SELECT COUNT(*) AS count FROM ChallengeAction")
        assert cursor.fetchone()["count"] == 10

        # Check specific action log created for url1
        cursor.execute(
            """
            SELECT al.*
            FROM ActionLog al
            JOIN Evidence e ON e.log_id = al.log_id
            WHERE e.evidence_url = %s
            """,
            ("url1",)
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["submitted_by"] == 1
        assert row["actionType_id"] == 1
        assert row["quantity"] == '2'
        assert row["co2e_saved"] == 1.4

        # Check specific action log created for url2
        cursor.execute(
            """
            SELECT al.*
            FROM ActionLog al
            JOIN Evidence e ON e.log_id = al.log_id
            WHERE e.evidence_url = %s
            """,
            ("url2",)
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["submitted_by"] == 1
        assert row["actionType_id"] == 2
        assert row["quantity"] == '4'
        assert row["co2e_saved"] == 3.6

        # Check Evidence row for url1
        cursor.execute(
            """
            SELECT *
            FROM Evidence
            WHERE evidence_url = %s
            """,
            ("url1",)
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["log_id"] is not None
        assert row["evidence_type"] is None
        assert row["evidence_url"] == "url1"

        # Check Evidence row for url2
        cursor.execute(
            """
            SELECT *
            FROM Evidence
            WHERE evidence_url = %s
            """,
            ("url2",)
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["log_id"] is not None
        assert row["evidence_type"] is None
        assert row["evidence_url"] == "url2"

        # Check accepted decision exists
        cursor.execute(
            """
            SELECT *
            FROM Decision
            WHERE decision_status = %s AND reason = %s
            """,
            ("accepted", "Evidence is accepted")
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["evidence_id"] is not None
        assert row["reviewer_id"] is not None
        assert row["decision_date"] is not None

        # Check rejected decision exists
        cursor.execute(
            """
            SELECT *
            FROM Decision
            WHERE decision_status = %s AND reason = %s
            """,
            ("rejected", "Wrong Challenge")
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["evidence_id"] is not None
        assert row["reviewer_id"] is not None
        assert row["decision_date"] is not None

        # Check ChallengeAction for the first travel challenge action
        cursor.execute(
            """
            SELECT ca.*
            FROM ChallengeAction ca
            JOIN ActionLog al ON al.log_id = ca.log_id
            WHERE ca.challenge_id = %s
              AND al.submitted_by = %s
              AND al.actionType_id = %s
              AND al.quantity = %s
            """,
            (1, 1, 1, '2')
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["challenge_id"] == 1
        assert row["group_id"] is None
        assert row["point_awarded"] == 1.4

        # Check ChallengeAction for the second travel challenge action
        cursor.execute(
            """
            SELECT ca.*
            FROM ChallengeAction ca
            JOIN ActionLog al ON al.log_id = ca.log_id
            WHERE ca.challenge_id = %s
              AND al.submitted_by = %s
              AND al.actionType_id = %s
              AND al.quantity = %s
            """,
            (1, 1, 2, '4')
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["challenge_id"] == 1
        assert row["group_id"] is None
        assert row["point_awarded"] == 3.6