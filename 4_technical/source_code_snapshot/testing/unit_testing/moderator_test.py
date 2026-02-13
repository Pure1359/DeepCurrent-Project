from datetime import datetime, timedelta
import pytest
from database_fixture import *
from app.db_config import db_cursor

def test_login_moderator(new_client_module, recorded_template_module, module_scope_database):
    response = new_client_module.post("/login", data = {
        "email" : "j.miller@exeter.ac.uk",
        "password" : "moderator456" 
    }, follow_redirects = True)

    assert len(recorded_template_module) == 1
    template, context = recorded_template_module[-1]
    assert response.request.path == "/dashboard"
    assert template.name == "dashboard.html"

    with new_client_module.session_transaction() as session:
        assert session.get("account_role") == "moderator"

def test_moderator_make_challenge(new_client_module, recorded_template_module, module_scope_database):
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

def test_moderator_view_pending_evidence(new_client_module, recorded_template_module, module_scope_database):
    response = new_client_module.post("/moderator_access/view_submission_list", json = {
        "offset" : 0,
        "limit" : 100
    }, follow_redirects = True)
    response = response.get_json()
    assert len(response) == 1
    

