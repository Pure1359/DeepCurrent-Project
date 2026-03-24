import pytest
from datetime import datetime, timedelta
from database_fixture import *
from app.db_config import db_cursor
from app.services.badges import check_and_award_badges, get_user_badges
from app.services.users_service import create_user, create_account
from app.services.challenges import create_challenge, join_challenge_individual


def setup_user_with_streak(account_id, challenge_id, streak_days):
    # Directly insert ActionLog + ChallengeAction for each consecutive day
    # so we can simulate past submissions without depending on datetime.now()
    walk_action_type_id = None
    with db_cursor() as (connection, cursor):
        cursor.execute("SELECT actionType_id FROM ActionType WHERE actionName = %s AND category = %s", ("walk", "travel"))
        row = cursor.fetchone()
        walk_action_type_id = row["actionType_id"]

    with db_cursor() as (connection, cursor):
        for day_offset in range(streak_days):
            log_dt = (datetime.now() - timedelta(days=streak_days - 1 - day_offset)).replace(hour=8, minute=0, second=0, microsecond=0)
            quantity = 5
            co2e = round(quantity * 0.7, 3)
            cursor.execute(
                "INSERT INTO ActionLog(submitted_by, actionType_id, log_date, quantity, co2e_saved) VALUES (%s, %s, %s, %s, %s)",
                (account_id, walk_action_type_id, log_dt.strftime("%Y-%m-%d %H:%M:%S"), quantity, co2e)
            )
            log_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO ChallengeAction(challenge_id, group_id, log_id, point_awarded) VALUES (%s, %s, %s, %s)",
                (challenge_id, None, log_id, co2e)
            )


def create_test_user_and_challenge(username, email):
    user_id = create_user("Test", username, email, "2000-01-01", "student", "Computer Science", None)
    import bcrypt
    hashed = bcrypt.hashpw(b"testpass123", bcrypt.gensalt())
    create_account(user_id, username, hashed, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    with db_cursor() as (connection, cursor):
        cursor.execute("SELECT account_id FROM Accounts WHERE username = %s", (username,))
        account_id = cursor.fetchone()["account_id"]

    moderator_id = 2  # jmiller from defaultDatabase()
    start = datetime.now() - timedelta(days=200)
    end = datetime.now() + timedelta(days=30)
    challenge_id = create_challenge(moderator_id, "Personal", f"Test Challenge for {username}", start, end, "test rules")
    join_challenge_individual(challenge_id, account_id)

    return account_id, challenge_id


def test_no_badges_without_streak(function_scope_database):
    account_id, challenge_id = create_test_user_and_challenge("nostreak", "nostreak@test.com")

    newly_awarded = check_and_award_badges(account_id)

    assert newly_awarded == []
    badges = get_user_badges(account_id)
    assert len(badges) == 0


def test_week_badge_awarded_after_7_day_streak(function_scope_database):
    account_id, challenge_id = create_test_user_and_challenge("user7day", "user7day@test.com")
    setup_user_with_streak(account_id, challenge_id, 7)

    newly_awarded = check_and_award_badges(account_id)

    assert "week" in newly_awarded
    badges = get_user_badges(account_id)
    badge_types = [b["badge_type"] for b in badges]
    assert "week" in badge_types
    assert "month" not in badge_types


def test_month_badge_awarded_after_30_day_streak(function_scope_database):
    account_id, challenge_id = create_test_user_and_challenge("user30day", "user30day@test.com")
    setup_user_with_streak(account_id, challenge_id, 30)

    newly_awarded = check_and_award_badges(account_id)

    assert "week" in newly_awarded
    assert "month" in newly_awarded
    badges = get_user_badges(account_id)
    badge_types = [b["badge_type"] for b in badges]
    assert "week" in badge_types
    assert "month" in badge_types
    assert "super" not in badge_types


def test_super_badge_awarded_after_60_day_streak(function_scope_database):
    account_id, challenge_id = create_test_user_and_challenge("user60day", "user60day@test.com")
    setup_user_with_streak(account_id, challenge_id, 60)

    newly_awarded = check_and_award_badges(account_id)

    assert "week" in newly_awarded
    assert "month" in newly_awarded
    assert "super" in newly_awarded
    badges = get_user_badges(account_id)
    badge_types = [b["badge_type"] for b in badges]
    assert "super" in badge_types
    assert "legend" not in badge_types


def test_legend_badge_awarded_after_180_day_streak(function_scope_database):
    account_id, challenge_id = create_test_user_and_challenge("user180day", "user180day@test.com")
    setup_user_with_streak(account_id, challenge_id, 180)

    newly_awarded = check_and_award_badges(account_id)

    assert set(newly_awarded) == {"week", "month", "super", "legend"}
    badges = get_user_badges(account_id)
    badge_types = [b["badge_type"] for b in badges]
    assert set(badge_types) == {"week", "month", "super", "legend"}


def test_no_duplicate_badges_on_repeated_calls(function_scope_database):
    account_id, challenge_id = create_test_user_and_challenge("usernodupe", "usernodupe@test.com")
    setup_user_with_streak(account_id, challenge_id, 7)

    check_and_award_badges(account_id)
    newly_awarded_second = check_and_award_badges(account_id)

    assert newly_awarded_second == []
    badges = get_user_badges(account_id)
    assert len(badges) == 1
    assert badges[0]["badge_type"] == "week"


def test_broken_streak_does_not_award_badge(function_scope_database):
    account_id, challenge_id = create_test_user_and_challenge("brokenstreak", "brokenstreak@test.com")

    # 6 days, then skip a day, then 6 more — max streak is 6, not 12
    walk_action_type_id = None
    with db_cursor() as (connection, cursor):
        cursor.execute("SELECT actionType_id FROM ActionType WHERE actionName = %s AND category = %s", ("walk", "travel"))
        walk_action_type_id = cursor.fetchone()["actionType_id"]

    with db_cursor() as (connection, cursor):
        days = list(range(13, 7, -1)) + list(range(5, -1, -1))  # skip day 6 and 7
        for day_offset in days:
            log_dt = (datetime.now() - timedelta(days=day_offset)).replace(hour=8, minute=0, second=0, microsecond=0)
            cursor.execute(
                "INSERT INTO ActionLog(submitted_by, actionType_id, log_date, quantity, co2e_saved) VALUES (%s, %s, %s, %s, %s)",
                (account_id, walk_action_type_id, log_dt.strftime("%Y-%m-%d %H:%M:%S"), 5, 3.5)
            )
            log_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO ChallengeAction(challenge_id, group_id, log_id, point_awarded) VALUES (%s, %s, %s, %s)",
                (challenge_id, None, log_id, 3.5)
            )

    newly_awarded = check_and_award_badges(account_id)

    assert newly_awarded == []
    badges = get_user_badges(account_id)
    assert len(badges) == 0
