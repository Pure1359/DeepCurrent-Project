from database_fixture import *
from app.db_config import db_cursor


def get_account_id_from_session(client):
    with client.session_transaction() as session:
        return session.get("account_id")


# --- Personal energy action: no challenge, no evidence ---

def test_log_heating_personal_action(new_client_module, module_scope_database, populated_database):
    # Heating at home for 4 hours - personal log, no challenge submission
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "e.watson@exeter.ac.uk",
        "password": "password123"
    }, follow_redirects=True)
    account_id = get_account_id_from_session(new_client_module)

    result = new_client_module.post("/user_access/submit_action", json={
        "action_name": "heating",
        "category": "energy",
        "quantity": 4,
        "challenge_id": None,
        "evidence_url": None
    })
    result = result.get_json()

    assert result["success"] == True

    with db_cursor() as (connection, cursor):
        cursor.execute("SELECT * FROM ActionLog WHERE log_id = %s", (result["action_log_id"],))
        action_log = cursor.fetchone()

        # heating co2e_factor is 0.148 per hour
        assert action_log is not None
        assert action_log["submitted_by"] == account_id
        assert action_log["quantity"] == "4"
        assert action_log["co2e_saved"] == 4 * 0.148

        # Personal action — no Evidence or ChallengeAction expected
        cursor.execute("SELECT * FROM Evidence WHERE log_id = %s", (result["action_log_id"],))
        assert cursor.fetchone() is None

        cursor.execute("SELECT * FROM ChallengeAction WHERE log_id = %s", (result["action_log_id"],))
        assert cursor.fetchone() is None


def test_log_lights_personal_action(new_client_module, module_scope_database, populated_database):
    # Leaving lights off for 6 hours — personal log
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "s.chen@exeter.ac.uk",
        "password": "student789"
    }, follow_redirects=True)
    account_id = get_account_id_from_session(new_client_module)

    result = new_client_module.post("/user_access/submit_action", json={
        "action_name": "lights",
        "category": "energy",
        "quantity": 6,
        "challenge_id": None,
        "evidence_url": None
    })
    result = result.get_json()

    assert result["success"] == True

    with db_cursor() as (connection, cursor):
        cursor.execute("SELECT * FROM ActionLog WHERE log_id = %s", (result["action_log_id"],))
        action_log = cursor.fetchone()

        # lights co2e_factor is 0.01056 per hour
        assert action_log is not None
        assert action_log["submitted_by"] == account_id
        assert action_log["quantity"] == "6"
        assert action_log["co2e_saved"] == 6 * 0.01056


# --- Challenge energy action: with evidence, creates full chain ---

def test_log_cold_wash_to_challenge(new_client_module, module_scope_database, populated_database):
    # Cold wash submitted to challenge with photo evidence — full chain should be created
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "e.watson@exeter.ac.uk",
        "password": "password123"
    }, follow_redirects=True)
    account_id = get_account_id_from_session(new_client_module)

    # Emma is already joined to challenge 1 (from populated_database)
    result = new_client_module.post("/user_access/submit_action", json={
        "action_name": "cold-wash",
        "category": "energy",
        "quantity": 2,
        "challenge_id": 1,
        "evidence_url": "https://evidence.example/cold-wash-energy-proof.jpg"
    })
    result = result.get_json()

    assert result["success"] == True

    with db_cursor() as (connection, cursor):
        cursor.execute("SELECT * FROM ActionLog WHERE log_id = %s", (result["action_log_id"],))
        action_log = cursor.fetchone()

        # cold-wash co2e_factor is 0.176 per load
        assert action_log is not None
        assert action_log["submitted_by"] == account_id
        assert action_log["co2e_saved"] == 2 * 0.176

        # Evidence row created
        cursor.execute("SELECT * FROM Evidence WHERE log_id = %s", (result["action_log_id"],))
        evidence = cursor.fetchone()
        assert evidence is not None
        assert evidence["evidence_url"] == "https://evidence.example/cold-wash-energy-proof.jpg"

        # Decision auto-approved (no anti-gaming flags triggered)
        cursor.execute("SELECT * FROM Decision WHERE evidence_id = %s", (evidence["evidence_id"],))
        decision = cursor.fetchone()
        assert decision is not None
        assert decision["decision_status"] == "approved"

        # ChallengeAction row created with correct points
        cursor.execute("SELECT * FROM ChallengeAction WHERE log_id = %s", (result["action_log_id"],))
        challenge_action = cursor.fetchone()
        assert challenge_action is not None
        assert challenge_action["challenge_id"] == 1
        assert challenge_action["point_awarded"] == 2 * 0.176


# --- Anti-gaming: impossible and suspicious quantity checks ---

def test_heating_above_hard_max_flagged_as_impossible(new_client_module, module_scope_database, populated_database):
    # 25 hours of heating exceeds hard_max (24 hrs) — should raise impossible_quantity flag
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "jdsiki@fakemail.com",
        "password": "johndoe123"
    }, follow_redirects=True)
    account_id = get_account_id_from_session(new_client_module)

    result = new_client_module.post("/user_access/submit_action", json={
        "action_name": "heating",
        "category": "energy",
        "quantity": 25,
        "challenge_id": None,
        "evidence_url": None
    })
    result = result.get_json()

    assert result["success"] == True
    flag_codes = [f["rule_code"] for f in result.get("flags", [])]
    assert "impossible_quantity" in flag_codes

    # Verify the flag is persisted in the database with high severity
    with db_cursor() as (connection, cursor):
        cursor.execute(
            "SELECT rule_code, severity FROM AntiGamingFlag WHERE action_log_id = %s",
            (result["action_log_id"],)
        )
        db_flags = cursor.fetchall()

    assert any(f["rule_code"] == "impossible_quantity" for f in db_flags)
    assert any(f["severity"] == "high" for f in db_flags)


def test_air_dry_above_max_flagged_as_suspicious(new_client_module, module_scope_database, populated_database):
    # 5 loads of air-dry exceeds expected max (3) but not hard_max (8) — suspicious_quantity flag
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "s.chen@exeter.ac.uk",
        "password": "student789"
    }, follow_redirects=True)
    account_id = get_account_id_from_session(new_client_module)

    result = new_client_module.post("/user_access/submit_action", json={
        "action_name": "air-dry",
        "category": "energy",
        "quantity": 5,
        "challenge_id": None,
        "evidence_url": None
    })
    result = result.get_json()

    assert result["success"] == True
    flag_codes = [f["rule_code"] for f in result.get("flags", [])]
    assert "suspicious_quantity" in flag_codes

    with db_cursor() as (connection, cursor):
        cursor.execute(
            "SELECT rule_code FROM AntiGamingFlag WHERE action_log_id = %s",
            (result["action_log_id"],)
        )
        db_flags = cursor.fetchall()

    assert any(f["rule_code"] == "suspicious_quantity" for f in db_flags)
