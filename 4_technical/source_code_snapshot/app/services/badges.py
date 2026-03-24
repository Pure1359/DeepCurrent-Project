from app.db_config import db_cursor
from datetime import datetime, date

# Badge thresholds: number of consecutive days required -> badge name
BADGE_THRESHOLDS = [
    (7,   "week"),
    (30,  "month"),
    (60,  "super"),
    (180, "legend"),
]

def get_max_streak(dates):
    # Given a list of date objects, return the longest consecutive day streak
    if not dates:
        return 0

    sorted_dates = sorted(set(dates), reverse=True)
    best = 1
    current = 1

    for i in range(1, len(sorted_dates)):
        diff = (sorted_dates[i - 1] - sorted_dates[i]).days
        if diff == 1:
            current += 1
            if current > best:
                best = current
        else:
            current = 1

    return best


def check_and_award_badges(account_id):
    # Called after every successful challenge submission.
    # Checks if the user has earned any new badges based on their challenge streak.
    with db_cursor() as (connection, cursor):

        # Get all distinct days the user has submitted to any challenge
        cursor.execute(
            """
            SELECT DISTINCT DATE(al.log_date) AS action_date
            FROM ChallengeAction ca
            JOIN ActionLog al ON al.log_id = ca.log_id
            WHERE al.submitted_by = %s
            ORDER BY action_date DESC
            """,
            (account_id,),
        )
        rows = cursor.fetchall()
        action_dates = [date.fromisoformat(r["action_date"]) for r in rows]

        streak = get_max_streak(action_dates)

        # Check which badges the user already has
        cursor.execute(
            "SELECT badge_type FROM UserBadge WHERE account_id = %s",
            (account_id,),
        )
        already_has = {r["badge_type"] for r in cursor.fetchall()}

        # Award any new badges the streak qualifies for
        newly_awarded = []
        now = datetime.now()

        for days_needed, badge_type in BADGE_THRESHOLDS:
            if streak >= days_needed and badge_type not in already_has:
                cursor.execute(
                    "INSERT INTO UserBadge (account_id, badge_type, awarded_at) VALUES (%s, %s, %s)",
                    (account_id, badge_type, now),
                )
                newly_awarded.append(badge_type)

        return newly_awarded


def get_user_badges(account_id):
    with db_cursor() as (connection, cursor):
        cursor.execute(
            "SELECT badge_type, awarded_at FROM UserBadge WHERE account_id = %s ORDER BY awarded_at ASC",
            (account_id,),
        )
        return cursor.fetchall()
