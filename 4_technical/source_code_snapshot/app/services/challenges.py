from app.db_config import db_cursor
from app.services.auth import verify_session_role
from flask import abort
from custom_error.Challenge_Exception import InvalidChallengeDate, ChallengeIdNotFound, UserAlreadyJoinChallenge, GroupAlreadyJoinChallenge
from custom_error.Group_Exception import *
from datetime import datetime

def _parse_date(value):
    if not isinstance(value, str):
        return value
    value = value.split(".")[0]
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

def require_active_challenge(cursor, challenge_id: int) -> dict[str, any]:
    cursor.execute(
        "SELECT challenge_id, start_date, end_date, title, challenge_type, rules FROM Challenge WHERE challenge_id = %s",
        (challenge_id,),
    )
    challenge = cursor.fetchone()

    # Check if challenge exists
    if challenge is None:
        raise ChallengeIdNotFound(f"The Challenge with ID: {challenge_id} does not exists in database")

    start_date = _parse_date(challenge["start_date"])
    end_date = _parse_date(challenge["end_date"])
    now = datetime.now()

    # Check if challenge is active
    if start_date and start_date > now:
        raise InvalidChallengeDate("The challenge is currently not active")
    if end_date and end_date < now:
        raise InvalidChallengeDate("The challenge is currently not active")

    return challenge

def create_challenge(created_by, challenge_type, title, start_date, end_date, rules):
    sql = """INSERT INTO Challenge (created_by, challenge_type, title, start_date, end_date, rules) 
            VALUES (%s, %s, %s, %s, %s, %s)"""
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (created_by, challenge_type, title, start_date, end_date, rules))
        return cursor.lastrowid

#Add user and challenge to the individualParticipation table
def join_challenge_individual(challenge_id, account_id):
    current_time = datetime.now()
    #check to see if the challenge is expired or not
    check_challenge = """SELECT start_date, end_date FROM Challenge WHERE challenge_id = %s"""
    check_duplicate_join = """SELECT challenge_id, account_id FROM IndividualParticipation WHERE challenge_id = %s AND account_id = %s"""
    sql = """INSERT INTO IndividualParticipation (challenge_id, account_id, joined_date) VALUES(%s, %s, %s)"""

    with db_cursor() as (connection, cursor):
        #check to see if the user already joined
        cursor.execute(check_duplicate_join, (challenge_id, account_id))
        if (cursor.fetchone() is not None):
            raise UserAlreadyJoinChallenge("The user already participate in this challenge")

        cursor.execute(check_challenge, (challenge_id,))
        check_challenge_result = cursor.fetchone()
        if (check_challenge_result is None):
            raise ChallengeIdNotFound(f"The Challenge with ID: {challenge_id} does not exists in database" )
        elif(check_challenge_result is not None):
            start_date = check_challenge_result["start_date"]
            end_date = check_challenge_result["end_date"]

            start_date = _parse_date(start_date)
            end_date = _parse_date(end_date)

            if (start_date > current_time or end_date < current_time):
                raise InvalidChallengeDate("The challenge is currently not active")


        #if this is reached then user is not already in the challenge and the challenge exists and is still active
        cursor.execute(sql, (challenge_id, account_id, current_time))
    
#Add group and challenge to the GroupParticipation table
def join_challenge_group(challenge_id, group_id, account_id):
    
    current_time = datetime.now()
    #check if you are the group owner
    check_owner = """SELECT * FROM UserGroup WHERE group_id = %s AND group_creator_id = %s"""
    #check if challenge exists
    check_challenge = """SELECT start_date, end_date FROM Challenge WHERE challenge_id = %s"""
    #check if group already join a challenge
    check_duplicate_join = """SELECT * FROM GroupParticipation WHERE challenge_id = %s AND group_id = %s"""
    sql = """INSERT INTO GroupParticipation(challenge_id, group_id, joined_date) VALUES(%s, %s, %s)"""
    with db_cursor() as (connection, cursor):

        cursor.execute(check_owner, (group_id, account_id))
        result = cursor.fetchone()
        if result is None:
            raise GroupPermissionError("Normal member can not tell which challenge the group can join")
        
        cursor.execute(check_challenge, (challenge_id,))
        check_challenge = cursor.fetchone()
        if check_challenge is None:
            raise ChallengeIdNotFound(f"The Challenge with ID: {challenge_id} does not exists in database")
        
        cursor.execute(check_duplicate_join, (challenge_id, group_id))
        check_duplicate_join = cursor.fetchone()
        if check_duplicate_join is not None:
            raise GroupAlreadyJoinChallenge("The group already participate in this challenge")
    
        if check_challenge is not None:
            #check if challenge is active or not
            start_date = _parse_date(check_challenge["start_date"])
            end_date = _parse_date(check_challenge["end_date"])

            if (start_date > current_time or end_date < current_time):
                raise InvalidChallengeDate("The challenge is currently not active")
        
        cursor.execute(sql, (challenge_id, group_id, current_time))
            

def get_all_active_challenges():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = """SELECT c.challenge_id, c.challenge_type, c.title, c.start_date, c.end_date, c.rules, c.created_by
             FROM Challenge c
             WHERE c.start_date <= %s AND c.end_date >= %s
             ORDER BY c.end_date ASC"""
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (now, now))
        return cursor.fetchall()

def get_challenge_for_user(account_id):
    sql = """SELECT challenge_id FROM IndividualParticipation WHERE account_id = %s"""
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (account_id,))
        return cursor.fetchall()

def get_user_active_challenges_by_category(account_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = """SELECT Challenge.challenge_id, Challenge.title, Challenge.challenge_type, Challenge.start_date, Challenge.end_date
             FROM Challenge
             JOIN IndividualParticipation ON IndividualParticipation.challenge_id = Challenge.challenge_id
             WHERE IndividualParticipation.account_id = %s
               AND Challenge.start_date <= %s
               AND Challenge.end_date >= %s
             UNION
             SELECT Challenge.challenge_id, Challenge.title, Challenge.challenge_type, Challenge.start_date, Challenge.end_date
             FROM Challenge
             JOIN GroupParticipation ON GroupParticipation.challenge_id = Challenge.challenge_id
             JOIN AccountGroup ON AccountGroup.group_id = GroupParticipation.group_id
             WHERE AccountGroup.account_id = %s
               AND Challenge.start_date <= %s
               AND Challenge.end_date >= %s
             ORDER BY end_date ASC"""
    with db_cursor() as (connection, cursor):
        cursor.execute(sql, (account_id, now, now, account_id, now, now))
        return cursor.fetchall()

def challenge_leaderboard_individual(challenge_id: int, limit: int = 10):
    with db_cursor() as (_connection, cursor):
        require_active_challenge(cursor, challenge_id)
        cursor.execute(
            """
            SELECT
                a.account_id,
                a.username,
                u.first_name,
                u.last_name,
                COALESCE(SUM(ca.point_awarded), 0) AS points,
                COALESCE(SUM(CASE WHEN ca.log_id IS NOT NULL THEN al.co2e_saved ELSE 0 END), 0) AS total_co2e_saved,
                COUNT(DISTINCT ca.log_id) AS actions_count
            FROM IndividualParticipation ip
            INNER JOIN Accounts a ON ip.account_id = a.account_id
            INNER JOIN Users u ON a.user_id = u.user_id
            LEFT JOIN ActionLog al
                ON al.submitted_by = a.account_id
            LEFT JOIN ChallengeAction ca
                ON ca.log_id = al.log_id
                AND ca.challenge_id = ip.challenge_id
                AND ca.group_id IS NULL
            LEFT JOIN Evidence e ON e.log_id = al.log_id
            LEFT JOIN Decision d ON d.evidence_id = e.evidence_id
            WHERE ip.challenge_id = %s
              AND d.decision_status IN ('approved', 'accepted')
            GROUP BY a.account_id, a.username, u.first_name, u.last_name
            ORDER BY points DESC, total_co2e_saved DESC, actions_count DESC, a.account_id ASC
            LIMIT %s
            """,
            (challenge_id, limit),
        )
        return cursor.fetchall()

def challenge_leaderboard_group(challenge_id: int, limit: int = 10):
    with db_cursor() as (_connection, cursor):
        require_active_challenge(cursor, challenge_id)
        cursor.execute(
            """
            SELECT
                ug.group_id,
                ug.group_name,
                ug.group_creator_id,
                (
                    SELECT COUNT(*)
                    FROM AccountGroup ag
                    WHERE ag.group_id = ug.group_id
                ) AS member_count,
                COALESCE(SUM(ca.point_awarded), 0) AS points,
                COALESCE(SUM(al.co2e_saved), 0) AS total_co2e_saved,
                COUNT(DISTINCT ca.log_id) AS actions_count,
                COALESCE(SUM(ca.point_awarded), 0) * 1.0 /
                    NULLIF((
                        SELECT COUNT(*)
                        FROM AccountGroup ag2
                        WHERE ag2.group_id = ug.group_id
                    ), 0) AS average_points
            FROM GroupParticipation gp
            INNER JOIN UserGroup ug ON gp.group_id = ug.group_id
            LEFT JOIN ChallengeAction ca
                ON ca.challenge_id = gp.challenge_id
                AND ca.group_id = gp.group_id
            LEFT JOIN ActionLog al ON ca.log_id = al.log_id
            LEFT JOIN Evidence e ON e.log_id = al.log_id
            LEFT JOIN Decision d ON d.evidence_id = e.evidence_id
            WHERE gp.challenge_id = %s
              AND d.decision_status IN ('approved', 'accepted')
            GROUP BY ug.group_id, ug.group_name, ug.group_creator_id
            ORDER BY average_points DESC, points DESC, total_co2e_saved DESC, ug.group_id ASC
            LIMIT %s
            """,
            (challenge_id, limit),
        )
        return cursor.fetchall()