from datetime import datetime, timedelta
import pytest
from database_fixture import *
from app.db_config import db_cursor
from custom_error.Challenge_Exception import UserAlreadyJoinChallenge, InvalidChallengeDate, ChallengeIdNotFound

def test_join_challenge_success(new_client_module, module_scope_database, populated_database):
    #test user join challenge as sarah
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
    #test error ,when the user join same challenge twice or more
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "e.watson@exeter.ac.uk",
        "password": "password123"
    }, follow_redirects=True)
    
    #emma join challenge id = 1 
    response = new_client_module.post("/user_access/join_challenge", json={
        "challenge_id": 1
    })
    data = response.get_json()
    assert response.status_code == 200
    
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
    #error when joining challenge that already expired
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
    #error when join challenge that hasn't started"""

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
    #check to see if user can join many challenge
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

    response = new_client_module.post("/user_access/get_challenge_for_user")

    response = response.get_json()

    assert len(response) == 2
    challenge_id = [each_response["challenge_id"] for each_response in response]
    assert 1 in challenge_id
    assert 2 in challenge_id
    

def test_join_challenge_without_login(new_client_module, module_scope_database):
    # Logout to ensure no session
    new_client_module.post("/logout")
    
    # Try to join challenge without login
    response = new_client_module.post("/user_access/join_challenge", json={
        "challenge_id": 1
    })
    
    # Should redirect or return error due to @user_bp.before_request
    assert response.status_code in [302, 400, 401, 403]

def test_get_user_challenges(new_client_module, module_scope_database, populated_database):
    #Test getting list of challenges user has joined
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