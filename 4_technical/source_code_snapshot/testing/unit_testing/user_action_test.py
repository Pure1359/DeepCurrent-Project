from datetime import datetime, timedelta
import pytest
from database_fixture import *
from app.db_config import db_cursor
from app.services.actions import log_action
from app.services.users_service import get_weekly_saved, get_monthly_saved, get_yearly_saved

def test_log_action_challenge(new_client_module, module_scope_database, populated_database):
    response = new_client_module.post("/login", data = {
        "email" : "e.watson@exeter.ac.uk",
        "password" : "password123"
    }, follow_redirects = True)

    result = new_client_module.post("/user_access/submit_action", json = {"action_name" : "walk", "category" : "travel", "quantity" : 50, "challenge_id" : 1, "evidence_url" : "url_new_challenge"})
    result = result.get_json()

    print(result)
    # Log a new challenge action with evidence
    
    # Verify ActionLog is created
    with db_cursor() as (connection, cursor):
        cursor.execute("SELECT * FROM ActionLog WHERE log_id = %s", (result["action_log_id"],))
        action_log = cursor.fetchone()
        
        assert action_log is not None
        assert action_log["submitted_by"] == 1
        assert action_log["quantity"] == 50
        assert action_log["actionType_id"] == 1  # walk
        assert action_log["co2e_saved"] == 50 * 0.7
        
        # Verify Evidence is created
        cursor.execute("SELECT * FROM Evidence WHERE log_id = %s", (result["action_log_id"],))
        evidence = cursor.fetchone()
        
        assert evidence is not None
        assert evidence["evidence_url"] == "url_new_challenge"
        
        # Verify Decision created with correct pending status
        cursor.execute("SELECT * FROM Decision WHERE evidence_id = %s", (evidence["evidence_id"],))
        decision = cursor.fetchone()
        
        assert decision is not None
        assert decision["decision_status"] == "pending"
        assert decision["reviewer_id"] is None
        
        # Verify ChallengeAction is created
        cursor.execute("SELECT * FROM ChallengeAction WHERE log_id = %s", (result["action_log_id"],))
        challenge_action = cursor.fetchone()
        
        assert challenge_action is not None
        assert challenge_action["challenge_id"] == 1
        assert challenge_action["point_awarded"] == 50 * 0.7

def test_log_action_personal(new_client_module, module_scope_database, populated_database):
    # Log a personal action (no challenge, no evidence)
    result = new_client_module.post("/user_access/submit_action", json = {"action_name" : "bus", "category" : "travel", "quantity" : 30})
    result = result.get_json()

    
    with db_cursor() as (connection, cursor):
        # Verify ActionLog created
        cursor.execute("SELECT * FROM ActionLog WHERE log_id = %s", (result["action_log_id"],))
        action_log = cursor.fetchone()
        
        assert action_log is not None
        assert action_log["submitted_by"] == 1
        assert action_log["quantity"] == 30
        assert action_log["actionType_id"] == 2  # bus
        assert action_log["co2e_saved"] == 30 * 0.9
        
        # Verify NO Evidence created
        cursor.execute("SELECT * FROM Evidence WHERE log_id = %s", (result["action_log_id"],))
        evidence = cursor.fetchone()
        assert evidence is None
        
        # Verify NO ChallengeAction created
        cursor.execute("SELECT * FROM ChallengeAction WHERE log_id = %s", (result["action_log_id"],))
        challenge_action = cursor.fetchone()
        assert challenge_action is None

def test_get_weekly_action(new_client_module, module_scope_database, populated_database):
   
    new_client_module.post("/logout")
    
    
    new_client_module.post("/login", data={
        "email": "e.watson@exeter.ac.uk",
        "password": "password123"
    }, follow_redirects=True)
    
    response = new_client_module.post("/user_access/get_weekly_co2e_saving", json={})
    data = response.get_json()
    assert data["total_saving"] == 133.4
    
 
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "s.chen@exeter.ac.uk",
        "password": "student789"
    }, follow_redirects=True)
    
    response = new_client_module.post("/user_access/get_weekly_co2e_saving", json={})
    data = response.get_json()
    assert data["total_saving"] == 87.6

def test_get_monthly_action(new_client_module, module_scope_database, populated_database):
    
    new_client_module.post("/logout")
    
   
    new_client_module.post("/login", data={
        "email": "e.watson@exeter.ac.uk",
        "password": "password123"
    }, follow_redirects=True)
    
    response = new_client_module.post("/user_access/get_monthly_co2e_saving", json={})
    data = response.get_json()
    assert data["total_saving"] == 133.4
    
   
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "s.chen@exeter.ac.uk",
        "password": "student789"
    }, follow_redirects=True)
    
    response = new_client_module.post("/user_access/get_monthly_co2e_saving", json={})
    data = response.get_json()
    assert data["total_saving"] == 87.6

def test_get_yearly_action(new_client_module, module_scope_database, populated_database):
    
    new_client_module.post("/logout")
    
  
    new_client_module.post("/login", data={
        "email": "e.watson@exeter.ac.uk",
        "password": "password123"
    }, follow_redirects=True)
    
    response = new_client_module.post("/user_access/get_yearly_co2e_saving", json={})
    data = response.get_json()
    assert data["total_saving"] == 133.4
    
    
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "s.chen@exeter.ac.uk",
        "password": "student789"
    }, follow_redirects=True)
    
    response = new_client_module.post("/user_access/get_yearly_co2e_saving", json={})
    data = response.get_json()
    assert data["total_saving"] == 87.6

def test_get_action_history(new_client_module, module_scope_database, populated_database):
    new_client_module.post("/logout")

    new_client_module.post("/login", data = {
        "email" : "e.watson@exeter.ac.uk",
        "password" : "password123"
    }, follow_redirects = True)

    response = new_client_module.post("/user_access/get_action_history", json = {"offset" : 0, "limit" : 100})

    response = response.get_json()
    #only count action with evidence for now
    for record in response:
        print(record)
        print("\n")
    assert len(response) == 13

    new_client_module.post("/logout")

    new_client_module.post("/login")

def test_user_view_submission_result(new_client_module, module_scope_database, populated_database):
    new_client_module.post("/logout")
    new_client_module.post("/login", data = {
        "email" : "j.miller@exeter.ac.uk",
        "password" : "moderator456" 
    }, follow_redirects = True)

    response = new_client_module.post("/moderator_access/make_decision", json = {
        "evidence_id" : 1,
        "result" : "accepted",
        "reason" : "Evidence is accepted"
    }, follow_redirects = True)

    new_client_module.post("/logout")
    new_client_module.post("/login", data = {
        "email" : "e.watson@exeter.ac.uk",
        "password" : "password123"
    }, follow_redirects = True)

    response = new_client_module.post("/user_access/get_action_history", json = {"offset" : 0, "limit" : 100})
    response = response.get_json()
    
    assert len(response) == 13
    
    result_list = []

    for record in response:
        result_list.append(record["decision_status"])

    assert "accepted" in result_list

    
