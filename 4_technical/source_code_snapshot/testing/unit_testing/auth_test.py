from datetime import datetime, timedelta
import pytest
from database_fixture import *
from app.db_config import db_cursor


def test_dashboard_requires_login(new_client_module, module_scope_database):
    new_client_module.post("/logout")
    response = new_client_module.get("/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.location

def test_user_cannot_access_moderator_routes(new_client_module, module_scope_database):
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "e.watson@exeter.ac.uk",
        "password": "password123"
    }, follow_redirects=False)
    
    # Try to access moderator route
    response = new_client_module.post("/moderator_access/create_challenge", data={
        "challenge_type": "travel",
        "title": "Test",
        "start_date": "2026-03-01",
        "end_date": "2026-03-30",
        "rule": "Test rule"
    })
    
    assert response.status_code == 404

def test_moderator_can_access_moderator_routes(new_client_module, module_scope_database):
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "j.miller@exeter.ac.uk",
        "password": "moderator456"
    }, follow_redirects=True)
    
    # Try to access moderator route
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    response = new_client_module.post("/moderator_access/create_challenge", data={
        "challenge_type": "travel",
        "title": "Moderator Test",
        "start_date": start_date,
        "end_date": end_date,
        "rule": "Test rule"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert "Successfully make a challenge" in data["message"]

def test_user_routes_require_login(new_client_module, module_scope_database):
    
    new_client_module.post("/logout")
    response = new_client_module.post("/user_access/submit_action", json={
        "action_name": "walk",
        "category": "travel",
        "quantity": 10,
        "challenge_id": None,
        "evidence_url": None
    }, follow_redirects=False)
    
    # Should redirect to login
    assert response.status_code == 302
    assert "/login" in response.location

def test_moderator_can_access_user_routes(new_client_module, module_scope_database, populated_database):
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "j.miller@exeter.ac.uk",
        "password": "moderator456"
    }, follow_redirects=True)
    
    # Moderator should be able to log actions (user route)
    response = new_client_module.post("/user_access/submit_action", json={
        "action_name": "walk",
        "category": "travel",
        "quantity": 10,
        "challenge_id": 1,
        "evidence_url": None
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] == True

def test_login_with_invalid_credentials(new_client_module, module_scope_database):
    new_client_module.post("/logout")
    
    response = new_client_module.post("/login", data={
        "email": "invalid@exeter.ac.uk",
        "password": "wrongpassword"
    }, follow_redirects=False)
    
    # Should not redirect (stays on login page), 200 is ok, 302 is redirect
    assert response.status_code == 200


def test_login_with_valid_credentials_sets_session(new_client_module, module_scope_database):
    new_client_module.post("/logout")
    
    response = new_client_module.post("/login", data={
        "email": "e.watson@exeter.ac.uk",
        "password": "password123"
    }, follow_redirects=True)
    
    # Check session is set
    with new_client_module.session_transaction() as session:
        assert session.get("account_id") == 1
        assert session.get("account_role") == "user"

def test_logout_clears_session(new_client_module, module_scope_database):
    # Login first
    new_client_module.post("/login", data={
        "email": "e.watson@exeter.ac.uk",
        "password": "password123"
    }, follow_redirects=True)
    
    # Verify session is set
    with new_client_module.session_transaction() as session:
        assert session.get("account_id") is not None
    
    # Logout
    new_client_module.post("/logout")
    with new_client_module.session_transaction() as session:
        assert session.get("account_id") is None
        assert session.get("account_role") is None



def test_access_without_session_redirects(new_client_module, module_scope_database):
    new_client_module.post("/logout")
    
    # Try to access protected routes
    protected_routes = "/dashboard"
    response = new_client_module.get(protected_routes, follow_redirects=False)
    #redirect to login page, code for redirect = 302
    assert response.status_code == 302
    assert "/login" in response.location