from database_fixture import *
from app.db_config import db_cursor


def get_account_id_from_session(client):
    with client.session_transaction() as session:
        return session.get("account_id")


# --- Single and multi-ingredient meal logging ---

def test_log_single_ingredient_food(new_client_module, module_scope_database, populated_database):
    # Log a meal with one ingredient — verify quantity text format and co2e
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "e.watson@exeter.ac.uk",
        "password": "password123"
    }, follow_redirects=True)
    account_id = get_account_id_from_session(new_client_module)

    result = new_client_module.post("/user_access/submit_action", json={
        "action_name": "food",
        "category": "food",
        "quantity": [("Broccoli", 0.5)],
        "challenge_id": None,
        "evidence_url": None
    })
    result = result.get_json()

    assert result["success"] == True

    with db_cursor() as (connection, cursor):
        cursor.execute("SELECT * FROM ActionLog WHERE log_id = %s", (result["action_log_id"],))
        action_log = cursor.fetchone()

        # Broccoli co2e_factor is 0.674 per kg
        assert action_log is not None
        assert action_log["submitted_by"] == account_id
        assert action_log["quantity"] == "Broccoli:0.5"
        assert action_log["co2e_saved"] == 0.5 * 0.674

        # No challenge — no Evidence or ChallengeAction
        cursor.execute("SELECT * FROM Evidence WHERE log_id = %s", (result["action_log_id"],))
        assert cursor.fetchone() is None

        cursor.execute("SELECT * FROM ChallengeAction WHERE log_id = %s", (result["action_log_id"],))
        assert cursor.fetchone() is None


def test_log_multi_ingredient_food_co2e_and_format(new_client_module, module_scope_database, populated_database):
    # Three-ingredient meal — quantity stored as "Ingredient:kg" text, co2e is summed across all
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "s.chen@exeter.ac.uk",
        "password": "student789"
    }, follow_redirects=True)
    account_id = get_account_id_from_session(new_client_module)

    food_quantity = [("Broccoli", 0.3), ("Chicken", 0.5), ("Potatoes", 0.4)]
    result = new_client_module.post("/user_access/submit_action", json={
        "action_name": "food",
        "category": "food",
        "quantity": food_quantity,
        "challenge_id": None,
        "evidence_url": None
    })
    result = result.get_json()

    assert result["success"] == True

    # Expected co2e: Broccoli(0.3*0.674) + Chicken(0.5*3.927) + Potatoes(0.4*0.462)
    expected_co2e = (0.3 * 0.674) + (0.5 * 3.927) + (0.4 * 0.462)

    with db_cursor() as (connection, cursor):
        cursor.execute("SELECT * FROM ActionLog WHERE log_id = %s", (result["action_log_id"],))
        action_log = cursor.fetchone()

        assert action_log is not None
        assert action_log["submitted_by"] == account_id
        assert action_log["quantity"] == "Broccoli:0.3 Chicken:0.5 Potatoes:0.4"
        assert action_log["co2e_saved"] == expected_co2e
        assert result["co2e_saved"] == expected_co2e


# --- Validation: ingredient limits and unknown items ---

def test_food_exceeds_max_ingredients_rejected(new_client_module, module_scope_database, populated_database):
    # More than 5 ingredients should be rejected with a 400 error
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "e.watson@exeter.ac.uk",
        "password": "password123"
    }, follow_redirects=True)

    oversized_meal = [
        ("Broccoli", 0.2), ("Chicken", 0.3), ("Potatoes", 0.2),
        ("Carrots", 0.1), ("Beef", 0.5), ("Eggs", 0.1)
    ]
    response = new_client_module.post("/user_access/submit_action", json={
        "action_name": "food",
        "category": "food",
        "quantity": oversized_meal,
        "challenge_id": None,
        "evidence_url": None
    })

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "5 ingredients" in data["error"]


def test_food_unknown_ingredient_rejected(new_client_module, module_scope_database, populated_database):
    # An ingredient that does not exist in ActionType should return a 400 error
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "jdsiki@fakemail.com",
        "password": "johndoe123"
    }, follow_redirects=True)

    response = new_client_module.post("/user_access/submit_action", json={
        "action_name": "food",
        "category": "food",
        "quantity": [("NotARealFood", 0.5)],
        "challenge_id": None,
        "evidence_url": None
    })

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "does not exists" in data["error"]


# --- Food to challenge: evidence required, ChallengeAction created ---

def test_log_food_to_challenge_creates_challenge_action(new_client_module, module_scope_database, populated_database):
    # Submit a meal to a food challenge with evidence — verify full chain in DB
    new_client_module.post("/logout")
    new_client_module.post("/login", data={
        "email": "e.watson@exeter.ac.uk",
        "password": "password123"
    }, follow_redirects=True)
    account_id = get_account_id_from_session(new_client_module)

    # Emma is joined to challenge 5 "Low Carbon Meals" (from populated_database)
    food_quantity = [("Broccoli", 0.4), ("Potatoes", 0.3)]
    result = new_client_module.post("/user_access/submit_action", json={
        "action_name": "food",
        "category": "food",
        "quantity": food_quantity,
        "challenge_id": 5,
        "evidence_url": "https://evidence.example/meal-photo-lowcarbon.jpg"
    })
    result = result.get_json()

    assert result["success"] == True

    expected_co2e = (0.4 * 0.674) + (0.3 * 0.462)

    with db_cursor() as (connection, cursor):
        cursor.execute("SELECT * FROM ActionLog WHERE log_id = %s", (result["action_log_id"],))
        action_log = cursor.fetchone()
        assert action_log is not None
        assert action_log["co2e_saved"] == expected_co2e

        # Evidence created
        cursor.execute("SELECT * FROM Evidence WHERE log_id = %s", (result["action_log_id"],))
        evidence = cursor.fetchone()
        assert evidence is not None
        assert evidence["evidence_url"] == "https://evidence.example/meal-photo-lowcarbon.jpg"

        # ChallengeAction created and linked to challenge 5
        cursor.execute("SELECT * FROM ChallengeAction WHERE log_id = %s", (result["action_log_id"],))
        challenge_action = cursor.fetchone()
        assert challenge_action is not None
        assert challenge_action["challenge_id"] == 5
        assert challenge_action["point_awarded"] == expected_co2e
