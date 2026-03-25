from database_fixture import *
from app.db_config import db_cursor


def get_account_id_from_session(client):
    with client.session_transaction() as session:
        return session.get("account_id")


# --- Personal waste actions: no challenge, no evidence ---

def test_log_recycle_paper_personal(new_client_module, module_scope_database, populated_database):
    # Recycling 2kg of paper — personal log, verify ActionLog and co2e
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "e.watson@exeter.ac.uk",
        "password": "password123"
    }, follow_redirects=True)
    account_id = get_account_id_from_session(new_client_module)

    result = new_client_module.post("/user_access/submit_action", json={
        "action_name": "recycle-paper",
        "category": "waste",
        "quantity": 2,
        "challenge_id": None,
        "evidence_url": None
    })
    result = result.get_json()

    assert result["success"] == True

    with db_cursor() as (connection, cursor):
        cursor.execute("SELECT * FROM ActionLog WHERE log_id = %s", (result["action_log_id"],))
        action_log = cursor.fetchone()

        # recycle-paper co2e_factor is 1.0 per kg
        assert action_log is not None
        assert action_log["submitted_by"] == account_id
        assert action_log["quantity"] == "2"
        assert action_log["co2e_saved"] == 2 * 1.0

        # No Evidence or ChallengeAction for personal log
        cursor.execute("SELECT * FROM Evidence WHERE log_id = %s", (result["action_log_id"],))
        assert cursor.fetchone() is None

        cursor.execute("SELECT * FROM ChallengeAction WHERE log_id = %s", (result["action_log_id"],))
        assert cursor.fetchone() is None


def test_log_recycle_aluminium_co2e(new_client_module, module_scope_database, populated_database):
    # Aluminium has a high co2e saving — 1kg should give 9.5 points
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "s.chen@exeter.ac.uk",
        "password": "student789"
    }, follow_redirects=True)
    account_id = get_account_id_from_session(new_client_module)

    result = new_client_module.post("/user_access/submit_action", json={
        "action_name": "recycle-aluminium",
        "category": "waste",
        "quantity": 1,
        "challenge_id": None,
        "evidence_url": None
    })
    result = result.get_json()

    assert result["success"] == True

    with db_cursor() as (connection, cursor):
        cursor.execute("SELECT * FROM ActionLog WHERE log_id = %s", (result["action_log_id"],))
        action_log = cursor.fetchone()

        # recycle-aluminium co2e_factor is 9.5 per kg
        assert action_log is not None
        assert action_log["submitted_by"] == account_id
        assert action_log["co2e_saved"] == 1 * 9.5


# --- Challenge waste action: evidence and full chain ---

def test_log_waste_to_challenge(new_client_module, module_scope_database, populated_database):
    # Recycling plastic submitted to challenge with evidence — verify full chain
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "e.watson@exeter.ac.uk",
        "password": "password123"
    }, follow_redirects=True)
    account_id = get_account_id_from_session(new_client_module)

    # Emma is joined to challenge 1 (from populated_database)
    result = new_client_module.post("/user_access/submit_action", json={
        "action_name": "recycle-plastic",
        "category": "waste",
        "quantity": 3,
        "challenge_id": 1,
        "evidence_url": "https://evidence.example/recycle-plastic-proof.jpg"
    })
    result = result.get_json()

    assert result["success"] == True

    with db_cursor() as (connection, cursor):
        cursor.execute("SELECT * FROM ActionLog WHERE log_id = %s", (result["action_log_id"],))
        action_log = cursor.fetchone()

        # recycle-plastic co2e_factor is 1.2 per kg
        assert action_log is not None
        assert action_log["co2e_saved"] == 3 * 1.2

        # Evidence row created
        cursor.execute("SELECT * FROM Evidence WHERE log_id = %s", (result["action_log_id"],))
        evidence = cursor.fetchone()
        assert evidence is not None
        assert evidence["evidence_url"] == "https://evidence.example/recycle-plastic-proof.jpg"

        # Decision auto-approved (no flags)
        cursor.execute("SELECT * FROM Decision WHERE evidence_id = %s", (evidence["evidence_id"],))
        decision = cursor.fetchone()
        assert decision is not None
        assert decision["decision_status"] == "approved"

        # ChallengeAction awarded with correct points
        cursor.execute("SELECT * FROM ChallengeAction WHERE log_id = %s", (result["action_log_id"],))
        challenge_action = cursor.fetchone()
        assert challenge_action is not None
        assert challenge_action["challenge_id"] == 1
        assert challenge_action["point_awarded"] == 3 * 1.2


# --- Anti-gaming: suspicious and impossible quantity ---

def test_recycle_paper_above_max_flagged_as_suspicious(new_client_module, module_scope_database, populated_database):
    # 12kg of recycle-paper exceeds expected max (10kg) — suspicious_quantity flag
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "jdsiki@fakemail.com",
        "password": "johndoe123"
    }, follow_redirects=True)
    account_id = get_account_id_from_session(new_client_module)

    result = new_client_module.post("/user_access/submit_action", json={
        "action_name": "recycle-paper",
        "category": "waste",
        "quantity": 12,
        "challenge_id": None,
        "evidence_url": None
    })
    result = result.get_json()

    assert result["success"] == True
    flag_codes = [f["rule_code"] for f in result.get("flags", [])]
    assert "suspicious_quantity" in flag_codes

    with db_cursor() as (connection, cursor):
        cursor.execute(
            "SELECT rule_code, severity FROM AntiGamingFlag WHERE action_log_id = %s",
            (result["action_log_id"],)
        )
        db_flags = cursor.fetchall()

    assert any(f["rule_code"] == "suspicious_quantity" for f in db_flags)
    assert any(f["severity"] == "medium" for f in db_flags)


def test_recycle_aluminium_above_hard_max_flagged_as_impossible(new_client_module, module_scope_database, populated_database):
    # 20kg of recycle-aluminium exceeds hard_max (15kg) — impossible_quantity flag
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "s.chen@exeter.ac.uk",
        "password": "student789"
    }, follow_redirects=True)
    account_id = get_account_id_from_session(new_client_module)

    result = new_client_module.post("/user_access/submit_action", json={
        "action_name": "recycle-aluminium",
        "category": "waste",
        "quantity": 20,
        "challenge_id": None,
        "evidence_url": None
    })
    result = result.get_json()

    assert result["success"] == True
    flag_codes = [f["rule_code"] for f in result.get("flags", [])]
    assert "impossible_quantity" in flag_codes

    with db_cursor() as (connection, cursor):
        cursor.execute(
            "SELECT rule_code, severity FROM AntiGamingFlag WHERE action_log_id = %s",
            (result["action_log_id"],)
        )
        db_flags = cursor.fetchall()

    assert any(f["rule_code"] == "impossible_quantity" for f in db_flags)
    assert any(f["severity"] == "high" for f in db_flags)
