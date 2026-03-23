from datetime import datetime, timedelta
import pytest

from database_fixture import *
from app.services.challenges import (
    create_challenge,
    join_challenge_group,
    challenge_leaderboard_individual,
    challenge_leaderboard_group,
)
from app.services.groups import UserCreateGroup, UserJoinGroup
from app.services.actions import log_action


def test_api_leaderboard_returns_ranked_users(new_client_function, module_scope_database, populated_database):
    response = new_client_function.get("/api/dashboard/leaderboard?limit=3")
    assert response.status_code == 200

    result = response.get_json()
    leaderboard = result["leaderboard"]

    assert len(leaderboard) == 3

    # Sarah should be first from the populated fixture data
    assert leaderboard[0]["first_name"] == "Sarah"
    assert leaderboard[0]["last_name"] == "Chen"
    assert float(leaderboard[0]["points"]) == pytest.approx(46.4)

    # Emma should be second
    assert leaderboard[1]["first_name"] == "Emma"
    assert leaderboard[1]["last_name"] == "Watson"
    assert float(leaderboard[1]["points"]) == pytest.approx(37.1553)

    # Third place should have no challenge points yet
    assert float(leaderboard[2]["points"]) == pytest.approx(0.0)

    # Ensure descending order
    assert float(leaderboard[0]["points"]) >= float(leaderboard[1]["points"])
    assert float(leaderboard[1]["points"]) >= float(leaderboard[2]["points"])


def test_api_leaderboard_respects_limit(new_client_function, module_scope_database, populated_database):
    response = new_client_function.get("/api/dashboard/leaderboard?limit=2")
    assert response.status_code == 200

    result = response.get_json()
    leaderboard = result["leaderboard"]

    assert len(leaderboard) == 2
    assert leaderboard[0]["first_name"] == "Sarah"
    assert leaderboard[1]["first_name"] == "Emma"


def test_individual_challenge_leaderboard_returns_expected_order(module_scope_database, populated_database):
    # challenge_id = 1 is "let walk" from populated_database
    result = challenge_leaderboard_individual(1, limit=10)

    assert len(result) == 2

    # Sarah: walk 20 + bus 25 = 14.0 + 22.5 = 36.5
    assert result[0]["first_name"] == "Sarah"
    assert result[0]["last_name"] == "Chen"
    assert float(result[0]["points"]) == pytest.approx(36.5)
    assert float(result[0]["total_co2e_saved"]) == pytest.approx(36.5)
    assert result[0]["actions_count"] == 2

    # Emma: walk 2 + bus 4 + walk 10 + bus 15 + walk 7
    # = 1.4 + 3.6 + 7.0 + 13.5 + 4.9 = 30.4
    assert result[1]["first_name"] == "Emma"
    assert result[1]["last_name"] == "Watson"
    assert float(result[1]["points"]) == pytest.approx(30.4)
    assert float(result[1]["total_co2e_saved"]) == pytest.approx(30.4)
    assert result[1]["actions_count"] == 5


def test_group_challenge_leaderboard_returns_expected_order(function_scope_database):
    # Account IDs from defaultDatabase():
    # Emma = 1, James (moderator) = 2, Sarah = 3, John = 4, Jack = 5

    start_date = datetime.now()
    end_date = datetime.now() + timedelta(days=30)

    # Create an active group challenge as moderator James
    challenge_id = create_challenge(
        2,
        "Group",
        "Team Commute Challenge",
        start_date,
        end_date,
        "Log sustainable travel as a group",
    )

    # Group 1: John + Emma
    group_one_id = UserCreateGroup(4, "Eco Warriors")
    UserJoinGroup(1, group_one_id)
    join_challenge_group(challenge_id, group_one_id, 4)  # John is owner

    # Group 2: Sarah + Jack
    group_two_id = UserCreateGroup(3, "Green Movers")
    UserJoinGroup(5, group_two_id)
    join_challenge_group(challenge_id, group_two_id, 3)  # Sarah is owner

    # Log actions for group 1 total = 7.0 + 4.5 = 11.5
    log_action(1, "walk", "travel", 10, challenge_id, "group1_walk")
    log_action(4, "bus", "travel", 5, challenge_id, "group1_bus")

    # Log actions for group 2 total = 5.6 + 3.6 = 9.2
    log_action(3, "walk", "travel", 8, challenge_id, "group2_walk")
    log_action(5, "bus", "travel", 4, challenge_id, "group2_bus")

    result = challenge_leaderboard_group(challenge_id, limit=10)

    assert len(result) == 2

    # Group 1 should be first
    assert result[0]["group_id"] == group_one_id
    assert result[0]["group_name"] == "Eco Warriors"
    assert result[0]["member_count"] == 2
    assert float(result[0]["points"]) == pytest.approx(11.5)
    assert float(result[0]["average_points"]) == pytest.approx(5.75)
    assert float(result[0]["total_co2e_saved"]) == pytest.approx(11.5)
    assert result[0]["actions_count"] == 2

    # Group 2 should be second
    assert result[1]["group_id"] == group_two_id
    assert result[1]["group_name"] == "Green Movers"
    assert result[1]["member_count"] == 2
    assert float(result[1]["points"]) == pytest.approx(9.2)
    assert float(result[1]["average_points"]) == pytest.approx(4.6)
    assert float(result[1]["total_co2e_saved"]) == pytest.approx(9.2)
    assert result[1]["actions_count"] == 2


def test_individual_challenge_leaderboard_raises_for_inactive_challenge(function_scope_database):
    start_date = datetime.now() - timedelta(days=60)
    end_date = datetime.now() - timedelta(days=30)

    expired_challenge_id = create_challenge(
        2,
        "Personal",
        "Expired leaderboard challenge",
        start_date,
        end_date,
        "This challenge is over",
    )

    with pytest.raises(Exception):
        challenge_leaderboard_individual(expired_challenge_id, limit=10)