from datetime import datetime, timedelta
import pytest
from database_fixture import *
from app.db_config import db_cursor
from app.services.actions import log_action
from app.services.users_service import get_weekly_saved, get_monthly_saved, get_yearly_saved

def test_log_action_challenge(module_scope_database):
    # Log a new challenge action with evidence
    result = log_action(1, "walk", "travel", 50, 1, "url_new_challenge")
    
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

def test_log_action_personal(module_scope_database):
    # Log a personal action (no challenge, no evidence)
    result = log_action(1, "bus", "travel", 30, None, None)
    
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

def test_get_weekly_action(module_scope_database):
    weekly_saved_emma = get_weekly_saved(1)
    assert weekly_saved_emma == 133.4
    weekly_saved_sarah = get_weekly_saved(3)
    assert weekly_saved_sarah == 87.6  
    
  

def test_get_monthly_action(module_scope_database):
   
    monthly_saved_emma = get_monthly_saved(1)
    assert monthly_saved_emma == 133.4
    monthly_saved_sarah = get_monthly_saved(3)
    assert monthly_saved_sarah == 87.6  
    
def test_get_yearly_action(module_scope_database):
    yearly_saved_emma = get_yearly_saved(1)
    assert yearly_saved_emma == 133.4
    yearly_saved_sarah = get_yearly_saved(3)
    assert yearly_saved_sarah == 87.6 
 
  