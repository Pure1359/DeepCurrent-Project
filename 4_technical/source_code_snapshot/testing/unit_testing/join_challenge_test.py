from datetime import datetime, timedelta
import pytest
from database_fixture import *
from app.db_config import db_cursor
from custom_error.Challenge_Exception import UserAlreadyJoinChallenge, InvalidChallengeDate, ChallengeIdNotFound

def test_join_challenge_success(new_client_module, module_scope_database, populated_database):
    """Test user successfully joins a challenge"""
    # Logout and login as Sarah
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "s.chen@exeter.ac.uk",
        "password": "student789"
    }, follow_redirects=True)
    
    response = new_client_module.post("/user_access/join_challenge", json={
        "challenge_id": 1
    })
    
    data = response.get_json()
    assert response.status_code == 200
    assert data["success"] == True
    assert "Successfully added" in data["message"]
    
    # Verify in database
    with db_cursor() as (connection, cursor):
        cursor.execute("SELECT * FROM IndividualParticipation WHERE account_id = %s AND challenge_id = %s", (3, 1))
        result = cursor.fetchone()
        assert result is not None
        assert result["account_id"] == 3
        assert result["challenge_id"] == 1

def test_join_challenge_already_joined(new_client_module, module_scope_database, populated_database):
    """Test error when user tries to join same challenge twice"""
    # Login as Emma (already has actions in challenge 1 from populated_database)
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "e.watson@exeter.ac.uk",
        "password": "password123"
    }, follow_redirects=True)
    
    # First join should work (if not already joined via populated_database)
    # But if Emma already joined via actions, this should fail
    response = new_client_module.post("/user_access/join_challenge", json={
        "challenge_id": 1
    })
    
    # Try to join challenge 1 again
    response2 = new_client_module.post("/user_access/join_challenge", json={
        "challenge_id": 1
    })
    
    data = response2.get_json()
    assert response2.status_code == 400
    assert "The user already participate in this challenge" in data["error"]

def test_join_challenge_not_found(new_client_module, module_scope_database, populated_database):
    """Test error when challenge doesn't exist"""
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "s.chen@exeter.ac.uk",
        "password": "student789"
    }, follow_redirects=True)
    
    # Try to join non-existent challenge
    response = new_client_module.post("/user_access/join_challenge", json={
        "challenge_id": 999
    })
    
    data = response.get_json()
    assert response.status_code == 400
    assert "error" in data

def test_join_challenge_expired(new_client_module, module_scope_database, populated_database):
    """Test error when trying to join expired challenge"""
    # Logout and login as student
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "s.chen@exeter.ac.uk",
        "password": "student789"
    }, follow_redirects=True)
    
    # Try to join expired challenge (challenge_id = 3)
    response = new_client_module.post("/user_access/join_challenge", json={
        "challenge_id": 3
    })
    
    data = response.get_json()
    assert response.status_code == 400
    assert "The challenge is currently not active" in data["error"]

def test_join_challenge_not_started(new_client_module, module_scope_database, populated_database):
    """Test error when trying to join challenge that hasn't started"""
    # Login as student
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "s.chen@exeter.ac.uk",
        "password": "student789"
    }, follow_redirects=True)
    
    # Try to join future challenge (challenge_id = 4)
    response = new_client_module.post("/user_access/join_challenge", json={
        "challenge_id": 4
    })
    
    data = response.get_json()
    assert response.status_code == 400
    assert "The challenge is currently not active" in data["error"]

def test_join_multiple_challenges(new_client_module, module_scope_database, populated_database):
    """Test user can join multiple different challenges"""
    # Use Emma instead - she doesn't have challenge 2
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "e.watson@exeter.ac.uk",
        "password": "password123"
    }, follow_redirects=True)
    
    # Emma already has challenge 1, try to join challenge 2
    response2 = new_client_module.post("/user_access/join_challenge", json={
        "challenge_id": 2
    })
    assert response2.status_code == 200
    
    # Verify Emma has both challenges now
    with db_cursor() as (connection, cursor):
        cursor.execute("SELECT * FROM IndividualParticipation WHERE account_id = %s", (1,))
        results = cursor.fetchall()
        challenge_ids = [r["challenge_id"] for r in results]
        assert 1 in challenge_ids
        assert 2 in challenge_ids

def test_join_challenge_without_login(new_client_module, module_scope_database):
    """Test error when not logged in"""
    # Logout to ensure no session
    new_client_module.post("/logout")
    
    # Try to join challenge without login
    response = new_client_module.post("/user_access/join_challenge", json={
        "challenge_id": 1
    })
    
    # Should redirect or return error due to @user_bp.before_request
    assert response.status_code in [302, 400, 401, 403]

def test_get_user_challenges(new_client_module, module_scope_database, populated_database):
    """Test getting list of challenges user has joined"""
    # Login as Sarah and join some challenges
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "s.chen@exeter.ac.uk",
        "password": "student789"
    }, follow_redirects=True)
    
    # Join challenges
    new_client_module.post("/user_access/join_challenge", json={"challenge_id": 1})
    new_client_module.post("/user_access/join_challenge", json={"challenge_id": 2})
    
    # Get user's challenges
    response = new_client_module.post("/user_access/get_challenge_for_user", json={})
    data = response.get_json()
    
    assert response.status_code == 200
    assert len(data) >= 2
    challenge_ids = [item["challenge_id"] for item in data]
    assert 1 in challenge_ids
    assert 2 in challenge_ids