from datetime import datetime, timedelta
import pytest
from database_fixture import *
from app.db_config import db_cursor

def get_action_type_id(action_name, category):
    with db_cursor() as (connection, cursor):
        cursor.execute(
            "SELECT actionType_id FROM ActionType WHERE actionName = %s AND category = %s",
            (action_name, category)
        )
        row = cursor.fetchone()
        assert row is not None
        return row["actionType_id"]

def get_latest_log_for_account_and_action(account_id, action_name, category):
    with db_cursor() as (connection, cursor):
        cursor.execute(
            """
            SELECT al.*
            FROM ActionLog al
            JOIN ActionType at ON at.actionType_id = al.actionType_id
            WHERE al.submitted_by = %s
              AND at.actionName = %s
              AND at.category = %s
            ORDER BY al.log_id DESC
            LIMIT 1
            """,
            (account_id, action_name, category)
        )
        return cursor.fetchone()

def get_flags_for_log(log_id):
    with db_cursor() as (connection, cursor):
        cursor.execute(
            """
            SELECT *
            FROM AntiGamingFlag
            WHERE action_log_id = %s
            ORDER BY flag_id ASC
            """,
            (log_id,)
        )
        return cursor.fetchall()

def get_account_id_from_session(client):
    with client.session_transaction() as session:
        return session.get("account_id")

def login_as_emma(client):
    return client.post("/login", data={
        "email": "e.watson@exeter.ac.uk",
        "password": "password123"
    }, follow_redirects=True)

def login_as_sarah(client):
    return client.post("/login", data={
        "email": "s.chen@exeter.ac.uk",
        "password": "student789"
    }, follow_redirects=True)

def login_as_john(client):
    return client.post("/login", data={
        "email": "jdsiki@fakemail.com",
        "password": "johndoe123"
    }, follow_redirects=True)

def test_duplicate_submission_creates_flag(new_client_function, module_scope_database):
    login_as_emma(new_client_function)
    account_id = get_account_id_from_session(new_client_function)

    first = new_client_function.post("/user_access/submit_action", json={
        "action_name": "bike",
        "category": "travel",
        "quantity": 3,
        "challenge_id": None,
        "evidence_url": None
    })
    assert first.status_code == 200

    second = new_client_function.post("/user_access/submit_action", json={
        "action_name": "bike",
        "category": "travel",
        "quantity": 3,
        "challenge_id": None,
        "evidence_url": None
    })
    assert second.status_code == 200

    latest_log = get_latest_log_for_account_and_action(account_id, "bike", "travel")
    assert latest_log is not None

    flags = get_flags_for_log(latest_log["log_id"])
    flag_codes = [flag["rule_code"] for flag in flags]
    assert "duplicate_submission" in flag_codes

def test_unrealistic_frequency_creates_flag(new_client_function, module_scope_database):
    login_as_emma(new_client_function)
    account_id = get_account_id_from_session(new_client_function)

    for _ in range(5):
        response = new_client_function.post("/user_access/submit_action", json={
            "action_name": "bike",
            "category": "travel",
            "quantity": 2,
            "challenge_id": None,
            "evidence_url": None
        })
        assert response.status_code == 200

    latest_log = get_latest_log_for_account_and_action(account_id, "bike", "travel")
    assert latest_log is not None

    flags = get_flags_for_log(latest_log["log_id"])
    flag_codes = [flag["rule_code"] for flag in flags]
    assert "unrealistic_frequency" in flag_codes

def test_contradictory_log_creates_flag(new_client_function, module_scope_database):
    login_as_emma(new_client_function)
    account_id = get_account_id_from_session(new_client_function)

    response1 = new_client_function.post("/user_access/submit_action", json={
        "action_name": "walk",
        "category": "travel",
        "quantity": 2,
        "challenge_id": None,
        "evidence_url": None
    })
    assert response1.status_code == 200

    response2 = new_client_function.post("/user_access/submit_action", json={
        "action_name": "car",
        "category": "travel",
        "quantity": 5,
        "challenge_id": None,
        "evidence_url": None
    })
    assert response2.status_code == 200

    latest_log = get_latest_log_for_account_and_action(account_id, "car", "travel")
    assert latest_log is not None

    flags = get_flags_for_log(latest_log["log_id"])
    flag_codes = [flag["rule_code"] for flag in flags]
    assert "contradictory_log" in flag_codes

def test_suspicious_quantity_creates_flag(new_client_function, module_scope_database):
    login_as_emma(new_client_function)
    account_id = get_account_id_from_session(new_client_function)

    response = new_client_function.post("/user_access/submit_action", json={
        "action_name": "heating",
        "category": "energy",
        "quantity": 20,
        "challenge_id": None,
        "evidence_url": None
    })
    assert response.status_code == 200

    latest_log = get_latest_log_for_account_and_action(account_id, "heating", "energy")
    assert latest_log is not None

    flags = get_flags_for_log(latest_log["log_id"])
    flag_codes = [flag["rule_code"] for flag in flags]
    assert "suspicious_quantity" in flag_codes or "impossible_quantity" in flag_codes

def test_impossible_quantity_creates_flag(new_client_function, module_scope_database):
    login_as_emma(new_client_function)
    account_id = get_account_id_from_session(new_client_function)

    response = new_client_function.post("/user_access/submit_action", json={
        "action_name": "heating",
        "category": "energy",
        "quantity": 30,
        "challenge_id": None,
        "evidence_url": None
    })
    assert response.status_code == 200

    latest_log = get_latest_log_for_account_and_action(account_id, "heating", "energy")
    assert latest_log is not None

    flags = get_flags_for_log(latest_log["log_id"])
    flag_codes = [flag["rule_code"] for flag in flags]
    assert "impossible_quantity" in flag_codes

def test_reused_evidence_creates_flag(new_client_function, module_scope_database):
    login_as_emma(new_client_function)
    account_id = get_account_id_from_session(new_client_function)

    shared_evidence = "duplicate_evidence_url"

    first = new_client_function.post("/user_access/submit_action", json={
        "action_name": "walk",
        "category": "travel",
        "quantity": 2,
        "challenge_id": None,
        "evidence_url": shared_evidence
    })
    assert first.status_code == 200

    second = new_client_function.post("/user_access/submit_action", json={
        "action_name": "bus",
        "category": "travel",
        "quantity": 4,
        "challenge_id": None,
        "evidence_url": shared_evidence
    })
    assert second.status_code == 200

    latest_log = get_latest_log_for_account_and_action(account_id, "bus", "travel")
    assert latest_log is not None

    flags = get_flags_for_log(latest_log["log_id"])
    flag_codes = [flag["rule_code"] for flag in flags]
    assert "reused_evidence" in flag_codes

def test_challenge_farming_creates_flag(new_client_function, module_scope_database, populated_database):
    login_as_john(new_client_function)
    account_id = get_account_id_from_session(new_client_function)

    with db_cursor() as (connection, cursor):
        # Ensure John is in challenge 1
        cursor.execute(
            "SELECT COUNT(*) AS count FROM IndividualParticipation WHERE challenge_id = %s AND account_id = %s",
            (1, account_id)
        )
        row = cursor.fetchone()
        if row["count"] == 0:
            cursor.execute(
                "INSERT INTO IndividualParticipation(challenge_id, account_id, joined_date) VALUES (%s, %s, %s)",
                (1, account_id, datetime.now())
            )

        # Pre-seed 5 challenge actions of the same type for the same challenge/user
        cursor.execute(
            "SELECT actionType_id, co2e_factor FROM ActionType WHERE actionName = %s AND category = %s",
            ("walk", "travel")
        )
        action_type = cursor.fetchone()
        assert action_type is not None
        action_type_id = action_type["actionType_id"]
        co2e_factor = action_type["co2e_factor"]

        for qty in [2, 3, 4, 5, 6]:
            cursor.execute(
                """
                INSERT INTO ActionLog(submitted_by, actionType_id, log_date, quantity, co2e_saved)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (account_id, action_type_id, datetime.now() - timedelta(days=1), qty, co2e_factor * qty)
            )
            log_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO ChallengeAction(challenge_id, group_id, log_id, point_awarded)
                VALUES (%s, %s, %s, %s)
                """,
                (1, None, log_id, co2e_factor * qty)
            )

    # Now submit one more same-action challenge entry through the route
    response = new_client_function.post("/user_access/submit_action", json={
        "action_name": "walk",
        "category": "travel",
        "quantity": 7,
        "challenge_id": 1,
        "evidence_url": "farm-proof-final"
    })
    assert response.status_code == 200

    latest_log = get_latest_log_for_account_and_action(account_id, "walk", "travel")
    assert latest_log is not None

    flags = get_flags_for_log(latest_log["log_id"])
    flag_codes = [flag["rule_code"] for flag in flags]
    assert "challenge_farming" in flag_codes

def test_flagged_submission_with_evidence_creates_decision_record(new_client_function, module_scope_database):
    login_as_emma(new_client_function)
    account_id = get_account_id_from_session(new_client_function)

    new_client_function.post("/user_access/submit_action", json={
        "action_name": "walk",
        "category": "travel",
        "quantity": 3,
        "challenge_id": None,
        "evidence_url": "same-proof"
    })

    response = new_client_function.post("/user_access/submit_action", json={
        "action_name": "walk",
        "category": "travel",
        "quantity": 3,
        "challenge_id": None,
        "evidence_url": "same-proof"
    })
    assert response.status_code == 200

    latest_log = get_latest_log_for_account_and_action(account_id, "walk", "travel")
    assert latest_log is not None

    with db_cursor() as (connection, cursor):
        cursor.execute(
            """
            SELECT e.evidence_id, d.decision_status
            FROM Evidence e
            LEFT JOIN Decision d ON d.evidence_id = e.evidence_id
            WHERE e.log_id = %s
            ORDER BY e.evidence_id DESC
            LIMIT 1
            """,
            (latest_log["log_id"],)
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["evidence_id"] is not None
        assert row["decision_status"] == "pending"

def test_train_8000km_flagged_impossible(new_client_function, module_scope_database):
    new_client_function.post("/logout")
    login_as_emma(new_client_function)
    account_id = get_account_id_from_session(new_client_function)

    response = new_client_function.post("/user_access/submit_action", json={
        "action_name": "train",
        "category": "travel",
        "quantity": 8000,
        "challenge_id": None,
        "evidence_url": None
    })
    assert response.status_code == 200

    latest_log = get_latest_log_for_account_and_action(account_id, "train", "travel")
    assert latest_log is not None

    flags = get_flags_for_log(latest_log["log_id"])
    flag_codes = [flag["rule_code"] for flag in flags]
    assert "impossible_quantity" in flag_codes

    flag = next(f for f in flags if f["rule_code"] == "impossible_quantity")
    assert flag["severity"] == "high"


def test_antigaming_rules_are_seeded(new_client_function, module_scope_database):
    with db_cursor() as (connection, cursor):
        cursor.execute("SELECT COUNT(*) AS count FROM AntiGamingRule")
        row = cursor.fetchone()
        assert row is not None
        assert row["count"] >= 7