from database_fixture import *
from app.db_config import db_cursor

def api_login(client, email, password):
    return client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
        follow_redirects=True
    )

def test_api_login_success_user(new_client_function, module_scope_database):
    resp = api_login(new_client_function, "e.watson@exeter.ac.uk", "password123")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["message"] == "Login successful"
    assert data["role"] == "user"
    assert isinstance(data["account_id"], int)

def test_api_login_success_moderator(new_client_function, module_scope_database):
    resp = api_login(new_client_function, "j.miller@exeter.ac.uk", "moderator456")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["role"] == "moderator"

def test_api_log_action_requires_login(new_client_function, module_scope_database):
    resp = new_client_function.post(
        "/api/actions",
        json={"action_name": "walk", "category": "travel", "quantity": 1},
    )
    assert resp.status_code == 401

def test_api_log_action_success(new_client_function, module_scope_database):
    api_login(new_client_function, "e.watson@exeter.ac.uk", "password123")
    resp = new_client_function.post(
        "/api/actions",
        json={"action_name": "walk", "category": "travel", "quantity": 2},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["message"] == "Action logged successfully"
    assert data["action_id"] is not None

def test_api_join_challenge_then_submit_awards_challenge_action(new_client_function, module_scope_database, populated_database):
    api_login(new_client_function, "e.watson@exeter.ac.uk", "password123")

    with db_cursor() as (_conn, cur):
        cur.execute("SELECT challenge_id FROM Challenge ORDER BY challenge_id ASC LIMIT 1")
        row = cur.fetchone()
        assert row is not None
        challenge_id = int(row["challenge_id"])

    join_resp = new_client_function.post(
        "/api/challenges/join",
        json={"challenge_id": challenge_id},
    )
    assert join_resp.status_code == 200

    action_resp = new_client_function.post(
        "/api/actions",
        json={"action_name": "bus", "category": "travel", "quantity": 3, "challenge_id": challenge_id},
    )
    assert action_resp.status_code == 200
    action_data = action_resp.get_json()
    assert action_data["challenge_id"] is not None

def test_api_moderation_pending_and_decision(new_client_function, module_scope_database):
    api_login(new_client_function, "j.miller@exeter.ac.uk", "moderator456")
    
    pending_resp = new_client_function.get("/api/moderation/pending")
    assert pending_resp.status_code == 200
    pending = pending_resp.get_json()
    assert isinstance(pending, list)

    # Pick an evidence_id directly from the DB and approve it
    with db_cursor() as (_conn, cur):
        cur.execute("SELECT evidence_id FROM Evidence ORDER BY evidence_id ASC LIMIT 1")
        ev = cur.fetchone()
        assert ev is not None
        evidence_id = int(ev["evidence_id"])

    decision_resp = new_client_function.post(
        "/api/moderation/decision",
        json={"evidence_id": evidence_id, "status": "approved", "reason": "Looks valid"},
    )
    assert decision_resp.status_code == 200

    # Check if DB has updated
    with db_cursor() as (_conn, cur):
        cur.execute(
            "SELECT decision_status, reviewer_id, reason FROM Decision WHERE evidence_id = %s",
            (evidence_id,),
        )
        dec = cur.fetchone()
        assert dec is not None
        assert dec["decision_status"] == "approved"
        assert dec["reviewer_id"] is not None
        assert dec["reason"] == "Looks valid"